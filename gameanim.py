from tkinter import Frame, Label, Menu, Button, messagebox, Tk, TclError
from tkinter import simpledialog
import math
from PIL import ImageTk, Image
from popup import InfoPop
import webbrowser
from logging import Logger
from typing import Optional
from picker import Picker
from game_classes import Stage, Modes, GameState
from turn_state import TurnState
from typing import Any
from card import Card
from socket import socket
import queue
from deck import Deck
import copy
from tkmacosx import Button as but
import json
from json import JSONDecodeError
from message_utils import recover
import utils

direction_for_img_location = "Images/directionfor.jpg.png"
direction_rev_img_location = "Images/directionrev.jpg.png"
icon_img_location = "Images/unoimg.png"

STACK_LABEL_TEXT = "Stack\n cards to take:\n"

BACKGROUND_COLOR = "#D1FFCC"
TURN_COLOR = "#FDFFD2"


class Game(Frame):

    # Initialise a frame. Setup the pile, hand, last played card and all gui
    def __init__(
        self,
        master: Tk,
        queue,  #: queue.Queue,
        msg: dict[str, Any],
        sock: socket,
        all_points,
        logger: Logger
    ):
        self.log = logger
        super().__init__(master)
        self.pack()
        self.game_state = GameState(
            msg["whoami"],
            msg["peeps"],
            Deck(),
            all_points,
            Modes.from_json(msg["modes"])
        )
        self.move_id = "0"
        self.sock = sock
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.send_bye_and_exit)
        self.q = queue
        self.quit_game = False
        other_players: list[str] = copy.deepcopy(self.game_state.peeps)
        other_players.pop(self.game_state.index)
        self.log.info(f"I am {self.game_state.identity}, playing against {other_players}")

        self.turn_state = TurnState(
            stack_counter=0 if "two" not in msg["played"] else 2,
            all_nums_of_cards=msg["other_left"],
            card_counter=1 if not self.game_state.modes.mult else 500,
            is_reversed=msg["dir"],
            pile=msg["pile"],
            uno=False,
            last_played=msg["played"],
            game_state=self.game_state,
            stage=msg["stage"]
        )

        self.init_ui_elements(msg, other_players)

    # UI settings
    def init_ui_elements(self, msg: dict[str, Any], opponents: list[str]):
        icon = ImageTk.PhotoImage(Image.open(icon_img_location))
        self.master.tk.call('wm', 'iconphoto', self.master, icon)
        self.last: Button
        self.challenge = but()
        self.valid_wild = but()
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight() - 100
        self.animated = False
        frames: list[Frame] = []
        self.childframes = {}
        frameleft = Frame(
            width=0.2 * self.screen_width,
            height=0.6 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="black")
        frameleft.place(x=0, y=0)
        frames.append(frameleft)
        frametop = Frame(
            width=0.6 * self.screen_width,
            height=0.3 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="black")
        frametop.place(x=0.2 * self.screen_width, y=0)
        frames.append(frametop)
        frameright = Frame(
            width=0.2 * self.screen_width,
            height=0.6 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="black")
        frameright.place(x=0.8 * self.screen_width, y=0)
        frames.append(frameright)

        Frame(
            width=0.6 * self.screen_width,
            height=0.3 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="black"
        ).place(x=0.2 * self.screen_width, y=0.3 * self.screen_height)

        self.card_frame = Frame(
            width=self.screen_width,
            height=0.4 * self.screen_height,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="black"
        )
        self.card_frame.place(x=0, y=0.6 * self.screen_height)
        self.childframes[self.game_state.identity] = self.card_frame
        self.stack_label = Label(
            text=f"{STACK_LABEL_TEXT}{self.turn_state.stack_counter}",
            fg="black",
            bg="PeachPuff",
            width=10,
            height=3
        )
        self.revdir = ImageTk.PhotoImage(
            Image.open(direction_rev_img_location).resize((95, 95), Image.LANCZOS)
        )
        self.fordir = ImageTk.PhotoImage(
            Image.open(direction_for_img_location).resize((95, 95), Image.LANCZOS)
        )

        self.direction_l = Label(
            image=self.revdir if self.turn_state.is_reversed else self.fordir,
            width=95,
            height=95,
            border=0
        )
        self.direction_l["image"] = self.revdir if self.turn_state.is_reversed else self.fordir
        if self.game_state.modes.stack:
            self.stack_label.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 2)
            self.direction_l.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 82)
        else:
            self.direction_l.place(x=0.68 * self.screen_width, y=0.3 * self.screen_height + 42)

        self.taken_label = Label(
            text="",
            fg="blue",
            bg=BACKGROUND_COLOR,
            width=28,
            height=1
        )
        self.taken_label.place(x=0.2 * self.screen_width + 1, y=0.3 * self.screen_height + 1)

        self.name_lbl = Label(
            text="You", fg="black", bg="pale green", width=18, height=1, font=("TkDefaultFont", 15)
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
            command=self.toggle_uno)
        self.uno_but.place(x=0.26 * self.screen_width, y=0.35 * self.screen_height)
        # self.new_card = None
        self.setup_menu()
        self.setup_pile(msg["played"])
        # Button for debugging
        self.debug = but(
            text="Skip turn", fg="red", bg="white", borderless=1,
            borderwidth=0, width=100,
            height=30, border=0,
            command=self.send_debug)
        self.debug.place(x=self.screen_width - 120, y=self.screen_height - 55)
        self.hand_btns: dict[int, Button] = {}
        self.setup_hand()
        if msg["player"]:
            if "two" in msg["played"] and \
                    (not self.turn_state.can_stack or not self.game_state.modes.stack):
                self.turn_need_taking = Label(
                    text="Take cards",
                    fg="black",
                    bg="orange",
                    width=12, height=1)
            else:
                self.turn_need_taking = Label(
                    text="", fg="Black", bg=TURN_COLOR, width=12, height=1
                )
        else:
            self.turn_need_taking = Label(
                text="", fg="black", bg=BACKGROUND_COLOR, width=12, height=1)
        self.turn_need_taking.place(x=0.18 * self.screen_width, y=0.6 * self.screen_height + 1)

        self.setup_other_players(opponents, frames)
        if msg["player"]:
            self.name_lbl.config(bg="green", fg="white")
            self.childframes[self.game_state.identity].config(bg=TURN_COLOR)
        else:
            self.name_lbl.config(bg="red", fg="white")
            self.childframes[self.game_state.identity].config(bg=BACKGROUND_COLOR)
        self.set_label_next(msg)
        self.show_enabled_modes()

    # UI settings
    def show_enabled_modes(self):
        txt_modes = ""
        if self.game_state.modes.is_regular():
            txt_modes = "\nRegular"
        else:
            txt_modes = "\n".join(self.game_state.modes.enabled_strings())
        # InfoPop(self, "Modes", txt_modes)
        self.show_information("Modes", txt_modes, default=True)

    # Create a menu bar, configure to add to master (which is the root window)
    # UI settings
    def setup_menu(self):
        menubar = Menu(self)

        menu = Menu(menubar)
        menu.add_command(label="Rules", command=show_rules)
        menu.add_command(label="Points", command=self.show_points)
        menu.add_command(label="Toggle animation", command=self.set_anim)
        menubar.add_cascade(label="Menu", menu=menu)
        mode = Menu(menubar)
        if self.game_state.modes.is_regular():
            mode.add_command(label="Regular enabled")
        else:
            for mode_str in self.game_state.modes.enabled_strings():
                mode.add_command(
                    label=f"{mode_str} enabled",
                    command=lambda mode_type=mode_str: show_mode(mode_type)
                )
        menubar.add_cascade(label="Game mode rules", menu=mode)

        self.master["menu"] = menubar

    # Add the pile and last played buttons
    # UI settings
    def setup_pile(self, last_played_card: str):
        photo = ImageTk.PhotoImage(self.game_state.deck.backofcard)
        # Button to take a card (so a pile)
        self.new_card = Button(image=photo, width=117, height=183, border=0, command=self.take_card)
        # self.new_card.image = photo
        self.new_card.__setattr__("image", photo)
        self.new_card.place(x=0.44 * self.screen_width, y=0.32 * self.screen_height)
        # Last played card from the message
        photo2 = ImageTk.PhotoImage(self.game_state.deck.get_card(last_played_card).card_pic)
        # Last is a disabled button with the last played card shown
        self.last = Button(
            text=last_played_card, image=photo2, width=117, height=183, border=0, state="disabled")
        # self.last.image = photo2
        self.last.__setattr__("image", photo2)
        self.last.place(x=0.56 * self.screen_width, y=0.32 * self.screen_height)

    # UI settings
    def setup_hand(self):
        # Setup a fresh hand, deleting anything that was there before (either on new game or card
        # swap)
        if len(self.hand_btns) > 0:
            for i in self.hand_btns:
                self.hand_btns[i].destroy()
        self.hand_btns: dict[int, Button] = {}
        dealt_cards = self.turn_state.hand_cards
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
            b["command"] = lambda ind=i, binst=b: self.place_card(ind, binst)
            b.__setattr__("image", photo)
            self.hand_btns[i] = b
            coords = self.get_card_placement(n, i)
            b.place(x=coords[1], y=coords[2])

    # UI settings
    def setup_other_players(self, peeps: list[str], frames: list[Frame]):

        if len(peeps) >= 2:
            x_coords = [0, 0.2, 0.8]
        else:
            x_coords = [0.2]
            frames = [frames[1]]
        self.other_cards_lbls: dict[str, Label] = {}
        self.other_names_lbls: dict[str, Label] = {}
        self.other_cards_imgs: dict[str, list[Label]] = {}
        ctr = 0  # refactor
        for j in range(
            self.game_state.index + 1,
            self.game_state.index + len(self.game_state.peeps)
        ):
            # id is 3 range is [4,5,6,7] or [0,1,2,3]
            # id 2 range [3,4,5,6] [3,0,1,2]
            i = j % len(self.game_state.peeps)
            person = self.game_state.peeps[i]
            name_lbl = Label(
                text=person,
                fg="black",
                bg="pale green",
                width=18,
                height=1,
                font=("TkDefaultFont", 15))
            name_lbl.place(x=x_coords[ctr] * self.screen_width + 1, y=1)
            self.other_names_lbls[person] = name_lbl
            self.childframes[person] = frames[ctr]
            other_card_lbl = Label(
                text="7 cards", fg="black", bg="pale green", width=8, height=1)
            self.other_cards_lbls[person] = other_card_lbl
            other_card_lbl.place(x=(0.01 + x_coords[ctr]) * self.screen_width, y=31)
            self.other_cards_imgs[person] = []
            self.put_other_cards(person, self.turn_state.all_nums_of_cards[person])
            ctr += 1

    # UI settings
    def put_other_cards(self, who: str, num: int):
        photo = ImageTk.PhotoImage(self.game_state.deck.smallback)
        size = num if num <= 18 else 18
        for c in range(size):
            cardback = Label(text="lbl", image=photo, width=80, height=125, border=0)
            cardback["image"] = photo
            cardback.__setattr__("image", photo)
            self.other_cards_imgs[who].append(cardback)
            skip_person = self.game_state.peeps[
                (self.game_state.index + 2) % len(self.game_state.peeps)
            ]
            next_person = self.game_state.peeps[
                (self.game_state.index + 1) % len(self.game_state.peeps)
            ]
            if (who == skip_person) or len(self.game_state.peeps) == 2:
                cardback.place(x=0.3 * self.screen_width + c * 30, y=40)
            elif who == next_person:
                cardback.place(x=0.1 * self.screen_width, y=35 + 15 * c)
            else:
                cardback.place(x=0.9 * self.screen_width, y=35 + 15 * c)

    # UI settings
    # Move card to the pile in an animation
    def move(self, origx: int, origy: int, dx: int, dy: int, i: int, binst, img, ind: int):
        card = self.turn_state.hand_cards[ind].name
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
            self.move_id = "ended"
            self.complete_placement(card, ind)

    # UI settings
    def get_card_placement(self, num_cards: int, i: int):
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
    # UI settings (if not UI, just call complete_placement)
    def place_card(self, ind: int, binst):
        card = self.turn_state.hand_cards[ind].name
        old_card = self.turn_state.last_played
        # Same color (0:3), same symbol (3:), black
        same_color = card[0:3] == old_card[0:3]
        same_symbol = card[3:] == old_card[3:]
        if same_color or same_symbol or "bla" in card[0:3]:
            # You can't have the "Illegal +4" when placing a card, as you never place it, so don't
            # handle it
            self.handle_challenge_button(player=None, destroy=True)
            # If animation is turned on, move, else place on pile straight away
            if self.animated:
                dest_x = self.last.winfo_x()
                dest_y = self.last.winfo_y()
                orig_x = binst.winfo_x()
                orig_y = binst.winfo_y()
                dx = dest_x - orig_x
                dy = dest_y - orig_y
                self.move(orig_x, orig_y, dx, dy, 0, binst, self.last["image"], ind)
            else:
                binst.destroy()
                self.complete_placement(card, ind)

    # Set new card on pile, send information, update hand - after animation or straight away
    def complete_placement(self, card: str, ind: int):
        if "reverse" in card:
            self.turn_state.is_reversed = not self.turn_state.is_reversed
        # Changes the black card to black with a color to show which one to play next
        if "bla" in card[0:3]:
            new_color = self.pick_option(
                "New color",
                "Which one?",
                ["Red", "Green", "Blue", "Yellow"])
            new_color = new_color.lower()[0:3]
            # Get the colored black cards from the deck for ease of transfer
            if "plus" in card:
                new_color += "plus"
                special_card = new_color + "four"
            else:
                new_color += "black"
                special_card = new_color + "black"
        else:  # Not a black card
            special_card = card

        # Remove card from "hand", update label with number
        self.turn_state.hand_cards.pop(ind)
        self.turn_state.all_nums_of_cards[self.game_state.identity] -= 1

        self.update_labels_buttons_card_placed(special_card, ind)

        data_to_send = {
            "played": card,
            "pile": self.turn_state.pile,
            "stage": Stage.GO,
            "color": special_card,
            "num_left": self.turn_state.num_cards_left
        }
        if "plusfour" in card:
            data_to_send["wild"] = self.turn_state.can_put_plusfour
        # If placed plustwo in the mode, send the counter
        elif "two" in card and self.game_state.modes.stack:
            data_to_send["counter"] = self.turn_state.stack_counter + 2
            self.turn_state.update_stack_counter(0)
        if "7" in card and self.game_state.modes.sevenzero and self.turn_state.num_cards_left > 0:
            self.send_design_update(0, self.turn_state.num_cards_left, card)
            players = [x for x in self.game_state.peeps if not x == self.game_state.identity]
            swap_with = self.pick_option(
                "Swap",
                "Who would you like to swap your cards with?",
                players)
            data_to_send["swapwith"] = swap_with
            data_to_send["hand"] = self.turn_state.get_hand_card_names()

        if "0" in card and self.game_state.modes.sevenzero and self.turn_state.num_cards_left > 0:
            data_to_send["hand"] = self.turn_state.get_hand_card_names()

        if self.turn_state.uno:
            data_to_send["said_uno"] = True
        # Send all the information either in progress of the game, or to end it
        if self.turn_state.num_cards_left > 0:
            self.send_info(data_to_send)
        else:
            self.send_final(data_to_send)
        self.turn_state.last_played = special_card

        self.update_last_played_img(special_card)

    # UI settings
    def update_labels_buttons_card_placed(self, card: str, ind: int):
        if "reverse" in card:
            self.direction_l["image"] = self.revdir if self.turn_state.is_reversed else self.fordir
        self.hand_btns.pop(ind)
        self.cards_left.config(text=self.turn_state.all_nums_of_cards[self.game_state.identity])
        self.move_buttons()
        if "two" in card and self.game_state.modes.stack:
            self.configure_stack_label(self.turn_state.stack_counter + 2)

    # UI settings
    def pick_option(self, title: str, question: str, options: Optional[list[str]]) -> str:
        if options:
            picker = Picker(self, title, question, options)
            return picker.result
        else:
            response = simpledialog.askstring(title, question)
            return response if response else "0"

    def take_card(self):
        # Take new card
        new = self.game_state.deck.get_card(self.turn_state.pile.pop(0))
        # Remove the "uno not placed" button as was ignored
        self.handle_challenge_button(player=None, destroy=True)
        self.handle_wild_button(destroy=True)
        # Decrease number of cards that need to be taken
        self.turn_state.card_counter -= 1

        if self.turn_state.stack_counter > 0 and "two" in self.turn_state.last_played:
            # or "four" in self.turn_state.last_played
            self.turn_state.stack_counter -= 1

        if not (self.turn_state.stage == Stage.ZEROCARDS):
            self.send_design_update(1, self.turn_state.num_cards_left + 1)
        # Since hand is a dict, the keys aren't in order.
        # Get the largest and add 1 for the next
        ind = max(list(self.turn_state.hand_cards.keys())) + 1
        # Add new card to the "hand", create new button, update number
        self.turn_state.hand_cards[ind] = new
        self.turn_state.all_nums_of_cards[self.game_state.identity] += 1
        self.log.info(f"Card counter: {self.turn_state.card_counter}")
        self.log.info(f"Stack counter: {self.turn_state.stack_counter}")
        # Is it possible to place a card right now?
        possible_move = self.turn_state.possible_move
        self.log.info(f"Move possible: {possible_move}")

        # Create and enable a new button for the card + update labels
        self.update_labels_buttons_card_taken(new, ind, possible_move)

        # Send the points from the cards if you had to take them at the end (last played was +,
        # but game is over)
        if self.turn_state.card_counter <= 0 and \
                self.turn_state.stack_counter == 0 and self.turn_state.stage == Stage.ZEROCARDS:
            data_to_send = {"stage": Stage.CALC, "points": self.turn_state.calculate_points()}
            self.send_info(data_to_send)

        # Send information about taken cards if can't go or had to take +2/4 due to challenge or
        # card
        if self.turn_state.card_counter <= 0 and self.turn_state.stack_counter == 0 and \
            (possible_move is False or
                (not self.turn_state.cards_taken_previously and
                    "plus" in self.turn_state.last_played) or
                self.turn_state.stage == Stage.CHALLENGE):
            data_to_send = {
                "played": self.turn_state.last_played,
                "pile": self.turn_state.pile,
                "stage": Stage.GO,
                "color": self.turn_state.last_played[0:3],
                "num_left": self.turn_state.num_cards_left
            }
            if self.turn_state.stage != Stage.CHALLENGE:
                data_to_send["taken"] = True
            else:
                data_to_send["stage"] = Stage.CHALLENGE_TAKEN
                data_to_send["why"] = self.turn_state.why_challenge_in_progress
            self.send_info(data_to_send)

    # UI settings
    def configure_stack_label(self, counter: int):
        self.stack_label.config(text=f"{STACK_LABEL_TEXT}{counter}")

    # UI settings
    def update_labels_buttons_card_taken(self, new_card: Card, index: int, move_is_possible: bool):
        if self.turn_state.stack_counter >= 0 and "two" in self.turn_state.last_played:
            # or "four" in self.turn_state.last_played
            self.configure_stack_label(self.turn_state.stack_counter)
        self.cards_left.config(text=self.turn_state.all_nums_of_cards[self.game_state.identity])

        photo = ImageTk.PhotoImage(new_card.card_pic)
        b = Button(
            text=new_card.name,
            image=photo,
            width=117,
            height=183,
            border=0,
            bg=BACKGROUND_COLOR,
            state="disabled"
        )
        b["command"] = lambda ind=index, binst=b: self.place_card(ind, binst)
        b.__setattr__("image", photo)
        self.hand_btns[index] = b
        if move_is_possible and \
            (self.turn_state.card_counter == 0 or
                (self.game_state.modes.mult and self.turn_state.card_counter > 6)) and \
                self.turn_state.stack_counter == 0:
            self.new_card.config(state="disabled")
            b.config(state="normal")
        self.move_buttons()

    def move_buttons(self):
        ctr = 0
        for i in self.hand_btns.keys():
            # Move all buttons
            b = self.hand_btns[i]
            coords = self.get_card_placement(len(self.hand_btns), ctr)
            b.place(x=coords[1], y=coords[2])
            ctr += 1

    # Change the button color and enable/disable the parameter
    def toggle_uno(self):
        self.toggle_uno_button_color()
        self.turn_state.set_uno(not self.turn_state.uno)
        self.log.info(f"UNO button clicked. Uno is {self.turn_state.uno}")

    # UI settings
    def toggle_uno_button_color(self):
        if self.turn_state.uno:
            self.uno_but["bg"] = BACKGROUND_COLOR
            self.uno_but["bg"] = "light sky blue"

        else:
            self.uno_but["bg"] = "lime green"

    # UI settings
    # Show the points that you have with your cards right now (option in menu)
    def show_points(self):
        text = f"Your points this session: {self.game_state.all_points[self.game_state.identity]}\n"
        for player, pts in self.game_state.all_points.items():
            if player == self.game_state.identity:
                text += "(You) "
            text += f"{player}: {pts} points\n"
        self.show_information("Points", text, default=True)

    # both settings
    def incoming(self):
        while self.q.qsize():
            try:
                msg = self.q.get(0)
                # Played, pile, num_left, color, player, saiduno, taken
                self.log.info("Processing message:")
                self.log.debug(msg)
                # todo probably update all turnstate elements in one go
                self.turn_state.stage = msg["stage"]
                self.turn_state.cards_taken_previously = msg.get("taken", False)
                self.turn_state.why_challenge_in_progress = msg.get("why", 0)
                # Normal play stage
                if msg["stage"] == Stage.GO:
                    self.process_regular_message(msg)
                # Forgot to say UNO - enable taking new cards only
                elif msg["stage"] == Stage.CHALLENGE:
                    self.enable_taking_for_challenge(msg["why"])

                elif msg["stage"] == Stage.SHOWCHALLENGE:
                    self.log.info("Another player tried to check you for illegal +4")
                    self.show_temp_banner("Someone checked if +4 was illegal!", 5000)

                # Another player has finished the game; you either take cards if last is a plus,
                # or automatically send the remaining points for the other player
                elif msg["stage"] == Stage.ZEROCARDS:
                    self.set_last_played(msg)
                    if msg["to_take"]:
                        # Enable taking cards
                        self.enable_taking_for_final_plus(msg)

                        self.turn_state.update_card_counter(
                            2 if "two" in msg["played"] else 4
                        )
                        if self.game_state.modes.stack and "counter" in msg:
                            self.turn_state.update_stack_counter(msg["counter"])
                            self.configure_stack_label(self.turn_state.stack_counter)

                    else:
                        # No cards need to be taken, send current points
                        points = {"stage": Stage.CALC, "points": self.turn_state.calculate_points()}
                        points["padding"] = "a" * (685 - len(json.dumps(points)))
                        self.sock.send(json.dumps(points).encode("utf-8"))

                # Get points from the opponent and show them
                elif msg["stage"] == Stage.CALC:
                    table_of_points = ""
                    self.game_state.all_points = msg["total"]
                    for player, pts in msg["total"].items():
                        table_of_points += \
                            f"\n{player}: {pts} points\n"

                    if msg["winner"] == self.game_state.identity:
                        start_new_game = self.process_winning(msg["points"], table_of_points)
                        if not start_new_game:
                            break
                    else:
                        self.show_information(
                            "Win",
                            f"{msg['winner']} won {msg['points']} points!\n"
                            f" Total this session: \n{table_of_points}",
                            default=True
                        )

                elif msg["stage"] == Stage.SEVEN or msg["stage"] == Stage.ZERO:
                    # Show hand, say who from, send back own hand
                    hand = {
                        "stage": msg["stage"],
                        "hand": self.turn_state.get_hand_card_names(),
                        "from": self.game_state.identity
                    }
                    what = "7" if msg["stage"] == Stage.SEVEN else "0"

                    hand["padding"] = "a" * (685 - len(json.dumps(hand)))
                    m = json.dumps(hand)
                    if "end" not in msg:
                        self.sock.send(m.encode("utf-8"))

                    self.inform_about_sevenzero(msg, what)

                elif msg["stage"] == Stage.NUMUPDATE:
                    self.update_other_nums_of_cards(msg)

                elif msg["stage"] == Stage.DESIGNUPD:
                    self.process_design_update(msg)

                elif msg["stage"] == Stage.INIT:
                    self.log.info("New game!")
                    self.start_new(msg)
                elif msg["stage"] == Stage.BYE:
                    self.log.info("Received a BYE message, closing (someone exited?)")
                    self.quit_game = True
                    break

            except queue.Empty:
                pass
        if self.quit_game:
            self.log.info("Loop ended")
            self.send_bye_and_exit()

    def process_regular_message(self, msg: dict[str, Any]):
        # todo some of this could be turn_state methods
        # Set the last played card and configure the pile + card counter
        self.set_last_played(msg)
        newly_played = msg["played"]
        self.log.info(f"Played: {newly_played}")
        if "plustwo" in newly_played and "taken" not in msg:
            self.turn_state.update_card_counter(2)
            if self.game_state.modes.stack:
                self.turn_state.update_stack_counter(msg["counter"])
        elif "taken" in msg:
            self.turn_state.update_stack_counter(0)
        self.update_labels_new_turn(newly_played, msg)
        self.update_other_nums_of_cards(msg)

        # Check if other player said UNO; place the challenge button if not said
        if "said_uno" in msg.keys() and not msg["said_uno"]:
            self.handle_challenge_button(msg["player"])
            # todo refactor other_left.values() should be by person
        elif "said_uno" in msg.keys() and msg["said_uno"] and 1 in msg["other_left"].values():
            from_player: str = msg["from"]
            # todo this says wrong player if uno after 7. after 0 no message on 2 bc the other
            # player doesn't get a message update - only a numupdate
            if "0" in newly_played and "taken" not in msg and self.game_state.modes.sevenzero:
                direction = -1 if self.turn_state.is_reversed else 1
                player_index = self.game_state.peeps.index(from_player)
                from_player = self.game_state.peeps[
                    (player_index + direction) % len(self.game_state.peeps)
                ]
            if from_player != self.game_state.identity:
                self.show_information(
                    "UNO",
                    f"{from_player}\n has only 1 card left!",
                    default=False
                )

        self.turn_state.all_nums_of_cards = msg["other_left"]

        # Enable buttons for cards if your turn; make UNO show if necessary
        if msg["player"]:
            self.log.info("Your turn, enabling buttons")
            self.enable_buttons_regular_turn(newly_played, msg)

    # UI settings
    def update_labels_new_turn(self, played_card: str, msg: dict[str, Any]):
        self.set_label_next(msg)
        self.turn_state.is_reversed = msg["dir"]
        self.direction_l.config(image=self.revdir if self.turn_state.is_reversed else self.fordir)
        self.direction_l["image"] = self.revdir if self.turn_state.is_reversed else self.fordir
        if "plustwo" in played_card and "taken" not in msg:
            if self.game_state.modes.stack:
                self.configure_stack_label(self.turn_state.stack_counter)
            self.taken_label.config(text="")
        elif "taken" in msg:
            self.configure_stack_label(0)
            self.taken_label.config(text="Other player took cards!")
        else:
            self.taken_label.config(text="")

    # UI settings
    def enable_buttons_regular_turn(self, card: str, msg: dict[str, Any]):
        self.name_lbl.config(bg="green")
        self.childframes[self.game_state.identity].config(bg=TURN_COLOR)
        if "plusfour" in card and "taken" not in msg and "wild" in msg:
            # Show "challenge +4" button
            self.handle_wild_button(validity=msg["wild"])
        # No moves possible, or move possible but need to take cards
        if not self.turn_state.possible_move or \
            (self.turn_state.card_counter == 2 or
                self.turn_state.card_counter == 4):
            self.new_card.config(state="normal")
        # Say your turn if either mode is normal, or take forever and not plus
        if (self.turn_state.card_counter < 2 and not self.game_state.modes.mult) or \
            (self.game_state.modes.mult and not self.turn_state.card_counter == 4 and not
                self.turn_state.card_counter == 2) or \
                (self.game_state.modes.stack and self.turn_state.can_stack and "two" in card):
            self.turn_need_taking.config(text="", bg=TURN_COLOR)
            for i in self.hand_btns:
                self.hand_btns[i].config(state="normal")
            if self.game_state.modes.stack and self.turn_state.can_stack and "two" in card \
                    and "taken" not in msg and self.turn_state.stack_counter > 0:
                for i in self.hand_btns:
                    if "two" not in self.hand_btns[i]["text"]:
                        self.hand_btns[i].config(state="disabled")
        else:
            self.turn_need_taking.config(text="Take cards!", bg="orange")

    def process_winning(self, points: int, table_of_points: str) -> bool:
        self.show_information(
            "Win",
            f"You won {points} points!\n\n Total this session: \n" +
            table_of_points,
            default=True)
        ans = self.ask_yes_no("New", "Would you like to continue with a new game?")
        if ans == 1:
            modes_response = self.pick_option(
                "Modes",
                "Input the modes (without spaces) that you'd like to use this game"
                " (or press enter for a normal game):\n"
                "1. 7/0\n"
                "2. Stack +2\n"
                "3. Take many cards at once", options=[])
            modes = Modes.from_string(modes_response)
            init = {"stage": Stage.INIT, "modes": modes.to_json()}
            init["padding"] = "a" * (685 - len(json.dumps(init)))
            self.sock.send(json.dumps(init).encode("utf-8"))
        else:
            # Don't want the new game
            bye: dict[str, Any] = {"stage": Stage.BYE}
            bye["padding"] = "a" * (685 - len(json.dumps(bye)))
            self.sock.send(json.dumps(bye).encode("utf-8"))
            self.log.info("No new game, sending a BYE message")
            # self.send_bye_and_exit()
            self.quit_game = True
        return ans == 1

    # UI settings
    def ask_yes_no(self, title: str, question: str) -> int:
        return messagebox.askyesno(title, question)

    # UI settings
    def enable_taking_for_challenge(self, reason: str):
        self.new_card.config(state="normal")
        if reason == 1:
            self.turn_state.update_card_counter(2)
            self.show_information(
                "UNO not said!",
                "You forgot to click UNO, so take 2 cards!",
                default=True
            )
            self.turn_need_taking.config(text="Take 2 cards!", bg="orange")
        else:
            self.turn_state.update_card_counter(4)
            self.show_information(
                "Illegal +4!",
                "You can't put +4 when you have other cards, so take 4!",
                default=True
            )
            self.turn_need_taking.config(text="Take 4 cards!", bg="orange")
        self.name_lbl.config(bg="orange")

    # UI settings
    def show_information(self, title: str, information: str, default: bool):
        if default:
            messagebox.showinfo(title, information)
        else:
            InfoPop(self, title, information)

    # UI settings
    def enable_taking_for_final_plus(self, message: dict[str, Any]):
        self.turn_need_taking.config(text="Take cards!", bg="orange")
        self.name_lbl.config(bg="green")
        self.childframes[self.game_state.identity].config(bg=TURN_COLOR)
        self.new_card.config(state="normal")
        if self.game_state.modes.stack and "counter" in message:
            self.configure_stack_label(self.turn_state.stack_counter)

    # UI settings
    def show_temp_banner(self, text: str, ttl: int):
        temp_banner = Label(text=text, bg="blue", fg="white", width=40, height=1)
        temp_banner.place(x=0.4 * self.screen_width, y=0.6 * self.screen_height + 1)
        self.master.after(ttl, temp_banner.destroy)

    # UI settings
    def inform_about_sevenzero(self, message: dict[str, Any], number: str):
        self.update_btns(message["hand"], message["from"])
        self.show_temp_banner("You got cards from " + message["from"], 10000)
        self.show_information(
            f"A {number} was played",
            f"{number} was played.\n You got cards from\n {message['from']}",
            default=False
        )

    # UI settings
    def update_other_nums_of_cards(self, message: dict[str, Any]):
        self.log.info("Updating the number of remaining cards for others")
        for person, label in self.other_cards_lbls.items():
            card_word = "cards" if not message["other_left"][person] == 1 else "card"
            label.config(text=f"{message['other_left'][person]} {card_word}")
            o_cards = self.other_cards_imgs[person]
            for car in o_cards:
                car.destroy()

            self.put_other_cards(person, message["other_left"][person])

    # UI settings
    # Another player either took a card, or placed a seven-zero, mostly
    def process_design_update(self, message: dict[str, Any]):
        self.log.info("A player has taken or placed a card")
        who_updated = message["from"]
        card_word = "cards" if not message["num_cards"] == 1 else "card"
        self.other_cards_lbls[who_updated].config(text=f"{message['num_cards']} {card_word}")
        o_cards = self.other_cards_imgs[who_updated]
        for car in o_cards:
            car.destroy()
        self.put_other_cards(who_updated, message["num_cards"])

        if message["type"] == 0:
            self.log.info("A new card was placed, updating")
            self.set_last_played(message)

    def set_last_played(self, msg: dict[str, Any]):
        proper_last_played = self.turn_state.update_last_played(msg)
        self.update_last_played_img(proper_last_played)

    # UI settings
    def update_last_played_img(self, card_name: str):
        if "four" in card_name or "bla" in card_name:
            img = ImageTk.PhotoImage(self.game_state.deck.get_special(card_name))
        else:
            img = ImageTk.PhotoImage(self.game_state.deck.get_card(card_name).card_pic)
        self.last.config(image=img, text=card_name)
        self.last["image"] = img
        self.last.__setattr__("image", img)

    # Put received message in queue for async processing
    def receive(self):
        while not self.quit_game:
            self.log.info("Waiting for a new message")
            try:
                json_msg, _ = self.sock.recvfrom(700)
                data = json_msg.decode("utf-8")
                if len(data) < 700 and len(data) > 0:
                    self.log.warning(
                        f"The message is short: {json_msg}, length: {len(data)}"
                    )
                message = json.loads(data)
                message.pop("padding")
            except JSONDecodeError as er:
                if "Expecting value" in str(er):
                    self.quit_game = True
                    self.log.info("Someone else's socket has been closed")
                    break
                elif "Unterminated string" in str(er):
                    self.log.error(
                        f"Message too long: {data}, length: {len(data)}. "
                        "If not, check your internet connection"
                    )
                    self.log.warning("Trying to recover")
                    message = recover(data)
                elif "Extra data" in str(er):
                    self.log.error(f"Got a message and some extra bits? {data}")
                    self.log.warning("Trying to recover")
                    message = recover(data)
                else:
                    self.log.error(er)
                    self.quit_game = True
                    raise
                # break
            except OSError as o:
                if o.errno == 9:
                    self.log.info("Tried to receive a message, but the socket has closed")
                    break
                else:
                    self.log.error(o)
                    self.quit_game = True
            self.q.put(message)
        self.log.info("Stopping listening for messages")

    def send_design_update(self, type: int, num: int, *args):
        # todo what are args
        # 1 = taken, 0 = placed
        data = {
            "stage": Stage.DESIGNUPD,
            "type": type,
            "num_cards": num,
            "from": self.game_state.identity
        }
        if type == 0:
            data["played"] = args[0]
        data["padding"] = "a" * (685 - len(json.dumps(data)))
        self.sock.send(json.dumps(data).encode("utf-8"))
        self.log.info("Design update sent")

    # Disable all buttons when sending information and when it's not your turn anymore
    def send_info(self, data_to_send: dict[str, Any]):
        data_to_send["padding"] = "a" * (685 - len(json.dumps(data_to_send)))
        self.sock.send(json.dumps(data_to_send).encode("utf-8"))
        self.turn_state.set_uno(False)
        self.turn_state.reset_card_counter()

        self.disable_buttons(data_to_send)
        self.log.info("Not your turn anymore")

    # UI settings
    def disable_buttons(self, sent_message: dict[str, Any]):
        self.new_card.config(state="disabled")
        self.uno_but["bg"] = "light sky blue"
        self.handle_challenge_button(player=None, destroy=True)
        self.handle_wild_button(destroy=True)
        go_or_debug = sent_message["stage"] == Stage.GO or sent_message["stage"] == Stage.DEBUG
        if go_or_debug:
            self.update_next_lbl(sent_message)

        if sent_message["stage"] == Stage.ZEROCARDS:
            self.turn_need_taking.config(text="Getting results!", bg=BACKGROUND_COLOR, fg="blue")
        else:
            self.turn_need_taking.config(text="", bg=BACKGROUND_COLOR)

        for i in self.hand_btns:
            self.hand_btns[i].config(state="disabled")
        self.name_lbl.config(bg="red", fg="white")
        self.childframes[self.game_state.identity].config(bg=BACKGROUND_COLOR)
        self.taken_label.config(text="")

    # Notify opponent that they forgot to say UNO; when clicking button
    def challenge_uno(self):
        data = {"stage": Stage.CHALLENGE, "why": 1}
        if self.game_state.modes.stack and self.turn_state.stack_counter > 0:
            data["counter"] = self.turn_state.stack_counter
        self.send_info(data)
        self.handle_challenge_button(player=None, destroy=True)

    # UI settings
    def handle_challenge_button(self, player: Optional[bool], destroy: bool = False):
        if destroy:
            if self.challenge:
                self.challenge.destroy()
        else:
            self.challenge = but(
                text="UNO not said!", bg="red", fg="white",
                width=150, height=30, command=self.challenge_uno,
                border=0)
            if player:
                self.challenge.place(
                    x=0.24 * self.screen_width,
                    y=0.49 * self.screen_height)
        self.update_idletasks()

    def challenge_plus(self, is_valid: bool):
        data = {"stage": Stage.CHALLENGE, "why": 4}
        # If true that can't put +4, so it was illegal, send it
        if not is_valid:
            self.send_info(data)
        else:
            self.turn_state.update_card_counter(6)
            data = {"stage": Stage.SHOWCHALLENGE, "from": self.game_state.identity}
            data["padding"] = "a" * (685 - len(json.dumps(data)))
            self.sock.send(json.dumps(data).encode("utf-8"))
            messagebox.showinfo("Legal move", "The player was honest, so take 6 cards!")
        self.handle_wild_button(destroy=True)

    # UI settings
    def handle_wild_button(self, validity: bool = False, destroy: bool = False):
        if destroy:
            if self.valid_wild:
                self.valid_wild.destroy()
        else:
            self.valid_wild = but(
                text="Illegal +4?", bg="HotPink", fg="black",
                width=150, height=30, borderless=1, border=0,
                command=lambda valid=validity: self.challenge_plus(valid))
            self.valid_wild.place(
                x=0.24 * self.screen_width,
                y=0.55 * self.screen_height)
        self.update_idletasks()

    # If for some reason the turn didn't change, this sends current info to server who prints it
    # out and changes turns
    def send_debug(self):
        self.log.warning("Skip turn was clicked - skipping")
        # todo get data information from the turn state as a method
        data = {
            "stage": Stage.DEBUG,
            "played": self.turn_state.last_played,
            "pile": self.turn_state.pile,
            "hand": self.turn_state.get_hand_card_names(),
            "num_left": self.turn_state.num_cards_left,
            "color": self.turn_state.last_played,
            "taken": True
        }
        self.send_info(data)
        # Reset any effects of the last played card
        self.turn_state.update_stack_counter(0)
        self.configure_stack_label(0)

    # Send all the final information with 0 cards left to end/finalise the game
    def send_final(self, data_to_send: dict[str, Any]):
        print("END")
        data_to_send["stage"] = Stage.ZEROCARDS
        self.turn_state.set_uno(False)
        self.turn_state.reset_card_counter()
        data_to_send["padding"] = "a" * (685 - len(json.dumps(data_to_send)))
        self.sock.send(json.dumps(data_to_send).encode("utf-8"))

        self.disable_buttons(data_to_send)
        self.log.info("Not your turn anymore")

    # UI settings
    def update_btns(self, new_hand: list[str], player: str):
        old_hand_size, new_hand_size = self.turn_state.replace_cards_after_swap(new_hand, player)
        self.sevenzero_update_buttons(player, old_hand_size, new_hand_size)

    # UI settings
    def sevenzero_update_buttons(self, player: str, old_hand_size: int, new_hand_size: int):
        self.setup_hand()
        for j in self.hand_btns:
            self.hand_btns[j].config(state="disabled")

        card_word = "card" if old_hand_size == 1 else "cards"
        self.other_cards_lbls[player].config(text=f"{old_hand_size} {card_word}")
        self.cards_left.config(text=f"{new_hand_size}")

    # UI settings
    def set_label_next(self, msg: dict[str, Any]):
        current_player = self.game_state.identity if msg["player"] else msg["curr"]

        for player, label in self.other_names_lbls.items():
            label.config(
                bg="green" if player == current_player else "red",
                fg="white"
            )
            self.childframes[player].config(
                bg=TURN_COLOR if player == current_player else BACKGROUND_COLOR)

    # UI settings
    def update_next_lbl(self, sent_message: dict[str, Any]):
        skip_player: bool = "stop" in sent_message["played"] and "taken" not in sent_message
        difference = 2 if skip_player else 1
        # Take all players and move them up by 1/2 when turn finished
        if not self.turn_state.is_reversed:
            next_index = (self.game_state.index + difference) % len(self.game_state.peeps)
        else:
            next_index = (self.game_state.index - difference) % len(self.game_state.peeps)
        next_player = self.game_state.peeps[next_index]
        if next_player in self.other_names_lbls.keys():
            self.other_names_lbls[next_player].config(bg="green")
            self.childframes[next_player].config(bg=TURN_COLOR)

    # UI settings
    def check_periodically(self):
        self.incoming()
        if not self.quit_game:
            self.after(100, self.check_periodically)

    # UI settings
    def start_new(self, message: dict[str, Any]):

        print("Destroying old game...")
        self.master.destroy()

        root = Tk()
        root.configure(bg="white")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry("{}x{}".format(screen_width, screen_height))
        utils.title_window(root, message["whoami"], message["peeps"])
        root.protocol("WM_DELETE_WINDOW", self.send_bye_and_exit)
        new = Game(root, self.q, message, self.sock, self.game_state.all_points, self.log)
        new.start_config(message)
        new.check_periodically()
        new.mainloop()

    def start_config(self, message: dict[str, Any]):
        self.turn_state.configure_counters_uno_on_start(message["played"], message["player"])
        self.config_start_buttons(message)

    # UI settings
    def config_start_buttons(self, message: dict[str, Any]):
        not_current = not message["player"]
        played_plus = "plus" in message["played"]
        stack_possible = self.game_state.modes.stack and self.turn_state.can_stack
        no_stack = not stack_possible
        if not_current:
            self.new_card.config(state="disabled")
            for i in self.hand_btns:
                self.hand_btns[i].config(state="disabled")
        elif played_plus and no_stack:
            for i in self.hand_btns:
                self.hand_btns[i].config(state="disabled")
        elif played_plus and stack_possible:
            for i in self.hand_btns:
                if "two" not in self.hand_btns[i]["text"]:
                    self.hand_btns[i].config(state="disabled")
        elif self.turn_state.possible_move:
            self.new_card.config(state="disabled")

    # UI settings
    def set_anim(self):
        self.animated = not self.animated

    def send_bye_and_exit(self):
        try:
            bye: dict[str, Any] = {"stage": Stage.BYE}
            bye["padding"] = "a" * (685 - len(json.dumps(bye)))
            self.sock.send(json.dumps(bye).encode("utf-8"))
            self.sock.close()
        except OSError:
            pass
        self.quit_game = True

        self.log.info("I am closing")
        self.close_window()

    # UI settings
    def close_window(self):
        try:
            self.master.destroy()
        except TclError:
            self.log.warning("The window seems to have been destroyed already")
            pass
        self.log.info("Bye")


# ######################################## SHOW FUNCTIONS #######################################
# UI settings all below
def show_rules():
    print("RULES")
    answer = messagebox.askyesno(
        "Rules",
        "No stacking, take one card only. You can click on cards when it's your turn. Press the"
        " UNO button BEFORE making the move, not after - otherwise you'll have to take 2 cards."
        " The \"Skip turn\" button is used for bug reporting and to change your turn to someone "
        "else.\n Would you like to visit Wiki for official rules?")
    if answer:
        webbrowser.open("https://www.ultraboardgames.com/uno/game-rules.php")


def show_mode(mode: str):
    if mode == Modes.SEVENZERO_STRING:
        messagebox.showinfo(
            "7/0",
            "When a player puts a 7, they have to choose someone (not themselves) to swap their "
            "cards with forever (or until another 7/0 is played).\nWhen a player puts a 0, all "
            "cards are moved to the next player in the direction of the game (that is, in "
            "not-reversed mode 0's cards go to 1, 1 to 2, 2 to 0)"
        )
    elif mode == Modes.STACK_STRING:
        messagebox.showinfo(
            "Stack +2",
            "If you're given a plus card and you have another, you can stack yours on top of the "
            "given card, increasing the number of cards needed to be taken for the next player"
        )

    elif mode == Modes.MULT_STRING:
        messagebox.showinfo(
            "Take many cards",
            "If you don't have a playable card, you have to take cards from the pile until a"
            " suitable one appears, rather than just take one and skip turn"
        )
