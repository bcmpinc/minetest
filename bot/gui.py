from Tkinter import *
import thread
import sys
import traceback
import connect as m

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
        self.list.insert(END, msg)
        if self.list.size() > 10:
            self.list.delete(0)
    echo = chat
    def __send(self, event):
        m.chat(self.entry.get())
        self.entry.delete(0,END)

tilecolors={
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
    0x80c:'#b7b7de', # CONENT_GLASS
    0x015:'#674e2a', # CONTENT_FENCE
    0x80d:'#dbcab2', # CONTENT_MOSSYCOBBLE
    0x80e:'#4e9a06', # CONTENT_GRAVEL
    0x80f:'#cc0000', # CONTENT_SANDSTONE
    0x810:'#d3d7cf', # CONTENT_CACTUS
    0x811:'#aa3219', # CONTENT_BRICK
    0x812:'#684e2a', # CONTENT_CLAY
    0x813:'#3a6912', # CONTENT_PAPYRUS    
}

class Map:
    pos=(0,0,0)
    blocks={}
    dirty=False
    def __init__(self, master):
        self.image = PhotoImage(width=256, height=256)
        self.canvas = Canvas(master, width=256, height=256, borderwidth=1, relief=SUNKEN)
        self.canvas.pack()
        self.canvas.create_image(2,2, image=self.image, anchor=NW)
        self.canvas.image = self.image
        self.canvas.bind("<Button-1>", self.__click)
        self.__schedule_repaint()
    def move(self, pos):
        self.pos=pos
        # create set with block positions
        sx = int(pos[0]-40)/16
        ex = int(pos[0]+40)/16+1
        sy = int(pos[1]-20)/16
        ey = int(pos[1]+20)/16+1
        sz = int(pos[2]-40)/16
        ez = int(pos[2]+40)/16+1
        poss = set([(x,y,z)
                    for x in xrange(sx,ex)
                    for y in xrange(sy,ey)
                    for z in xrange(sz,ez)])
        # compute difference with registered set
        #dels = set(self.blocks.keys()) - poss
        #adds = poss - set(self.blocks.keys())
        #if (dels):
        #    m.deleted_blocks(list(dels))
        #    for i in dels:
        #        del self.blocks[i]
        #if (adds):
        #    m.got_blocks(list(adds))
        # schedule repaint
        self.__schedule_repaint()
    def blockdata(self, pos, nodes):
        self.blocks[pos] = nodes
        m.got_blocks([pos])
        self.__schedule_repaint()
    def __getnode(self, pos):
        pos = [int(i) for i in pos]
        block_pos = tuple([i/16 for i in pos])
        if not block_pos in self.blocks:
            return None
        block = self.blocks[block_pos]
        node_pos = [pos[i] - block_pos[i]*16 for i in xrange(3)]
        return block(*node_pos)
    def __schedule_repaint(self):
        if not self.dirty:
            self.dirty = True
            root.after_idle(self.__repaint)
    def __repaint(self):
        self.image.put('#ff00ff',(0,0,256,256))
        for row in xrange(64):
            for col in xrange(64):
                for y in xrange(-16,16):
                    n = self.__getnode((self.pos[0]-31.5+row, self.pos[1]-y, self.pos[2]+31.5-col))
                    if n is None:
                        continue
                    c = n.content
                    if c in tilecolors:
                        self.image.put(tilecolors[c], (row*4,col*4,row*4+4,col*4+4))
                        break
                    elif c!=126:
                        print c
        self.dirty = False
    def __click(self,event):
        pos = list(self.pos)
        pos[0]+=(event.x-130)/4
        pos[2]-=(event.y-130)/4
        m.setpos(pos,0,0)
        print "clicked at", pos[0], pos[2]

root = Tk()
root.title("Minetest bot")
chat = Chatbox(root)
mapview = Map(root)

m.install_handler(ShopKeeper())
m.install_handler(chat)
m.install_handler(mapview)
try:
    m.connect()
    m.init("test","test")
    while m.pos is None:
        m.wait()
    root.createfilehandler(m.udp, READABLE, m.wait)
    root.mainloop()
finally:
    m.disconnect()
    
