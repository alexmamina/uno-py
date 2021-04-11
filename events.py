from tkinter import *
from math import *
from PIL import ImageTk, Image
from os import *
import card
import game
from game import *
import webbrowser
from card import *
from deck import *
from random import *
import copy



def show_rules():
	print("RULES")
	answer = messagebox.askyesno("Rules", "explain how this program works; would you like to "
										  "visit Wiki for official rules?")
	if answer:
		webbrowser.open("https://www.ultraboardgames.com/uno/game-rules.php")


#def show_points():
#	print("POINTS")
#	a = game.hand_cards

