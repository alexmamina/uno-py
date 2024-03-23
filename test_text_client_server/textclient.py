from sys import argv
from socket import socket, AF_INET, SOCK_DGRAM
import json

if __name__ == "__main__":

	port = argv[1]
	sock = socket(AF_INET, SOCK_DGRAM)
	sock.bind(('localhost', int(port)))
	while True:

		json_msg, addr = sock.recvfrom(8000)
		message = json.loads(json_msg.decode())

		pile = message['pile']
		last_played = message['played']
		prev_played = message['last_played']
		if message['stage'] == "INIT":
			hand = []
			for i in range(7):
				hand.append(pile.pop(0))

		print("CARDS LEFT: ", message["num_left"])
		print("YOUR CARDS LEFT: ", len(hand))
		print("HAND: ", hand)
		print("PLAYED CARD: ", last_played)
		curr_color = message['color']

		# IF NONE: IF STOP OR PLUS, IGNORE
		if last_played is not None:
			curr_card = last_played[3:]
		else:
			# Someone took cards and hasn't played
			curr_card = prev_played[3:]
		next_played = None
		if message['player'] == 1:
			# Your turn
			col = curr_color

			# PICK COLOR IF FIRST IS BLACK
			if (curr_color == "bla"):
				while True:
					new_col = input("Select a color: \n blu, yel, gre or redn\n")
					if (new_col == "blu" or new_col == "yel" or new_col == "red" or new_col == "gre"):
						col = new_col
						break
					else:
						print("Select a normal color")

			# Check if a move can be made
			possible_move = False

			for c in hand:
				if curr_card in c or "bla" in c or curr_color in c:
					possible_move = True
					break

			# Take a card; the last was plus which was put on the last move
			if ("plus" in curr_card and last_played is not None):
				while True:
					try:
						take = input("How many cards are you taking? \n")
						for i in range(int(take)):
							hand.append(pile.pop())
						print("NEW HAND: ", hand)
						break
					except ValueError:
						print("Please enter 2 or 4")
			elif (possible_move is False):
				print("NEW CARD IS BEING TAKEN")
				# THIS ONLY TAKES ONE CARD NOW, CHANGE LATER FOR OPTIONS
				new_card = pile.pop()
				print("NEW CARD: ", new_card)
				if curr_card in new_card or "bla" in new_card or curr_color in new_card:
					next_played = new_card
					col = new_card[0:3]
					confirm = input("The new card will be played now. Press enter")
					# PICK A COLOR
					if col == "bla":
						col = input("Select a color: \n blu, yel, gre or red\n")
					print("This works!")
				else:
					hand.append(new_card)
					print("NEW HAND: ", hand)
					confirm = input("The new card can't be played. Press enter")

			else:
				# Don't take a card
				while True:
					try:
						# Pick a card
						next = input("What card would you like to play?\n")

						taken = hand[int(next)]
						if (curr_card in taken or "bla" in taken or curr_color in taken):
							# Check if valid
							next_played = hand.pop(int(next))

							# Pick color if black
							if (next_played[0:3] == "bla"):
								col = input("Select a color: \n blu, yel, gre or red\n")
							else:
								col = next_played[0:3]
							break
						else:
							print("Wrong card, pick again!")

					except (ValueError, IndexError):
						print("Please enter a valid number")
			# Send data
			print("YOU PLAYED: ", next_played)

			data = {
				"pile": pile,
				"num_left": len(hand),
				"played": next_played,
				"last_played": last_played if next_played is None else None,
				"stage": "GO",
				"color": col
			}
			sock.sendto(json.dumps(data).encode(), addr)
			print("Sent")
		else:
			# Not your turn
			print("Waiting")
