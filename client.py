from tkinter import *
from socket import *
from json import *
from sys import *
import queue
from game import *

port = argv[1]

def checkPeriodically(w):
	w.incoming()
	w.after(100, checkPeriodically, w)

def close_window():
	try:
		sock.send("bye".encode())
	except OSError:
		pass
	window.sock.close()
	root.destroy()
	print("Bye")


def new_game(w):
	w.destroy()
	w.master.destroy()

	root = Tk()
	q = queue.Queue()
	init = {'stage': INIT}
	sock.send(dumps(init).encode())
	message = sock.recvfrom(8000)
	newgame = Game(root, q, message, sock, addr)
	newgame.mainloop()


root = Tk()
root.configure(bg='white')
root.geometry("700x553")
#todo remove this line after testing:
root.geometry("650x553")
sock = socket(AF_INET, SOCK_STREAM)
try:
	sock.connect(('', int(port)))
	print("Connected to server")
except error as e:
	print("ERROR")
	print(str(e))

init, addr = sock.recvfrom(8000)
message = loads(init.decode())

root.title("UNO - player "+ str(message['whoami']))

q = queue.Queue()
window = Game(root, q, message, sock, addr)
if message['player'] == 0:
	window.new_card.config(state="disabled")
	window.uno = False
	window.uno_but.config(fg="red", bg="white", state='disabled')
	for i in window.hand_btns:
		window.hand_btns[i].config(state='disabled')
elif "plus" in message['played']:
	window.card_counter = 2
	window.uno = False
	window.uno_but.config(fg="red", bg="white", state='disabled')
	for i in window.hand_btns:
		window.hand_btns[i].config(state='disabled')
elif window.possible_move():
	window.new_card.config(state="disabled")

thread = Thread(target=window.receive)
thread.start()
checkPeriodically(window)
root.protocol("WM_DELETE_WINDOW", close_window)
window.mainloop()
#hello