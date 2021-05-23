from tkinter import *
from socket import *
from json import *
from sys import *
import queue
from game import *
from tkinter.simpledialog import *

#port = argv[2]
#host = argv[1]
small_window = Tk()
small_window.withdraw()
address = askstring("Address", "Paste the \"CONNECT TO\" information you see on the "
												   "server:")
small_window.destroy()
if address is not None and len(address) > 0:
	host, port = address.split()
else:
	host, port = 'localhost', 44444
root = Tk()
root.configure(bg='white')
root.geometry("700x553")
sock = socket(AF_INET, SOCK_STREAM)
try:
	sock.connect((host, int(port)))
	print("Connected to server. Waiting for other players to connect before we can show you "
		  "your cards!")
except error as e:
	print("ERROR CONNECTING TO SERVER:")
	print(str(e))
init, addr = sock.recvfrom(8000)
try:
	message = loads(init.decode('utf-8'))
except JSONDecodeError:
	print("Check that you have input a correct port! Or that the server is running before you "
		  "start.")

root.title("UNO - player "+ str(message['whoami']))

q = queue.Queue()
window = Game(root, q, message, sock, addr)
window.config_start_btns()

thread = Thread(target=window.receive)
thread.start()
window.checkPeriodically()
window.mainloop()
