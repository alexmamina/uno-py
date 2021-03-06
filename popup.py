from tkinter import *
from tkinter import simpledialog
from PIL import ImageTk, Image
from os import *
from sys import *
from tkinter.simpledialog import *
from tkmacosx import Button as but


class InfoPop(Toplevel):
	def __init__(self, parent, title, text):
		Toplevel.__init__(self, parent)
		self.title(title)
		x = parent.winfo_rootx()
		y = parent.winfo_rooty()
		self.config(bg='Ivory')
		self.geometry("200x150+%d+%d" % (500, 250))
		# self.geometry("385x50+%d+%d" % (x - 150, y + 150))
		self.text=text
		self.transient(parent)
		self.protocol("WM_DELETE_WINDOW", self.destroy)

		self.create_widgets()
		self.attributes('-topmost', True)
		self.grab_set()
		self.focus_set()
		self.focus()
		# wait.window ensures that calling function waits for the window to
		# close before the result is returned.
		#self.wait_window()

	def create_widgets(self):
		frmL = Frame(self)
		Label(self, text=self.text, font=("TkDefaultFont", 20),bg='Ivory').pack(side=TOP)
		frmButton = Frame(self)
		btn = but(self, text='OK',width=180,height=40,bg='light blue', command=self.cancel,
				   borderless=1)
		btn.focus_set()
		self.bind('<Return>', self.cancel)

		btn.pack(side=BOTTOM)

	def cancel(self, *args):
		self.destroy()

