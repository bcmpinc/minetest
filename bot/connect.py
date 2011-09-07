from socket import socket, AF_INET, SOCK_DGRAM, timeout
from struct import Struct
import sys
import codecs
import zlib
import sqlite3

class Package:
    def __wrapper(type):
        type = Struct(type)
        def token(self, value=None):
            if value is None:
                r = type.unpack_from(self.buffer, self.offset)[0]
                self.offset += type.size
                return r
            else:
                self.buffer += type.pack(value)
                self.offset += type.size
                return self
        return token
    def __vwrapper(type):
        type = Struct(type)
        def token(self, *value):
            if len(value) == 0:
                r = type.unpack_from(self.buffer, self.offset)
                self.offset += type.size
                return r
            else:
                if len(value)==1:
                    value = value[0]
                self.buffer += type.pack(*value)
                self.offset += type.size
                return self
        return token
    
    s32 = __wrapper("!i")
    v3s32 = __vwrapper("!iii")
    u32 = __wrapper("!I")
    s16 = __wrapper("!h")
    v3s16 = __vwrapper("!hhh")
    u16 = __wrapper("!H")
    u8  = __wrapper("!B")
    player_name = __wrapper("!20s")
    password = __wrapper("!28s")
    def __init__(self, buffer=""):
        self.buffer = buffer
        self.offset = 0
    def available(self):
        return len(self.buffer) > self.offset
    def remains(self):
        return self.buffer[self.offset:]
    def append(self,buf):
        self.buffer+=buf
        self.offset+=len(buf)
        return self
    def obtain(self,length):
        self.offset+=length
        return self.buffer[self.offset-length:self.offset]
    def f1000(self, value=None):
        if value is None:
            return self.s32()/1000.0
        else:
            return self.s32(int(value*1000))
    def wstring(self, value=None):
        if value is None:
            length = self.u16()
            return codecs.getdecoder("utf_16_be")(self.obtain(length*2))[0]
        else:
            value = codecs.getencoder("utf_16_be")(value)[0]
            self.u16(len(value)/2)
            self.append(value)
            return self
        

class __self:
    def __getattr__(self, name):
        return globals()[name]
    def __setattr__(self, name, value):
        globals()[name]=value

class Node:
    """These are stored in a complicated way."""
    def __init__(self, p0, p1, p2):
        if p0<0x80:
            self.content = p0
        else:
            self.content = (p0<<4) + (p2>>4)

nodecount = 16**3
def wrap_node_data(data):
    def nodes(x,y,z):
        i = x + y*16 + z*256
        return Node(ord(data[i]), ord(data[i+nodecount]), ord(data[i+2*nodecount]))
    return nodes

self = __self()
protocol_id = 0x4f457403
peer = 0
seqnr = 65500
splitmap = {}
pos = None # position (x,y,z)-tuple
connected = False

def basic(channel=0):
    p = Package()
    p.u32(self.protocol_id)
    p.u16(self.peer)
    p.u8(channel)
    p.send = lambda : self.udp.send(p.buffer)
    #p.send = lambda : sys.stdout.write("[out %d/%db]" % (self.udp.send(p.buffer), len(p.buffer)))
    return p

def reliable():
    # TODO: cache the message and retransmit if not acknowledged
    p = self.basic()
    p.u8(3) # reliable
    p.u16(self.seqnr) # sequence
    self.seqnr = (self.seqnr + 1) & 0xffff
    return p

def connect(hostname='localhost', port=30000):
    print "Connecting"
    self.udp = socket(AF_INET,SOCK_DGRAM)
    self.udp.connect((hostname, port))
    self.udp.settimeout(0.2)
    
    p = self.reliable()
    p.u8(1) # original
    p.send()
    # wait for peer id to be assigned.
    while self.peer==0:
        self.wait()

    self.conn = sqlite3.connect("cache-%s-%d.db"%(hostname,port))
    self.cur = self.conn.cursor()
    self.cur.execute('''create table if not exists blocks (x INTEGER, y INTEGER, z INTEGER, data BLOB, PRIMARY KEY(x,y,z))''')

    print "Connected"
    self.connected = True
    __handle.connected()

def get_node(pos):
    ref = self.cur.execute('''SELECT data FROM blocks WHERE x=? AND y=? AND z=?''', pos)
    f = None
    for r in ref:
        f = wrap_node_data(r[0])
    return f

# message sending
def init(name, pwd):
    print "Logging in as", name
    self.name = name
    from hashlib import sha1
    from base64 import b64encode
    pwd = b64encode(sha1(name+pwd).digest())
    p = self.reliable()
    p.u8(1) # original
    p.u16(0x10) # init
    p.u8(20) # server format
    p.player_name(name)
    p.password(pwd)
    p.u16(1) # protocol version
    p.send()

def init2():
    p = self.reliable()
    p.u8(1) # original
    p.u16(0x11) # init2
    p.send()

def setpos((x,y,z), pitch, yaw):
    p = self.basic()
    p.u8(1) # original
    p.u16(0x23) # set player position
    # position
    p.s32(int(x*1000))
    p.s32(int(y*1000))
    p.s32(int(z*1000))
    # speed
    p.s32(0)
    p.s32(0)
    p.s32(0)
    p.s32(int(pitch*100))
    p.s32(int(yaw*100))
    print "Setting position to", x, y, z
    p.send()        
    __handle.move((x,y,z))

def chat(msg):
    p = self.reliable()
    p.u8(1) # original
    p.u16(0x32) # chat message
    print msg
    __handle.echo("<%s> %s"%(self.name, msg))
    p.wstring(msg)
    p.send()
    
def disconnect():
    print "Disconnecting"
    if hasattr(self, "conn"):
        self.conn.commit()
    self.connected = False
    __handle.disconnect()
    p = self.basic()
    p.u8(0) # control
    p.u8(3) # disconnect
    p.send()

def ack(channel, num):
    p = self.basic(channel)
    p.u8(0) # control
    p.u8(0) # acknowledge
    p.u16(num)
    p.send()
    # print "[acknowledged %d]" % num,

def got_blocks(pos_array):
    p = self.reliable()
    p.u8(1) # original
    p.u16(0x24) # gotblocks
    p.u8(len(pos_array)) # length
    for i in pos_array:
        p.v3s16(i) # (x,y,z)
    p.send()

def deleted_blocks(pos_array):
    p = self.reliable()
    p.u8(1) # original
    p.u16(0x25) # deletedblocks
    p.u8(len(pos_array)) # length
    for i in pos_array:
        p.v3s16(i) # (x,y,z)
    p.send()

# handlers
class __proxy:
    handlers = {}
    def __getattr__(self, name):
        self.name = name
        return self
    def __call__(self, *args):
        if self.name in self.handlers:
            for i in self.handlers[self.name]:
                i(*args)
__handle = __proxy()

def install_handler(handler):
    print "Installing handler: ", handler.__class__.__name__
    for i in dir(handler):
        if not i.startswith('_'):
            f = getattr(handler,i)
            if callable(f):
                print "\t%s" % i
                if not i in __handle.handlers:
                    __handle.handlers[i] = []
                __handle.handlers[i].append(f)

# Package reading and handling.

def wait(*args):
    try:
        p = Package(self.udp.recv(4096))
    except timeout:
        return
    
    msg = "Rcv msg %db," % len(p.buffer)

    # basic
    protocol_id = p.u32()
    peer = p.u16()
    channel = p.u8()
    if protocol_id != self.protocol_id:
        print msg, "with invalid protocol:", protocol_id, "!=", self.protocol_id
        return
    msg += " c%d" % channel
    
    type = p.u8()
    if type==3: # reliable
        # TODO: prevent receiving duplicates
        # TODO: make sure these are handled in-order.
        seq = p.u16()
        msg += " reliable with seq = %d" % seq
        self.ack(channel, seq) # acknowledge receipt
        type = p.u8()

    if type==2: # splitted
        seqnum=p.u16()
        chunk_count=p.u16()
        chunk_num=p.u16()
        #print msg, "of splitted-type #%d - %d/%d" % (seqnum,chunk_num+1,chunk_count)
        if not seqnum in self.splitmap:
            self.splitmap[seqnum]=[None]*chunk_count
        if self.splitmap[seqnum][chunk_num] is None:
            self.splitmap[seqnum][chunk_num] = p.remains()
            if None in self.splitmap[seqnum]:
                return
            else:
                p = Package("".join(self.splitmap[seqnum]))
                del self.splitmap[seqnum]
                msg = "Completed split package (%db)" % len(p.buffer)
                type = 1

    if type==0: # control
        msg += " of control-type"
        ctype = p.u8()
        if ctype==0: # ACK
            seqnum = p.u16()
            #print msg, "acknowledging", seqnum
        elif ctype==1: # set peer id
            self.peer = p.u16()
            print msg, "setting peer id", self.peer
        elif ctype==2: # ping
            #print msg, "pinging"
            pass
        elif ctype==3: # disconnect
            print msg, "disconnecting"
        else:
            print msg, "with unkown type", ctype
    elif type==1: # original
        msg += " of original-type"
        cmd = p.u16()
        if cmd==0x10: # init
            version = p.u8()
            print msg, "init, version =", version
            if version != 20:
                raise AssertionError("Server version is not 20.")
            self.init2()
            __handle.logged_in()
        elif cmd==0x20: # block data
            # block node coordinates
            pos = p.v3s16() 
            flags = p.u8()
            print msg, "block data @ (%d,%d,%d) flags=%s" % (pos+(bin(flags),))
            dec = zlib.decompressobj()
            data = dec.decompress(p.remains())
            if len(data) != nodecount * 3:
                raise AssertionError("block data size mismatch: %d != %d" % (len(data), nodecount * 3))
            self.cur.execute('''INSERT OR REPLACE INTO blocks (x,y,z,data) VALUES (?,?,?,?);''', pos+(buffer(data),))
            __handle.blockdata(pos,wrap_node_data(data))
            p = Package(dec.unused_data)
            
        elif cmd==0x21: # add node
            # block node coordinates
            pos = p.v3s16()
            print msg, "add node @ (%d,%d,%d)" % pos
        elif cmd==0x22: # remove node
            # block node coordinates
            pos = p.v3s16()
            print msg, "remove node @ (%d,%d,%d)" % pos
        elif cmd==0x24: # player info
            print msg, "playerinfo:"
            pi = {}
            while p.available():
                id = p.u16()
                name = p.player_name().strip()
                print "\t",id, "=", name
                pi[id] = name
            __handle.player_info(pi)
        elif cmd==0x27: # player inventory
            print msg, "player inventory"
        elif cmd==0x28: # object data (player pos's & other objects)
            players = p.u16()
            pd={}
            #print msg, "object data"
            for i in xrange(players):
                id = p.u16()
                pos = tuple([i/1000.0 for i in p.v3s32()])
                speed = tuple([i/1000.0 for i in p.v3s32()])
                pitch = p.s32()/1000.0
                yaw = p.s32()/1000.0
                pd[id]=(pos,speed,pitch,yaw)
                #print "\t",id,":",pd[id]
            __handle.player_data(pd)
            blocks = p.u16()
            #for i in xrange(blocks):
                #pos = p.v3s16()
                # {block objects}?
            pass
        elif cmd==0x29: # server time
            time = p.u16()
            print msg, "time =", time
            __handle.time(time)
        elif cmd==0x30: # chat message
            chat = p.wstring()
            print chat
            __handle.chat(chat)
        elif cmd==0x31: # add & remove active objects
            try:
                print msg, "active objects:"
                rem_cnt = p.u16()
                for i in xrange(rem_cnt):
                    rem_id = p.u16()
                    print "\tremove %d" % rem_id
                msg += " add"
                add_cnt = p.u16()
                for i in xrange(add_cnt):
                    add_id = p.u16()
                    objtype = p.u8()
                    length = p.u16()
                    data = p.obtain(length)
                    print "\tadd %d: type=%d, data=%s" % (add_id, objtype, repr(data))
            except:
                print >>sys.stderr, "Something went wrong parsing active objects"
        elif cmd==0x33: # tell hp
            hp = p.u8()
            print msg, "hp =", hp
            __handle.hp(hp)
        elif cmd==0x34: # move player to pos
            x = p.f1000()/10
            y = p.f1000()/10
            z = p.f1000()/10
            print msg, "moved to (%.2f,%.2f,%.2f)" % (x,y,z)
            __handle.move((x,y,z))
            __handle.setpos((x,y,z))
            self.pos = (x,y,z) # update local pos variable afterwards
            
            #pitch = p.f1000()
            #yaw = p.f1000()
            #print "moved to (%.2f,%.2f,%.2f) pitch=%.2f yaw=%.2f" % (x,y,z,pitch,yaw)
        elif cmd==0x35: # access denied
            error = p.wstring()
            print >>sys.stderr, msg, "access denied:", error
        else:
            print >>sys.stderr, msg, "unknown command", hex(cmd)
        return
    else:
        print >>sys.stderr, msg, "of unknown type", type

def protect(fn):
    """Protects functions from being called when disconnecting."""
    def safe(*args):
        if self.connected:
            fn(*args)
    return safe

