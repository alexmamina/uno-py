from tkinter import *
from tkinter import simpledialog
from PIL import ImageTk, Image
from os import *
from sys import *
from tkinter.simpledialog import *
from tkmacosx import Button as but

class Picker(Toplevel):
	def __init__(self,parent,title,question,options):
		Toplevel.__init__(self,parent)
		self.title(title)
		x = parent.winfo_rootx()
		y = parent.winfo_rooty()
		self.geometry("+%d+%d" % (x - 150, y + 150))
		self.question = question
		self.transient(parent)
		self.protocol("WM_DELETE_WINDOW",self.cancel)
		self.options = options
		self.result = '_'
		self.createWidgets(title)
		self.grab_set()
		## wait.window ensures that calling function waits for the window to
		## close before the result is returned.
		self.wait_window()
	def createWidgets(self, title):
		frmQuestion = Frame(self)
		Label(frmQuestion,text=self.question).grid()
		frmQuestion.grid(row=1)
		frmButtons = Frame(self)
		frmButtons.grid(row=2)
		column = 0
		for option in self.options:
			if 'color' in title:
				btn = but(frmButtons,text=option,command=lambda x=option:self.setOption(x),
						  bg=option, borderless=1)

			else:
				btn = Button(frmButtons,text=option,command=lambda x=option:self.setOption(x))
			btn.grid(column=column,row=0)
			column += 1
	def setOption(self,optionSelected):
		self.result = optionSelected
		self.destroy()
	def cancel(self):
		self.result = self.options[0]
		self.destroy()

