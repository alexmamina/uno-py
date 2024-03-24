from tkinter import Frame, Label, Menu, Button, messagebox, Tk
from tkinter import simpledialog
import math
from PIL import ImageTk
import webbrowser
from typing import Any
from picker import Picker
from stages import Stage
import re
import queue
import json
from json import JSONDecodeError
from deck import Deck
from tkmacosx import Button as but


class Game(Frame):
	global new_deck
	new_deck = Deck()
	pile = new_deck.deck
	global message
	message = {}

	# Initialise a frame. Setup the pile, hand, last played card and all gui
	def __init__(self, master, queue, msg, sock, all_points):
		global message
		message = msg
		super().__init__(master)
		self.pack()
		self.peeps = message['peeps']
		self.move_id = '0'
		self.modes = msg['modes']
		self.sock = sock
		self.all_points = all_points
		self.parent = master
		self.master.protocol("WM_DELETE_WINDOW", self.close_window)
		# Take one card only
		self.card_counter = 1 if not self.modes[2] else 500
		self.q = queue
		self.quit = False
		self.identity = msg['whoami']
		self.last = None
		self.challenge = None
		self.valid_wild = None
		self.stack_counter = 0
		self.animated = False
		self.stack_label = Label(
			text=f"Stack\n cards to take:\n{str(self.stack_counter)}",
			fg='black',
			bg='PeachPuff',
			width=10,
			height=3)
		self.is_reversed = message['dir']
		self.direction_l = Label(
			text=self.set_label_next(message),
			fg='black',
			bg='Lavender',
			width=10,
			height=9
		)
		if self.modes[1]:
			self.stack_label.place(x=600, y=0)
			self.direction_l.place(x=600, y=80)
		else:
			self.direction_l.place(x=600, y=5)
		self.hand_cards = {}
		self.pile = msg['pile']
		self.all_nums_of_cards = msg['other_left']
		text_cards_left = "Your cards: " + str(7)
		pl = 0
		for x in msg['other_left']:
			if pl != self.identity:
				text_cards_left += f"\n {self.peeps[pl]} : {str(x)} cards"
			pl += 1
		self.cards_left = Label(
			text=text_cards_left,
			fg="blue",
			bg="pale green",
			width=20,
			height=5
		)
		self.cards_left.place(x=10, y=30)
		self.uno_but = but(
			text="UNO",
			fg="black",
			bg="deep sky blue",
			width=100,
			height=80,
			borderless=1,
			command=self.one_card
		)
		self.uno_but.place(x=50, y=150)
		self.uno = False
		self.new_card = None
		self.setup_menu()
		self.setup_pile(msg)
		self.cards = self.deal_cards(msg)
		# Button for debugging
		self.debug = but(
			text="Not my turn",
			fg='red',
			bg='white',
			borderless=1,
			width=100,
			height=30,
			command=self.send_debug)
		self.debug.place(x=600, y=498)
		self.hand_btns = {}
		self.setup_hand(self.cards)
		if msg['player'] == 1:
			if 'two' in msg['played'] and (not self.can_stack() or not self.modes[1]):
				self.turn = Label(
					text="Your turn, take cards",
					fg='white',
					bg='green',
					width=30,
					height=1)
			else:
				self.turn = Label(
					text="Your turn",
					fg='white',
					bg='green',
					width=30,
					height=1)
		else:
			self.turn = Label(
				text="Wait for other players!",
				fg='white',
				bg='red',
				width=30,
				height=1)
		self.turn.place(x=300, y=0)
		self.taken_label = Label(text="", fg="blue", bg="white", width=30, height=1)
		self.taken_label.place(x=300, y=20)

	# Create a hand of 7 cards from pile from message
	def deal_cards(self, message):
		global new_deck
		hand = []
		self.pile = message["pile"]
		for i in range(7):
			c = self.pile.pop(0)
			# Lookup the card name from pile to get card itself
			card = new_deck.get_card(c)
			hand.append(card)  # CARDS
		return hand

	# Create a menu bar, configure to add to parent (which is the root window)
	def setup_menu(self):
		menubar = Menu(self)

		menu = Menu(menubar)
		menu.add_command(label="Rules", command=show_rules)
		menu.add_command(label="Points", command=self.show_points)
		menu.add_command(label="Toggle animation", command=self.set_anim)
		menubar.add_cascade(label="Menu", menu=menu)
		mode = Menu(menubar)
		if not any(self.modes):
			mode.add_command(label="Regular enabled")
		else:
			if self.modes[1]:
				mode.add_command(
					label="Stack enabled", command=lambda i=2: show_mode(i)
				)
			if self.modes[0]:
				mode.add_command(label="7-0 enabled", command=lambda i=1: show_mode(i))
			if self.modes[2]:
				mode.add_command(
					label="Take many cards enabled", command=lambda i=3: show_mode(i)
				)
		menubar.add_cascade(label="Game mode rules", menu=mode)

		self.parent.configure(menu=menubar)

	# Add the pile and last played buttons
	def setup_pile(self, message):
		photo = ImageTk.PhotoImage(deck.backofcard)  # deck is a class, backofcard is global. make dataclass?
		# Button to take a card (so a pile)
		self.new_card = Button(
			image=photo, width=117, height=183, command=self.take_card
		)
		self.new_card.image = photo
		self.new_card.place(x=300, y=50)
		# Last played card from the message
		lastplayed2 = message["played"]  # this is a name!!
		photo2 = ImageTk.PhotoImage(new_deck.get_card(lastplayed2).card_pic)
		# Last is a disabled button with the last played card shown
		self.last = Button(
			text=lastplayed2,
			image=photo2,
			width=117,
			height=183,
			border=0,
			state="disabled",
		)
		self.last.image = photo2
		self.last.place(x=453, y=50)

	def setup_hand(self, dealt_cards):
		n = len(dealt_cards)
		for i in range(n):
			# Create a button for each card in dealt cards, add a command
			photo = ImageTk.PhotoImage(dealt_cards[i].card_pic)
			b = Button(
				text=dealt_cards[i].name,
				image=photo,
				width=117,
				height=183,
				border=0,
				bg="white",
			)
			b['command'] = lambda ind=i, binst=b: self.place_card(ind, binst)
			b.image = photo
			self.hand_btns[i] = b
			self.hand_cards[i] = dealt_cards[i]
			coords = self.get_card_placement(n,i)
			b.place(x=coords[1], y=coords[2])

	# Move card to the pile in an animation
	def move(self, origx, origy, dx, dy, i, binst, img, ind):
		card = self.hand_cards[ind].name
		ratio = 20 if abs(dx) < 250 else 40
		time = 5 if abs(dx) < 250 else 2
		if not i == ratio:
			x = origx + (dx / ratio) * i
			y = origy + (dy / ratio) * i
			binst.place(x=x, y=y)
			i += 1
			self.move_id = self.after(5, self.move, origx, origy, dx, dy, i, binst, img, ind)
		else:
			self.after_cancel(self.move_id)
			binst.destroy()
			self.move_id = 'ended'
			self.complete_placement(card, ind)

	def get_card_placement(self, num_cards, i):
		# Returns coordinates of a button  given specific parameters
		# Like the width and length of cards, as well as how apart they should be
		result = []
		if num_cards == 1:
			num_cards = 2
		if num_cards <= 15:
			overlap = math.floor((117 - ((117 * num_cards) - 650) / (num_cards - 1)))
		else:
			overlap = math.floor((117 - ((117 * 15) - 650) / (15 - 1)))
		result.append(overlap)
		result.append(25 + overlap * (i % 15) + 15 * (math.floor(i / 15)))
		result.append(280 + 40 * (math.floor(i / 15)))
		return result

	# #################################### EVENTS ##################################
	def place_card(self, ind, binst):
		if self.challenge:
			self.challenge.place_forget()
		if self.valid_wild:
			self.valid_wild.place_forget()
		card = self.hand_cards[ind].name
		old_card = self.last['text']
		# Same color (0:3), same symbol (3:), black
		if card[0:3] == old_card[0:3] or card[3:] == old_card[3:] or "bla" in card[0:3]:
			dest_x = self.last.winfo_x()
			dest_y = self.last.winfo_y()
			orig_x = binst.winfo_x()
			orig_y = binst.winfo_y()
			dx = dest_x - orig_x
			dy = dest_y - orig_y
			# If animation is turned on, move, else place on pile straight away
			if self.animated:
				self.move_id = self.move(orig_x, orig_y, dx, dy, 0, binst, self.last.image, ind)
			else:
				binst.destroy()
				self.complete_placement(card, ind)

	# Set new card on pile, send information, update hand - after animation or straight away
	def complete_placement(self, card, ind):
		if 'reverse' in card:
			self.is_reversed = not self.is_reversed

		if 'plusfour' in card:
			is_valid_plus = self.can_put_plusfour()

		# Changes the black card to black with a color to show which one to play next
		if "bla" in card[0:3]:
			picker = Picker(self, "New color", "Which one?", ['Red', 'Green', 'Blue', 'Yellow'])
			new_color = picker.result
			new_color = new_color.lower()[0:3]
			# Get the colored black cards from the deck for ease of transfer
			if "plus" in card:
				new_color += "plus"
				card_col = new_color + "four.png"
				photocard = new_deck.get_special(new_color)
			else:
				new_color += "black"
				card_col = new_color + "black.png"
				photocard = new_deck.get_special(new_color)
		else:  # Not a black card
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
			"played": card,
			"pile": self.pile,
			"stage": Stage.GO,
			"color": card_col,
			"num_left": len(self.hand_cards)
		}
		if "plusfour" in card:
			data_to_send["wild"] = is_valid_plus
		# If placed plustwo in the mode, send the counter
		elif "two" in card and self.modes[1]:
			data_to_send["counter"] = self.stack_counter + 2
			self.stack_counter = 0
		if str(7) in card and self.modes[0] and len(self.hand_cards) > 0:
			players = [
				x for x in self.peeps if not self.peeps.index(x) == self.identity
			]
			swap = Picker(
				self, "Swap", "Who would you like to swap your cards with?", players
			)
			data_to_send["swapwith"] = self.peeps.index(swap.result)
			# data_to_send['stage'] = Stage.SEVEN
			data_to_send["hand"] = [self.hand_cards[c].name for c in self.hand_cards]
		if str(0) in card and self.modes[0] and len(self.hand_cards) > 0:
			print("Zero")
			data_to_send["hand"] = [self.hand_cards[c].name for c in self.hand_cards]

		if self.uno:
			data_to_send["said_uno"] = True
		# Send all the information either in progress of the game, or to end it
		if len(self.hand_cards) > 0:
			self.sendInfo(data_to_send)
		else:
			self.sendFinal(data_to_send)

	def take_card(self):
		global new_deck, message

		# Take new card
		new = new_deck.get_card(self.pile.pop(0))
		# Remove the 'uno not placed' button as was ignored
		if self.challenge:
			self.challenge.place_forget()
		if self.valid_wild:
			self.valid_wild.place_forget()
		# Decrease number of cards that need to be taken
		self.card_counter -= 1
		if self.stack_counter > 0 and self.modes[1] and "two" in self.last["text"]:
			self.stack_counter -= 1
			self.stack_label.config(
				text=f"Stack\n cards to take:\n{str(self.stack_counter)}"
			)
			print("Stack: ", self.stack_counter)

		# Since hand is a dict, the keys aren't in order.
		# Get the largest and add 1 for the next
		ind = max(list(self.hand_cards.keys())) + 1
		# Add new card to the 'hand', create new button, update number
		self.hand_cards[ind] = new
		photo = ImageTk.PhotoImage(new.card_pic)
		b = Button(
			text=new.name,
			image=photo,
			width=117,
			height=183,
			border=0,
			bg="white",
			state="disabled",
		)
		b["command"] = lambda ind=ind, binst=b: self.place_card(ind, binst)
		b.image = photo
		self.hand_btns[ind] = b
		self.all_nums_of_cards[self.identity] += 1
		text = self.label_for_cards_left(self.all_nums_of_cards)
		self.cards_left.config(text=text)
		ctr = 0
		print("Card counter: ", self.card_counter)
		print("Stack counter: ", self.stack_counter)
		# Is it possible to place a card right now?
		possible_move = self.possible_move()

		if (
			possible_move and
			(self.card_counter == 0 or (self.modes[2] and self.card_counter > 6)) and
			self.stack_counter == 0
		):
			self.new_card.config(state='disabled')
			b.config(state='normal')
		for i in self.hand_btns.keys():
			# Move all buttons
			b = self.hand_btns[i]
			coords = self.get_card_placement(len(self.hand_btns),ctr)
			b.place(x=coords[1], y=coords[2])
			ctr += 1

		# Send the points from the cards if you had to take them at the end (last played was +,
		# but game is over)
		if self.card_counter <= 0 and \
			self.stack_counter == 0 and 'stage' in message.keys() and \
			message['stage'] == Stage.ZEROCARDS:
			data_to_send = {"stage": Stage.CALC, "points": self.calculate_points()}
			self.sendInfo(data_to_send)

		# Send information about taken cards if can't go or had to take +2/4 due to challenge or
		# card
		if self.card_counter <= 0 and self.stack_counter == 0 and \
			(possible_move is False or ('taken' not in message and
				"plus" in self.last['text']) or message['stage'] == Stage.CHALLENGE):
			data_to_send = {
				"played": self.last['text'],
				"pile": self.pile,
				"stage": Stage.GO,
				"color": self.last['text'][0:3],
				"num_left": len(self.hand_cards)
			}
			if message['stage'] != Stage.CHALLENGE:
				data_to_send['taken'] = True
			else:
				data_to_send['stage'] = Stage.CHALLENGE_TAKEN
				data_to_send['why'] = message['why']
			self.sendInfo(data_to_send)

	# Remove UNO button when clicked, set the value to True to be sent
	def one_card(self):
		if self.uno:
			self.uno = False
			self.uno_but.config(bg="white")
			self.uno_but.config(bg='deep sky blue')

		else:
			self.uno = True
			self.uno_but.config(bg="lime green")
			# self.uno_but.place_forget()
		print("UNO")

	# Show the points that you have with your cards right now (option in menu)
	def show_points(self):
		text = f"Your points this session: {str(self.all_points[self.identity])}\n"
		for i in range(len(self.all_points)):
			if i == self.identity:
				text += "(You) "
			text += "{}: {} points\n".format(self.peeps[i], self.all_points[i])
		messagebox.showinfo("Points", text)

	# Go through the hand and calculate points; regex is for finding numbers
	def calculate_points(self):
		result = 0
		for k in self.hand_cards.keys():
			c = self.hand_cards[k].name
			if re.search(r'\d+', c) is not None:
				point = int(re.search(r'\d+', c).group())
				result += point
			else:
				# non-numbers
				if ("two" in c or "reverse" in c or "stop" in c):
					result += 20
				else:
					result += 50
		return result

	def incoming(self):
		while self.q.qsize():
			try:
				msg = self.q.get(0)
				# Played, pile, num_left, color, player, saiduno, taken
				print("LOOKING AT MESSAGE")
				# show(msg)
				# Normal play stage
				if msg['stage'] == Stage.GO:
					# Set the last played card and configure the pile + card counter
					self.set_played_img(msg)
					newC = msg['played']
					print("Played: ", newC)
					self.is_reversed = msg['dir']
					self.direction_l.config(text=self.set_label_next(msg))

					if "plustwo" in newC and 'taken' not in msg:
						self.card_counter = 2
						if self.modes[1]:
							self.stack_counter = msg['counter']
							self.stack_label.config(text=f'Stack\n cards to take:\n \
							{str(self.stack_counter)}')
							print("CTR: ", self.stack_counter)
						self.taken_label.config(text='')
					elif 'taken' in msg:
						self.stack_counter = 0
						self.stack_label.config(text=f'Stack\n cards to take:\n{str(0)}')
						self.taken_label.config(text='Other player took cards!')
					else:
						self.taken_label.config(text='')
					# Check if other player said UNO; place the challenge button if not said
					# Update label to show that
					if 'said_uno' in msg.keys() and not msg['said_uno']:
						uno_said = "\nUNO not said!"
						self.challenge = but(
							text="UNO not said!",
							bg='red',
							fg='white',
							width=150,
							height=30,
							command=self.challengeUno)
						if msg['player'] == 1:
							self.challenge.place(x=30, y=120)
					elif 'said_uno' in msg.keys() and msg['said_uno'] and 1 in msg['other_left']:
						uno_said = "\nUNO said!"
						p = msg['from']
						print("From: ", p)
						# todo this says wrong player if uno after 7/0
						if '0' in newC and 'taken' not in msg and self.modes[0]:
							if self.is_reversed:
								p = (p - 1) % len(self.peeps)
							else:
								p = (p + 1) % len(self.peeps)
						if p != self.identity:
							messagebox.showinfo("UNO", self.peeps[p] + " has only 1 card left!")
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
							self.valid_wild = but(
								text='Illegal +4?',
								bg='HotPink',
								fg='black',
								width=150,
								height=30,
								borderless=1,
								command=lambda valid=msg['wild']: self.challenge_plus(valid))
							self.valid_wild.place(x=30, y=230)
						# No moves possible, or move possible but need to take cards
						if not self.possible_move() or \
							(self.card_counter == 2 or self.card_counter == 4):
							self.new_card.config(state='normal')
						# Say your turn if either mode is normal, or take forever and not plus
						if (self.card_counter < 2 and not self.modes[2]) or \
							(self.modes[2] and not self.card_counter == 4 and not
								self.card_counter == 2) or \
							(self.modes[1] and self.can_stack() and 'two' in newC):
							self.turn.config(text="Your turn", bg='green')
							for i in self.hand_btns:
								self.hand_btns[i].config(state='normal')
							if self.modes[1] and self.can_stack() and 'two' in newC and \
								'taken' not in msg and self.stack_counter > 0:
								for i in self.hand_btns:
									if 'two' not in self.hand_btns[i]['text']:
										self.hand_btns[i].config(state='disabled')
						else:
							self.turn.config(text="Your turn, take cards!", bg='green')
				# Forgot to say UNO - enable taking new cards only
				elif msg['stage'] == Stage.CHALLENGE:
					self.new_card.config(state='normal')
					if msg['why'] == 1:
						self.card_counter = 2
						messagebox.showinfo(
							"UNO not said!",
							"You forgot to click UNO, so take 2 cards!")
						self.turn.config(text="Your turn, take 2 cards!", bg='orange')
					else:
						self.card_counter = 4
						messagebox.showinfo(
							"Illegal +4!",
							"You can't put +4 when you have other cards, so take 4!")
						self.turn.config(text="Your turn, take 4 cards!", bg='orange')

				# Another player has finished the game; you either take cards if last is a plus,
				# or automatically send the remaining points for the other player
				elif msg['stage'] == Stage.ZEROCARDS:
					self.set_played_img(msg)
					if msg['to_take']:
						# Enable taking cards
						self.turn.config(text='Your turn, take cards!', bg='green')
						self.new_card.config(state='normal')
						self.card_counter = 2 if "two" in msg['played'] else 4
						if self.modes[1] and 'counter' in msg:
							self.stack_counter = msg['counter']
							self.stack_label.config(text=f'Stack\n cards to take:\n \
								{str(self.stack_counter)}')

					else:
						# No cards need to be taken, send current points
						points = {"stage": Stage.CALC, "points": self.calculate_points()}
						points['padding'] = 'a' * (685 - len(str(points)))
						self.sock.send(json.dumps(points).encode('utf-8'))

					self.cards_left.config(text='Game over!')
				# Get points from the opponent and show them
				elif msg['stage'] == Stage.CALC:
					table_of_points = ""
					self.all_points = msg['total']
					for i in range(len(msg['total'])):
						table_of_points += f"\n{self.peeps[i]}: {str(msg['total'][i])} points\n"
					if msg['winner'] == self.identity:
						messagebox.showinfo(
							"Win",
							f"You won {str(msg['points'])} points!\n\n" +
							f" Total this session: \n{table_of_points}")
						ans = messagebox.askyesno(
							"New",
							"Would you like to continue with a new game?")
						if ans == 1:
							modes = simpledialog.askstring(
								"Modes",
								"Input the modes (without spaces) that you'd like to use this game"
								" (or press enter for a normal game):\n"
								"1. 7/0\n"
								"2. Stack +2\n"
								"3. Take many cards at once")
							init = {'stage': Stage.INIT, "modes": modes}
							init['padding'] = 'a' * (685 - len(str(init)))
							self.sock.send(json.dumps(init).encode('utf-8'))
						else:
							# Don't want the new game

							bye = {"stage": Stage.BYE}
							bye['padding'] = 'a' * (685 - len(str(bye)))
							self.sock.send(json.dumps(bye).encode('utf-8'))
							print("No new game, sending a BYE message")
							self.quit = True
							break

					else:
						messagebox.showinfo(
							"Win",
							f"{self.peeps[msg['winner']]} won {str(msg['points'])} points!\n" +
							f" Total this session: \n{table_of_points}"
						)

				elif msg['stage'] == Stage.SEVEN or msg['stage'] == Stage.ZERO:
					# Show hand, say who from, send back own hand
					hand = {
						'stage': msg['stage'],
						'hand': [self.hand_cards[c].name for c in self.hand_cards],
						'from': self.identity
					}

					self.update_btns(msg['hand'], msg['from'])
					if msg['stage'] == Stage.SEVEN:
						messagebox.showinfo(
							"New cards",
							f"A 7 was played. \nYou swapped cards with {self.peeps[msg['from']]}")
					else:
						messagebox.showinfo(
							"New cards",
							f"A 0 was played. You get cards from \n{self.peeps[msg['from']]}")

					hand['padding'] = 'a' * (685 - len(str(hand)))
					m = json.dumps(hand)
					if 'end' not in msg:
						self.sock.send(m.encode('utf-8'))

				elif msg['stage'] == Stage.NUMUPDATE:
					self.cards_left.config(text=self.label_for_cards_left(msg['other_left']))

				elif msg['stage'] == Stage.INIT:
					print("New game!")
					self.start_new(msg)
				elif msg['stage'] == Stage.BYE:
					print("Received a BYE message, closing (another player decided to stop)")
					self.quit = True
					break

			except queue.Empty:
				pass
		if self.quit:
			print("Loop ended")
			self.close_window()

	def set_played_img(self, msg):
		newC = msg['played']
		# if plus take cards else send points
		if 'four' in newC:
			newC = msg['color'][0:3] + "plusfour.png"
			img = ImageTk.PhotoImage(new_deck.get_special(newC))
			if 'taken' not in msg:
				self.card_counter = 4
			else:
				self.card_counter = 1 if not self.modes[2] else 500
		elif 'bla' in newC:
			newC = msg['color'][0:3] + "black.png"
			img = ImageTk.PhotoImage(new_deck.get_special(newC))
		else:
			img = ImageTk.PhotoImage(new_deck.get_card(newC).card_pic)
			self.card_counter = 1 if not self.modes[2] else 500
		self.last.config(image=img, text=newC)
		self.last.image = img
		self.pile = msg['pile']

	# Put received message in queue for async processing
	def receive(self):
		global message, root
		while not self.quit:
			print("Waiting")
			try:
				json, addr = self.sock.recvfrom(700)
				# print("LENGTH: ", len(json))
				data = json.decode('utf-8')
				message = json.loads(data)
				if len(data) < 700:
					print("[BUG] This message is short, find out why!")
					print(message)
					print("PADDING: ", len(message['padding']))
				self.q.put(message)
			except JSONDecodeError as er:
				if "Expecting value" in str(er):
					print("Another player's socket has been closed")
				elif "Unterminated string" in str(er):
					print(data)
					print("[BUG] TELL ME TO INCREASE BUFFER SIZE")
				elif "Extra data" in str(er):
					print(data)
					print("[BUG] TELL ME TO LOOK AT MESSAGE SIZE")
				else:
					print(er)
					print("[BUG] Different decoding error line 491")
					print(data)
				break
			except OSError as o:
				if o.errno == 9:
					print("Socket closed, no more receiving messages")
					break
				else:
					print(o)
					break
		print("No more receiving messages")

	# Disable all buttons when sending information and when it's not your turn anymore
	def sendInfo(self, data_to_send):
		data_to_send['padding'] = 'a' * (685 - len(str(data_to_send)))
		self.sock.send(json.dumps(data_to_send).encode('utf-8'))
		self.new_card.config(state="disabled")
		self.uno = False
		self.card_counter = 1 if not self.modes[2] else 500
		self.uno_but.config(bg="deep sky blue")
		if data_to_send['stage'] == Stage.GO and 'stop' in data_to_send['played'] \
			and 'taken' not in data_to_send:
			self.update_next_lbl(2)
		elif data_to_send['stage'] == Stage.GO:
			self.update_next_lbl(1)

		for i in self.hand_btns:
			self.hand_btns[i].config(state='disabled')
		self.turn.config(text="Wait for other players!", bg='red')
		self.taken_label.config(text='')
		print("Not your turn anymore")

	# Notify opponent that they forgot to say UNO; when clicking button
	def challengeUno(self):
		data = {"stage": Stage.CHALLENGE, 'why': 1}
		if self.modes[1] and self.stack_counter > 0:
			data['counter'] = self.stack_counter
		self.sendInfo(data)
		self.challenge.place_forget()

	def challenge_plus(self, is_valid):
		data = {'stage': Stage.CHALLENGE, 'why': 4}
		# If true that can't put +4, so it was illegal, send it
		if not is_valid:
			self.sendInfo(data)
			self.valid_wild.place_forget()
		else:
			self.card_counter = 6
			messagebox.showinfo("Legal move", "The player was honest, so take 6 cards!")

	# If for some reason the turn didn't change, this sends current info to server who prints it
	# out and changes turns
	def send_debug(self):
		print("Changing turns")
		data = {
			'stage': Stage.DEBUG,
			"played": self.last['text'],
			"pile": self.pile,
			"hand": [self.hand_cards[x].name for x in self.hand_cards],
			"num_left": len(self.hand_cards),
			"color": self.last['text'],
			"taken": True
		}
		self.sendInfo(data)

	# Send all the final information with 0 cards left to end/finalise the game
	def sendFinal(self, data_to_send):
		print("END")
		data_to_send['stage'] = Stage.ZEROCARDS
		self.new_card.config(state="disabled")
		self.uno = False
		self.card_counter = 1 if not self.modes[2] else 500
		self.taken_label.config(text='')
		# self.uno_but.config(fg="red", bg="white", state='disabled')
		# self.uno_but.place_forget()
		self.turn.config(text="Waiting for the results!", bg='white', fg='blue')
		data_to_send['padding'] = 'a' * (685 - len(str(data_to_send)))
		self.sock.send(json.dumps(data_to_send).encode('utf-8'))
		print("Not your turn anymore")

	# Go through the hand and see if there are cards that could be played
	def possible_move(self):
		move = False
		for i in self.hand_cards.keys():
			c = self.hand_cards[i]
			if "bla" in c.name or self.last['text'][0:3] in c.name or self.last['text'][3:] \
				in c.name:
				move = move or True
		return move

	def can_put_plusfour(self):
		result = True
		curr = self.last['text']
		for i in self.hand_cards:
			c = self.hand_cards[i]
			if curr[0:3] in c.name:  # Color
				result = False
				break
			else:
				result = True

		return result

	def can_stack(self):
		result = False
		for i in self.hand_cards:
			if 'two' in self.hand_cards[i].name:
				result = True
		return result

	# From a list of numbers of cards left from other players return the text to show
	# in the label
	def label_for_cards_left(self, others):
		# left_cards_text = "Your cards: " + str(len(self.hand_cards))
		left_cards_text = "Your cards: " + str(others[self.identity])
		pl = 0
		for x in others:
			if pl != self.identity:
				left_cards_text += f"\n {self.peeps[pl]}: {str(x)} cards"
			pl += 1
		return left_cards_text

	def update_btns(self, new_hand, player):
		global new_deck
		old = len(self.hand_btns)
		new = len(new_hand)
		for i in self.hand_btns:
			self.hand_btns[i].destroy()
		self.hand_btns = {}
		self.hand_cards = {}
		for i in range(len(new_hand)):
			# Add new card
			c = new_hand[i]
			self.hand_cards[i] = new_deck.get_card(c)
		self.setup_hand(self.hand_cards)
		for j in self.hand_btns:
			self.hand_btns[j].config(state='disabled')
		self.all_nums_of_cards[self.identity] = new
		self.all_nums_of_cards[player] = old
		self.cards_left.config(text=self.label_for_cards_left(self.all_nums_of_cards))

	def set_label_next(self, msg):
		if msg['player'] == 1:
			a = self.identity
			curr = "Current:\nYou\n\n"
		else:
			a = msg['curr']
			curr = f"Current:\n{self.peeps[a]}\n\n"
		next = "Next:\n"
		if not self.is_reversed:
			for i in range(a + 1, a + len(self.peeps) + 1):
				if not (i % len(self.peeps)) == self.identity:
					next += f"{self.peeps[(i % len(self.peeps))]}\n"
				else:
					next += "You\n"
		else:
			for i in range(a - 1, a - 1 - len(self.peeps), -1):
				if not (i % len(self.peeps)) == self.identity:
					next += f"{self.peeps[(i % len(self.peeps))]}\n"
				else:
					next += "You\n"
		return curr + next

	def update_next_lbl(self, ind):

		# Take all players and move them up by 1/2 when turn finished
		next = "Next:\n"
		if not self.is_reversed:
			a = (self.identity + ind) % len(self.peeps)
			curr = f"Current:\n{self.peeps[a]}\n\n"
			for i in range(a + 1, a + len(self.peeps) + 1):
				if not (i % len(self.peeps)) == self.identity:
					next += f"{self.peeps[(i % len(self.peeps))]}\n"
				else:
					next += "You\n"
		else:
			a = (self.identity - ind) % len(self.peeps)
			curr = f"Current:\n{self.peeps[a]}\n\n"
			for i in range(a - 1, a - 1 - len(self.peeps), -1):
				if not (i % len(self.peeps)) == self.identity:
					next += f"{self.peeps[(i % len(self.peeps))]}\n"
				else:
					next += "You\n"
		self.direction_l.config(text=curr + next)

	def checkPeriodically(self):
		self.incoming()
		if not self.quit:
			self.after(100, self.checkPeriodically)

	def start_new(self, message):

		print("Destroying old game...")
		self.master.destroy()

		root = Tk()
		root.configure(bg='white')
		root.geometry("700x553+250+120")
		root.title(f"UNO - player {str(message['whoami'])} - {message['peeps'][message['whoami']]}")
		root.protocol("WM_DELETE_WINDOW", self.close_window)
		new = Game(root, self.q, message, self.sock, self.all_points)
		new.config_start_btns(message)
		new.checkPeriodically()
		new.mainloop()

	def config_start_btns(self, message):
		if message['player'] == 0:
			self.new_card.config(state="disabled")
			self.uno = False
			# self.uno_but.config(fg="red", bg="white", state='disabled')
			for i in self.hand_btns:
				self.hand_btns[i].config(state='disabled')
		elif "plus" in message['played'] and (not self.can_stack() or not self.modes[1]):
			self.card_counter = 2
			self.uno = False
			# self.uno_but.config(fg="red", bg="white", state='disabled')
			for i in self.hand_btns:
				self.hand_btns[i].config(state='disabled')
		elif "plus" in message['played'] and self.modes[1] and self.can_stack():
			self.stack_counter = 2
			self.card_counter = 2
			for i in self.hand_btns:
				if 'two' not in self.hand_btns[i]['text']:
					self.hand_btns[i].config(state='disabled')
		elif self.possible_move():
			self.new_card.config(state="disabled")

	def set_anim(self):
		self.animated = not self.animated

	def close_window(self):
		try:
			bye: dict[str, Any] = {"stage": Stage.BYE}
			bye["padding"] = 'a' * (685 - len(str(bye)))
			self.sock.send(json.dumps(bye).encode('utf-8'))
			self.sock.close()
		except OSError:
			pass
		self.quit = True

		print("I am closing")
		self.master.destroy()
		print("Bye")

# ######################################## SHOW FUNCTIONS #######################################


def show(m):
	if m['stage'] == Stage.GO:
		print("PLAYED: ", m['played'])
		if 'other_left' in m:
			print("ALL LEFT: ", m['other_left'])
		else:
			print("Zero cards left")
		print("STAGE: ", m['stage'])
		print("PLAYER: ", m['player'])
	else:
		print("STAGE:", m['stage'])
		print("Special message")


def show_rules():
	print("RULES")
	answer = messagebox.askyesno(
		"Rules",
		"No stacking, take one card only. You can click on cards when it's your turn. Press the "
		"UNO button BEFORE making the move, not after - otherwise you'll have to take 2 cards. The"
		" \"Not my turn\" button is used for bug reporting and to change your turn to someone else."
		"\n Would you like to visit Wiki for official rules?")
	if answer:
		webbrowser.open("https://www.ultraboardgames.com/uno/game-rules.php")


def show_mode(m):
	if m == 1:
		messagebox.showinfo(
			"7/0",
			"When a player puts a 7, they have to choose someone (not themselves) to swap their "
			"cards with forever (or until another 7/0 is played).\nWhen a player puts a 0, all "
			"cards are moved to the next player in the direction of the game (that is, in "
			"not-reversed mode 0's cards go to 1, 1 to 2, 2 to 0)"
		)
	elif m == 2:
		messagebox.showinfo(
			"Stack +2",
			"If you're given a plus card and you have another, you can stack yours on top of the "
			"given card, increasing the number of cards needed to be taken for the next player"
		)

	else:
		messagebox.showinfo(
			"Take many cards",
			"If you don't have a playable card, you have to take cards from the pile until a"
			" suitable one appears, rather than just take one and skip turn"
		)
