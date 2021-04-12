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
from card import *
import re
from deck import *
from random import *
from tkinter.simpledialog import *
import copy
from tkmacosx import Button as but

class Game(Frame):
	global pile
	#TODO add which player you are
	global new_deck
	new_deck = Deck()
	pile = new_deck.deck
	global message
	message = {}
	#global cards_left
	#Last played card
	global lastplayed
	lastplayed = pile.pop(0)
	#button with that card
	global last
	#global uno
	#List of cards on your hands
	global hand_cards
	hand_cards = {}
	global window
	#List of buttons, same as hand_cards
	global hand_btns
	hand_btns = {}
	global uno
	uno = False
	global all_played
	all_played = []


	# Initialise a frame (going to be within the window). Set the cards label
	def __init__(self, master, message):
		super().__init__(master)
		self.pack()
		self.parent = master
		self.hand_cards = []
		text_cards_left = "Your cards left: " + str(7) + "\n Other player's cards " \
																	"left: " + str(7)
		self.cards_left = Label(text=text_cards_left, fg="blue", bg="white", width=20, height=10)
		self.cards_left.place(x=10, y=5)
		self.uno = but(text="UNO?", fg="red", bg="yellow", width=100, height=80, borderless=1,
					   command=self.one_card)
		self.uno.place(x=50,y=150)
		self.setup_menu()
		self.setup_pile(message)
		self.cards = self.deal_cards(message)
		self.setup_hand(self.cards)

	# Create a hand of 7 cards
	def deal_cards(self, message):
		global hand_cards, pile, new_deck
		hand = []
		pile = message['pile']
		for i in range(7):
			c = pile.pop(0)
			card = new_deck.get_card(c)
			hand.append(card) #NAMES
			#hand_cards.append(c)
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
		global last, new_deck
		photo = ImageTk.PhotoImage(deck.backofcard)

		new_card = Button(image=photo, width=117, height=183, command=self.take_card)
		new_card.image = photo
		new_card.place(x=300, y=50)
		#Put the last played card from the message
		lastplayed2 = message['played'] #this is a name!!
		photo2 = ImageTk.PhotoImage(new_deck.get_card(lastplayed2).card_pic)
		last = Button(text=lastplayed2, image=photo2, width=117, height=183, border=0,
					  state="disabled")
		last.image = photo2
		last.place(x=453, y=50)

	def setup_hand(self, dealt_cards):
		global hand_cards, hand_btns
		n = len(dealt_cards)
		for i in range(n):
			photo = ImageTk.PhotoImage(dealt_cards[i].card_pic)
			b = Button(text=dealt_cards[i].name, image=photo, width=117, height=183, border=0,
					   bg="white")
			b['command'] = lambda ind=i, binst=b: self.place_card(ind, binst)
			b.image = photo
			hand_btns[i] = b
			hand_cards[i] = dealt_cards[i]
			coords = self.get_card_placement(n,i)
			b.place(x=coords[1], y=coords[2])
		print(pile)

	def get_card_placement(self,num_cards, i):
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
		global hand_btns, hand_cards, last, all_played, cards_left, uno
		card = hand_cards[ind].name
		old_card = last['text']
		print("OLD: ", old_card, " NEW: ", card)
		#Same color (0:3), same symbol (3:), black
		if (card[0:3] == old_card[0:3] or card[3:] == old_card[3:] or "bla" in card[0:3]):
			binst.destroy()
			all_played.append(hand_cards[ind].name)
			if "bla" in card[0:3]:
				new_color = askinteger("Color picker", "Input a number between 1 and 4: \n"
													   "1. Red \n"
													   "2. Blue \n"
													   "3. Green \n"
													   "4. Yellow", minvalue=1, maxvalue=4)
				if new_color == 1:
					#Get the new red black card (open file)
					if "plus" in card:
						photocard = new_deck.redplus
						card_col = "redplusfour.png"
					else:
						photocard = new_deck.redblack
						card_col = "redblack.png"
				elif new_color == 2:
					#Get the new blue black card (open file)
					if "plus" in card:
						photocard = new_deck.bluplus
						card_col = "bluplusfour.png"
					else:
						photocard = new_deck.blublack
						card_col = "blublack.png"
				elif new_color == 3:
					#Get the new green black card (open file)
					if "plus" in card:
						photocard = new_deck.greplus
						card_col = "greplusfour.png"
					else:
						photocard = new_deck.greblack
						card_col = "greblack.png"
				else:
					#Get the new yellow black card (open file)
					if "plus" in card:
						photocard = new_deck.yelplus
						card_col = "yelplusfour.png"
					else:
						photocard = new_deck.yelblack
						card_col = "yelblack.png"
			else:
				photocard = hand_cards[ind].card_pic
				card_col = card
			img = ImageTk.PhotoImage(photocard)
			last.config(image=img, text=card_col)
			last.image = img
			last.text = card_col
			hand_cards.pop(ind)
			hand_btns.pop(ind)
			self.cards_left.config(text="Your cards left: " + str(len(hand_cards)) +
								   "\n Other player's cards left: " + str(8))
			ctr = 0
			for i in hand_btns.keys():
				b = hand_btns[i]
				coords = self.get_card_placement(len(hand_btns),ctr)
				b.place(x=coords[1], y=coords[2])
				ctr += 1
			data_to_send = {
				"played" : card,
				"pile" : pile,
				"stage" : "GO",
				"said_uno" : uno,
				"color" : card[0:3],
				"all_played" : all_played,
				"num_left" : len(hand_cards)
			}
			sock.sendto(dumps(data_to_send).encode(), addr)

	def take_card(self):
		global pile, hand_cards, hand_btns, all_played, new_deck
		print("CARD")
		#If pile is empty, reshuffle the all_played cards
		if (len(pile) < 1 or pile is None):
			print(all_played)
			pile = copy.deepcopy(all_played)
			shuffle(pile)
			all_played = all_played[-1:]
			print(pile)
		new = new_deck.get_card(pile.pop(0))
		#Since hand is a dict, the keys aren't in order.
		#Get the largest and add 1 for the next
		ind = max(list(hand_cards.keys())) + 1
		hand_cards[ind] = new
		photo = ImageTk.PhotoImage(new.card_pic)
		b = Button(text=new.name, image=photo, width=117, height=183, border=0,
				   bg="white")
		b['command'] = lambda ind=ind, binst=b: self.place_card(ind, binst)
		b.image = photo
		hand_btns[ind] = b
		self.cards_left.config(text="Your cards left: " + str(len(hand_cards)) +
									"\n Other player's cards left: " + str(7))
		ctr = 0
		for i in hand_btns.keys():
			b = hand_btns[i]
			coords = self.get_card_placement(len(hand_btns),ctr)
			b.place(x=coords[1], y=coords[2])
			ctr += 1

	def one_card(self):
		global uno
		uno = True
		self.uno.config(fg="green",bg="white")
		print("UNO")


	def show_points(self):
		result = 0
		ans = messagebox.askyesno("Points","  Card   | Points\n"
							"   0-9   |  0-9 \n"
							"-----------------\n"
							" Reverse |       \n"
							"  Stop   |  20   \n"
							"   +2    |       \n"
							"  Black  |  50")
		if ans:
			for k in hand_cards.keys():
				c = hand_cards[k].name
				if re.search(r'\d+', c) is not None:
					point = int(re.search(r'\d+', c).group())
					print(point)
					result += point
				else:
					#non-numbers
					if ("two" in c or "reverse" in c or "stop" in c):
						result += 20
					else:
						result += 50
			messagebox.showinfo("Points", "Your points are: "+str(result))


	##################################### CLIENT ##################################
def receive():
		global message, root, addr
		while True:
			print("Waiting")
			json, addr = sock.recvfrom(8000)
			message = loads(json.decode())
			#print(message)
			if message['stage'] == "INIT":
				print("HERE")
				# Window is a frame
				window = Game(root, message)
			if message['stage'] == "GO":
				print(message)
			if message['stage'] == "END":
				break
		sock.close()

	##################################### MAIN ##################################

if __name__ == "__main__":
	global window, message, root

	port = argv[1]
	sock = socket(AF_INET, SOCK_DGRAM)
	#window = Game(root, message)
	sock.bind(('localhost', int(port)))

	thread = Thread(target=receive)
	thread.start()
	thread.join()
	#Start thread, receive first info
	#Use it in here
	if len(message) > 0:
		root = Tk()

		root.title("UNO")
		root.configure(bg='white')
		root.geometry("700x553")
		#print(message)
		window = Game(root, message)
		window.mainloop()
