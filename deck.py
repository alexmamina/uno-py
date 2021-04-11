from tkinter import *
from math import *
from PIL import ImageTk, Image
from os import *
import card
from card import *
from random import *
import copy
#frame = Tk()
#b = Button(frame, "Hello")
#b.place(50,50)

class Deck:

	global backofcard
	backofcard = Image.open("/Users/alexmamina/IdeaProjects/uno/backofcard.jpg")
	backofcard = backofcard.resize((117, 183), Image.ANTIALIAS)

	redplus = Image.open("/Users/alexmamina/IdeaProjects/uno/redplusfour.jpeg")
	redplus = redplus.resize((117, 183), Image.ANTIALIAS)
	redblack = Image.open("/Users/alexmamina/IdeaProjects/uno/redblack.jpeg")
	redblack = redblack.resize((117, 183), Image.ANTIALIAS)
	bluplus = Image.open("/Users/alexmamina/IdeaProjects/uno/bluplusfour.jpeg")
	bluplus = bluplus.resize((117, 183), Image.ANTIALIAS)
	blublack = Image.open("/Users/alexmamina/IdeaProjects/uno/blublack.jpeg")
	blublack = blublack.resize((117, 183), Image.ANTIALIAS)
	greplus = Image.open("/Users/alexmamina/IdeaProjects/uno/greplusfour.jpeg")
	greplus = greplus.resize((117, 183), Image.ANTIALIAS)
	greblack = Image.open("/Users/alexmamina/IdeaProjects/uno/greblack.jpeg")
	greblack = greblack.resize((117, 183), Image.ANTIALIAS)
	yelplus = Image.open("/Users/alexmamina/IdeaProjects/uno/yelplusfour.jpeg")
	yelplus = yelplus.resize((117, 183), Image.ANTIALIAS)
	yelblack = Image.open("/Users/alexmamina/IdeaProjects/uno/yelblack.jpeg")
	yelblack = yelblack.resize((117, 183), Image.ANTIALIAS)


#List of all Card objects
	def __init__(self):
		self.deck = []
		files = listdir("/Users/alexmamina/IdeaProjects/uno/UNO")
		if len(files) == 0:
			print("No files found")
			return
		for f in files:
			if ((f != ".DS_Store") and (f != ".idea")):
				card_pic = Image.open("/Users/alexmamina/IdeaProjects/uno/UNO/"+f)
				card = Card(card_pic, f)
				#print(card)
				self.deck.append(card)
				if "0" not in f:
				#Non-zero cards appear twice
					self.deck.append(card)
				if "black" in f:
					self.deck.append(card)
					self.deck.append(card)
		#Shuffles the deck in place
		shuffle(self.deck)
	
			
	def get_card(self, name):
		for c in self.deck:
			if c.name == name:
				return c
		return None
				
	
	def __str__(self):
		str = ""
		for c in self.deck:
			str += c.name
			str += ", "
		return str
		
	def __repr__(self):
		str = ""
		for c in self.deck:
			str += c.name
			str += ", "
		return str


if __name__ == "__main__":
	print ("hello")
	d = Deck()
	print(len(d.deck))
	#This is the 'queue', deck not affected
	c = copy.deepcopy(d.deck)
	c.pop(0)
	
	print (len(c))
	print (len(d.deck))
	
	#do stuff
	#main()