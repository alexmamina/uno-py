from threading import Thread
from tkinter import Tk, Frame, Button, Label

from socket import socket, AF_INET, SOCK_DGRAM
from sys import argv

import queue


port = argv[1]
# port = 44444
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('localhost', int(port)))

# global dest


class Butt(Frame):

	#  Initialise a frame (going to be within the window). Set the cards label
	def __init__(self, master, quue, message):
		global cards_left
		super().__init__(master)
		self.pack()
		self.quue = quue
		self.parent = master

		text_cards_left = "Your cards left: " + \
			str(7) + "\n Other player's cards " \
			"left: " + str(7)
		self.cards_left = Label(text=text_cards_left, fg="blue", bg="white", width=20, height=10)
		self.cards_left.place(x=10, y=5)
		self.uno = Button(text="UNO?", fg="red", bg="yellow", width=10, height=2, command=self.send)
		self.uno.place(x=50, y=150)

	def send(self):
		sock.sendto("hello".encode(), ('localhost', 44445 if int(port) == 44444 else 44444))
		print("Hello")

	def incoming(self):
		global cards_left
		while self.quue.qsize():
			try:
				msg = self.quue.get(0)
				#  Check contents of message and do whatever is needed. As a
				#  simple test, print it (in real life, you would
				#  suitably update the GUI's display in a richer fashion).
				print(msg)
				self.cards_left.config(text=msg)
			except queue.Empty:
				#  just on general principles, although we don't
				#  expect this branch to be taken in this case
				pass

	def receiv(self):
		while True:
			msg, a = sock.recvfrom(8000)
			self.quue.put(msg)
		print("bye")


def periodic(win):
	win.incoming()
	win.after(500, periodic, win)


if __name__ == "__main__":

	# Start thread, receive first info
	# Use it in here
	# if len(message) > 0:
	root = Tk()
	# message, dest = sock.recvfrom(8000)
	message = ""
	root.title("UNO - port " + str(port))
	root.configure(bg='white')
	root.geometry("200x253")
	# print(message)
	quue = queue.Queue()
	window = Butt(root, quue, message)
	thread = Thread(target=window.receiv)
	thread.start()
	periodic(window)
	window.mainloop()
