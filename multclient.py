from socket import *
from sys import *

port = argv[1]

sock = socket(AF_INET, SOCK_STREAM)
try:
	sock.connect(('', int(port)))
	print("Connected")
except error as e:
	print(str(e))

msg, addr = sock.recvfrom(2000)
print(msg)