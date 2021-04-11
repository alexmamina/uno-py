from socket import *

from deck import *

sock = socket(AF_INET, SOCK_DGRAM)
sock2 = socket(AF_INET, SOCK_DGRAM)

ip = 'localhost'
port = 44444
port2 = 44445
addresses = {}
current = 1
d = Deck().deck
pile = [c.name for c in d]
print(pile)
first_card = pile.pop(14)
#Skeleton of json to be sent
data_to_send = {"stage" : "INIT",
				"played" : first_card,
				"pile" : pile,
				"num_left" : 7,
				"color" : first_card[0:3],
				"all_played" : [],
				"player" : 1,
				"said_uno" : False}

#Send init stage deck + first card played
info = data_to_send
sock.sendto(dumps(info).encode(), (ip, port))
print("Sent to player 1")
#"Remove" the first 7 cards used for player 1
pile = pile[7:]
#Update values and send to player 2
data_to_send["pile"] = pile
data_to_send["player"] = 0
info2 = data_to_send
sock2.sendto(dumps(info2).encode(), (ip, port2))
print("Sent to player 2")
pile = pile[7:]

#ALL SENT

while True:

	if current == 1:
		print("Waiting for player one")
		json, addr = sock.recvfrom(8000)
		addresses[1] = addr

	else:
		print("Waiting for player two")
		json, addr = sock2.recvfrom(8000)
		addresses[2] = addr
	message = loads(json.decode())

	card = message['played']
	print ("PLAYED CARD: ", card)
	print("FROM player: ", " one " if current==1 else " two ")
	#Check if played is a skip, send json to both, but the orig player is 1
	#new is 0

	data = {"pile" : message["pile"],
			"num_left" : message['num_left'],
			"played" : message['played'],
			"stage" : "GO",
			"player" : 1,
			"all_played" : message['all_played'],
			"color" : message['color'],
			}
	#If the last played card is stop
	if card is not None and "stop" in card:
		#receiver is 0, sender is 1
		if current == 1:
			print("Player 1 will go again")
			sock.sendto(dumps(data).encode(), addresses[1])
			data['player'] = 0
			sock2.sendto(dumps(data).encode(), addresses[2])
			print("Player 2 waits")
		else:
			print("Player 2 will go again")
			sock2.sendto(dumps(data).encode(), addresses[2])
			data['player'] = 0
			sock.sendto(dumps(data).encode(), addresses[1])
			print("Player 1 waits")
	#Not stop, so just relay info
	else:
		if current==1:
			#Relay to player 2
			sock2.sendto(dumps(data).encode(), addresses[2])
			print("Sent to player 2")
			waiting_for_one = False

		else:
			print("Sent to player 1")
			sock.sendto(dumps(data).encode(), addresses[1])
			waiting_for_one = True