from tkinter import *
from socket import *
from json import *
from sys import *
import queue
from game import *

port = argv[1]


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
window.config_start_btns()

thread = Thread(target=window.receive)
thread.start()
window.checkPeriodically()
window.mainloop()
