from socket import *
from sys import *
import time
import game
from deck import *
from stages import *
sock = socket(AF_INET, SOCK_STREAM)
# [0] = 7/0, [1] = stack, [2] = take forever
modes = [False]*3
if str(0) not in argv[4]:
	modes[0] = str(1) in argv[4]
	if modes[0]:
		print("7/0 enabled")
	modes[1] = str(2) in argv[4]
	if modes[1]:
		print("Stacking enabled")
	modes[2] = str(3) in argv[4]
	if modes[2]:
		print("Taking many cards enabled")
ip = argv[1]
port = int(argv[2])
sock.bind((ip, port))
num_players = int(argv[3])
socks = []
addresses = []
current_player = 0
is_reversed = False
sock.listen(128)
player_counter = 0
stack_counter = 0


# Reshuffle pile and all_played if few cards left, else just return original pile
def fit_pile_to_size(pile, all_played):
	if len(pile) < 20:
		shuffle(all_played)
		pile += all_played
		all_played = []
	return pile, all_played


# Deck initialisation
d = Deck().deck
pile = [c.name for c in d]
resulting_points = 0
first_card = pile.pop(7*num_players)
previous_message = {}
peeps = []
all_played = []
all_players_points = [0]*num_players
total_games_played = 0
# Black card will not be played first. If popped, reshuffle and get new
while "bla" in first_card:
	pile.append(first_card)
	shuffle(pile)
	first_card = pile.pop(7*num_players)
'''
first_card = 'bluplustwo.png'
pile[0] = 'bluplustwo.png'
pile[1] = 'bluplustwo.png'
pile[2] = 'bluplustwo.png'
pile[9] = 'bluplustwo.png'
pile[10] = 'greplustwo.png'
pile[11] = 'greplustwo.png'
pile[7] = 'yelplustwo.png'
'''

left_cards = [7]*num_players
# Skeleton of json to be sent
data_to_send = {"stage": INIT,
				"modes": modes,
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
	name, a = player.recvfrom(200)
	peeps.append(name.decode('utf-8'))
	socks.append(player)
	addresses.append(addr)
	list_of_players.append(player_counter)
	print("Connected player ", player_counter)
	n = num_players - 1 - player_counter
	print("Waiting for "+str(n)+" more players")
	player_counter += 1
curr_list_index = 0
print(peeps)
data_to_send['peeps'] = peeps
if 'reverse' in first_card:
	list_of_players.reverse()
	is_reversed = not is_reversed
data_to_send['dir'] = is_reversed
# Send the data: pile is first 7 + rest of pile common for all.
# Player 3 is current if reverse True
# Player 2 is current if stop True
# Else player 1 is current
for i in range(num_players):
	data_to_send['pile'] = pile[0:7] + pile[7*(num_players-i):7*(num_players-i)+20]
	data_to_send['whoami'] = i
	if (i == list_of_players[0] and "stop" not in first_card) or \
			(i == 1 and "stop" in first_card):
		data_to_send['player'] = 1
		current_player = i
		curr_list_index = 1 if (i == 1 and 'stop' in first_card) else 0
		prev_player = list_of_players[num_players-1]
	else:
		data_to_send['player'] = 0
		if i == list_of_players[0] and 'stop' in first_card:
			data_to_send['curr'] = current_player + 1
		else:
			data_to_send['curr'] = current_player
	data_to_send['padding'] = 'a'*(685-len(str(data_to_send)))
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
#todo uno not said if stopped played sent to curr player on 2 (can't be fixed now)
while True:
	print("Waiting for player ", current_player)
	json, addr = socks[current_player].recvfrom(700)
	try:
		dec_json = json.decode('utf-8')
		message = loads(dec_json)
		#print(pile)
	except JSONDecodeError as e:
		print(str(e))
		print(json)
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
		if 'plusfour' in card and 'taken' not in message:
			data['wild'] = message['wild']
		if 'taken' not in message:
			all_played.append(card)
			#print(all_played)
			if not (pile[0:5] == message['pile'][0:5]):
				pile.pop(0)
				#print("Popped")
			if modes[2]:
				num_taken = message['num_left'] - left_cards[current_player]
				for i in range(num_taken):
					pile.pop(0)
		else:
			stack_counter = 0
			data['taken'] = message['taken']
			num_taken = message['num_left'] - left_cards[current_player]
			#print("Taken ", str(num_taken))
			for i in range(num_taken):
				pile.pop(0)
		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)
		data['pile'] = pile[:20]
		left_cards[current_player] = message['num_left']
		data['other_left'] = left_cards
		if str(7) in card and modes[0] and 'taken' not in message:
			swapped_player = message['swapwith']
			hand = message['hand']
			print("Player {} has {}".format(current_player, hand))
			print("Swapping hands")
			left_cards[swapped_player] = message['num_left']
			ask = {'stage': SEVEN,
				   "hand": hand,
				   "from": current_player}
			# Ask cards from the swapped player, send those to current, msg['cards'] to swapped
			ask['padding'] = 'a'*(685-len(str(ask)))
			socks[swapped_player].sendto(dumps(ask).encode('utf-8'),addresses[swapped_player])
			new_hand, add = socks[swapped_player].recvfrom(1000)
			js = loads(new_hand.decode('utf-8'))
			js.pop('padding')
			print("Player {} has {}".format(swapped_player, js['hand']))

			js['end'] = True
			js['padding'] = 'a'*(685-len(str(js)))
			socks[current_player].sendto(dumps(js).encode('utf-8'), addresses[current_player])
			# Swap number of cards
			left_cards[current_player] = len(loads(new_hand.decode('utf-8'))['hand'])

			data['other_left'] = left_cards

		if str(0) in card and modes[0] and 'taken' not in message:
			hand = message['hand']
			# Get the indices of current and next players
			i = list_of_players.index(current_player)
			next = (i + 1) % num_players
			swap = {'stage': ZERO,
					'hand': hand,
					'from': list_of_players[i]}
			swap['padding'] = 'a'*(685-len(str(swap)))
			j = dumps(swap)
			left_cards[list_of_players[next]] = len(hand)
			print("{}, len {}, goes to player {}".format(hand,len(hand), list_of_players[next]))

			socks[list_of_players[next]].sendto(j.encode('utf-8'), addresses[list_of_players[next]])
			other, ad = socks[list_of_players[next]].recvfrom(2000)
			j = other.decode('utf-8')
			j2 = loads(j)
			hand = j2['hand']
			i = (i + 1) % num_players
			next = (i + 1) % num_players
			while not (i == list_of_players.index(current_player)):
				swap = {'stage': ZERO,
						'hand': hand,
						'from': list_of_players[i]}
				swap['padding'] = 'a'*(685-len(str(swap)))
				print("{} goes to player {}".format(hand, list_of_players[next]))

				j = dumps(swap)
				left_cards[list_of_players[next]] = len(hand)
				socks[list_of_players[next]].sendto(j.encode('utf-8'), addresses[list_of_players[next]])
				other, ad = socks[list_of_players[next]].recvfrom(2000)
				j = other.decode('utf-8')
				j2 = loads(j)
				hand = j2['hand']
				i = (i + 1) % num_players
				next = (i + 1) % num_players
		data['other_left'] = left_cards

		if modes[1] and 'counter' in message:
			data['counter'] = message['counter']
			stack_counter = message['counter']

		if "reverse" in card and 'taken' not in message:
			list_of_players.reverse()
			is_reversed = not is_reversed
			curr_list_index = num_players - 1 - curr_list_index
		data['dir'] = is_reversed

		if message['num_left'] == 1 and 'said_uno' not in message.keys():
			data['said_uno'] = False
		elif 'said_uno' in message.keys() and message['said_uno']:
			data['said_uno'] = True
			data['from'] = current_player
		# If the last played card is stop
		if "stop" in card and 'taken' not in message:
			# Current+2 is 1, rest are 0 (as skip in between)

			for i in range(num_players):
				if i == list_of_players[(curr_list_index + 2) % num_players]:
					data['player'] = 1
				else:
					data['player'] = 0
					data['curr'] = list_of_players[((curr_list_index+2) % num_players)]
				data['num_left'] = previous_message['num_left']
				if 'padding' in data:
					data.pop('padding')
				data['padding'] = 'a'*(685-len(str(data)))

				print('in stop, ',len(str(data)))
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
			prev_player = current_player
			current_player = list_of_players[((curr_list_index+2) % num_players)]
			curr_list_index = (curr_list_index + 2) % num_players

		# Not stop, so just relay info
		else:

			for i in range(num_players):
				if i != current_player:
					if i == list_of_players[(curr_list_index+1) % num_players]:
						data['player'] = 1
					else:
						data['player'] = 0
						data['curr'] = list_of_players[((curr_list_index+1) % num_players)]
					if 'padding' in data:
						data.pop('padding')
					data['padding'] = 'a'*(685-len(str(data)))
					socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
					print("Sent to player ", i)
				else:

					left = {'stage': NUMUPDATE, 'other_left': left_cards}
					left['padding'] = 'a'*(685-len(str(left)))
					socks[i].sendto(dumps(left).encode('utf-8'), addresses[i])

			prev_player = current_player
			current_player = list_of_players[(curr_list_index+1) % num_players]
			#print(prev_player, " and now ", current_player)
			curr_list_index = (curr_list_index + 1) % num_players

		if "stop" not in message['played']:
			previous_message = message
	elif message['stage'] == CHALLENGE:
		# From a current player to the previous player; need to send to previous player only
		print("UNO has not been said or +4")
		pile, all_played = fit_pile_to_size(pile, all_played)
		data = message
		data['pile'] = pile[:20]
		data.pop('padding')
		rulebreaker = prev_player
		data['padding'] = 'a'*(685-len(str(data)))
		#print("CHAL ", len(dumps(data)))
		socks[rulebreaker].sendto(dumps(data).encode('utf-8'), addresses[rulebreaker])
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
		if 'why' in message and message['why'] == 4:
			pile.pop(0)
			pile.pop(0)

		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)

		data = {"pile": pile[:20],
				"num_left": message['num_left'],
				"played": message['played'],
				"other_left": left_cards,
				"stage": GO,
				"player": 1,
				"color": message['color']
				}

		if 'why' in message and message['why'] == 4:
			data['taken'] = True
		data['dir'] = is_reversed
		data['counter'] = stack_counter
		data['padding'] = 'a'*(685-len(str(data)))

		for i in range(num_players):

			if i != prev_player:
				if i == current_player:
					data['player'] = 1
				else:
					data['player'] = 0
					data['curr'] = current_player
				data.pop('padding')
				data['padding'] = 'a'*(685-len(str(data)))
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
				#print("Sent to player ", i)


	elif message['stage'] == ZEROCARDS:
		print("ENDING")
		taking_cards = "plus" in message['played']
		pile, all_played = fit_pile_to_size(pile, all_played)
		#print(pile, all_played)

		data = {"pile": pile[0:20],
				"played": message['played'],
				"stage": ZEROCARDS,
				"player": 1,
				"color": message['color'],
				"to_take" : taking_cards
				}
		if 'counter' in message and modes[1]:
			data['counter'] = message['counter']
			stack_counter = message['counter']
		# Either: next takes cards, then all send. Or: all send
		data['padding'] = 'a'*(685-len(str(data)))

		for i in range(num_players):
			if i != current_player:
				if not ((i == list_of_players[(curr_list_index+1) % num_players]) and taking_cards):
					data.pop('padding')
					data["to_take"] = False
					data['padding'] = 'a'*(685-len(str(data)))
				else:
					data.pop('padding')
					data['to_take'] = True
					data['padding'] = 'a'*(685-len(str(data)))
				#print(685-len(str(data)))
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])
				pts, a = socks[i].recvfrom(1000)
				resulting_points += loads(pts.decode('utf-8'))['points']
				#print(resulting_points)

		all_players_points[current_player] += resulting_points
		#print(all_players_points)


		for i in range(num_players):
			msg = {'stage': CALC, 'points': resulting_points,
				   'total': all_players_points , 'winner': current_player}
			msg['padding'] = 'a'*(685-len(str(msg)))
			socks[i].sendto(dumps(msg).encode('utf-8'), addresses[i])

	elif message['stage'] == INIT:
		total_games_played += 1
		print("New game! Total played: ", total_games_played)
		# Deck initialisation
		d = Deck().deck
		pile = [c.name for c in d]
		all_played = []
		modes = [False]*3
		if message['modes'] is not None and len(message['modes']) > 0:
			modes[0] = '1' in message['modes']
			modes[1] = '2' in message['modes']
			modes[2] = '3' in message['modes']
		#print(pile)
		#print(modes)
		resulting_points = 0
		first_card = pile.pop(7*num_players)
		previous_message = {}
		# Black card will not be played first. If popped, reshuffle and get new
		while "bla" in first_card:
			pile.append(first_card)
			shuffle(pile)
			first_card = pile.pop(7*num_players)
		list_of_players.sort()
		is_reversed = False
		left_cards = [7]*num_players
		# Skeleton of json to be sent
		data_to_send = {"stage": INIT,
						"modes": modes,
						"played": first_card,
						"pile": pile[0:7],
						"num_left": 7,
						"other_left": left_cards,
						"color": first_card[0:3],
						"player": 0}
		previous_message = data_to_send
		data_to_send['peeps'] = peeps

		if 'reverse' in first_card:
			list_of_players.reverse()
			is_reversed = not is_reversed
		data_to_send['dir'] = is_reversed

		data_to_send['padding'] = ''
		#data_to_send['padding'] = 'a'*(685-len(str(data_to_send)))

		for i in range(num_players):
			data_to_send.pop('padding')
			data_to_send['pile'] = pile[0:7] + pile[7*(num_players-i):7*(num_players-i)+20]
			data_to_send['whoami'] = i
			if (i == list_of_players[0] and "stop" not in first_card) or \
					(i == 1 and "stop" in first_card):
				data_to_send['player'] = 1
				current_player = i
				curr_list_index = 1 if (i == 1 and 'stop' in first_card) else 0
				prev_player = list_of_players[num_players-1]
			else:
				data_to_send['player'] = 0
				data_to_send['curr'] = current_player
			data_to_send['padding'] = 'a'*(685-len(str(data_to_send)))
			socks[i].sendto(dumps(data_to_send).encode('utf-8'), addresses[i])
			#print("Sent init to player ", i)
			pile = pile[7:]

	elif message['stage'] == DESIGNUPD:
		print('design update')
		for i in range(num_players):
			if i != current_player:
				data = message
				socks[i].sendto(dumps(data).encode('utf-8'), addresses[i])

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
