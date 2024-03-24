from PIL import Image
from card import Card
from random import shuffle
from os import listdir

CARD_IMAGE_PATH = "Images/Cards/"


class Deck:
	global backofcard, special_blacks, smallback
	backofcard = Image.open(f"{CARD_IMAGE_PATH}backofcard.jpg")
	backofcard = backofcard.resize((117, 183), Image.ANTIALIAS)

	smallback = backofcard.resize((80, 125), Image.ANTIALIAS)

	redplus = Image.open(f"{CARD_IMAGE_PATH}redplusfour.jpeg")
	redplus = redplus.resize((117, 183), Image.ANTIALIAS)
	redblack = Image.open(f"{CARD_IMAGE_PATH}redblack.jpeg")
	redblack = redblack.resize((117, 183), Image.ANTIALIAS)
	bluplus = Image.open(f"{CARD_IMAGE_PATH}bluplusfour.jpeg")
	bluplus = bluplus.resize((117, 183), Image.ANTIALIAS)
	blublack = Image.open(f"{CARD_IMAGE_PATH}blublack.jpeg")
	blublack = blublack.resize((117, 183), Image.ANTIALIAS)
	greplus = Image.open(f"{CARD_IMAGE_PATH}greplusfour.jpeg")
	greplus = greplus.resize((117, 183), Image.ANTIALIAS)
	greblack = Image.open(f"{CARD_IMAGE_PATH}greblack.jpeg")
	greblack = greblack.resize((117, 183), Image.ANTIALIAS)
	yelplus = Image.open(f"{CARD_IMAGE_PATH}yelplusfour.jpeg")
	yelplus = yelplus.resize((117, 183), Image.ANTIALIAS)
	yelblack = Image.open(f"{CARD_IMAGE_PATH}yelblack.jpeg")
	yelblack = yelblack.resize((117, 183), Image.ANTIALIAS)

	special_blacks = {
		"redplus": redplus, "greplus": greplus, "bluplus": bluplus,
		"yelplus": yelplus, "redblack": redblack, "blublack": blublack,
		"yelblack": yelblack, "greblack": greblack
	}

	# List of all Card objects
	def __init__(self):
		self.deck = []
		files = listdir(f"{CARD_IMAGE_PATH}UNO")
		if len(files) == 0:
			print("No files found")
			return
		for f in files:
			if (f != ".DS_Store") and (f != ".idea"):
				card_pic = Image.open(f"{CARD_IMAGE_PATH}UNO/" + f)
				new_card = Card(card_pic, f)
				self.deck.append(new_card)
				if "0" not in f:
					# Non-zero cards appear twice
					self.deck.append(new_card)
				if "black" in f:
					self.deck.append(new_card)
					self.deck.append(new_card)
		# Shuffles the deck in place
		shuffle(self.deck)

	def get_card(self, name):
		for c in self.deck:
			if c.name == name:
				return c
		return None

	def get_special(self, name):
		for i in special_blacks:
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
