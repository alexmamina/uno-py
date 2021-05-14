from socket import *
from sys import *
from deck import *
from stages import *
sock = socket(AF_INET, SOCK_STREAM)

ip = ''
port = int(argv[1])
sock.bind((ip, port))
num_players = int(argv[2])
socks = []
addresses = []
current_player = 0
sock.listen(5)
player_counter = 0
reverse = False

# Deck initialisation
d = Deck().deck
pile = [c.name for c in d]
print(pile)
resulting_points = 0
first_card = pile.pop(7*num_players)
previous = {}
# Black card will not be played first. If popped, reshuffle and get new
while "bla" in first_card:
	pile.append(first_card)
	shuffle(pile)
	first_card = pile.pop(7*num_players)

left_cards = [7]*num_players
# Skeleton of json to be sent
data_to_send = {"stage": INIT,
				"played": first_card,
				"pile": pile[0:7],
				"num_left": 7,
				"other_left": left_cards,
				"color": first_card[0:3],
				"all_played": [],
				"player": 0,
				"said_uno": False}
previous = data_to_send
# End of initialisation


# Wait for clients to connect, save them
while player_counter < num_players:
	player, addr = sock.accept()
	socks.append(player)
	addresses.append(addr)
	player_counter += 1
	print("Connected player ", player_counter)

# Send the data: pile is first 7 + rest of pile common for all.
# Player 3 is current if reverse True
# Player 2 is current if stop True
# Else player 1 is current
for i in range(num_players):
	data_to_send['pile'] = pile[0:7] + pile[7*(num_players-i):]
	data_to_send['whoami'] = i
	if (i == 0 and "stop" not in first_card and "reverse" not in first_card) or \
			(i == 1 and "stop" in first_card) or \
		(i == num_players-1 and "reverse" in first_card):
		data_to_send['player'] = 1
		current_player = i
		reverse = "reverse" in first_card
		prev_player = i-1 % num_players if reverse else i+1 % num_players
	else:
		data_to_send['player'] = 0
	socks[i].sendto(dumps(data_to_send).encode(), addresses[i])
	print("Sent init to player ", i)
	pile = pile[7:]


# ALL SENT
# Go - regular play, regular relay
	# Debug - change turn, regular play, print data
# Challenge - only send packet to make player take two cards
# Zerocards - one player is out of cards, forward to the other who will either take cards or send
	# points
# Takecards - send back to player out of cards while waiting for the other to take more
# Calc - other player sends points
while True:
	print("Waiting for player ", current_player)
	json, addr = socks[current_player].recvfrom(8000)
	message = loads(json.decode())


	if message['stage'] == GO or message['stage'] == DEBUG:
		card = message['played']
		print("PLAYED CARD: ", card)
		print("FROM player: ", current_player)

		left_cards[current_player] = message['num_left']
		if message['stage'] == DEBUG:
			print("DEBUGGING ERROR INFORMATION------------")
			for x in message:
				print(x, "  --  ", message[x])
			print("---------------------------------------")
		data = {"pile": message["pile"],
				"num_left": message['num_left'],
				"played": message['played'],
				"other_left": left_cards,
				"stage": GO,
				"player": 1,
				"all_played": message['all_played'],
				"color": message['color'],
				"said_uno": message['said_uno']
				}
		if 'taken' in message:
			data['taken'] = message['taken']
		if "reverse" in card and 'taken' not in message:
			reverse = not reverse
		# If the last played card is stop
		if "stop" in card and 'taken' not in message:
			# Current+2 is 1, rest are 0 (as skip in between)

			# If reverse, current -2
			for i in range(num_players):
				if (i == ((current_player + 2) % num_players) and not reverse) or (reverse and
										i == ((current_player - 2) % num_players)):
					data['player'] = 1
					print(current_player)
				else:
					data['player'] = 0
				data['num_left'] = previous['num_left']
				socks[i].sendto(dumps(data).encode(), addresses[i])
			current_player = ((current_player - 2) % num_players) if reverse \
				else ((current_player + 2) % num_players)

		# Not stop, so just relay info
		else:
			for i in range(num_players):
				if i != current_player:
					if (i == ((current_player + 1) % num_players) and not reverse) or\
						(i == ((current_player - 1) % num_players) and reverse):
						data['player'] = 1
					else:
						data['player'] = 0
					socks[i].sendto(dumps(data).encode(), addresses[i])
					print("Sent to player ", i)
			current_player = ((current_player + 1) % num_players) if not reverse\
							else ((current_player - 1) % num_players)

		if "stop" not in message['played']:
			previous = message
		prev_player = current_player
	elif message['stage'] == CHALLENGE:
		#From a current player to the previous player; need to send to previous player only
		print("UNO has not been said")
		#todo what if skipped?. sendt o previous player only if their uno not said. in main
		#rulebreaker = (current_player - 1) % num_players if not reverse else (current_player + 1)\
		#																	 % num_players
		rulebreaker = prev_player
		socks[rulebreaker].sendto(dumps(message).encode(), addresses[rulebreaker])
		print("Sent to player who forgot to take UNO")
		current_player = rulebreaker


	elif message['stage'] == ZEROCARDS:
		print("ENDING")
		taking_cards = "plus" in message['played']
		data = {"pile": message["pile"],
				"played": message['played'],
				"stage": ZEROCARDS,
				"player": 1,
				"all_played": message['all_played'],
				"color": message['color'],
				"to_take" : taking_cards
				}
		# Either: next takes cards, then all send. Or: all send
		for i in range(num_players):
			if i != current_player:
				if ((i == (current_player + 1) % num_players and not reverse) or
						(reverse and i == (current_player - 1) % num_players)) and taking_cards:
					socks[i].sendto(dumps(data).encode(), addresses[i])
					pts, a = socks[i].recvfrom(8000)
					resulting_points += loads(pts.decode())['points']
					print(resulting_points)
				else:
					data["to_take"] = False
					socks[i].sendto(dumps(data).encode(), addresses[i])
					pts, a = socks[i].recvfrom(8000)
					resulting_points += loads(pts.decode())['points']
					print(resulting_points)

		for i in range(num_players):
			msg = {'stage': CALC, 'points': resulting_points, 'winner': current_player}
			socks[i].sendto(dumps(msg).encode(), addresses[i])
