from deck import Deck
from socket import socket, AF_INET, SOCK_DGRAM
import json

sock = socket(AF_INET, SOCK_DGRAM)
sock2 = socket(AF_INET, SOCK_DGRAM)

ip = 'localhost'
port = 44444
port2 = 44445

waiting_for_one = True

d = Deck().deck
pile = [c.name for c in d]
first_card = pile.pop(14)

# warning: played card is none if the other player takes cards. needs to be last played

# Skeleton of json to be sent
data_to_send = {
	"stage": "INIT",
	"played": first_card,
	"pile": pile,
	"num_left": 7,
	"color": first_card[0:3],
	"last_played": None,
	"player": 1,
	"said_uno": True
}

# Send init stage deck + first card played
info = data_to_send
sock.sendto(json.dumps(info).encode(), (ip, port))
print("Sent to player 1")
pile = pile[7:]
data_to_send["pile"] = pile
data_to_send["player"] = 0
info2 = data_to_send
sock2.sendto(json.dumps(info2).encode(), (ip, port2))
print("Sent to player 2")
pile = pile[7:]

while True:

	if waiting_for_one:
		print("Waiting for player one")
		json_msg, addr = sock.recvfrom(8000)
	else:
		print("Waiting for player two")
		json_msg, addr = sock2.recvfrom(8000)
	message = json.loads(json_msg.decode())

	card = message['played']
	print("PLAYED CARD: ", card)
	print("FROM player: ", " one " if waiting_for_one else " two ")
# Check if played is a skip, send json to both, but the orig player is 1
# new is 0

	data = {
		"pile": message["pile"],
		"num_left": message['num_left'],
		"played": message['played'],
		"stage": "GO",
		"player": 1,
		"last_played": message['last_played'],
		"color": message['color'],
	}
	if card is not None and "stop" in card:
		# receiver is 0, sender is 1
		if waiting_for_one:
			print("Player 1 will go again")
			sock.sendto(json.dumps(data).encode(), (ip, port))
			# waiting_for_one = True
			data['player'] = 0
			sock2.sendto(json.dumps(data).encode(), (ip, port2))
			print("Player 2 waits")
		else:
			print("Player 2 will go again")
			sock2.sendto(json.dumps(data).encode(), (ip, port2))
			# waiting_for_one = False
			data['player'] = 0
			sock.sendto(json.dumps(data).encode(), (ip, port))
			print("Player 1 waits")
	else:
		if waiting_for_one:
			# Relay to player 2
			sock2.sendto(json.dumps(data).encode(), (ip, port2))
			print("Sent to player 2")
			waiting_for_one = False

		else:
			print("Sent to player 1")
			sock.sendto(json.dumps(data).encode(), (ip, port))
			waiting_for_one = True
