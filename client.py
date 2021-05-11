from tkinter import *
from socket import *
from json import *
from sys import *
import queue
from game import *




port = argv[1]

#class Client():


def checkPeriodically(w):
	w.incoming()
	w.after(100, checkPeriodically, w)

def close_window():
	window.sock.close()
	root.destroy()
	print()

	#def __init__(self):
root = Tk()
root.configure(bg='white')
root.geometry("700x553")
#todo remove this line after testing:
root.geometry("650x553")
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('', int(port)))
init, addr = sock.recvfrom(8000)
message = loads(init.decode())
root.title("UNO - port " + port + " player - " + (str(1) if (message['player'] == 1 and
															 "stop" not in message['played']) or ('stop' in message['played']
																								  and message['player'] == 0) else str(2)))
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



#if __name__ == "main":
#	c = Client()