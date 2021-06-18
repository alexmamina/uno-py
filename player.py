from game import *
from time import *
class Player(Game):

	global new_deck
	new_deck = Deck()

	def __init__(self,master, q, message, sock, all_points):
		super().__init__(master,q,message, sock, all_points)
		self.aware = True
		self.am_challenging = False
		self.optimal = randint(0,100)
		if message['player'] == 1:
			print("First move")
			self.after(2000,self.make_move(message))

	def incoming(self):
		while self.q.qsize():
			try:
				msg = self.q.get(0)
				self.am_challenging = False
				# Played, pile, num_left, color, player, saiduno, taken
				# Normal play stage
				if msg['stage'] == GO:
					# Set the last played card and configure the pile + card counter
					self.set_played_img(msg)
					newC = msg['played']
					self.is_reversed = msg['dir']
					self.direction_l.config(text=self.set_label_next(msg))

					if "plustwo" in newC and 'taken' not in msg:
						self.card_counter = 2
						if self.modes[1]:
							self.stack_counter = msg['counter']
							self.stack_label.config(text='Stack\n cards to take:\n'+str(
								self.stack_counter))
							print("CTR: ",self.stack_counter)
					elif 'taken' in msg:
						self.stack_counter = 0
						self.stack_label.config(text='Stack\n cards to take:\n'+str(0))

					# Check if other player said UNO; place the challenge button if not said
					# Update label to show that
					if 'said_uno' in msg.keys() and not msg['said_uno']:
						uno_said = "\nUNO not said!"
						self.challenge = but(text="UNO not said!", bg='red', fg='white',
											 width=150, height=30,command=self.challengeUno)
						if msg['player'] == 1:
							self.challenge.place(x=30, y=120)
							if self.challenge:
								self.challengeUno()
								self.am_challenging = True

					else:
						uno_said = ""
					self.all_nums_of_cards = msg['other_left']
					left_cards_text = self.label_for_cards_left(msg['other_left'])
					left_cards_text += uno_said
					# Set up label with number of remaining cards
					self.cards_left.config(text=left_cards_text)
					# Enable buttons for cards if your turn; make UNO show if necessary
					if int(msg['player']) == 1:
						print("Your turn, enabling buttons")
						if 'plusfour' in newC and 'taken' not in msg and 'wild' in msg:
							# Show 'challenge +4' button
							self.valid_wild = but(text='Illegal +4?', bg='HotPink',fg='black',
												  width=150, height=30, borderless=1,
												  command=lambda valid=msg['wild']: self.challenge_plus(valid))
							self.valid_wild.place(x=30, y=230)
							from_player = (self.identity - 1) % len(msg['other_left'])\
											if not self.is_reversed else \
												self.identity+1 % len(msg['other_left'])
							prob_of_illegal = randint(0,100)
							if self.valid_wild and prob_of_illegal > 90:
								self.challenge_plus(msg['wild'])
								self.am_challenging = True
						# No moves possible, or move possible but need to take cards
						if not self.possible_move() or (self.card_counter == 2
														or self.card_counter == 4):
							self.new_card.config(state='normal')
						# Say your turn if either mode is normal, or take forever and not plus
						if (self.card_counter < 2 and not self.modes[2]) or \
								(self.modes[2] and not self.card_counter == 4 and not
								self.card_counter == 2) or (self.modes[1] and self.can_stack() and
															'two' in newC):
							self.turn.config(text="Your turn", bg='green')
							for i in self.hand_btns:
								self.hand_btns[i].config(state='normal')
							if self.modes[1] and self.can_stack() and 'two' in newC:
								for i in self.hand_btns:
									if 'two' not in self.hand_btns[i]['text']:
										self.hand_btns[i].config(state='disabled')
						else:
							self.turn.config(text="Your turn, take cards!", bg='green')
				# Forgot to say UNO - enable taking new cards only
				elif msg['stage'] == CHALLENGE:
					self.new_card.config(state='normal')
					if msg['why'] == 1:
						self.card_counter = 2
						self.turn.config(text="Your turn, take 2 cards!", bg='orange')

					else:
						self.card_counter = 4
						self.turn.config(text="Your turn, take 4 cards!", bg='orange')
					for i in range(self.card_counter):
						self.take_card()

				# Another player has finished the game; you either take cards if last is a plus,
				# or automatically send the remaining points for the other player
				elif msg['stage'] == ZEROCARDS:
					self.set_played_img(msg)
					if msg['to_take']:
						# Enable taking cards
						self.turn.config(text='Your turn, take cards!', bg='green')
						self.new_card.config(state='normal')
						self.card_counter = 2 if "two" in msg['played'] else 4
						if self.modes[1] and 'counter' in msg:
							self.stack_counter = msg['counter']
							self.stack_label.config(text='Stack\n cards to take:\n'+str(
								self.stack_counter))
						for i in range(self.card_counter):
							self.take_card()

					else:
						# No cards need to be taken, send current points
						points = {"stage" : CALC, "points" : self.calculate_points()}
						points['padding'] = 'a'*(685-len(str(points)))
						self.sock.send(dumps(points).encode('utf-8'))

					self.cards_left.config(text='Game over!')
				# Get points from the opponent and show them
				elif msg['stage'] == CALC:
					table_of_points = ""
					self.all_points = msg['total']
					for i in range(len(msg['total'])):
						table_of_points += "\n"+self.peeps[i]+": "+str(msg['total'][i])+" points\n"
					if msg['winner'] == self.identity:
						print("New game")
						m = [str(i+1) for i in range(3) if self.modes[i]]
						init = {'stage': INIT, "modes": m}
						init['padding'] = 'a'*(685-len(str(init)))
						self.sock.send(dumps(init).encode('utf-8'))

				elif msg['stage'] == SEVEN or msg['stage'] == ZERO:
					# Show hand, say who from, send back own hand
					hand = {'stage': msg['stage'],
							'hand': [self.hand_cards[c].name for c in self.hand_cards],
							'from': self.identity}

					self.update_btns(msg['hand'], msg['from'])

					hand['padding'] = 'a'*(685-len(str(hand)))
					m = dumps(hand)
					if not 'end' in msg:
						self.sock.send(m.encode('utf-8'))


				elif msg['stage'] == NUMUPDATE:
					self.cards_left.config(text=self.label_for_cards_left(msg['other_left']))

				elif msg['stage'] == INIT:
					print("New game!")
					self.start_new(msg)
				elif msg['stage'] == BYE:
					print("Received a BYE message, closing (another player decided to stop)")
					self.quit = True
					break
				if not self.quit:
					sleep(0.5)
					self.make_move(msg)

			except queue.Empty:
				pass
		if self.quit:
			print("Loop ended")
			self.close_window()

	def make_move(self, msg):
		if (msg['stage'] == GO or msg['stage'] == INIT) and not self.am_challenging \
				and not self.quit:
			#print("Played: ", msg['played'])
			if msg['stage'] == INIT:
				sleep(1)
			if ('taken' in msg or 'plus' not in msg['played']) \
					and msg['player'] == 1:
				self.take_or_place_card(msg['played'], msg['color'])
			elif 'plus' in msg['played'] and 'taken' not in msg:
				if self.stack_counter == 0:
					ctr = 2 if 'two' in msg['played'] else 4
				else:
					ctr = self.stack_counter
				sleep(0.5)
				if not self.can_stack() or 'four' in msg['played']:
					for i in range(ctr):
						self.take_card()
				else:
					self.stack_plus_two()
			#else:
				#print("move here")

	def stack_plus_two(self):
		n = list(self.hand_btns.keys())
		for i in n:
			if 'two' in self.hand_cards[i].name:
				self.say_uno(n, i)
				self.place_card(i, self.hand_btns[i])
				break

	def take_or_place_card(self, lst, col):
		found = False
		n = list(self.hand_btns.keys())
		if self.optimal > 66:
			if 'stop' in lst:
				for i in n:
					if 'stop' in self.hand_cards[i].name:
						self.say_uno(n, i)
						self.place_card(i, self.hand_btns[i])
						found = True
						break
			if not found:
				i = self.find_suitable_card(lst, col)
				if not i is None:
					print("LAST ", lst)
					print("PLACED ", self.hand_cards[i].name)
					self.say_uno(n, i)
					self.place_card(i, self.hand_btns[i])
					found = True
		else:
			for i in n:
				c = self.hand_cards[i].name
				if c[0:3] in lst[0:3] or c[3:] in lst[3:] or (col[0:3] in c and 'bla' in lst) or 'bla' \
						in c:
					print("LAST ", lst)
					print("PLACED ", self.hand_cards[i].name)
					#sleep(0.5)
					self.say_uno(n, i)
					self.place_card(i, self.hand_btns[i])
					found = True
					break
		if not found:
			self.take_card()
			print("TAKEN")
			ind = max(list(self.hand_cards.keys()))
			c = self.hand_cards[ind].name
			if not self.modes[2]:
				if c[0:3] in lst[0:3] or c[3:] in lst[3:] or (col[0:3] in c and 'bla' in lst) \
						or 'bla' in c:
					print("LAST ", lst)
					print("PLACED ", self.hand_cards[ind].name)
					self.say_uno(self.hand_cards, ind)
					self.place_card(ind, self.hand_btns[ind])
			else:
				while not (c[0:3] in lst[0:3] or c[3:] in lst[3:]
						   or (col[0:3] in c and 'bla' in lst) or 'bla' in c):
					self.take_card()
					print("TAKEN")
					ind = max(list(self.hand_cards.keys()))
					c = self.hand_cards[ind].name
				self.say_uno(self.hand_cards, ind)
				self.place_card(ind, self.hand_btns[ind])

	def find_suitable_card(self, lst, col):
		general_index = None
		n = list(self.hand_btns.keys())
		valid_cards = {}
		for i in n:
			c = self.hand_cards[i].name
			if c[0:3] in lst[0:3] or c[3:] in lst[3:] or (col[0:3] in c and 'bla' in lst) or 'bla' \
					in c:
				if re.search(r'\d+', c) is not None:
					valid_cards[c] = int(re.search(r'\d+', c).group())
				else:
					valid_cards[c] = 50 if 'bla' in c else 20
		remove_plus_four_probability = randint(0, 100)
		print(valid_cards)
		if remove_plus_four_probability > 40 and len(valid_cards) > 1:
			for i in list(valid_cards.keys()):
				if 'bla' in i:
					valid_cards.pop(i)
		print(valid_cards)
		if len(valid_cards) > 0:
			index = list(valid_cards.values()).index(max(valid_cards.values()))
			#print(max(valid_cards.values()))
			#print(index)
			new_card = list(valid_cards.keys())[index]
			#print(new_card)
			cards = [x.name for x in self.hand_cards.values()]
			ind = cards.index(new_card)
			general_index = list(self.hand_cards.keys())[ind]
			#print(general_index)
		return general_index

	def say_uno(self, n, i):
		if len(n) == 2 and 'stop' in self.hand_cards[i].name:
			sleep(0.3)
			self.one_card()
		elif len(n) == 2:
			r = randint(0,100)
			if r <= 95:
				self.one_card()

	def start_new(self, message):

		print("Destroying old game...")
		self.master.destroy()

		root = Tk()
		root.withdraw()
		root.configure(bg='white')
		root.geometry("700x553+250+120")
		root.title("UNO - player "+ str(message['whoami'])+" - "+message['peeps'][message[
			'whoami']])
		root.protocol("WM_DELETE_WINDOW", self.close_window)
		new = Player(root, self.q, message, self.sock, self.all_points)
		new.config_start_btns(message)
		new.checkPeriodically()
		new.mainloop()

	def place_card(self,ind, binst):
		if self.challenge:
			self.challenge.place_forget()
		if self.valid_wild:
			self.valid_wild.place_forget()
		card = self.hand_cards[ind].name
		old_card = self.last['text']

		# Same color (0:3), same symbol (3:), black
		if (card[0:3] == old_card[0:3] or card[3:] == old_card[3:] or "bla" in card[0:3]):

			binst.destroy()
			if 'reverse' in card:
				self.is_reversed = not self.is_reversed

			if 'plusfour' in card:
				is_valid_plus = self.can_put_plusfour()

			# Changes the black card to black with a color to show which one to play next
			if "bla" in card[0:3]:
				colors = {'red':0, 'blu':0, 'gre':0, 'yel':0}
				for i in self.hand_cards:
					temp_name = self.hand_cards[i].name
					if 'bla' not in temp_name:
						colors[temp_name[0:3]] += 1
				new_color = max(colors, key=lambda key: colors[key])
				new_color = new_color.lower()[0:3]
				# Get the colored black cards from the deck for ease of transfer
				if "plus" in card:
					new_color += "plus"
					card_col = new_color+"four.png"
					photocard = new_deck.get_special(new_color)
				else:
					new_color += "black"
					card_col = new_color+"black.png"
					photocard = new_deck.get_special(new_color)
			else: # Not a black card
				photocard = self.hand_cards[ind].card_pic
				card_col = card
			img = ImageTk.PhotoImage(photocard)
			self.last.config(image=img, text=card_col)
			self.last.image = img
			self.last.text = card_col
			# Remove card from 'hand', update label with number
			self.hand_cards.pop(ind)
			self.hand_btns.pop(ind)
			self.all_nums_of_cards[self.identity] -= 1
			text = self.label_for_cards_left(self.all_nums_of_cards)
			self.cards_left.config(text=text)
			ctr = 0
			for i in self.hand_btns.keys():
				# Move all buttons
				b = self.hand_btns[i]
				coords = self.get_card_placement(len(self.hand_btns),ctr)
				b.place(x=coords[1], y=coords[2])
				ctr += 1

			data_to_send = {
				"played" : card,
				"pile" : self.pile,
				"stage" : GO,
				"color" : card_col,
				"num_left" : len(self.hand_cards)
			}
			if 'plusfour' in card:
				data_to_send['wild'] = is_valid_plus
			# If placed plustwo in the mode, send the counter
			elif 'two' in card and self.modes[1]:
				data_to_send['counter'] = self.stack_counter + 2
				self.stack_counter = 0
			if str(7) in card and self.modes[0] and len(self.hand_cards) > 0:
				players = [x for x in self.peeps if not self.peeps.index(x) == self.identity]
				#swap = Picker(self,"Swap", "Who would you like to swap your cards with?",
				#			  players)
				data_to_send['swapwith'] = self.peeps.index(players[0])
				#data_to_send['stage'] = SEVEN
				data_to_send['hand'] = [self.hand_cards[c].name for c in self.hand_cards]
			if str(0) in card and self.modes[0] and len(self.hand_cards) > 0:
				print("Zero")
				data_to_send['hand'] = [self.hand_cards[c].name for c in self.hand_cards]

			if self.uno:
				data_to_send['said_uno'] = True
			# Send all the information either in progress of the game, or to end it
			if len(self.hand_cards) > 0:
				self.sendInfo(data_to_send)
			else:
				self.sendFinal(data_to_send)

	def challenge_plus(self, is_valid):
		data = {'stage': CHALLENGE, 'why': 4}
		# If true that can't put +4, so it was illegal, send it
		if not is_valid:
			self.sendInfo(data)
			self.valid_wild.place_forget()
		else:
			self.card_counter = 6
			for i in range(self.card_counter):
				self.take_card()
