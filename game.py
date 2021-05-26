from threading import Thread
from tkinter import *
from tkinter import simpledialog
from math import *
from PIL import ImageTk, Image
import card
import deck
import webbrowser
from socket import *
from sys import *

from time import *
from picker import *
from stages import *
from card import *
import re
import queue
from deck import *
from random import *
from tkinter.simpledialog import *
import copy
from tkmacosx import Button as but

#port = argv[1]


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
		self.sock = sock
		self.all_points = all_points
		self.parent = master
		self.master.protocol("WM_DELETE_WINDOW", self.close_window)
		#Take one card only
		self.card_counter = 1
		self.q = queue
		self.quit = False
		self.identity = msg['whoami']
		self.last = None
		self.challenge = None
		if msg['player'] == 1:
			self.turn = Label(text="Your turn",
						  fg='white', bg='green', width=30, height=1)
		else:
			self.turn = Label(text="Your turn" if msg['player'] == 1 else "Wait for other players!",
							  fg='white', bg='red', width=30, height=1)
		self.turn.place(x=300,y=0)
		self.hand_cards = {}
		self.pile = msg['pile']
		self.all_nums_of_cards = msg['other_left']
		text_cards_left = "Your cards: " + str(7)
		pl = 0
		for x in msg['other_left']:
			if pl != self.identity:
				text_cards_left += "\n Player "+str(pl) + ": " + str(x) + " cards"
			pl += 1
		self.cards_left = Label(text=text_cards_left, fg="blue", bg="pale green", width=20,
								height=5)
		self.cards_left.place(x=10, y=30)
		self.uno_but = but(text="UNO", fg="black", bg="deep sky blue", width=100, height=80,
						   borderless=1,
						   command=self.one_card)
		self.uno = False
		self.new_card = None
		self.setup_menu()
		self.setup_pile(msg)
		self.cards = self.deal_cards(msg)
		# Button for debugging
		self.debug = but(text="Not my turn", fg='red', bg='white', borderless=1, width=100,
						 height=30,
						 command=self.send_debug)
		self.debug.place(x=600,y=498)
		self.hand_btns = {}
		self.setup_hand(self.cards)

	# Create a hand of 7 cards from pile from message
	def deal_cards(self, message):
		global new_deck
		hand = []
		self.pile = message['pile']
		for i in range(7):
			c = self.pile.pop(0)
			#Lookup the card name from pile to get card itself
			card = new_deck.get_card(c)
			hand.append(card) #CARDS
		return hand

	# Create a menu bar, configure to add to parent (which is the root window)
	def setup_menu(self):
		menubar = Menu(self)

		menu = Menu(menubar)
		menu.add_command(label="Rules", command=show_rules)
		menu.add_command(label="Points", command=self.show_points)
		menubar.add_cascade(label="Menu", menu=menu)
		mode = Menu(menubar)
		# This is not working yet, so not added to the menu
		mode.add_command(label="Regular")
		mode.add_command(label="Stack")
		mode.add_command(label="Jump-in")
		mode.add_command(label="7-0")
		#menubar.add_cascade(label="Game mode", menu=mode)

		self.parent.configure(menu=menubar)

	# Add the pile and last played buttons
	def setup_pile(self, message):
		photo = ImageTk.PhotoImage(deck.backofcard)
		# Button to take a card (so a pile)
		self.new_card = Button(image=photo, width=117, height=183, command=self.take_card)
		self.new_card.image = photo
		self.new_card.place(x=300, y=50)
		# Last played card from the message
		lastplayed2 = message['played'] # this is a name!!
		photo2 = ImageTk.PhotoImage(new_deck.get_card(lastplayed2).card_pic)
		# Last is a disabled button with the last played card shown
		self.last = Button(text=lastplayed2, image=photo2, width=117, height=183, border=0,
					  state="disabled")
		self.last.image = photo2
		self.last.place(x=453, y=50)

	def setup_hand(self, dealt_cards):
		n = len(dealt_cards)
		for i in range(n):
			# Create a button for each card in dealt cards, add a command
			photo = ImageTk.PhotoImage(dealt_cards[i].card_pic)
			b = Button(text=dealt_cards[i].name, image=photo, width=117, height=183, border=0,
					   bg="white")
			b['command'] = lambda ind=i, binst=b: self.place_card(ind, binst)
			b.image = photo
			self.hand_btns[i] = b
			self.hand_cards[i] = dealt_cards[i]
			coords = self.get_card_placement(n,i)
			b.place(x=coords[1], y=coords[2])

	def get_card_placement(self,num_cards, i):
		# Returns coordinates of a button  given specific parameters
		# Like the width and length of cards, as well as how apart they should be
		result = []
		if num_cards == 1:
			num_cards = 2
		if num_cards <= 15:
			overlap = floor((117-((117*num_cards)-650)/(num_cards-1)))
		else:
			overlap = floor((117-((117*15)-650)/(15-1)))
		result.append(overlap)
		result.append(25+overlap*(i%15)+15*(floor(i/15)))
		result.append(280+40*(floor(i/15)))
		return result

#todo if card taken and move possible, disable button
	##################################### EVENTS ##################################
	def place_card(self,ind, binst):
		if self.challenge:
			self.challenge.place_forget()
		card = self.hand_cards[ind].name
		old_card = self.last['text']
		# Same color (0:3), same symbol (3:), black
		if (card[0:3] == old_card[0:3] or card[3:] == old_card[3:] or "bla" in card[0:3]):
			binst.destroy()
			# Changes the black card to black with a color to show which one to play next
			if "bla" in card[0:3]:
				picker = Picker(self, "New color", "Which one?", ['Red','Green','Blue',
																	 'Yellow'])
				new_color = picker.result
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
			if self.uno:
				data_to_send['said_uno'] = True
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
		# Decrease number of cards that need to be taken
		self.card_counter -= 1
		# Since hand is a dict, the keys aren't in order.
		# Get the largest and add 1 for the next
		ind = max(list(self.hand_cards.keys())) + 1
		# Add new card to the 'hand', create new button, update number
		self.hand_cards[ind] = new
		photo = ImageTk.PhotoImage(new.card_pic)
		b = Button(text=new.name, image=photo, width=117, height=183, border=0,
				   bg="white",state='disabled')
		b['command'] = lambda ind=ind, binst=b: self.place_card(ind, binst)
		b.image = photo
		self.hand_btns[ind] = b
		text = self.label_for_cards_left(self.all_nums_of_cards)
		self.cards_left.config(text=text)
		ctr = 0
		# Is it possible to place a card right now?
		possible_move = self.possible_move()
		if possible_move and self.card_counter == 0:
			self.new_card.config(state='disabled')
			b.config(state='normal')
		for i in self.hand_btns.keys():
			# Move all buttons
			b = self.hand_btns[i]
			coords = self.get_card_placement(len(self.hand_btns),ctr)
			b.place(x=coords[1], y=coords[2])
			ctr += 1
		# Make UNO button appear as uno is possible
		if len(self.hand_cards) == 2 and possible_move\
				and message['stage'] != CHALLENGE:
			self.uno_but.place(x=50,y=150)
			#self.uno_but.config(state='normal')
		# Remove UNO button if many cards (should be unnecessary)
		if len(self.hand_cards) > 2:
			self.uno_but.place_forget()

		# Send the points from the cards if you had to take them at the end (last played was +,
			# but game is over)
		if self.card_counter <= 0 and 'stage' in message.keys() and message['stage'] == ZEROCARDS:
			data_to_send = {"stage": CALC, "points": self.calculate_points()}
			self.sendInfo(data_to_send)

		# Send information about taken cards if can't go or had to take +2/4 due to challenge or
		# card
		if self.card_counter <= 0 and (possible_move == False or
									   ('taken' not in message and "plus" in self.last['text']) or
										message['stage']==CHALLENGE):
			data_to_send = {
				"played" : self.last['text'],
				"pile" : self.pile,
				"stage" : GO,
				"color" : self.last['text'][0:3],
				"num_left" : len(self.hand_cards)
			}
			if message['stage'] != CHALLENGE:
				data_to_send['taken'] = True
			else:
				data_to_send['stage'] = CHALLENGE_TAKEN
			self.sendInfo(data_to_send)

	# Remove UNO button when clicked, set the value to True to be sent
	def one_card(self):
		if self.uno:
			self.uno = False
		else:
			self.uno = True
			self.uno_but.place_forget()
		print("UNO")

	# Show the points that you have with your cards right now (option in menu)
	def show_points(self):
		text = "Your points this session: "+str(self.all_points[self.identity])+"\n"
		for i in range(len(self.all_points)):
			if i == self.identity:
				text += "(You) "
			text += "Player {}: {} points\n".format(i,self.all_points[i])
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
				#non-numbers
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
				#show(msg)
				# Normal play stage
				if msg['stage'] == GO:
					# Set the last played card and configure the pile + card counter
					self.set_played_img(msg)
					newC = msg['played']
					if "plustwo" in newC and 'taken' not in msg:
						self.card_counter = 2
					# Check if other player said UNO; place the challenge button if not said
					# Update label to show that
					if 'said_uno' in msg.keys() and not msg['said_uno']:
						uno_said = "\nUNO not said!"
						self.challenge = but(text="UNO not said!", bg='red', fg='white',
											 width=150, height=30,command=self.challengeUno)
						if msg['player'] == 1:
							self.challenge.place(x=30, y=120)
					elif 'said_uno' in msg.keys() and msg['said_uno']:
						uno_said = "\nUNO said!"
						p = msg['other_left'].index(1)
						#todo test if this works with many players having uno

						if p != self.identity:
							messagebox.showinfo("UNO", "Player "+str(p)+" has only 1 card left!")
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
						if not self.possible_move() or self.card_counter > 1:
							self.new_card.config(state='normal')
						if self.card_counter < 2: # Here can add stack option later
							self.turn.config(text="Your turn", bg='green')
							if self.possible_move() and len(self.hand_cards) == 2:
								self.uno_but.place(x=50,y=150)
								#self.uno_but.config(state='normal')
							for i in self.hand_btns:
									self.hand_btns[i].config(state='normal')
						else:
							self.turn.config(text="Your turn, take cards!", bg='green')
				# Forgot to say UNO - enable taking new cards only
				elif msg['stage'] == CHALLENGE:
					self.new_card.config(state='normal')
					self.card_counter = 2
					messagebox.showinfo("UNO not said!", "You forgot to click UNO, "
																 "so take 2 cards!")
					self.turn.config(text="Your turn, take 2 cards!", bg='orange')

				# Another player has finished the game; you either take cards if last is a plus,
				# or automatically send the remaining points for the other player
				elif msg['stage'] == ZEROCARDS:
					self.set_played_img(msg)
					if msg['to_take']:
						# Enable taking cards
						self.turn.config(text='Your turn, take cards!', bg='green')
						self.new_card.config(state='normal')
						self.card_counter = 2 if "two" in msg['played'] else 4
					else:
						# No cards need to be taken, send current points
						points = {"stage" : CALC, "points" : self.calculate_points()}
						self.sock.send(dumps(points).encode('utf-8'))

					self.cards_left.config(text='Game over!')
				# Get points from the opponent and show them
				elif msg['stage'] == CALC:
					table_of_points = ""
					self.all_points = msg['total']
					for i in range(len(msg['total'])):
						table_of_points += "\nPlayer "+str(i)+": "+str(msg['total'][i])+" points\n"
					if msg['winner'] == self.identity:
						messagebox.showinfo("Win", "You won "+str(msg['points'])+" points!\n\n"
										" Total this session: \n"+table_of_points)
						ans = messagebox.askyesno("New", "Would you like to continue with a new "
														 "game?")
						if ans == 1:
							init = {'stage': INIT}
							self.sock.send(dumps(init).encode('utf-8'))
						else:
							# Don't want the new game
							bye = {'stage': BYE}
							self.sock.send(dumps(bye).encode('utf-8'))
							print("No new game, sending a BYE message")
							self.quit = True
							break

					else:
						messagebox.showinfo("Win", "Player "+str(msg['winner'])
										+" won "+str(msg['points'])+" points!\n"+
											" Total this session: \n"+table_of_points)

				elif msg['stage'] == INIT:
					print("New game!")
					self.start_new(msg)
				elif msg['stage'] == BYE:
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
				self.card_counter = 1
		elif 'bla' in newC:
			newC = msg['color'][0:3] + "black.png"
			img = ImageTk.PhotoImage(new_deck.get_special(newC))
		else:
			img = ImageTk.PhotoImage(new_deck.get_card(newC).card_pic)
			self.card_counter = 1
		self.last.config(image=img, text=newC)
		self.last.image = img
		self.pile = msg['pile']

	# Put received message in queue for async processing
	def receive(self):
			global message, root
			while not self.quit:
				print("Waiting")
				try:
					json, addr = self.sock.recvfrom(16000)
					print("LENGTH: ", len(json))
					data = json.decode('utf-8')
					message = loads(data)
					self.q.put(message)
				except JSONDecodeError as er:
					if "Expecting value" in str(er):
						print("Another player's socket has been closed")
					else:
						print(er)
						print("Different decoding error line 491")
						print(data)
					break
				except OSError as o:
					if o.errno == 9:
						print("Socket closed, no more receiving messages")
						break
				except:
					raise
			print("No more receiving messages")


	# Disable all buttons when sending information and when it's not your turn anymore
	def sendInfo(self, data_to_send):
		self.sock.send(dumps(data_to_send).encode('utf-8'))
		self.new_card.config(state="disabled")
		self.uno = False
		self.card_counter = 1
		#self.uno_but.config(fg="red", bg="white", state='disabled')
		self.uno_but.place_forget()
		for i in self.hand_btns:
			self.hand_btns[i].config(state='disabled')
		self.turn.config(text="Wait for other players!", bg='red')
		print("Not your turn anymore")

	# Notify opponent that they forgot to say UNO; when clicking button
	def challengeUno(self):
		data = {"stage" : CHALLENGE}
		self.sendInfo(data)
		self.challenge.place_forget()

	# If for some reason the turn didn't change, this sends current info to server who prints it
	# out and changes turns
	def send_debug(self):
		print("Changing turns")
		data = {'stage' : DEBUG,
				"played" : self.last['text'],
				"pile" : self.pile,
				"hand" : [self.hand_cards[x].name for x in self.hand_cards],
				"num_left" : len(self.hand_cards),
				"color" : self.last['text'],
				"taken" : True
				}
		self.sendInfo(data)

	# Send all the final information with 0 cards left to end/finalise the game
	def sendFinal(self,data_to_send):
		print("END")
		data_to_send['stage'] = ZEROCARDS
		self.new_card.config(state="disabled")
		self.uno = False
		self.card_counter = 1
		#self.uno_but.config(fg="red", bg="white", state='disabled')
		self.uno_but.place_forget()
		self.turn.config(text="Waiting for the results!",bg='white',fg='blue')
		self.sock.send(dumps(data_to_send).encode('utf-8'))
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


	# From a list of numbers of cards left from other players return the text to show
	# in the label
	def label_for_cards_left(self, others):
		left_cards_text = "Your cards: " + str(len(self.hand_cards))
		pl = 0
		for x in others:
			if pl != self.identity:
				left_cards_text += "\n Player "+str(pl) + ": " + str(x) + " cards"
			pl += 1
		return left_cards_text


	def checkPeriodically(self):
		self.incoming()
		if not self.quit:
			self.after(100, self.checkPeriodically)

	def start_new(self, message):

		print("Destroying old game...")
		self.master.destroy()

		root = Tk()
		root.configure(bg='white')
		root.geometry("700x553")
		root.title("UNO - player "+ str(message['whoami']))
		root.protocol("WM_DELETE_WINDOW", self.close_window)
		new = Game(root, self.q, message, self.sock, self.all_points)
		new.config_start_btns()
		new.checkPeriodically()
		new.mainloop()

	def config_start_btns(self):
		if message['player'] == 0:
			self.new_card.config(state="disabled")
			self.uno = False
			#self.uno_but.config(fg="red", bg="white", state='disabled')
			for i in self.hand_btns:
				self.hand_btns[i].config(state='disabled')
		elif "plus" in message['played']:
			self.card_counter = 2
			self.uno = False
			#self.uno_but.config(fg="red", bg="white", state='disabled')
			for i in self.hand_btns:
				self.hand_btns[i].config(state='disabled')
		elif self.possible_move():
			self.new_card.config(state="disabled")



	def close_window(self):
		try:
			bye = {"stage": BYE}
			self.sock.send(dumps(bye).encode('utf-8'))
			self.sock.close()
		except OSError:
			pass
		self.quit = True

		print("I am closing")
		self.master.destroy()
		print("Bye")


def show(m):
	if m['stage'] == GO:
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
	answer = messagebox.askyesno("Rules", "No stacking, take one card only. You can click on "
			"cards when it's your turn. Press the UNO button BEFORE making the move, not after - "
				"otherwise you'll have to take 2 cards. The \"Not my turn\" button is used for "
										  "bug reporting and to change your turn to someone else."
										  "\n Would you like to "
										  "visit Wiki for official rules?")
	if answer:
		webbrowser.open("https://www.ultraboardgames.com/uno/game-rules.php")
