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
        m.setpos((10,10.5,10),0,0)
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
        
root = Tk()
root.title("Minetest bot")
chat = Chatbox(root)

m.install_handler(ShopKeeper())
m.install_handler(chat)
try:
    m.connect()
    m.init("test","test")
    while m.pos is None:
        m.wait()
    root.createfilehandler(m.udp, READABLE, m.wait)
    root.mainloop()
    m.disconnect()
except:
    m.disconnect()
    raise
    
