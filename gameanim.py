import copy
import json
import math
import utils
import queue
import webbrowser

from buttons import HandCardButton, PileButton, TakeCardButton, ColorfulButton
from tkinter import Menu, messagebox, Tk, TclError
from frames_and_labels import Frame, Label
from tkinter import simpledialog
from PIL import ImageTk, Image
from popup import InfoPop
from picker import Picker
from logging import Logger
from typing import Optional, Any

from game_classes import Stage, Modes, GameState
from turn_state import TurnState
from card import Card, CardType
from socket import socket

from deck import Deck
from json import JSONDecodeError
from message_utils import recover


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
        logger: Logger,
        localhost: bool = False
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
        self.master: Tk = master
        self.master.protocol("WM_DELETE_WINDOW", self.send_bye_and_exit)
        self.q = queue
        self.quit_game = False
        other_players: list[str] = copy.deepcopy(self.game_state.peeps)
        other_players.pop(self.game_state.index)
        self.log.info(f"I am {self.game_state.identity}, playing against {other_players}")

        self.turn_state = TurnState(
            stack_counter=0 if not Card(msg["played"]).type_is(CardType.PLUSTWO) else 2,
            all_nums_of_cards=msg["other_left"],
            card_counter=1 if not self.game_state.modes.mult else 500,
            is_reversed=msg["dir"],
            pile=msg["pile"],
            uno=False,
            last_played=msg["played"],
            game_state=self.game_state,
            stage=msg["stage"]
        )

        self.init_ui_elements(msg, localhost)

    # UI settings
    def init_ui_elements(self, msg: dict[str, Any], localhost: bool = False):
        icon = ImageTk.PhotoImage(Image.open(icon_img_location))
        self.revdir = ImageTk.PhotoImage(
            Image.open(direction_rev_img_location).resize((95, 95), Image.LANCZOS)
        )
        self.fordir = ImageTk.PhotoImage(
            Image.open(direction_for_img_location).resize((95, 95), Image.LANCZOS)
        )

        self.master.tk.call('wm', 'iconphoto', self.master, icon)

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight() - 100
        self.animated = False
        self.childframes = {}
        self.other_cards_lbls: dict[str, Label] = {}
        self.other_names_lbls: dict[str, Label] = {}
        self.other_cards_imgs: dict[str, list[Label]] = {}

        self.central_frame = self.set_up_central_frame(msg)
        self.set_up_card_frame(msg)

        frames = self.set_up_other_frames()

        self.set_up_other_players(frames)

        self.setup_menu()

        if msg["player"] == self.game_state.identity:
            self.name_lbl.config(bg="green")
            self.childframes[self.game_state.identity].set_color(TURN_COLOR)
        else:
            self.name_lbl.config(bg="red")
            self.childframes[self.game_state.identity].set_color(BACKGROUND_COLOR)
        self.set_label_next(msg)
        if not localhost:
            self.show_enabled_modes()

    def set_up_central_frame(self, msg: dict[str, Any]) -> Frame:
        self.challenge = ColorfulButton()
        self.valid_wild = ColorfulButton()
        frame_width = 0.6 * self.screen_width
        frame_height = 0.3 * self.screen_height
        frame = Frame(
            parent=self.master,
            width=frame_width,
            height=frame_height,
            bg=BACKGROUND_COLOR,
        )
        frame.place(x=0.2 * self.screen_width, y=0.3 * self.screen_height)

        self.stack_label = Label(
            frame,
            text=f"{STACK_LABEL_TEXT}{self.turn_state.stack_counter}",
            bg="PeachPuff",
            width=10,
            height=3
        )

        self.direction_l = Label(
            frame,
            image=self.revdir if self.turn_state.is_reversed else self.fordir,
            width=93,
            height=93,
        )

        if self.game_state.modes.stack:
            self.stack_label.place(x=0.8 * frame_width, y=2)
            self.direction_l.place(x=0.8 * frame_width, y=82)
        else:
            self.direction_l.place(x=0.8 * frame_width, y=42)

        self.taken_label = Label(
            frame,
            fg="blue",
            bg=BACKGROUND_COLOR,
            width=28,
            height=1
        )
        self.taken_label.place(x=1, y=1)

        self.uno_but = ColorfulButton(
            parent_frame=frame,
            text="UNO",
            bg="light sky blue",
            width=100,
            height=80,
            command=self.toggle_uno)
        self.uno_but.place(x=0.1 * frame_width, y=0.16 * frame_height)
        self.setup_pile(msg["played"], frame)

        return frame

    def set_up_card_frame(self, msg: dict[str, Any]):
        frame_width = self.screen_width
        frame_height = 0.4 * self.screen_height
        self.card_frame = Frame(
            parent=self.master,
            width=frame_width,
            height=frame_height,
            bg=BACKGROUND_COLOR,
        )
        self.card_frame.place(x=0, y=0.6 * self.screen_height)
        self.childframes[self.game_state.identity] = self.card_frame

        self.name_lbl = Label(
            parent=self.card_frame,
            text="You",
            fg="white",
            bg="pale green",
            width=18,
            height=1)
        self.name_lbl.place(x=1, y=1)

        self.cards_left = Label(self.card_frame, text="7", bg="pale green", width=2, height=1)
        self.cards_left.place(x=0.15 * frame_width + 1, y=1)

        # Button for debugging
        debug = ColorfulButton(
            parent_frame=self.card_frame,
            text="Skip turn", fg="red", bg="white",
            width=100,
            height=30,
            command=self.send_debug)
        debug.place(x=frame_width - 120, y=frame_height - 55)
        self.sort_btns = ColorfulButton(
            parent_frame=self.card_frame,
            text="Sort cards",
            width=200,
            height=40,
            command=self.sort_hand_buttons)
        self.sort_btns.place(x=int(frame_width / 2) - 100, y=0.8 * frame_height)

        self.hand_btns: dict[int, HandCardButton] = {}
        self.setup_hand()

        if msg["player"] == self.game_state.identity:
            if Card(msg["played"]).type_is(CardType.PLUSTWO) and \
                    (not self.turn_state.can_stack or not self.game_state.modes.stack):
                self.turn_need_taking = Label(
                    parent=self.card_frame,
                    text="Take cards",
                    bg="orange",
                    width=12,
                    height=1
                )
            else:
                self.turn_need_taking = Label(
                    parent=self.card_frame, bg=TURN_COLOR, width=12, height=1
                )
        else:
            self.turn_need_taking = Label(
                parent=self.card_frame,
                bg=BACKGROUND_COLOR,
                width=12,
                height=1
            )
        self.turn_need_taking.place(x=0.18 * frame_width, y=1)

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
    def setup_pile(self, last_played_card: str, parent_frame: Frame):
        # Button to take a card (so a pile)
        frame_width = parent_frame["width"]
        frame_height = parent_frame["height"]

        self.new_card = TakeCardButton(
            image=self.game_state.deck.backofcard, method=self.take_card, parent_frame=parent_frame)
        self.new_card.place(x=0.6 * frame_width, y=0.07 * frame_height)
        # Last is a disabled button with the last played card (from the message) shown
        self.last = PileButton(Card(last_played_card), parent_frame)
        self.last.place(x=0.4 * frame_width, y=0.07 * frame_height)

    # UI settings
    def setup_hand(self):
        # Setup a fresh hand, deleting anything that was there before (either on new game or card
        # swap)
        if len(self.hand_btns) > 0:
            for i in self.hand_btns:
                self.hand_btns[i].destroy()
        self.hand_btns: dict[int, HandCardButton] = {}
        dealt_cards = self.turn_state.hand_cards
        n = len(dealt_cards)
        for i in range(n):
            # Create a button for each card in dealt cards
            b = HandCardButton(
                parent_frame=self.card_frame,
                index=i,
                card=dealt_cards[i],
                method=self.place_card,
                bg=BACKGROUND_COLOR,
            )
            self.hand_btns[i] = b
            coords = self.get_card_placement(n, i)
            b.place(x=coords[1], y=coords[2])

    # UI settings
    def set_up_other_players(self, frames: list[Frame]):
        for i in range(len(frames)):
            frame = frames[i]
            person_index = (self.game_state.index + i + 1) % self.game_state.num_players
            person = self.game_state.peeps[person_index]
            self.childframes[person] = frame
            self.set_up_opponent_info(person, frame)

    def set_up_other_frames(self) -> list[Frame]:
        frames = []
        frame_ratio_sizes = {
            0: [0.2, 0.6],
            0.2: [0.6, 0.3],
            0.8: [0.2, 0.6]
        }
        for x_coord, (width, height) in frame_ratio_sizes.items():
            frame = self.create_opponent_frame(x_coord, width, height)
            frames.append(frame)
        if self.game_state.num_players == 2:
            # Only return the top center frame
            return [frames[1]]
        # Return as many frames as there are other players
        return frames[0:self.game_state.num_players - 1]

    def create_opponent_frame(self, x_coord: float, width: float, height: float) -> Frame:
        frame = Frame(
            parent=self.master,
            width=width * self.screen_width,
            height=height * self.screen_height,
            bg=BACKGROUND_COLOR,
        )
        frame.place(x=x_coord * self.screen_width, y=0)
        return frame

    def set_up_opponent_info(self, person: str, frame: Frame):
        name_lbl = Label(
            parent=frame,
            text=person,
            fg="white",
            bg="pale green",
            width=18,
            height=1,
        )
        name_lbl.place(x=1, y=1)
        self.other_names_lbls[person] = name_lbl
        other_card_lbl = Label(parent=frame, text="7 cards", bg="pale green", width=8, height=1)
        self.other_cards_lbls[person] = other_card_lbl
        other_card_lbl.place(x=1, y=31)
        self.put_other_cards(person, self.turn_state.all_nums_of_cards[person])

    # UI settings
    def put_other_cards(self, who: str, num_cards: int):
        frame = self.childframes[who]
        self.other_cards_imgs[who] = []
        frame_width = frame["width"]
        frame_height = frame["height"]
        photo = ImageTk.PhotoImage(self.game_state.deck.smallback)
        # Cap the number of visible cards at 18
        size = num_cards if num_cards <= 18 else 18
        for step in range(size):
            cardback = Label(parent=frame, image=photo, width=80, height=125)
            self.other_cards_imgs[who].append(cardback)

            if frame_width > frame_height:
                # Place horizontally
                cardback.place(x=0.16 * frame_width + step * 30, y=40)
            else:
                cardback.place(x=0.5 * frame_width, y=35 + 15 * step)

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
    def get_card_placement(self, num_cards: int, i: int) -> list[float]:
        # Returns coordinates of a button  given specific parameters
        # Like the width and length of cards, as well as how apart they should be
        frame_height = self.card_frame.height
        frame_width = self.card_frame.width
        result = []
        if num_cards == 1:
            num_cards = 2
        if num_cards <= 20:
            overlap = math.floor(
                (117 - ((117 * num_cards) - 0.95 * frame_width) / (num_cards - 1)))
        else:
            overlap = math.floor((117 - ((117 * 20) - 0.95 * frame_width) / (20 - 1)))
        result.append(overlap)
        result.append(25 + overlap * (i % 20) + 15 * (math.floor(i / 20)))
        result.append(0.125 * frame_height + 40 * (math.floor(i / 20)))
        return result

    # #################################### EVENTS ##################################
    # UI settings (if not UI, just call complete_placement)
    def place_card(self, ind: int, binst: HandCardButton):
        card = self.turn_state.hand_cards[ind].name
        old_card = self.turn_state.last_played
        # Same color (0:3), same symbol (3:), black
        same_color = card[0:3] == old_card[0:3]
        same_symbol = card[3:] == old_card[3:]
        is_black = Card(card).type_is(CardType.BLACK)
        if same_color or same_symbol or is_black:
            # You can't have the "Illegal +4" when placing a card, as you never place it, so don't
            # handle it
            self.handle_challenge_button(destroy=True)
            # If animation is turned on, move, else place on pile straight away
            if self.animated:
                dest_x, dest_y = self.last.coords()
                orig_x, orig_y = binst.coords()
                dx = dest_x - orig_x
                dy = dest_y - orig_y
                self.move(orig_x, orig_y, dx, dy, 0, binst, self.last.get_image(), ind)
            else:
                binst.destroy()
                self.complete_placement(card, ind)

    # Set new card on pile, send information, update hand - after animation or straight away
    def complete_placement(self, card: str, ind: int):
        proper_card = Card(card)
        if proper_card.type_is(CardType.REVERSE):
            self.turn_state.is_reversed = not self.turn_state.is_reversed
        # Changes the black card to black with a color to show which one to play next
        if proper_card.type_is(CardType.BLACK):
            new_color = self.pick_option(
                "New color",
                "Which one?",
                ["Red", "Green", "Blue", "Yellow"])
            new_color = new_color.lower()[0:3]
            # Get the colored black cards from the deck for ease of transfer
            if proper_card.is_plus():
                new_color += "plus"
                special_card = new_color + "four"
            else:
                new_color += "black"
                special_card = new_color
        else:  # Not a black card
            special_card = card

        # Remove card from "hand", update label with number
        self.turn_state.hand_cards.pop(ind)
        self.turn_state.all_nums_of_cards[self.game_state.identity] -= 1

        self.update_labels_buttons_card_placed(special_card, ind)

        data_to_send = {
            "played": special_card,
            "pile": self.turn_state.pile,
            "stage": Stage.GO,
            "num_left": self.turn_state.num_cards_left
        }
        if proper_card.type_is(CardType.PLUSFOUR):
            data_to_send["wild"] = self.turn_state.can_put_plusfour
        # If placed plustwo in the mode, send the counter
        elif proper_card.type_is(CardType.PLUSTWO) and self.game_state.modes.stack:
            data_to_send["counter"] = self.turn_state.stack_counter + 2
            self.turn_state.update_stack_counter(0)
        if proper_card.type_is(CardType.SEVEN) and self.game_state.modes.sevenzero and \
                self.turn_state.num_cards_left > 0:
            self.send_design_update(self.turn_state.num_cards_left, card)
            players = [x for x in self.game_state.peeps if not x == self.game_state.identity]
            swap_with = self.pick_option(
                "Swap",
                "Who would you like to swap your cards with?",
                players)
            data_to_send["swapwith"] = swap_with
            data_to_send["hand"] = self.turn_state.get_hand_card_names()

        if proper_card.type_is(CardType.ZERO) and self.game_state.modes.sevenzero and \
                self.turn_state.num_cards_left > 0:
            data_to_send["hand"] = self.turn_state.get_hand_card_names()

        if self.turn_state.uno:
            data_to_send["said_uno"] = True
        # Send all the information either in progress of the game, or to end it
        if self.turn_state.num_cards_left > 0:
            self.send_info(data_to_send)
        else:
            self.send_design_update(0, data_to_send["played"])
            self.send_final(data_to_send)
        self.turn_state.last_played = special_card

        self.update_last_played_img(special_card)

    # UI settings
    def update_labels_buttons_card_placed(self, placed_card: str, ind: int):
        card = Card(placed_card)
        if card.type_is(CardType.REVERSE):
            self.direction_l.set_image(self.revdir if self.turn_state.is_reversed else self.fordir)
        self.hand_btns.pop(ind)
        self.cards_left.config(text=self.turn_state.all_nums_of_cards[self.game_state.identity])
        self.move_buttons()
        if card.type_is(CardType.PLUSTWO) and self.game_state.modes.stack:
            self.configure_stack_label(self.turn_state.stack_counter + 2)

    # UI settings
    def pick_option(self, title: str, question: str, options: Optional[list[str]]) -> str:
        if options:
            picker = Picker(self.master, title, question, options)
            return picker.result
        else:
            response = simpledialog.askstring(title, question)
            return response if response else "0"

    def take_card(self):
        # Take new card
        new = Card(self.turn_state.pile.pop(0))
        # Remove the "uno not placed" button as was ignored
        self.handle_challenge_button(destroy=True)
        self.handle_wild_button(destroy=True)
        # Decrease number of cards that need to be taken
        self.turn_state.card_counter -= 1

        if self.turn_state.stack_counter > 0 and \
                Card(self.turn_state.last_played).type_is(CardType.PLUSTWO):
            # Card.card_is(self.turn_state.last_played, CardType.PLUSFOUR)
            self.turn_state.stack_counter -= 1

        if not (self.turn_state.stage == Stage.ZEROCARDS):
            self.send_design_update(self.turn_state.num_cards_left + 1)
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
        if self.turn_state.can_send_points_after_taking():
            data_to_send = {"stage": Stage.CALC, "points": self.turn_state.calculate_points()}
            self.send_info(data_to_send)

        # Send information about taken cards if can't go or had to take +2/4 due to challenge or
        # card
        if self.turn_state.can_send_card_taken_update():
            data_to_send = {
                "played": self.turn_state.last_played,
                "pile": self.turn_state.pile,
                "stage": Stage.GO,
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
        if self.turn_state.stack_counter >= 0 and \
                Card(self.turn_state.last_played).type_is(CardType.PLUSTWO):
            # or Card.card_is(self.turn_state.last_played, CardType.PLUSFOUR)
            self.configure_stack_label(self.turn_state.stack_counter)
        self.cards_left.config(text=self.turn_state.all_nums_of_cards[self.game_state.identity])

        b = HandCardButton(
            parent_frame=self.card_frame,
            index=index,
            card=new_card,
            method=self.place_card,
            bg=BACKGROUND_COLOR,
            enabled=False,
        )
        self.hand_btns[index] = b
        if move_is_possible and \
            (self.turn_state.card_counter == 0 or
                (self.game_state.modes.mult and self.turn_state.card_counter > 6)) and \
                self.turn_state.stack_counter == 0:
            self.new_card.set_enabled(False)
            b.set_enabled(True)
        self.move_buttons()

    def move_buttons(self):
        ctr = 0
        for i in self.hand_btns.keys():
            # Move all buttons
            b = self.hand_btns[i]
            coords = self.get_card_placement(len(self.hand_btns), ctr)
            card = Card(b["text"])
            enabled = b["state"] == "normal" or b["state"] == "active"
            b.destroy()
            # Recreate the button for a new reference to the object
            b = HandCardButton(
                parent_frame=self.card_frame,
                index=i,
                card=card,
                method=self.place_card,
                bg=BACKGROUND_COLOR,
                enabled=enabled,
            )
            b.place(x=coords[1], y=coords[2])
            self.hand_btns[i] = b
            ctr += 1

    def sort_hand_buttons(self) -> None:
        # Sort hand cards and retrieve the sorted indices
        self.log.debug(self.turn_state.hand_cards)

        card_indices = self.turn_state.sort_cards()
        self.log.debug(self.turn_state.hand_cards)
        old_buttons = copy.copy(self.hand_btns)
        # Get buttons from the sorted indices, but move indices to start from 0 again for an
        # increasing list
        self.hand_btns = {i: old_buttons[k] for (i, k) in enumerate(card_indices)}

        self.move_buttons()

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
                            2 if Card(msg["played"]).type_is(CardType.PLUSTWO) else 4
                        )
                        if self.game_state.modes.stack and "counter" in msg:
                            self.turn_state.update_stack_counter(msg["counter"])
                            self.configure_stack_label(self.turn_state.stack_counter)

                    else:
                        # No cards need to be taken, send current points
                        points = {"stage": Stage.CALC, "points": self.turn_state.calculate_points()}
                        self.send_message(points)

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

                    if "end" not in msg:
                        self.send_message(hand)

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
        if Card(newly_played).type_is(CardType.PLUSTWO) and "taken" not in msg:
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
            if Card(newly_played).type_is(CardType.ZERO) and "taken" not in msg and \
                    self.game_state.modes.sevenzero:
                direction = -1 if self.turn_state.is_reversed else 1
                player_index = self.game_state.peeps.index(from_player)
                from_player = self.game_state.peeps[
                    (player_index + direction) % self.game_state.num_players
                ]
            if from_player != self.game_state.identity:
                self.show_information(
                    "UNO",
                    f"{from_player}\n has only 1 card left!",
                    default=False
                )

        self.turn_state.all_nums_of_cards = msg["other_left"]

        # Enable buttons for cards if your turn; make UNO show if necessary
        if msg["player"] == self.game_state.identity:
            self.log.info("Your turn, enabling buttons")
            self.enable_buttons_regular_turn(newly_played, msg)

    # UI settings
    def update_labels_new_turn(self, played_card: str, msg: dict[str, Any]):
        self.set_label_next(msg)
        self.turn_state.is_reversed = msg["dir"]
        self.direction_l.set_image(self.revdir if self.turn_state.is_reversed else self.fordir)
        if Card(played_card).type_is(CardType.PLUSTWO) and "taken" not in msg:
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
        self.childframes[self.game_state.identity].set_color(TURN_COLOR)
        if Card(card).type_is(CardType.PLUSFOUR) and \
                "taken" not in msg and "wild" in msg:
            # Show "challenge +4" button
            self.handle_wild_button(validity=msg["wild"])
        # No moves possible, or move possible but need to take cards
        if not self.turn_state.possible_move or \
            (self.turn_state.card_counter == 2 or
                self.turn_state.card_counter == 4):
            self.new_card.set_enabled(True)
        # Say your turn if either mode is normal, or take forever and not plus
        if (self.turn_state.card_counter < 2 and not self.game_state.modes.mult) or \
            (self.game_state.modes.mult and not self.turn_state.card_counter == 4 and not
                self.turn_state.card_counter == 2) or \
                (self.game_state.modes.stack and self.turn_state.can_stack and
                    Card(card).type_is(CardType.PLUSTWO)):
            self.turn_need_taking.config(text="", bg=TURN_COLOR)
            for i in self.hand_btns:
                self.hand_btns[i].set_enabled(True)
            if self.game_state.modes.stack and self.turn_state.can_stack and \
                    Card(card).type_is(CardType.PLUSTWO) and "taken" not in msg and \
                    self.turn_state.stack_counter > 0:
                for i in self.hand_btns:
                    # Go through cards on buttons and enable only +2s
                    if not self.hand_btns[i].card.type_is(CardType.PLUSTWO):
                        self.hand_btns[i].set_enabled(False)
        else:
            self.turn_need_taking.config(text="Take cards!", bg="orange")

    def process_winning(self, points: int, table_of_points: str) -> bool:
        self.show_information(
            "Win",
            f"You won {points} points!\n\n Total this session: \n" +
            table_of_points,
            default=True)
        ans = self.ask_yes_no("New", "Would you like to continue\n with a new game?")
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
            self.send_message(init)
        else:
            # Don't want the new game
            bye: dict[str, Any] = {"stage": Stage.BYE}
            self.send_message(bye)
            self.log.info("No new game, sending a BYE message")
            # self.send_bye_and_exit()
            self.quit_game = True
        return ans == 1

    # UI settings
    def ask_yes_no(self, title: str, question: str) -> int:
        return messagebox.askyesno(title, question)

    # UI settings
    def enable_taking_for_challenge(self, reason: str):
        self.new_card.set_enabled(True)
        if reason == 1:
            self.turn_state.update_card_counter(2)
            self.show_information(
                "UNO not said!",
                "You forgot to click UNO, \nso take 2 cards!",
                default=True
            )
            self.turn_need_taking.config(text="Take 2 cards!", bg="orange")
        else:
            self.turn_state.update_card_counter(4)
            self.show_information(
                "Illegal +4!",
                "You can't put +4 when you \nhave other cards, so take 4!",
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
        self.childframes[self.game_state.identity].set_color(TURN_COLOR)
        self.new_card.set_enabled(True)
        if self.game_state.modes.stack and "counter" in message:
            self.configure_stack_label(self.turn_state.stack_counter)

    # UI settings
    def show_temp_banner(self, text: str, ttl: int):
        frame_width = self.card_frame.width
        temp_banner = Label(self.card_frame, text=text, bg="blue", fg="white", width=40, height=1)
        temp_banner.place(x=0.4 * frame_width, y=1)
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

        if message.get("played"):
            self.log.info("A new card was placed, updating")
            self.set_last_played(message)

    def set_last_played(self, msg: dict[str, Any]):
        proper_last_played = self.turn_state.update_last_played(msg)
        self.update_last_played_img(proper_last_played)

    # UI settings
    def update_last_played_img(self, card_name: str):
        proper_card = Card(card_name)
        self.last.update_card(proper_card)

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

    def send_design_update(self, num: int, played_card: str = ""):
        # 1 = taken, 0 = placed
        data = {
            "stage": Stage.DESIGNUPD,
            "num_cards": num,
            "from": self.game_state.identity
        }
        if played_card:
            data["played"] = played_card

        self.send_message(data)
        self.log.info("Design update sent")

    # Disable all buttons when sending information and when it's not your turn anymore
    def send_info(self, data_to_send: dict[str, Any]):
        self.send_message(data_to_send)
        self.turn_state.set_uno(False)
        self.turn_state.reset_card_counter()

        self.disable_buttons(data_to_send)
        self.log.info("Not your turn anymore")

    # UI settings
    def disable_buttons(self, sent_message: dict[str, Any]):
        self.new_card.set_enabled(False)
        self.uno_but["bg"] = "light sky blue"
        self.handle_challenge_button(destroy=True)
        self.handle_wild_button(destroy=True)
        go_or_debug = sent_message["stage"] == Stage.GO or sent_message["stage"] == Stage.DEBUG
        if go_or_debug:
            self.update_next_lbl(sent_message)

        if sent_message["stage"] == Stage.ZEROCARDS:
            self.turn_need_taking.config(text="Getting results!", bg=BACKGROUND_COLOR, fg="blue")
        else:
            self.turn_need_taking.config(text="", bg=BACKGROUND_COLOR)

        for i in self.hand_btns:
            self.hand_btns[i].set_enabled(False)
        self.name_lbl.config(bg="red")
        self.childframes[self.game_state.identity].set_color(BACKGROUND_COLOR)
        self.taken_label.config(text="")

    # Notify opponent that they forgot to say UNO; when clicking button
    def challenge_uno(self):
        data = {"stage": Stage.CHALLENGE, "why": 1}
        if self.game_state.modes.stack and self.turn_state.stack_counter > 0:
            data["counter"] = self.turn_state.stack_counter
        self.send_info(data)
        self.handle_challenge_button(destroy=True)

    # UI settings
    def handle_challenge_button(self, player: Optional[bool] = None, destroy: bool = False):
        if destroy:
            if self.challenge:
                self.challenge.destroy()
        else:
            self.challenge = ColorfulButton(
                parent_frame=self.central_frame,
                text="UNO not said!", bg="red", fg="white",
                width=150, height=30, command=self.challenge_uno)
            if player and player == self.game_state.identity:
                frame_width = self.central_frame["width"]
                frame_height = self.central_frame["height"]
                self.challenge.place(x=0.07 * frame_width, y=0.63 * frame_height)
        self.update_idletasks()

    def challenge_plus(self, is_valid: bool):
        data = {"stage": Stage.CHALLENGE, "why": 4}
        # If true that can't put +4, so it was illegal, send it
        if not is_valid:
            self.send_info(data)
        else:
            self.turn_state.update_card_counter(6)
            data = {"stage": Stage.SHOWCHALLENGE, "from": self.game_state.identity}
            self.send_message(data)
            self.show_information("Legal move", "The player was honest,\nso take 6 cards!", True)
        self.handle_wild_button(destroy=True)

    # UI settings
    def handle_wild_button(self, validity: bool = False, destroy: bool = False):
        if destroy:
            if self.valid_wild:
                self.valid_wild.destroy()
        else:
            self.valid_wild = ColorfulButton(
                parent_frame=self.central_frame,
                text="Illegal +4?", bg="HotPink",
                width=150, height=30,
                command=lambda valid=validity: self.challenge_plus(valid))
            frame_width = self.central_frame["width"]
            frame_height = self.central_frame["height"]
            self.valid_wild.place(x=0.07 * frame_width, y=0.83 * frame_height)
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
            "taken": True
        }
        self.send_info(data)
        # Reset any effects of the last played card
        self.turn_state.update_stack_counter(0)
        self.configure_stack_label(0)

    # Send all the final information with 0 cards left to end/finalise the game
    def send_final(self, data_to_send: dict[str, Any]):
        self.log.info("END")
        data_to_send["stage"] = Stage.ZEROCARDS
        self.turn_state.set_uno(False)
        self.turn_state.reset_card_counter()
        self.send_message(data_to_send)

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
            self.hand_btns[j].set_enabled(False)

        card_word = "card" if old_hand_size == 1 else "cards"
        self.other_cards_lbls[player].config(text=f"{old_hand_size} {card_word}")
        self.cards_left.config(text=f"{new_hand_size}")

    # UI settings
    def set_label_next(self, msg: dict[str, Any]):
        current_player = msg["player"]

        for player, label in self.other_names_lbls.items():
            label.config(bg="green" if player == current_player else "red")
            self.childframes[player].config(
                bg=TURN_COLOR if player == current_player else BACKGROUND_COLOR)

    # UI settings
    def update_next_lbl(self, sent_message: dict[str, Any]):
        skip_player: bool = Card(sent_message["played"]).type_is(CardType.STOP) and \
            "taken" not in sent_message
        difference = 2 if skip_player else 1
        # Take all players and move them up by 1/2 when turn finished
        if not self.turn_state.is_reversed:
            next_index = (self.game_state.index + difference) % self.game_state.num_players
        else:
            next_index = (self.game_state.index - difference) % self.game_state.num_players
        next_player = self.game_state.peeps[next_index]
        if next_player in self.other_names_lbls.keys():
            self.other_names_lbls[next_player].config(bg="green")
            self.childframes[next_player].set_color(TURN_COLOR)

    # UI settings
    def check_periodically(self):
        self.incoming()
        if not self.quit_game:
            self.after(100, self.check_periodically)

    # UI settings
    def start_new(self, message: dict[str, Any]):

        self.log.info("Destroying old game...")
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
        current = message["player"] == self.game_state.identity
        played_plus = Card(message["played"]).is_plus()
        stack_possible = self.game_state.modes.stack and self.turn_state.can_stack
        no_stack = not stack_possible
        if not current:
            self.new_card.set_enabled(False)
            for i in self.hand_btns:
                self.hand_btns[i].set_enabled(False)
        elif played_plus and no_stack:
            for i in self.hand_btns:
                self.hand_btns[i].set_enabled(False)
        elif played_plus and stack_possible:
            for i in self.hand_btns:
                if not self.hand_btns[i].card.type_is(CardType.PLUSTWO):
                    self.hand_btns[i].set_enabled(False)
        elif self.turn_state.possible_move:
            self.new_card.set_enabled(False)

    # UI settings
    def set_anim(self):
        self.animated = not self.animated

    def send_bye_and_exit(self):
        try:
            bye: dict[str, Any] = {"stage": Stage.BYE}
            self.send_message(bye)
            self.sock.close()
        except OSError:
            pass
        self.quit_game = True

        self.log.info("I am closing")
        self.close_window()

    def send_message(self, message: dict[str, Any]):
        message["padding"] = "a" * (685 - len(json.dumps(message)))
        # todo remove for message class
        # with open("gamemsgs.txt", "a") as f:
        #     f.write(f"{list(message.keys())}stage: {message['stage']}")
        #     f.write("\n")
        self.sock.send(json.dumps(message).encode("utf-8"))

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
