from tkinter import Frame, Label, Menu, Button, messagebox, Tk
from tkinter import simpledialog
import math
from PIL import ImageTk, Image
from popup import InfoPop
import webbrowser
import logging
from logmanager import setup_logger
from picker import Picker
from stages import Stage
from typing import Any
import re
import queue
from deck import Deck
import copy
from tkmacosx import Button as but
import json
from json import JSONDecodeError

direction_for_img_location = "Images/directionfor.jpg.png"
direction_rev_img_location = "Images/directionrev.jpg.png"
BACKGROUND_COLOR = "#D1FFCC"
log = logging.getLogger(__name__)


class Game(Frame):
    global message
    message = {}

    # test if 7/0 when played is not too fast
    # perhaps uno button has a white border that can't be removed- try style?
    # perhaps make it more obvious if same card played twice in a row
    # perhaps unterminated string server when taking 4 ??
    # perhaps animation when someone places their card
    # test if animation is fast

    # todo save/ load game

    # Initialise a frame. Setup the pile, hand, last played card and all gui
    def __init__(self, master: Tk, queue, msg, sock, all_points):
        setup_logger(log)
        global message
        message = msg
        super().__init__(master)
        self.pack()
        log.info(message)
        self.peeps = message['peeps']
        self.move_id = '0'
        self.new_deck = Deck()
        self.modes = msg['modes']
        self.sock = sock
        self.master = master
        self.all_points = all_points
        self.parent = master
        self.master.protocol("WM_DELETE_WINDOW", self.close_window)
        # Take one card only
        self.card_counter = 1 if not self.modes[2] else 500
        self.q = queue
        self.quit_game = False
        self.identity = msg['whoami']
        self.last: Button
        self.challenge = but()
        self.valid_wild = but()
        self.stack_counter = 0 if 'two' not in msg['played'] else 2
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight() - 100
        self.animated = False
        frames: list[Frame] = []
        other_players = copy.deepcopy(self.peeps)
        other_players.pop(self.identity)
        self.childframes = {}
        frameleft = Frame(
            width=0.2 * self.screen_width,
            height=0.6 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground='black')
        frameleft.place(x=0, y=0)
        frames.append(frameleft)
        frametop = Frame(
            width=0.6 * self.screen_width,
            height=0.3 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground='black')
        frametop.place(x=0.2 * self.screen_width, y=0)
        frames.append(frametop)
        frameright = Frame(
            width=0.2 * self.screen_width,
            height=0.6 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground='black')
        frameright.place(x=0.8 * self.screen_width, y=0)
        frames.append(frameright)

        Frame(
            width=0.6 * self.screen_width,
            height=0.3 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground='black'
        ).place(x=0.2 * self.screen_width, y=0.3 * self.screen_height)

        self.card_frame = Frame(
            width=self.screen_width,
            height=0.4 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground='black'
        )
        self.card_frame.place(x=0, y=0.6 * self.screen_height)
        self.childframes[self.identity] = self.card_frame
        self.stack_label = Label(
            text="Stack\n cards to take:\n" + str(self.stack_counter),
            fg='black',
            bg='PeachPuff',
            width=10,
            height=3
        )
        self.is_reversed = message['dir']
        self.revdir = ImageTk.PhotoImage(
            Image.open(direction_rev_img_location).resize((95, 95), Image.LANCZOS)
        )
        self.fordir = ImageTk.PhotoImage(
            Image.open(direction_for_img_location).resize((95, 95), Image.LANCZOS)
        )

        self.direction_l = Label(
            image=self.revdir if self.is_reversed else self.fordir,
            width=95,
            height=95,
            border=0
        )
        # self.direction_l.image = self.revdir if self.is_reversed else self.fordir
        self.direction_l['image'] = self.revdir if self.is_reversed else self.fordir
        if self.modes[1]:
            self.stack_label.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 2)
            self.direction_l.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 82)
        else:
            self.direction_l.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 42)
        self.hand_cards = {}
        self.pile = msg['pile']
        self.all_nums_of_cards = msg['other_left']

        self.taken_label = Label(
            text="",
            fg='blue',
            bg=BACKGROUND_COLOR,
            width=28,
            height=1
        )
        self.taken_label.place(x=0.2 * self.screen_width + 1, y=0.3 * self.screen_height + 1)

        self.name_lbl = Label(
            text='You', fg="black", bg="pale green", width=18, height=1, font=("TkDefaultFont", 15)
        )
        self.name_lbl.place(x=1, y=0.6 * self.screen_height + 1)

        self.cards_left = Label(text="7", fg="black", bg="pale green", width=2, height=1)
        self.cards_left.place(x=0.15 * self.screen_width + 1, y=0.6 * self.screen_height + 1)
        self.uno_but = but(
            text="UNO",
            fg="black",
            bg="light sky blue",
            width=100,
            height=80,
            borderless=1,
            borderwidth=0,
            command=self.one_card)
        self.uno_but.place(x=0.26 * self.screen_width, y=0.35 * self.screen_height)
        self.uno = False
        # self.new_card = None
        self.setup_menu()
        self.setup_pile(msg)
        self.cards = self.deal_cards(msg)
        # Button for debugging
        self.debug = but(
            text="Not my turn", fg='red', bg='white', borderless=1,
            borderwidth=0, width=100,
            height=30, border=0,
            command=self.send_debug)
        self.debug.place(x=self.screen_width - 110, y=self.screen_height - 45)
        self.hand_btns = {}
        self.setup_hand(self.cards)
        if msg['player'] == 1:
            if 'two' in msg['played'] and (not self.can_stack() or not self.modes[1]):
                self.turn_need_taking = Label(
                    text="Take cards",
                    fg='black',
                    bg='orange',
                    width=12, height=1)
            else:
                self.turn_need_taking = Label(
                    text="", fg='Black', bg=BACKGROUND_COLOR, width=12, height=1)
        else:
            self.turn_need_taking = Label(
                text="", fg='black', bg=BACKGROUND_COLOR, width=12, height=1)
        self.turn_need_taking.place(x=0.18 * self.screen_width, y=0.6 * self.screen_height + 1)

        self.setup_other_players(other_players, frames)
        if msg['player'] == 1:
            self.name_lbl.config(bg='green', fg='white')
            # self.childframes[self.identity].config(highlightbackground='green',
        # highlightthickness=2)
        else:
            self.name_lbl.config(bg='red', fg='white')
            # self.childframes[self.identity].config(highlightbackground='red',highlightthickness=2)
        self.set_label_next(msg)

        txt_modes = ""
        if self.modes[0]:
            txt_modes += '7/0\n'
        else:
            txt_modes += '\n'
        if self.modes[1]:
            txt_modes += 'Stack +2\n'
        else:
            txt_modes += '\n'
        if self.modes[2]:
            txt_modes += 'Take many cards\n'
        else:
            txt_modes += '\n'
        if not any(self.modes):
            txt_modes = '\nRegular'
        InfoPop(self, 'Modes', txt_modes)

    # Create a hand of 7 cards from pile from message
    def deal_cards(self, message):
        hand = []
        self.pile = message['pile']
        for _ in range(7):
            c = self.pile.pop(0)
            # Lookup the card name from pile to get card itself
            card = self.new_deck.get_card(c)
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
                mode.add_command(label="Stack enabled", command=lambda i=2: show_mode(i))
            if self.modes[0]:
                mode.add_command(label="7-0 enabled", command=lambda i=1: show_mode(i))
            if self.modes[2]:
                mode.add_command(label="Take many cards enabled", command=lambda i=3: show_mode(i))
        menubar.add_cascade(label="Game mode rules", menu=mode)

        self.parent.configure(menu=menubar)

    # Add the pile and last played buttons
    def setup_pile(self, message):
        photo = ImageTk.PhotoImage(self.new_deck.backofcard)
        # Button to take a card (so a pile)
        self.new_card = Button(image=photo, width=117, height=183, border=0, command=self.take_card)
        # self.new_card.image = photo
        self.new_card.__setattr__("image", photo)
        self.new_card.place(x=0.44 * self.screen_width, y=0.32 * self.screen_height)
        # Last played card from the message
        lastplayed2 = message['played']  # this is a name!!
        photo2 = ImageTk.PhotoImage(self.new_deck.get_card(lastplayed2).card_pic)
        # Last is a disabled button with the last played card shown
        self.last = Button(
            text=lastplayed2, image=photo2, width=117, height=183, border=0, state="disabled")
        # self.last.image = photo2
        self.last.__setattr__("image", photo2)
        self.last.place(x=0.56 * self.screen_width, y=0.32 * self.screen_height)

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
                bg=BACKGROUND_COLOR)
            b['command'] = lambda ind=i, binst=b: self.place_card(ind, binst)
            # b.image = photo
            b.__setattr__("image", photo)
            self.hand_btns[i] = b
            self.hand_cards[i] = dealt_cards[i]
            coords = self.get_card_placement(n, i)
            b.place(x=coords[1], y=coords[2])

    def setup_other_players(self, peeps, frames):

        if len(peeps) >= 2:
            x_coords = [0, 0.2, 0.8]
        else:
            x_coords = [0.2]
            frames = [frames[1]]
        self.other_cards_lbls = {}
        self.other_names_lbls = {}
        self.other_cards_imgs = {}
        ctr = 0
        for j in range(self.identity + 1, self.identity + len(self.peeps)):
            # id is 3 range is [4,5,6,7] or [0,1,2,3]
            # id 2 range [3,4,5,6] [3,0,1,2]
            i = j % len(self.peeps)
            name_lbl = Label(
                text=self.peeps[i],
                fg="black",
                bg="pale green",
                width=18,
                height=1,
                font=("TkDefaultFont", 15))
            name_lbl.place(x=x_coords[ctr] * self.screen_width + 1, y=1)
            self.other_names_lbls[i] = name_lbl
            self.childframes[i] = frames[ctr]
            other_card_lbl = Label(
                text="7 cards", fg="black", bg="pale green", width=8, height=1)
            self.other_cards_lbls[i] = other_card_lbl
            other_card_lbl.place(x=(0.01 + x_coords[ctr]) * self.screen_width, y=31)
            self.other_cards_imgs[i] = []
            self.put_other_cards(i, self.all_nums_of_cards[i])
            ctr += 1

    def put_other_cards(self, who, num):
        photo = ImageTk.PhotoImage(self.new_deck.smallback)
        size = num if num <= 18 else 18
        for c in range(size):
            cardback = Label(text='lbl', image=photo, width=80, height=125, border=0)
            cardback['image'] = photo
            cardback.__setattr__("image", photo)
            # cardback.image = photo
            self.other_cards_imgs[who].append(cardback)

            if (who == (self.identity + 2) % len(self.peeps)) or (len(self.peeps) == 2):
                cardback.place(x=0.3 * self.screen_width + c * 30, y=40)
            elif who == (self.identity + 1) % len(self.peeps):
                cardback.place(x=0.1 * self.screen_width, y=35 + 15 * c)
            else:
                cardback.place(x=0.9 * self.screen_width, y=35 + 15 * c)

    # Move card to the pile in an animation
    def move(self, origx, origy, dx, dy, i, binst, img, ind):
        card = self.hand_cards[ind].name
        ratio = 40 if abs(dx) < 250 else 200
        time = 5 if abs(dx) < 250 else 1
        if not i == ratio:
            x = origx + (dx / ratio) * i
            y = origy + (dy / ratio) * i
            binst.place(x=x, y=y)
            i += 1
            self.move_id = self.after(time, self.move, origx, origy, dx, dy, i, binst, img, ind)
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
        if num_cards <= 20:
            overlap = math.floor(
                (117 - ((117 * num_cards) - 0.95 * self.screen_width) / (num_cards - 1)))
        else:
            overlap = math.floor((117 - ((117 * 20) - 0.95 * self.screen_width) / (20 - 1)))
        result.append(overlap)
        result.append(25 + overlap * (i % 20) + 15 * (math.floor(i / 20)))
        result.append(0.65 * self.screen_height + 40 * (math.floor(i / 20)))
        return result

    # #################################### EVENTS ##################################
    def place_card(self, ind, binst):
        if self.challenge:
            self.challenge.destroy()
        if self.valid_wild:
            self.valid_wild.destroy()
        self.update_idletasks()
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
                self.move(orig_x, orig_y, dx, dy, 0, binst, self.last["image"], ind)
            else:
                binst.destroy()
                self.complete_placement(card, ind)

    # Set new card on pile, send information, update hand - after animation or straight away
    def complete_placement(self, card, ind):
        if 'reverse' in card:
            self.is_reversed = not self.is_reversed
            # self.direction_l.image = self.revdir if self.is_reversed else self.fordir
            self.direction_l['image'] = self.revdir if self.is_reversed else self.fordir
            print('reversed')

        if 'plusfour' in card:
            is_valid_plus = self.can_put_plusfour()
        # Changes the black card to black with a color to show which one to play next
        if "bla" in card[0:3]:
            picker = Picker(
                self,
                "New color",
                "Which one?",
                ['Red', 'Green', 'Blue', 'Yellow'])
            new_color = picker.result
            new_color = new_color.lower()[0:3]
            # Get the colored black cards from the deck for ease of transfer
            if "plus" in card:
                new_color += "plus"
                card_col = new_color + "four"
                photocard = self.new_deck.get_special(new_color)
            else:
                new_color += "black"
                card_col = new_color + "black"
                photocard = self.new_deck.get_special(new_color)
        else:  # Not a black card
            photocard = self.hand_cards[ind].card_pic
            card_col = card
        img = ImageTk.PhotoImage(photocard)
        self.last.config(image=img, text=card_col)
        self.last["image"] = img
        self.last.__setattr__("image", img)
        self.last["text"] = card_col
        # Remove card from 'hand', update label with number
        self.hand_cards.pop(ind)
        self.hand_btns.pop(ind)
        self.all_nums_of_cards[self.identity] -= 1
        # text = self.label_for_cards_left(self.all_nums_of_cards)
        self.cards_left.config(text=self.all_nums_of_cards[self.identity])
        ctr = 0
        for i in self.hand_btns.keys():
            # Move all buttons
            b = self.hand_btns[i]
            coords = self.get_card_placement(len(self.hand_btns), ctr)
            b.place(x=coords[1], y=coords[2])
            ctr += 1

        data_to_send = {
            "played": card,
            "pile": self.pile,
            "stage": Stage.GO,
            "color": card_col,
            "num_left": len(self.hand_cards)
        }
        if 'plusfour' in card:
            data_to_send['wild'] = is_valid_plus
        # If placed plustwo in the mode, send the counter
        elif 'two' in card and self.modes[1]:
            data_to_send['counter'] = self.stack_counter + 2
            self.stack_label.config(text='Stack\n cards to take:\n' + str(
                self.stack_counter + 2))
            self.stack_counter = 0
        if "7" in card and self.modes[0] and len(self.hand_cards) > 0:
            self.send_design_update(0, len(self.hand_cards), card)
            players = [x for x in self.peeps if not self.peeps.index(x) == self.identity]
            swap = Picker(
                self,
                "Swap",
                "Who would you like to swap your cards with?",
                players)
            data_to_send['swapwith'] = self.peeps.index(swap.result)
            # data_to_send['stage'] = Stage.SEVEN
            data_to_send['hand'] = [self.hand_cards[c].name for c in self.hand_cards]
        if "0" in card and self.modes[0] and len(self.hand_cards) > 0:
            print("Zero")
            data_to_send['hand'] = [self.hand_cards[c].name for c in self.hand_cards]

        if self.uno:
            data_to_send['said_uno'] = True
        # Send all the information either in progress of the game, or to end it
        if len(self.hand_cards) > 0:
            self.sendInfo(data_to_send)
        else:
            self.sendFinal(data_to_send)

    def take_card(self):
        global message

        # Take new card
        new = self.new_deck.get_card(self.pile.pop(0))
        # Remove the 'uno not placed' button as was ignored
        if self.challenge:
            self.challenge.destroy()
        if self.valid_wild:
            self.valid_wild.destroy()
        self.update_idletasks()
        # Decrease number of cards that need to be taken
        self.card_counter -= 1
        # this at the bottom used to have 'and self.modes[1]' which it doesn't bc stack needs
        # to change always, no matter the mode
        if self.stack_counter > 0 and 'two' in self.last['text']:
            self.stack_counter -= 1
            self.stack_label.config(text='Stack\n cards to take:\n' + str(self.stack_counter))
            print("Stack: ", self.stack_counter)

        if not ('stage' in message.keys() and message['stage'] == Stage.ZEROCARDS):
            self.send_design_update(1, len(self.hand_cards) + 1)
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
            bg=BACKGROUND_COLOR,
            state='disabled'
        )
        b['command'] = lambda ind=ind, binst=b: self.place_card(ind, binst)
        b.__setattr__("image", photo)
        self.hand_btns[ind] = b
        self.all_nums_of_cards[self.identity] += 1
        # text = self.label_for_cards_left(self.all_nums_of_cards)
        self.cards_left.config(text=self.all_nums_of_cards[self.identity])
        ctr = 0
        print("Card counter: ", self.card_counter)
        print("Stack counter: ", self.stack_counter)
        # Is it possible to place a card right now?
        possible_move = self.possible_move()

        if possible_move and \
            (self.card_counter == 0 or (self.modes[2] and self.card_counter > 6)) and \
                self.stack_counter == 0:
            self.new_card.config(state='disabled')
            b.config(state='normal')
        for i in self.hand_btns.keys():
            # Move all buttons
            b = self.hand_btns[i]
            coords = self.get_card_placement(len(self.hand_btns), ctr)
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
            (possible_move is False or ('taken' not in message and "plus" in self.last['text']) or
                message['stage'] == Stage.CHALLENGE):
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
            # self.uno_but.config(bg=BACKGROUND_COLOR)
            # self.uno_but.config(bg='light sky blue')
            self.uno_but["bg"] = BACKGROUND_COLOR
            self.uno_but["bg"] = "light sky blue"

        else:
            self.uno = True
            self.uno_but["bg"] = "lime green"
        # self.uno_but.place_forget()
        print("UNO")

    # Show the points that you have with your cards right now (option in menu)
    def show_points(self):
        text = "Your points this session: " + str(self.all_points[self.identity]) + "\n"
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
            regex_point = re.search(r'\d+', c)
            if regex_point is not None:
                point = int(regex_point.group())
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
                    self.set_label_next(msg)
                    self.is_reversed = msg['dir']
                    self.direction_l.config(image=self.revdir if self.is_reversed else self.fordir)
                    # self.direction_l.image = self.revdir if self.is_reversed else self.fordir
                    self.direction_l['image'] = self.revdir if self.is_reversed else self.fordir
                    if "plustwo" in newC and 'taken' not in msg:
                        self.card_counter = 2
                        if self.modes[1]:
                            self.stack_counter = msg['counter']
                            self.stack_label.config(text='Stack\n cards to take:\n' + str(
                                self.stack_counter))
                            print("CTR: ", self.stack_counter)
                        self.taken_label.config(text='')
                    elif 'taken' in msg:
                        self.stack_counter = 0
                        self.stack_label.config(text='Stack\n cards to take:\n0')
                        self.taken_label.config(text='Other player took cards!')
                    else:
                        self.taken_label.config(text='')

                    for lbl in self.other_cards_lbls.keys():
                        crdtxt = " cards" if not msg['other_left'][lbl] == 1 else " card"
                        self.other_cards_lbls[lbl].config(
                            text=str(msg['other_left'][lbl]) + crdtxt)
                        for c in self.other_cards_imgs[lbl]:
                            c.destroy()
                        self.put_other_cards(lbl, msg['other_left'][lbl])
                    # Check if other player said UNO; place the challenge button if not said
                    # Update label to show that
                    if 'said_uno' in msg.keys() and not msg['said_uno']:
                        self.challenge = but(
                            text="UNO not said!", bg='red', fg='white',
                            width=150, height=30, command=self.challengeUno,
                            border=0)
                        if msg['player'] == 1:
                            self.challenge.place(
                                x=0.24 * self.screen_width,
                                y=0.49 * self.screen_height)
                    elif 'said_uno' in msg.keys() and msg['said_uno'] and 1 in msg['other_left']:
                        p = msg['from']
                        print("From: ", p)
                        # todo this says wrong player if uno after 7/0
                        if '0' in newC and 'taken' not in msg and self.modes[0]:
                            if self.is_reversed:
                                p = (p - 1) % len(self.peeps)
                            else:
                                p = (p + 1) % len(self.peeps)
                        if p != self.identity:
                            # messagebox.showinfo("UNO", self.peeps[p]+" has only 1 card left!")
                            InfoPop(self, 'UNO', self.peeps[p] + " \nhas only 1 card left!")

                    self.all_nums_of_cards = msg['other_left']

                    # left_cards_text = self.label_for_cards_left(msg['other_left'])
                    # left_cards_text += uno_said
                    # Set up label with number of remaining cards
                    # self.cards_left.config(text=left_cards_text)
                    # Enable buttons for cards if your turn; make UNO show if necessary
                    if int(msg['player']) == 1:
                        print("Your turn, enabling buttons")
                        self.name_lbl.config(bg='green')
                        # self.childframes[self.identity].config(highlightbackground='green',
                        # highlightthickness=2)
                        if 'plusfour' in newC and 'taken' not in msg and 'wild' in msg:
                            # Show 'challenge +4' button
                            self.valid_wild = but(
                                text='Illegal +4?', bg='HotPink', fg='black',
                                width=150, height=30, borderless=1, border=0,
                                command=lambda valid=msg['wild']: self.challenge_plus(valid))
                            self.valid_wild.place(
                                x=0.24 * self.screen_width,
                                y=0.55 * self.screen_height)
                        # No moves possible, or move possible but need to take cards
                        if not self.possible_move() or (self.card_counter == 2 or
                                                        self.card_counter == 4):
                            self.new_card.config(state='normal')
                        # Say your turn if either mode is normal, or take forever and not plus
                        if (self.card_counter < 2 and not self.modes[2]) or \
                            (self.modes[2] and not self.card_counter == 4 and not
                                self.card_counter == 2) or \
                                (self.modes[1] and self.can_stack() and 'two' in newC):
                            self.turn_need_taking.config(text="", bg=BACKGROUND_COLOR)
                            for i in self.hand_btns:
                                self.hand_btns[i].config(state='normal')
                            if self.modes[1] and self.can_stack() and 'two' in newC \
                                    and 'taken' not in msg and self.stack_counter > 0:
                                for i in self.hand_btns:
                                    if 'two' not in self.hand_btns[i]['text']:
                                        self.hand_btns[i].config(state='disabled')
                        else:
                            self.turn_need_taking.config(text="Take cards!", bg='orange')
                # Forgot to say UNO - enable taking new cards only
                elif msg['stage'] == Stage.CHALLENGE:
                    self.new_card.config(state='normal')
                    if msg['why'] == 1:
                        self.card_counter = 2
                        messagebox.showinfo(
                            "UNO not said!",
                            "You forgot to click UNO, so take 2 cards!")
                        self.turn_need_taking.config(text="Take 2 cards!", bg='orange')
                    else:
                        self.card_counter = 4
                        messagebox.showinfo(
                            "Illegal +4!",
                            "You can't put +4 when you have other cards, so take 4!")
                        self.turn_need_taking.config(text="Take 4 cards!", bg='orange')
                    self.name_lbl.config(bg='orange')

                elif msg['stage'] == Stage.SHOWCHALLENGE:
                    print('other player tried to check you for illegal +4')
                    was_challenge = Label(
                        text="Someone checked if +4 was illegal!",
                        bg='blue', fg='white', width=40, height=1)

                    was_challenge.place(x=0.4 * self.screen_width, y=0.6 * self.screen_height + 1)
                    self.master.after(5000, was_challenge.destroy)

                # Another player has finished the game; you either take cards if last is a plus,
                # or automatically send the remaining points for the other player
                elif msg['stage'] == Stage.ZEROCARDS:
                    self.set_played_img(msg)
                    if msg['to_take']:
                        # Enable taking cards
                        self.turn_need_taking.config(text='Take cards!', bg='orange')
                        self.name_lbl.config(bg='green')
                        # self.childframes[self.identity].config(highlightbackground='green',
                        # highlightthickness=2)
                        self.new_card.config(state='normal')
                        self.card_counter = 2 if "two" in msg['played'] else 4
                        if self.modes[1] and 'counter' in msg:
                            self.stack_counter = msg['counter']
                            self.stack_label.config(text='Stack\n cards to take:\n' + str(
                                self.stack_counter))

                    else:
                        # No cards need to be taken, send current points
                        points = {"stage": Stage.CALC, "points": self.calculate_points()}
                        points['padding'] = 'a' * (685 - len(json.dumps(points)))
                        self.sock.send(json.dumps(points).encode('utf-8'))

                # self.cards_left.config(text='Game over!')
                # Get points from the opponent and show them
                elif msg['stage'] == Stage.CALC:
                    table_of_points = ""
                    self.all_points = msg['total']
                    for i in range(len(msg['total'])):
                        table_of_points += "\n" + self.peeps[i] + ": " + str(
                            msg['total'][i]) + " points\n"
                    if msg['winner'] == self.identity:
                        messagebox.showinfo(
                            "Win",
                            f"You won {str(msg['points'])} points!\n\n Total this session: \n" +
                            table_of_points)
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
                            init['padding'] = 'a' * (685 - len(json.dumps(init)))
                            self.sock.send(json.dumps(init).encode('utf-8'))
                        else:
                            # Don't want the new game

                            bye: dict[str, Any] = {"stage": Stage.BYE}
                            bye['padding'] = 'a' * (685 - len(json.dumps(bye)))
                            self.sock.send(json.dumps(bye).encode('utf-8'))
                            print("No new game, sending a BYE message")
                            self.quit_game = True
                            break

                    else:
                        messagebox.showinfo(
                            "Win",
                            f"{self.peeps[msg['winner']]} won {str(msg['points'])} points!\n" +
                            " Total this session: \n" + table_of_points)

                elif msg['stage'] == Stage.SEVEN or msg['stage'] == Stage.ZERO:
                    # Show hand, say who from, send back own hand
                    hand = {
                        'stage': msg['stage'],
                        'hand': [self.hand_cards[c].name for c in self.hand_cards],
                        'from': self.identity}

                    self.update_btns(msg['hand'], msg['from'])
                    from_who = Label(
                        text="You got cards from " + self.peeps[msg['from']],
                        bg='blue', fg='white', width=40, height=1)

                    from_who.place(x=0.4 * self.screen_width, y=0.6 * self.screen_height + 1)
                    what = '7' if msg['stage'] == Stage.SEVEN else '0'
                    InfoPop(
                        self,
                        f'A {what} was played',
                        f"{what} was played.\n You got cards from \n {self.peeps[msg['from']]}")
                    self.master.after(10000, from_who.destroy)
                    # if msg['stage'] == Stage.SEVEN:
                    # 	messagebox.showinfo("New cards", "A 7 was played. \nYou swapped "
                    # 									 "cards with "+self.peeps[msg['from']])
                    # else:
                    # 	messagebox.showinfo("New cards", "A 0 was played. You get cards from \n"
                    # 						+self.peeps[msg['from']])

                    hand['padding'] = 'a' * (685 - len(json.dumps(hand)))
                    m = json.dumps(hand)
                    if 'end' not in msg:
                        self.sock.send(m.encode('utf-8'))

                elif msg['stage'] == Stage.NUMUPDATE:
                    print()
                    # self.cards_left.config(text=self.label_for_cards_left(msg['other_left']))
                    for other_label in self.other_cards_lbls.keys():
                        crdtxt = " cards" if not msg['other_left'][other_label] == 1 else " card"
                        self.other_cards_lbls[other_label].config(
                            text=str(msg['other_left'][other_label]) + crdtxt
                        )
                        o_cards = self.other_cards_imgs[other_label]
                        for car in o_cards:
                            car.destroy()

                        self.put_other_cards(other_label, msg['other_left'][other_label])

                elif msg['stage'] == Stage.DESIGNUPD:
                    print('design update')
                    who_updated = msg['from']
                    crdtxt = " cards" if not msg['num_cards'] == 1 else " card"
                    self.other_cards_lbls[who_updated].config(
                        text=str(msg['num_cards']) + crdtxt)
                    o_cards = self.other_cards_imgs[who_updated]
                    for car in o_cards:
                        car.destroy()

                    self.put_other_cards(who_updated, msg['num_cards'])
                    if msg['type'] == 0:
                        print('card placed design update')
                        img = ImageTk.PhotoImage(self.new_deck.get_card(msg['played']).card_pic)
                        self.last.config(image=img)
                        self.last["image"] = img
                        self.last.__setattr__("image", img)

                elif msg['stage'] == Stage.INIT:
                    print("New game!")
                    self.start_new(msg)
                elif msg['stage'] == Stage.BYE:
                    print("Received a BYE message, closing (another player decided to stop)")
                    self.quit_game = True
                    break

            except queue.Empty:
                pass
        if self.quit_game:
            print("Loop ended")
            self.close_window()

    def set_played_img(self, msg):
        newC = msg['played']
        # if plus take cards else send points
        if 'four' in newC:
            newC = msg['color'][0:3] + "plusfour"
            img = ImageTk.PhotoImage(self.new_deck.get_special(newC))
            if 'taken' not in msg:
                self.card_counter = 4
            else:
                self.card_counter = 1 if not self.modes[2] else 500
        elif 'bla' in newC:
            newC = msg['color'][0:3] + "black"
            img = ImageTk.PhotoImage(self.new_deck.get_special(newC))
        else:
            img = ImageTk.PhotoImage(self.new_deck.get_card(newC).card_pic)
            self.card_counter = 1 if not self.modes[2] else 500
        self.last.config(image=img, text=newC)
        self.last["image"] = img
        self.last.__setattr__("image", img)
        self.pile = msg['pile']

    # Put received message in queue for async processing
    def receive(self):
        global message, root
        while not self.quit_game:
            print("Waiting")
            try:
                json_msg, addr = self.sock.recvfrom(700)
                # print("LENGTH: ", len(json_msg))
                data = json_msg.decode('utf-8')
                message = json.loads(data)
                if len(data) < 700:
                    print("[BUG] This message is short, find out why!")
                    print(message)
                    print("PADDING: ", len(message['padding']))
                self.q.put(message)
            except JSONDecodeError as er:
                if "Expecting value" in str(er):
                    self.quit_game = True
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

    def send_design_update(self, type, num, *args):
        # 1 = taken, 0 = placed
        data = {
            'stage': Stage.DESIGNUPD,
            'type': type,
            'num_cards': num,
            'from': self.identity
        }
        if type == 0:
            data['played'] = args[0]
        data['padding'] = 'a' * (685 - len(json.dumps(data)))
        self.sock.send(json.dumps(data).encode('utf-8'))
        print('Design update sent')

    # Disable all buttons when sending information and when it's not your turn anymore
    def sendInfo(self, data_to_send):
        data_to_send['padding'] = 'a' * (685 - len(json.dumps(data_to_send)))
        self.sock.send(json.dumps(data_to_send).encode('utf-8'))
        self.new_card.config(state="disabled")
        self.uno = False
        self.card_counter = 1 if not self.modes[2] else 500
        self.uno_but["bg"] = "light sky blue"
        if data_to_send['stage'] == Stage.GO and 'stop' in data_to_send['played'] \
                and 'taken' not in data_to_send:
            self.update_next_lbl(2)
        elif data_to_send['stage'] == Stage.GO:
            self.update_next_lbl(1)

        for i in self.hand_btns:
            self.hand_btns[i].config(state='disabled')
        self.turn_need_taking.config(text="", bg=BACKGROUND_COLOR)
        self.name_lbl.config(bg='red', fg='white')
        # self.childframes[self.identity].config(highlightbackground='red',highlightthickness=2)
        self.taken_label.config(text='')
        print("Not your turn anymore")

    # Notify opponent that they forgot to say UNO; when clicking button
    def challengeUno(self):
        data = {"stage": Stage.CHALLENGE, 'why': 1}
        if self.modes[1] and self.stack_counter > 0:
            data['counter'] = self.stack_counter
        self.sendInfo(data)
        self.challenge.destroy()
        self.update_idletasks()

    def challenge_plus(self, is_valid):
        data = {'stage': Stage.CHALLENGE, 'why': 4}
        # If true that can't put +4, so it was illegal, send it
        if not is_valid:
            self.sendInfo(data)
        else:
            self.card_counter = 6
            data = {'stage': Stage.SHOWCHALLENGE, 'from': self.identity}
            data['padding'] = 'a' * (685 - len(json.dumps(data)))
            self.sock.send(json.dumps(data).encode('utf-8'))
            messagebox.showinfo("Legal move", "The player was honest, so take 6 cards!")
        self.valid_wild.destroy()
        self.update_idletasks()

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
        self.turn_need_taking.config(text="Getting results!", bg=BACKGROUND_COLOR, fg='blue')
        data_to_send['padding'] = 'a' * (685 - len(json.dumps(data_to_send)))
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
                crdtxt = " cards" if not self.peeps[pl] == 1 else " card"
                left_cards_text += "\n " + self.peeps[pl] + ": " + str(x) + crdtxt
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
            self.hand_cards[i] = self.new_deck.get_card(c)
        self.setup_hand(self.hand_cards)
        for j in self.hand_btns:
            self.hand_btns[j].config(state='disabled')
        self.all_nums_of_cards[self.identity] = new
        self.all_nums_of_cards[player] = old
        crdtxt = " cards" if not old == 1 else " card"
        self.other_cards_lbls[player].config(text=str(old) + crdtxt)
        self.cards_left.config(text=str(new))

    # self.cards_left.config(text=self.label_for_cards_left(self.all_nums_of_cards))

    def set_label_next(self, msg):
        if msg['player'] == 1:
            a = self.identity
        else:
            a = msg['curr']

        for other_label in self.other_names_lbls.keys():
            self.other_names_lbls[other_label].config(
                bg='green' if other_label == a else 'red',
                fg='white'
            )
            # self.childframes[l].config(highlightbackground='green' if l == a else 'red',
            # highlightthickness=2)

    def update_next_lbl(self, ind):

        # Take all players and move them up by 1/2 when turn finished
        if not self.is_reversed:
            a = (self.identity + ind) % len(self.peeps)
        else:
            a = (self.identity - ind) % len(self.peeps)
        # if a in self.other_names_lbls.keys():
        # bug keyerror: 0 and 1 below (mostly on stop. errors for the player who placed stop)
        self.other_names_lbls[a].config(bg='green')
        # self.childframes[a].config(highlightbackground='green',highlightthickness=2)

    def checkPeriodically(self):
        self.incoming()
        if not self.quit_game:
            self.after(100, self.checkPeriodically)

    def start_new(self, message):

        print("Destroying old game...")
        self.master.destroy()

        root = Tk()
        root.configure(bg='white')
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry("{}x{}".format(screen_width, screen_height))
        root.title("UNO - player " + str(message['whoami']) + " - " + message['peeps'][message[
            'whoami']])
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
            bye['padding'] = 'a' * (685 - len(json.dumps(bye)))
            self.sock.send(json.dumps(bye).encode('utf-8'))
            self.sock.close()
        except OSError:
            pass
        self.quit_game = True

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
        "No stacking, take one card only. You can click on cards when it's your turn. Press the"
        " UNO button BEFORE making the move, not after - otherwise you'll have to take 2 cards."
        " The \"Not my turn\" button is used for bug reporting and to change your turn to someone "
        "else.\n Would you like to visit Wiki for official rules?")
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
