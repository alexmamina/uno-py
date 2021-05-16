from tkinter import *

class New(Frame):
	def __init__(self, master):
		super().__init__(master)
		self.pack()
		b = Button(text='newgame', command=self.newgame)
		b.pack()


	def newgame(self):
		self.destroy()
		self.master.destroy()
		root = Tk()
		n = New(root)
		n.mainloop()

def start():
	root = Tk()
	root.configure(bg='white')
	root.geometry("700x553")
	w = New(root)
	w.mainloop()

start()

