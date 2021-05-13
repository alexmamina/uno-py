from socket import *
from sys import *


port = argv[1]
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('', int(port)))
sock.listen(5)
peeps = []
addresses = []

num = argv[2]
ctr = 0
while ctr < int(num):
	client, addr = sock.accept()
	print(client, " and ", str(addr))
	peeps.append(client)
	addresses.append(addr)
	ctr += 1


for a in range(len(addresses)):
	peeps[a].sendto("hello".encode(), addresses[a])

