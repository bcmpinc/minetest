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
        m.chat("Shop open!")
    def disconnect(self):
        m.chat("Shop closed!")
        
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
        self.frame.pack(fill = BOTH)
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
}

SCALE=4
WIDTH=128
HEIGHT=128
class Map:
    pos=(0,0,0)
    blocks={}
    cache={}
    names={}
    name_tags={}
    dirty=False
    def __init__(self, master):
        self.image = PhotoImage(width=WIDTH*SCALE, height=HEIGHT*SCALE)
        self.canvas = Canvas(master, width=WIDTH*SCALE, height=HEIGHT*SCALE, borderwidth=1, relief=SUNKEN)
        self.canvas.pack()
        self.canvas.create_image(2,2, image=self.image, anchor=NW)
        self.canvas.image = self.image
        self.canvas.bind("<Button-1>", self.__click)
        self.__schedule_repaint()
    def move(self, pos):
        if self.pos[1] != pos[1]:
            print "Map cache reset."
            self.cache={}
        self.canvas.move(ALL, (-pos[0]+self.pos[0])*SCALE, (pos[2]-self.pos[2])*SCALE)
        self.pos=pos
        self.__schedule_repaint()
    def blockdata(self, pos, nodes):
        self.blocks[pos] = nodes
        m.got_blocks([pos])
        cpos = (pos[0],pos[2])
        if -2<pos[1]-self.pos[1]/16<2:
            if cpos in self.cache:
                del self.cache[cpos] #invalidate cache
            self.__schedule_repaint()
    def __schedule_repaint(self):
        if not self.dirty:
            self.dirty = True
            root.after_idle(self.__repaint)
    def __repaint(self):
        print "Drawing map ...",
        self.image.put('#ff00ff',(0,0,WIDTH*SCALE,HEIGHT*SCALE))
        pos = (lint(self.pos[0]-WIDTH/2.0+.5), lint(self.pos[1]), lint(self.pos[2]+HEIGHT/2.0+.5))
        from_cache=[]
        for row in xrange(WIDTH):
            for col in xrange(HEIGHT):
                x=-WIDTH/2+row
                z=HEIGHT/2-col
                pillar = (x,z)
                block_pillar = (x/16,z/16)
                if not block_pillar in self.cache:
                    self.cache[block_pillar]={}
                if pillar in self.cache[block_pillar]:
                    c=self.cache[block_pillar][pillar]
                else:
                    for y in xrange(pos[1]+16,pos[1]-16,-1):
                        block_pos=(x/16,y/16,z/16)
                        if not block_pos in self.blocks:
                            self.blocks[block_pos]=m.get_node(block_pos)
                        if self.blocks[block_pos] is None:
                            continue
                        n = self.blocks[block_pos](x%16,y%16,z%16)
                        if n is None:
                            continue
                        c = n.content
                        if c in tilecolors:
                            if y==pos[1]+16 and not c == 3:
                                c=-1
                            self.cache[block_pillar][pillar]=c
                            break
                        elif c!=126:
                            print hex(c)
                    else:
                        self.cache[block_pillar][pillar]=c=None
                if not c is None:
                    self.image.put(tilecolors[c], (row*SCALE,col*SCALE,row*SCALE+SCALE,col*SCALE+SCALE))                    
        self.dirty = False
        if from_cache:
            m.got_blocks(from_cache)
        print "done"
    def __click(self,event):
        pos = list(self.pos)
        pos[0]+=(event.x-2-WIDTH*SCALE/2.0)/SCALE
        pos[2]-=(event.y-2-HEIGHT*SCALE/2.0)/SCALE
        m.setpos(pos,0,0)
        print "clicked at", pos[0], pos[2]
    def player_data(self, p):
        for i in p:
            (x,y) = ((p[i][0][0]-self.pos[0]+2+WIDTH/2.0)*SCALE, (-p[i][0][2]+self.pos[2]+2+HEIGHT/2.0)*SCALE)
            if not i in self.name_tags:
                if not i in self.names:
                    continue
                t = self.canvas.create_text(x, y, text=self.names[i], fill="white")
                self.name_tags[i] = t
            else:
                self.canvas.coords(self.name_tags[i], x, y)
    def player_info(self, p):
        self.names = p
        for i in self.name_tags:
            if i not in p:
                self.canvas.delete(self.name_tags[i])
                del self.name_tags[i]

root = Tk()
root.title("Minetest bot")

#shop = ShopKeeper()
#m.install_handler(shop)
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
    
