from tkinter import *
from socket import *
from json import *
from sys import *
import queue
from player import *
from game import *
from tkinter.simpledialog import *
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--sentient", action="store_true")
parser.add_argument("--human", action="store_true")
parser.add_argument("-name", type=str)
conditions = parser.parse_args()
if not conditions.sentient:
	small_window = Tk()
	small_window.withdraw()
	address = None
	if not conditions.human:
		address = askstring("Address", "Paste the \"CONNECT TO\" information you see on the "
													   "server:")
		name = askstring("Name", "What's your name?")
	else:
		name = conditions.name
	small_window.destroy()
	if address is not None and len(address) > 0:
		host, port = address.split()
	else:
		host, port = 'localhost', 44444

	if name is None or len(name) == 0:
		name = 'default'+str(randint(0, 1000))
else:
	host, port = 'localhost', 44444
	name = "Pudding"
root = Tk()
root.configure(bg='white')
root.geometry("700x553+250+120")
sock = socket(AF_INET, SOCK_STREAM)
try:
	sock.connect((host, int(port)))
	sock.send(name.encode('utf-8'))
	print("Connected to server. Waiting for other players to connect before we can show you "
		  "your cards!")
except error as e:
	print("ERROR CONNECTING TO SERVER:")
	print(str(e))
init, addr = sock.recvfrom(1000)
try:
	data = init.decode('utf-8')
	message = loads(data)
	root.title("UNO - player "+ str(message['whoami'])+" - "+message['peeps'][message[
	'whoami']])
	q = queue.Queue()
	all_points = [0]*len(message['other_left'])
	if conditions.sentient:
		window = Player(root, q, message, sock, all_points)
		root.withdraw()
	else:
		window = Game(root, q, message, sock, all_points)
	window.config_start_btns(message)
	thread = Thread(target=window.receive)
	thread.start()
	window.checkPeriodically()
	window.mainloop()
except JSONDecodeError as e:
	print(init.decode('utf-8'))
	print(str(e))
	print("Check that you have input a correct port! Or that the server is running before you "
		  "start. Or something else went wrong")


