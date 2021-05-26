from socket import *
from sys import *

import game
from deck import *
from stages import *
sock = socket(AF_INET, SOCK_STREAM)

#ip = gethostbyname(gethostname())
ip = argv[1]
port = int(argv[2])
sock.bind((ip, port))
#print("CONNECT TO: \n", ip, " ", port)
num_players = int(argv[3])
socks = []
addresses = []
current_player = 0
sock.listen(128)
player_counter = 0

# Reshuffle pile and all_played if few cards left, else just return original pile
def fit_pile_to_size(pile, all_played):
	if len(pile) < 10:
		shuffle(all_played)
		pile += all_played
		all_played = []
	return pile, all_played


# Deck initialisation
d = Deck().deck
pile = [c.name for c in d]
#print(pile)
resulting_points = 0
first_card = pile.pop(7*num_players)
previous_message = {}
all_played = []
all_players_points = [0]*num_players
total_games_played = 0
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
				"player": 0}
previous_message = data_to_send
# End of initialisation
list_of_players = []

# Wait for clients to connect, save them
while player_counter < num_players:
	player, addr = sock.accept()
	socks.append(player)
	addresses.append(addr)
	list_of_players.append(player_counter)
	print("Connected player ", player_counter)
	n = num_players - 1 - player_counter
	print("Waiting for "+str(n)+" more players")
	player_counter += 1
curr_list_index = 0
if 'reverse' in first_card:
	list_of_players.reverse()
# Send the data: pile is first 7 + rest of pile common for all.
# Player 3 is current if reverse True
# Player 2 is current if stop True
# Else player 1 is current
for i in range(num_players):
	data_to_send['pile'] = pile[0:7] + pile[7*(num_players-i):7*(num_players-i)+10]
	data_to_send['whoami'] = i
	if (i == list_of_players[0] and "stop" not in first_card) or \
			(i == 1 and "stop" in first_card):
		data_to_send['player'] = 1
		current_player = i
		curr_list_index = 1 if (i == 1 and 'stop' in first_card) else 0
		prev_player = list_of_players[num_players-1]
	else:
		data_to_send['player'] = 0
	socks[i].sendto(dumps(data_to_send).encode('utf-8'), addresses[i])
	print("Sent init to player ", i)
	pile = pile[7:]

# ALL SENT
# Go - regular play, regular relay
	# Debug - change turn, regular play, print data
# Challenge - only send packet to make player take two cards
# Zerocards - one player is out of cards, forward to the other who will either take cards or send
	# points
# Calc - other player sends points
while True:
	print("Waiting for player ", current_player)
	json, addr = socks[current_player].recvfrom(16000)
	try:
		dec_json = json.decode('utf-8')
		message = loads(dec_json)
		#print(pile)
	except JSONDecodeError as e:
		print(str(e))
		break
	#print(message)
	if message['stage'] == GO or message['stage'] == DEBUG:
		card = message['played']

		print("PLAYED CARD: ", card)
		print("FROM player: ", current_player)

		if message['stage'] == DEBUG:
			print("DEBUGGING ERROR INFORMATION------------")
			for x in message:
				print(x, "  --  ", message[x])
			print("---------------------------------------")

		data = {"pile": pile,
				"num_left": message['num_left'],
				"played": message['played'],
				"other_left": left_cards,
				"stage": GO,
				"player": 1,

				"color": message['color']
				}
		if 'taken' not in message:
			all_played.append(card)
			#print(all_played)
			if not (pile[0:5] == message['pile'][0:5]):
				pile.pop(0)
		else:
			data['taken'] = message['taken']
			num_taken = message['num_left'] - left_cards[current_player]
			#print(num_taken)
			for i in range(num_taken):
				pile.pop(0)
		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)
		data['pile'] = pile[:10]
		left_cards[current_player] = message['num_left']
		data['other_left'] = left_cards
		if "reverse" in card and 'taken' not in message:
			list_of_players.reverse()
			curr_list_index = num_players - 1 - curr_list_index
		if message['num_left'] == 1 and 'said_uno' not in message.keys():
			data['said_uno'] = False
		elif 'said_uno' in message.keys() and message['said_uno']:
			data['said_uno'] = True
		# If the last played card is stop
		if "stop" in card and 'taken' not in message:
			# Current+2 is 1, rest are 0 (as skip in between)
			for i in range(num_players):
				if (i == list_of_players[(curr_list_index+2) % num_players]):
					data['player'] = 1
				else:
					data['player'] = 0
				data['num_left'] = previous_message['num_left']
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
			prev_player = current_player
			current_player = list_of_players[(curr_list_index+2) % num_players]
			curr_list_index = (curr_list_index + 2) % num_players

		# Not stop, so just relay info
		else:
			for i in range(num_players):
				if i != current_player:
					if i == list_of_players[(curr_list_index+1) % num_players]:
						data['player'] = 1
					else:
						data['player'] = 0
					socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
					print("Sent to player ", i)
			prev_player = current_player
			current_player = list_of_players[(curr_list_index+1) % num_players]
			#print(prev_player, " and now ", current_player)
			curr_list_index = (curr_list_index + 1) % num_players

		if "stop" not in message['played']:
			previous_message = message
	elif message['stage'] == CHALLENGE:
		# From a current player to the previous player; need to send to previous player only
		print("UNO has not been said")
		pile, all_played = fit_pile_to_size(pile, all_played)
		data = message
		data['pile'] = pile[:10]
		rulebreaker = prev_player
		socks[rulebreaker].sendto(dumps(message).encode('utf-8'), addresses[rulebreaker])
		#print("Sent to player who forgot to take UNO")
		prev_player = current_player
		current_player = rulebreaker

	elif message['stage'] == CHALLENGE_TAKEN:
		old = current_player
		current_player = prev_player
		prev_player = old
		left_cards[prev_player] = message['num_left']
		pile.pop(0)
		pile.pop(0)
		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)

		data = {"pile": pile[:10],
				"num_left": message['num_left'],
				"played": message['played'],
				"other_left": left_cards,
				"stage": GO,
				"player": 1,
				"color": message['color']
				}
		for i in range(num_players):
			if i != prev_player:
				if i == current_player:
					data['player'] = 1
				else:
					data['player'] = 0
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
				#print("Sent to player ", i)


	elif message['stage'] == ZEROCARDS:
		print("ENDING")
		taking_cards = "plus" in message['played']
		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)

		data = {"pile": pile[0:10],
				"played": message['played'],
				"stage": ZEROCARDS,
				"player": 1,
				"color": message['color'],
				"to_take" : taking_cards
				}
		# Either: next takes cards, then all send. Or: all send
		for i in range(num_players):
			if i != current_player:
				if not ((i == list_of_players[(curr_list_index+1) % num_players]) and taking_cards):
					data["to_take"] = False

				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
				pts, a = socks[i].recvfrom(8000)
				resulting_points += loads(pts.decode('utf-8'))['points']
				#print(resulting_points)

		all_players_points[current_player] += resulting_points
		#print(all_players_points)


		for i in range(num_players):
			msg = {'stage': CALC, 'points': resulting_points,
				   'total': all_players_points , 'winner': current_player}
			socks[i].sendto(dumps(msg).encode('utf-8'), addresses[i])

	elif message['stage'] == INIT:
		total_games_played += 1
		print("New game! Total played: ", total_games_played)
		# Deck initialisation
		d = Deck().deck
		pile = [c.name for c in d]
		all_played = []
		#print(pile)
		resulting_points = 0
		first_card = pile.pop(7*num_players)
		previous_message = {}
		# Black card will not be played first. If popped, reshuffle and get new
		while "bla" in first_card:
			pile.append(first_card)
			shuffle(pile)
			first_card = pile.pop(7*num_players)
		list_of_players.sort()
		left_cards = [7]*num_players
		# Skeleton of json to be sent
		data_to_send = {"stage": INIT,
						"played": first_card,
						"pile": pile[0:7],
						"num_left": 7,
						"other_left": left_cards,
						"color": first_card[0:3],
						"player": 0}
		previous_message = data_to_send

		if 'reverse' in first_card:
			list_of_players.reverse()

		for i in range(num_players):
			data_to_send['pile'] = pile[0:7] + pile[7*(num_players-i):7*(num_players-i)+10]
			data_to_send['whoami'] = i
			if (i == list_of_players[0] and "stop" not in first_card) or \
					(i == 1 and "stop" in first_card):
				data_to_send['player'] = 1
				current_player = i
				curr_list_index = 1 if (i == 1 and 'stop' in first_card) else 0
				prev_player = list_of_players[num_players-1]
			else:
				data_to_send['player'] = 0
			socks[i].sendto(dumps(data_to_send).encode('utf-8'), addresses[i])
			#print("Sent init to player ", i)
			pile = pile[7:]

	else:
		for i in range(num_players):
			if i != current_player:
				data = message
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
		print('Sending BYE message')
		break
for i in range(num_players):
	socks[i].close()
sock.close()
