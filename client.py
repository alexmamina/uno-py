from tkinter import Tk
from socket import socket, AF_INET, SOCK_STREAM
import json
from json import JSONDecodeError
from threading import Thread
import queue
from player import Player
import gameanim
from random import randint
from tkinter.simpledialog import askstring
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--sentient", action="store_true")
parser.add_argument("--human", action="store_true")
parser.add_argument("-name", type=str)

if __name__ == "__main__":
	conditions = parser.parse_args()
	if not conditions.sentient:
		small_window = Tk()
		small_window.withdraw()
		address = None
		if not conditions.human:
			address = askstring(
				"Address",
				"Paste the \"CONNECT TO\" information you see on the server:"
			)
			name = askstring("Name", "What's your name?")
		else:
			name = conditions.name
		small_window.destroy()
		if address is not None and len(address) > 0:
			host, port = address.split()
		else:
			host, port = 'localhost', 44444

		if name is None or len(name) == 0:
			name = f"default-{str(randint(0, 1000))}"
	else:
		host, port = 'localhost', 44444
		name = "Pudding"
	root = Tk()
	root.configure(bg='white')
	root.geometry("700x553+250+120")

	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	root.geometry("{}x{}".format(screen_width, screen_height))

	sock = socket(AF_INET, SOCK_STREAM)
	try:
		sock.connect((host, int(port)))
		sock.send(name.encode('utf-8'))
		print(
			"Connected to server. Waiting for other players to connect before we can show you "
			"your cards!"
		)
	except Exception as e:
		print("ERROR CONNECTING TO SERVER:")
		print(str(e))
	init, addr = sock.recvfrom(1000)
	try:
		data = init.decode('utf-8')
		message = json.loads(data)
		root.title(f"UNO - player {str(message['whoami'])} - {message['peeps'][message['whoami']]}")
		q = queue.Queue()
		all_points = [0] * len(message['other_left'])
		if conditions.sentient:
			window = Player(root, q, message, sock, all_points)
			root.withdraw()
		else:
			window = gameanim.Game(root, q, message, sock, all_points)
			# window = Game(root, q, message, sock, all_points)
		window.config_start_btns(message)
		thread = Thread(target=window.receive)
		thread.start()
		window.checkPeriodically()
		window.mainloop()
	except JSONDecodeError as e:
		print(init.decode('utf-8'))
		print(str(e))
		print("Error decoding the response from the server")
