from threading import Thread
from tkinter import *
from tkinter import simpledialog
from math import *
from PIL import ImageTk, Image
from os import *
import card
import deck
import events
from socket import *
from sys import *
from events import *

from picker import *
from card import *
import re
import queue
from deck import *
from random import *
from tkinter.simpledialog import *
import copy
from tkmacosx import Button as but

port = argv[1]
sock = socket(AF_INET, SOCK_DGRAM)
#sock.bind(('', int(port)))


class Game(Frame):
	global new_deck
	new_deck = Deck()
	pile = new_deck.deck
	global message
	message = {}
	global all_played
	all_played = []


	# Initialise a frame. Setup the pile, hand, last played card and all gui
	def __init__(self, master, queue, message):
		super().__init__(master)
		self.pack()
		self.parent = master
		#Take one card only
		self.card_counter = 1
		self.q = queue
		self.last = None
		self.turn = Label(text="Your turn" if message['player'] == 1 else "Waiting...",
						  fg='blue', bg='white', width=10, height=1)
		self.turn.place(x=300,y=0)
		self.hand_cards = {}
		self.pile = message['pile']
		self.other_cards_left = message['num_left']
		text_cards_left = "Your cards left: " + str(7) + "\n Other player's cards " \
																	"left: " + str(7)
		self.cards_left = Label(text=text_cards_left, fg="blue", bg="white", width=20, height=5)
		self.cards_left.place(x=10, y=30)
		self.uno_but = but(text="UNO?", fg="red", bg="white", width=100, height=80, borderless=1,
						   command=self.one_card)
		#self.uno_but.place(x=50, y=150)
		self.uno = False
		self.new_card = None
		self.setup_menu()
		self.setup_pile(message)
		self.cards = self.deal_cards(message)
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
			hand.append(card) #NAMES
		return hand

	# Create a menu bar, configure to add to parent (which is the root window)
	def setup_menu(self):
		menubar = Menu(self)

		menu = Menu(menubar)
		menu.add_command(label="Rules", command=show_rules)
		menu.add_command(label="Points", command=self.show_points)
		menubar.add_cascade(label="Menu", menu=menu)
		mode = Menu(menubar)
		mode.add_command(label="Regular")
		mode.add_command(label="Stack")
		mode.add_command(label="Jump-in")
		mode.add_command(label="7-0")
		menubar.add_cascade(label="Game mode", menu=mode)

		self.parent.configure(menu=menubar)

	# Add the pile and last played buttons
	def setup_pile(self, message):
		photo = ImageTk.PhotoImage(deck.backofcard)
		#Button to take a card (so a pile)
		self.new_card = Button(image=photo, width=117, height=183, command=self.take_card)
		self.new_card.image = photo
		self.new_card.place(x=300, y=50)
		#Last played card from the message
		lastplayed2 = message['played'] #this is a name!!
		photo2 = ImageTk.PhotoImage(new_deck.get_card(lastplayed2).card_pic)
		#Last is a disabled button with the last played card shown
		self.last = Button(text=lastplayed2, image=photo2, width=117, height=183, border=0,
					  state="disabled")
		self.last.image = photo2
		self.last.place(x=453, y=50)

	def setup_hand(self, dealt_cards):
		n = len(dealt_cards)
		for i in range(n):
			#Createa button for each card in dealt cards, add a command
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
		#Returns coordinates of a button  given specific parameters
		#Like the width and length of cards, as well as how apart they should be
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


	##################################### EVENTS ##################################
	def place_card(self,ind, binst):
		global all_played
		card = self.hand_cards[ind].name
		old_card = self.last['text']
		print("OLD: ", old_card, " NEW: ", card)
		#Same color (0:3), same symbol (3:), black
		if (card[0:3] == old_card[0:3] or card[3:] == old_card[3:] or "bla" in card[0:3]):
			binst.destroy()
			all_played.append(self.hand_cards[ind].name)
			#Changes the black card to black with a color to show which one to play next
			if "bla" in card[0:3]:
				picker = Picker(self, "New color", "Which one?", ['Red','Green','Blue',
																	 'Yellow'])
				new_color = picker.result
				print(new_color)
				print(type(new_color))
				new_color = new_color.lower()[0:3]
				print(new_color)
				if "plus" in card:
					new_color += "plus"
					card_col = new_color+"four.png"
					photocard = new_deck.get_special(new_color)
				else:
					new_color += "black"
					card_col = new_color+"black.png"
					photocard = new_deck.get_special(new_color)


			else:
				photocard = self.hand_cards[ind].card_pic
				card_col = card
			img = ImageTk.PhotoImage(photocard)
			self.last.config(image=img, text=card_col)
			self.last.image = img
			self.last.text = card_col
			self.hand_cards.pop(ind)
			self.hand_btns.pop(ind)
			self.cards_left.config(text="Your cards left: " + str(len(self.hand_cards)) +
								   "\n Other player's cards left: " + str(self.other_cards_left))
			ctr = 0
			for i in self.hand_btns.keys():
				#Move all buttons
				b = self.hand_btns[i]
				coords = self.get_card_placement(len(self.hand_btns),ctr)
				b.place(x=coords[1], y=coords[2])
				ctr += 1
			if (len(self.hand_cards) <= 2):
				self.uno_but.place(x=50, y=150)
			data_to_send = {
				"played" : card,
				"pile" : self.pile,
				"stage" : "GO",
				"said_uno" : self.uno,
				"color" : card_col,
				"all_played" : all_played,
				"num_left" : len(self.hand_cards)
			}
			self.sendInfo(data_to_send, addr)

	def take_card(self):
		global all_played, new_deck
		print("CARD")
		#If pile is empty, reshuffle the all_played cards
		if len(self.pile) < 1 or self.pile is None:
			print(all_played)
			print("Shuffling those cards")
			self.pile = copy.deepcopy(all_played)
			shuffle(self.pile)
			all_played = all_played[-1:]
			print(self.pile)
		new = new_deck.get_card(self.pile.pop(0))

		self.card_counter -= 1
		#Since hand is a dict, the keys aren't in order.
		#Get the largest and add 1 for the next
		ind = max(list(self.hand_cards.keys())) + 1
		self.hand_cards[ind] = new
		photo = ImageTk.PhotoImage(new.card_pic)
		b = Button(text=new.name, image=photo, width=117, height=183, border=0,
				   bg="white")
		b['command'] = lambda ind=ind, binst=b: self.place_card(ind, binst)
		b.image = photo
		self.hand_btns[ind] = b
		self.cards_left.config(text="Your cards left: " + str(len(self.hand_cards)) +
									"\n Other player's cards left: " + str(self.other_cards_left))
		ctr = 0
		possible_move = False
		for i in self.hand_btns.keys():
			b = self.hand_btns[i]
			coords = self.get_card_placement(len(self.hand_btns),ctr)
			print(b['text'])
			print(self.last['text'])
			b.place(x=coords[1], y=coords[2])
			ctr += 1
			if "bla" in b['text'] or self.last['text'][0:3] in b['text'] or self.last['text'][3:]\
					in b['text']:
				possible_move = possible_move or True
		if (len(self.hand_cards) > 2):
			self.uno_but.place_forget()
				#Here don't break the loop bc we need the rest to replace buttons
#todo stop doesn't send to other player; keeps on one until card placed
		if self.card_counter == 0 and (possible_move == False or
									   ('taken' not in message and "plus" in self.last['text'])):
			data_to_send = {
				"played" : self.last['text'],
				"pile" : self.pile,
				"stage" : "GO",
				"said_uno" : self.uno,
				"color" : self.last['text'][0:3],
				"all_played" : all_played,
				"num_left" : len(self.hand_cards),
				"taken" : True
			}
			self.sendInfo(data_to_send, addr)

	def one_card(self):
		if self.uno:
			self.uno = False
			self.uno_but.config(fg="red", bg="white")
		else:
			self.uno = True
			self.uno_but.config(fg="green", bg="white")
		print("UNO")


	def show_points(self):
		result = 0
		ans = messagebox.askyesno("Points",
							"0-9 - 0-9\n"
							" Reverse - 20\n"
							" Stop - 20\n"
							" +2 - 20\n"
							" Black - 50\n"
							"Calculate automatically?")
		if ans:
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
			messagebox.showinfo("Points", "Your points are: "+str(result))


	def incoming(self):
		global all_played
		while self.q.qsize():
			try:
				msg = self.q.get(0)
				#Played, pile, num_left, color, all_played, player, saiduno, taken
				newC = msg['played']

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
				if "plustwo" in newC and 'taken' not in msg:
					self.card_counter = 2
				self.last.config(image=img, text=newC)
				self.last.image = img
				self.pile = msg['pile']
				self.other_cards_left = msg['num_left']
				if self.other_cards_left == 1:
					if msg['said_uno']:
						uno_said = "\nUNO said!"
					else:
						uno_said = "\nUNO not said!"
						#todo challenge uno
						self.challenge = but(text="UNO not said!", bg='red', fg='white',
											  width=150, height=30,command=self.challengeUno)
						self.challenge.place(x=50, y=120)
				else:
					uno_said = ""

				left_cards_text = "Your cards left: " + str(len(self.hand_cards))\
								  +"\n Other player's cards left: " + str(self.other_cards_left)\
								+uno_said
				self.cards_left.config(text=left_cards_text)
				all_played = msg['all_played']
				if int(msg['player']) == 1:
					self.new_card.config(state='normal')
					self.turn.config(text="Your turn")
					if self.card_counter < 2: # Here can add stack option later
						self.uno_but.config(state='normal')
						for i in self.hand_btns:
								self.hand_btns[i].config(state='normal')
				if len(self.hand_cards) == 2:
					self.uno_but.place(x=50, y=150)
					print('here')
				q.queue.clear()
			except queue.Empty:
				pass
	#todo ending (also end with +2/4)
	def receive(self):
			global message, root, addr
			while True:
				print("Waiting")
				json, addr = sock.recvfrom(8000)
				message = loads(json.decode())
				print(message)
				self.q.put(message)

	def sendInfo(self, data_to_send, addr):
		sock.sendto(dumps(data_to_send).encode(), addr)
		self.new_card.config(state="disabled")
		self.uno = False
		self.uno_but.config(fg="red", bg="white", state='disabled')
		self.uno_but.place_forget()
		for i in self.hand_btns:
			self.hand_btns[i].config(state='disabled')
		self.turn.config(text="Waiting...")

	def challengeUno(self):
		data = {
			"played" : self.last['text'],
			"pile" : self.pile,
			"stage" : "CHALLENGE",
			"said_uno" : self.uno,
			"color" : self.last['text'][0:3],
			"all_played" : all_played,
			"num_left" : len(self.hand_cards),
			"taken" : True
		}
		#todo finish this
##################################### CLIENT ##################################

def checkPeriodically(w):
	w.incoming()
	w.after(100, checkPeriodically, w)

def close_window():
	sock.close()
	root.destroy()

	##################################### MAIN ##################################

if __name__ == "__main__":

	root = Tk()
	root.configure(bg='white')
	root.geometry("700x553")
	sock.bind(('', int(port)))
	init, addr = sock.recvfrom(8000)
	message = loads(init.decode())
	#todo if stop both have title 2 but correct palyer goes
	root.title("UNO - port " + port + " player - " + (str(1) if message['player'] == 1 and 'stop'
			not in message['played'] else str(2)))
	q = queue.Queue()
	window = Game(root, q, message)
	if message['player'] == 0:
		window.new_card.config(state="disabled")
		window.uno = False
		window.uno_but.config(fg="red", bg="white", state='disabled')
		for i in window.hand_btns:
			window.hand_btns[i].config(state='disabled')
	if "plus" in message['played']:
		window.card_counter = 2
		window.uno = False
		window.uno_but.config(fg="red", bg="white", state='disabled')
		for i in window.hand_btns:
			window.hand_btns[i].config(state='disabled')
	thread = Thread(target=window.receive)
	thread.start()
	checkPeriodically(window)
	root.protocol("WM_DELETE_WINDOW", close_window)
	window.mainloop()
