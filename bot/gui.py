from Tkinter import *
import thread
import sys
import traceback
import connect as m
import math

def lint(x):
    return int(math.floor(x))

class App:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()
        self.w = Label(self.frame, text="Hello world!")
        self.w.pack()
        self.b = Button(self.frame, text="Ok", command=master.destroy)
        self.b.pack()

class ShopKeeper:
    def setpos(self,(x,y,z)):
        #m.setpos((10,10.5,10),0,0)
        #m.chat("Shop open!")
        pass
    def disconnect(self):
        #m.chat("Shop closed!")
        pass
    def chat(self, msg):
        if msg[0]==u'<':
            (name, msg) = msg.split(u'> ')
            name=str(name[1:])
            msg = msg.strip()
            print repr(name),repr(msg)
            if not name in m.player_id:
                m.chat("I can't help you %s." % name)
                return
            id = m.player_id[name]
            if msg == u'summon shop':
                data = m.player_data[id]
                m.setpos(data[0],0,0)
            
class Chatbox:
    def __init__(self, master):
        self.frame = Frame(master, borderwidth=1, relief=RAISED)
        self.frame.pack(fill = BOTH)
        self.list = Listbox(self.frame, takefocus=False, width=80)
        self.list.pack(fill = BOTH)
        self.entry = Entry(self.frame)
        self.entry.pack(fill = X)
        self.entry.bind('<Return>', self.__send)
    @m.protect
    def chat(self, msg):
        for i in msg.split("\n"):
            self.list.insert(END, i)
            if self.list.size() > 10:
                self.list.delete(0)
    echo = chat
    def __send(self, event):
        m.chat(self.entry.get())
        self.entry.delete(0,END)

class Position:
    def __init__(self, master):
        self.frame = Frame(master, borderwidth=1, relief=RAISED)
        self.frame.pack(fill = BOTH, side = LEFT)
        Label(self.frame, text="X:").grid(column=0,row=0)
        self.x = Entry(self.frame)
        self.x.grid(column=1,row=0)
        self.x.bind('<Return>', self.__move)
        Label(self.frame, text="Y:").grid(column=0,row=1)
        self.y = Entry(self.frame)
        self.y.grid(column=1,row=1)
        self.y.bind('<Return>', self.__move)
        Label(self.frame, text="Z:").grid(column=0,row=2)
        self.z = Entry(self.frame)
        self.z.grid(column=1,row=2)
        self.z.bind('<Return>', self.__move)
    def move(self, pos):
        self.x.delete(0, END)
        self.x.insert(0, str(pos[0]))
        self.y.delete(0, END)
        self.y.insert(0, str(pos[1]))
        self.z.delete(0, END)
        self.z.insert(0, str(pos[2]))
    def __move(self, event):
        try:
            pos=(float(self.x.get()),float(self.y.get()),float(self.z.get()))
            m.setpos(pos,0,0)
        except:
            print >>sys.stderr, "Failed parsing."
            pass

tilecolors={
       -1:'#000000', # Might not be the top item
    0x000:'#808080', # CONTENT_STONE
    0x800:'#6c8633', # CONTENT_GRASS
    0x002:'#27426a', # CONTENT_WATER
    0x003:'#ffff00', # CONTENT_TORCH
    0x801:'#563a1f', # CONTENT_TREE
    0x802:'#305f08', # CONTENT_LEAVES
    0x803:'#668126', # CONTENT_GRASS_FOOTSTEPS
    0x804:'#b2b200', # CONTENT_MESE
    0x805:'#655424', # CONTENT_MUD
    0x009:'#27426a', # CONTENT_WATERSOURCE
    0x808:'#684e2a', # CONTENT_WOOD
    0x809:'#d2c29c', # CONTENT_SAND
    0x00e:'#755629', # CONTENT_SIGN_WALL
    0x00f:'#804f00', # CONTENT_CHEST
    0x010:'#767676', # CONTENT_FURNACE
    0x80a:'#7b7b7b', # CONTENT_COBBLE
    0x80b:'#c7c7c7', # CONTENT_STEEL
    0x80c:'#b7b7de', # CONTENT_GLASS
    0x015:'#674e2a', # CONTENT_FENCE
    0x80d:'#dbcab2', # CONTENT_MOSSYCOBBLE
    0x80e:'#9a4e06', # CONTENT_GRAVEL
    0x80f:'#cc0000', # CONTENT_SANDSTONE
    0x810:'#d3d7cf', # CONTENT_CACTUS
    0x811:'#aa3219', # CONTENT_BRICK
    0x812:'#684e2a', # CONTENT_CLAY
    0x813:'#3a6912', # CONTENT_PAPYRUS

    0x01e:'#ffcc66', # RAILS
    0x816:'#66ff33', # BUSH
}

SCALE=4
WIDTH=150
HEIGHT=150
class MapTile:
    def __init__(self, canvas, cell, pos):
        self.canvas = canvas
        self.image = PhotoImage(width=16*SCALE, height=16*SCALE)
        self.imgelt = canvas.create_image((cell[0]*16-pos[0]+WIDTH/2)*SCALE, (pos[2]-15-cell[1]*16+HEIGHT/2)*SCALE, image=self.image, anchor=NW)
        canvas.tag_lower(self.imgelt)
        self.dirty = True
        self.cell = cell
        self.scheduled = False
    def repaint(self):
        self.scheduled = False
        #print "Updating tile", self.cell, "at coords", self.canvas.coords(self.imgelt)
        from_cache = []
        cur_block_y = None
        cur_block = None
        self.image.put('#ff00ff',(0,0,16*SCALE,16*SCALE))
        for x in xrange(16):
            for z in xrange(16):
                for y in xrange(self.high,self.low,-1):
                    if cur_block_y != y/16:
                        cur_block_y = y/16
                        block_pos = (self.cell[0], cur_block_y, self.cell[1])
                        cur_block = m.get_node(block_pos)
                    if cur_block is None:
                        continue
                    n = cur_block(x,y%16,15-z)
                    if n is None:
                        continue
                    c = n.content
                    if c==126:
                        continue
                    if c in tilecolors:
                        if y==self.high and not c == 3:
                            c=-1
                        self.image.put(tilecolors[c], (x*SCALE,z*SCALE,x*SCALE+SCALE,z*SCALE+SCALE))                    
                        break
                    print hex(c)
        self.dirty = False
    def schedule(self,low,high):
        self.low = low
        self.high = high
        if self.dirty and not self.scheduled:
            self.scheduled = True
            root.after_idle(self.repaint)
        
class Map:
    pos=(0,0,0)
    cache={}
    names={}
    name_tags={}
    name_arrows={}
    dirty=False
    def __init__(self, master):
        self.canvas = Canvas(master, width=WIDTH*SCALE, height=HEIGHT*SCALE, borderwidth=1, relief=SUNKEN)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.__click)
        #self.canvas.create_line(2,2,WIDTH*SCALE+2,HEIGHT*SCALE+2)
        #self.canvas.create_line(2,HEIGHT*SCALE+2,WIDTH*SCALE+2,2)
    def move(self, pos):
        if self.pos[1] != pos[1]:
            print "Invalidate all map tiles."
            for i in self.cache:
                self.cache[i].dirty=True
        self.canvas.move(ALL, (-pos[0]+self.pos[0])*SCALE, (pos[2]-self.pos[2])*SCALE)
        self.pos=pos
        self.__schedule_repaint()
    def blockdata(self, pos, nodes):
        cell = (pos[0],pos[2])
        if -2<pos[1]-self.pos[1]/16<2:
            if cell in self.cache:
                self.cache[cell].dirty=True #invalidate cache
            self.__schedule_repaint()
    def __schedule_repaint(self):
        if not self.dirty:
            self.dirty = True
            root.after_idle(self.__repaint)
    def __repaint(self):
        px = lint(self.pos[0])/16
        py = lint(self.pos[2])/16
        dx = WIDTH/32
        dy = HEIGHT/32
        low = lint(self.pos[1]-8)
        high = lint(self.pos[1]+8)
        for y in xrange(py-dy,py+dy+1):
            for x in xrange(px-dx,px+dx+1):
                cell = (x,y)
                if not cell in self.cache:
                    self.cache[cell] = MapTile(self.canvas, cell, self.pos)
                self.cache[cell].schedule(low, high)
        self.dirty = False
    def __click(self,event):
        pos = list(self.pos)
        pos[0]+=(event.x-2-WIDTH*SCALE/2.0)/SCALE
        pos[2]-=(event.y-2-HEIGHT*SCALE/2.0)/SCALE
        m.setpos(pos,0,0)
        print "clicked at", pos[0], pos[2]
    def player_data(self, p):
        for i in p:
            x = ( p[i][0][0]-self.pos[0]+WIDTH /2.0)*SCALE+2
            y = (-p[i][0][2]+self.pos[2]+HEIGHT/2.0)*SCALE+2
            dx = -math.sin(p[i][3]*math.pi/180)
            dy = -math.cos(p[i][3]*math.pi/180)
            path = (x+10*dx,y+10*dy,x+25*dx,y+25*dy)
            if not i in self.name_tags:
                if not i in self.names:
                    continue
                t = self.canvas.create_text(x, y, text=self.names[i], fill="white")
                self.name_tags[i] = t
                a = self.canvas.create_line(path, arrow=LAST, fill="white")
                self.name_arrows[i] = a
            else:
                self.canvas.coords(self.name_tags[i], x, y)
                self.canvas.coords(self.name_arrows[i], *path)
    def player_info(self, p):
        self.names = p
        rm = set(self.name_tags.keys()) - set(p.keys())
        for i in rm:
            self.canvas.delete(self.name_tags[i])
            del self.name_tags[i]
            self.canvas.delete(self.name_arrows[i])
            del self.name_arrows[i]

root = Tk()
root.title("Minetest bot")

shop = ShopKeeper()
m.install_handler(shop)
chat = Chatbox(root)
m.install_handler(chat)
mapview = Map(root)
m.install_handler(mapview)
pos = Position(root)
m.install_handler(pos)
try:
    m.connect()
    #m.connect("mt1.gameboom.net")
    m.init("bcmpinc-test","test")
    while m.pos is None:
        m.wait()
    root.createfilehandler(m.udp, READABLE, m.wait)
    root.mainloop()
finally:
    m.disconnect()
    
