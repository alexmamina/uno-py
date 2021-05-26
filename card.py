from tkinter import *
from math import *
from PIL import ImageTk, Image
from json import *

class Card():
	def __init__(self, card_pic, name):
		self.card_pic = card_pic.resize((117, 183), Image.ANTIALIAS)
		self.name = name
		
	def __str__(self):
		return "Card: "+ self.name
		
	def __repr__(self):
		return self.name
		
	def default(self, o):
		return o.__dict__
		
