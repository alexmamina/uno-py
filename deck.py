from tkinter import *
from math import *
from PIL import ImageTk, Image
from os import *
import card
from card import *
from random import *
import copy


class Deck:

	global backofcard, special_blacks
	backofcard = Image.open("Cards/backofcard.jpg")
	backofcard = backofcard.resize((117, 183), Image.ANTIALIAS)

	redplus = Image.open("Cards/redplusfour.jpeg")
	redplus = redplus.resize((117, 183), Image.ANTIALIAS)
	redblack = Image.open("Cards/redblack.jpeg")
	redblack = redblack.resize((117, 183), Image.ANTIALIAS)
	bluplus = Image.open("Cards/bluplusfour.jpeg")
	bluplus = bluplus.resize((117, 183), Image.ANTIALIAS)
	blublack = Image.open("Cards/blublack.jpeg")
	blublack = blublack.resize((117, 183), Image.ANTIALIAS)
	greplus = Image.open("Cards/greplusfour.jpeg")
	greplus = greplus.resize((117, 183), Image.ANTIALIAS)
	greblack = Image.open("Cards/greblack.jpeg")
	greblack = greblack.resize((117, 183), Image.ANTIALIAS)
	yelplus = Image.open("Cards/yelplusfour.jpeg")
	yelplus = yelplus.resize((117, 183), Image.ANTIALIAS)
	yelblack = Image.open("Cards/yelblack.jpeg")
	yelblack = yelblack.resize((117, 183), Image.ANTIALIAS)

	special_blacks = {"redplus": redplus, "greplus": greplus, "bluplus": bluplus, 'yelplus' :
		yelplus, 'redblack': redblack,  'blublack': blublack,  'yelblack': yelblack,  'greblack':
		greblack }

#List of all Card objects
	def __init__(self):
		self.deck = []
		files = listdir("Cards/UNO")
		if len(files) == 0:
			print("No files found")
			return
		for f in files:
			if ((f != ".DS_Store") and (f != ".idea")):
				card_pic = Image.open("Cards/UNO/"+f)
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
				
	def get_special(self, name):
		for i in special_blacks:
			print(i, " ", name)
			if i in name:
				return special_blacks[i]
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

