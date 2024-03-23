from socket import socket, AF_INET, SOCK_STREAM
import sys


if __name__ == "__main__":
	port = sys.argv[1]

	sock = socket(AF_INET, SOCK_STREAM)
	try:
		sock.connect(('', int(port)))
		print("Connected")
	except Exception as e:
		print(str(e))

	msg, addr = sock.recvfrom(2000)
	print(msg)
