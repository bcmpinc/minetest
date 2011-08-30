from socket import socket, AF_INET, SOCK_DGRAM
from struct import Struct
import sys
import codecs

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
    
    s32 = __wrapper("!i")
    u32 = __wrapper("!I")
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
    def f1000(self, value=None):
        if value is None:
            return self.s32()/1000.0
        else:
            return self.s32(int(value*1000))

class Minetest:
    protocol_id = 0x4f457403
    peer = 0
    seqnr = 65500
    splitmap = {}
    
    def basic(self, channel=0):
        p = Package()
        p.u32(self.protocol_id)
        p.u16(self.peer)
        p.u8(channel)
        p.send = lambda : self.udp.send(p.buffer)
        #p.send = lambda : sys.stdout.write("[out %d/%db]" % (self.udp.send(p.buffer), len(p.buffer)))
        return p

    def reliable(self):
        p = self.basic()
        p.u8(3) # reliable
        p.u16(self.seqnr) # sequence
        self.seqnr = (self.seqnr + 1) & 0xffff
        return p

    def __init__(self, hostname='127.0.0.1', port=30000):
        self.udp = socket(AF_INET,SOCK_DGRAM)
        self.udp.connect((hostname, port))
        
    def connect(self):
        print "Connecting"
        p = self.reliable()
        p.u8(1) # original
        p.send()
        while self.peer==0:
            self.wait()
        print "Connected"

    def init(self, name, pwd):
        print "Logging in as", name
        from hashlib import sha1
        from base64 import b64encode
        pwd = b64encode(sha1(pwd).digest())
        p = self.reliable()
        p.u8(1) # original
        p.u16(0x10) # init
        p.u8(20) # server format
        p.player_name(name)
        p.password(pwd)
        p.u16(1) # protocol version
        print repr(p.buffer), p.offset
        p.send()

    def init2(self):
        p = self.reliable()
        p.u8(1) # original
        p.u16(0x11) # init2
        p.send()        
        
    def disconnect(self):
        print "Disconnecting"
        p = self.basic()
        p.u8(0) # control
        p.u8(3) # disconnect
        p.send()

    def ack(self, channel, num):
        p = self.basic(channel)
        p.u8(0) # control
        p.u8(0) # acknowledge
        p.u16(num)
        p.send()
        print "[acknowledged %d]" % num, 
        
    def wait(self):
        p = Package(self.udp.recv(4096))
        print "Rcv msg %db," % len(p.buffer),

        # basic
        protocol_id = p.u32()
        peer = p.u16()
        channel = p.u8()
        if protocol_id != self.protocol_id:
            print "with invalid protocol:", protocol_id, "!=", self.protocol_id
            return
        print "c%d" % channel, 
        
        type = p.u8()
        if type==3: # reliable
            seq = p.u16()
            print "reliable with seq =", seq,
            self.ack(channel, seq) # acknowledge receipt
            type = p.u8()

        if type==2: # splitted
            seqnum=p.u16()
            chunk_count=p.u16()
            chunk_num=p.u16()
            print "of splitted-type #%d - %d/%d" % (seqnum,chunk_num+1,chunk_count)
            if not seqnum in self.splitmap:
                self.splitmap[seqnum]=[None]*chunk_count
            if self.splitmap[seqnum][chunk_num] is None:
                self.splitmap[seqnum][chunk_num] = p.remains()
                if None in self.splitmap[seqnum]:
                    return
                else:
                    p = Package("".join(self.splitmap[seqnum]))
                    del self.splitmap[seqnum]
                    print "Completed split package (%db)" % len(p.buffer),
                    type = 1

        if type==0: # control
            print "of control-type",
            ctype = p.u8()
            if ctype==0: # ACK
                seqnum = p.u16()
                print "acknowledging", seqnum
            elif ctype==1: # set peer id
                self.peer = p.u16()
                print "setting peer id", self.peer
            elif ctype==2: # ping
                print "pinging"
            elif ctype==3: # disconnect
                print "disconnecting"
            else:
                print "with unkown type", ctype
        elif type==1: # original
            print "of original-type",
            cmd = p.u16()
            if cmd==0x10: # init
                version = p.u8()
                print "init, version =", version
                self.init2()
            elif cmd==0x24: # player info
                print "playerinfo:"
                while p.available():
                    id = p.u16()
                    name = p.player_name()
                    print "\t",id, "=", name.strip()
            elif cmd==0x27: # player inventory
                print "player inventory"
            elif cmd==0x28: # object data (player pos's & other objects)
                print "object data"
            elif cmd==0x29: # server time
                time = p.u16()
                print "time =", time
            elif cmd==0x30: # chat message
                length = p.u16()
                print codecs.getdecoder("utf_16_be")(p.remains())
            elif cmd==0x34: # move player to pos
                x = p.f1000()/10
                y = p.f1000()/10
                z = p.f1000()/10
                print "moved to (%.2f,%.2f,%.2f)" % (x,y,z)
                #pitch = p.f1000()
                #yaw = p.f1000()
                #print "moved to (%.2f,%.2f,%.2f) pitch=%.2f yaw=%.2f" % (x,y,z,pitch,yaw)
            else:
                print "unknown command", hex(cmd)
            return
        else:
            print "of unknown type", type

m = Minetest()
m.connect()
m.init("test","test")
try:
    while True:
        m.wait()
except:
    m.disconnect()
    raise
    
