from socket import *
from sys import *
from deck import *

sock = socket(AF_INET, SOCK_DGRAM)
sock2 = socket(AF_INET, SOCK_DGRAM)

ip = 'localhost'
#port = 44444
#port2 = 44445
#port = 54456
#port2 = 54455
port = int(argv[1])
port2 = int(argv[2])
addresses = {}
d = Deck().deck
pile = [c.name for c in d]
print(pile)
first_card = pile.pop(14)
previous = {}
# Black card will not be played first. If popped, reshuffle and get new
while "bla" in first_card:
	pile.append(first_card)
	shuffle(pile)
	first_card = pile.pop(14)

#TO 1 we need to send [0:7]:[15:]
#TO 2 we need to send [8:]

#Skeleton of json to be sent
data_to_send = {"stage" : "INIT",
				"played" : first_card,
				"pile" : pile[0:7]+pile[14:],
				"num_left" : 7,
				"color" : first_card[0:3],
				"all_played" : [],
				"player" : 1,
				"said_uno" : False}

#Send data to different players depending on if the first one needs to skip a turn
if "stop" in first_card:
	current = 2

	#Send init stage deck + first card played
	data_to_send["player"] = 0
	info = data_to_send
	sock.sendto(dumps(info).encode(), (ip, port))
	print("Sent to player 1")
	#"Remove" the first 7 cards used for player 1
	pile = pile[7:]
	#Update values and send to player 2
	data_to_send["pile"] = pile
	data_to_send["player"] = 1
	info2 = data_to_send
	sock2.sendto(dumps(info2).encode(), (ip, port2))
	print("Sent to player 2")
	pile = pile[7:]

else:
	current = 1
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


	if (message['stage'] == "GO"):
		card = message['played']
		print ("PLAYED CARD: ", card)
		print("UNO SAID: ", message['said_uno'])
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
				"said_uno" : message['said_uno']
				}
		if 'taken' in message:
			data['taken'] = message['taken']
		#If the last played card is stop
		if "stop" in card and 'taken' not in message:
			#receiver is 0, sender is 1
			if current == 1:
				data['player'] = 0
				sock2.sendto(dumps(data).encode(), (ip, port2))
				print("Player 2 waits")
				print("Player 1 will go again")
				data['num_left'] = previous['num_left']
				data['player'] = 1
				sock.sendto(dumps(data).encode(), (ip, port))
			else:
				data['player'] = 0
				sock.sendto(dumps(data).encode(), (ip, port))
				print("Player 1 waits")
				data['player'] = 1
				data['num_left'] = previous['num_left']
				print("Player 2 will go again")
				sock2.sendto(dumps(data).encode(), (ip, port2))
		#Not stop, so just relay info
		else:
			if current==1:
				#Relay to player 2
				sock2.sendto(dumps(data).encode(), (ip, port2))
				print("Sent to player 2")
				current = 2

			else:
				print("Sent to player 1")
				sock.sendto(dumps(data).encode(), (ip, port))
				current = 1
		if "stop" not in message['played']:
			previous = message
	elif (message['stage'] == "CHALLENGE"):
		print("UNO has not been said")
		if current == 1:
			#Relay to player 2
			sock2.sendto(dumps(message).encode(), (ip, port2))
			print("Sent to player 2")
			current = 2

		else:
			print("Sent to player 1")
			sock.sendto(dumps(message).encode(), (ip, port))
			current = 1