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
host, port = address.split()

root = Tk()
root.configure(bg='white')
root.geometry("700x553")
sock = socket(AF_INET, SOCK_STREAM)
try:
	sock.connect((host, int(port)))
	print("Connected to server")
except error as e:
	print("ERROR")
	print(str(e))

init, addr = sock.recvfrom(8000)
message = loads(init.decode())

root.title("UNO - player "+ str(message['whoami']))

q = queue.Queue()
window = Game(root, q, message, sock, addr)
window.config_start_btns()

thread = Thread(target=window.receive)
thread.start()
window.checkPeriodically()
window.mainloop()
#hello