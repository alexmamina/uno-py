import copy
import math
from message_processor import Message
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
from typing import Optional

from game_classes import ChallengeReason, Stage, Modes
from card import Card, CardType
from socket import socket

from gameanim import GameLogic


direction_for_img_location = "Images/directionfor.jpg.png"
direction_rev_img_location = "Images/directionrev.jpg.png"
icon_img_location = "Images/unoimg.png"

STACK_LABEL_TEXT = "Stack\n cards to take:\n"

BACKGROUND_COLOR = "#D1FFCC"
TURN_COLOR = "#FDFFD2"


class GameUI(Frame):
    def __init__(
        self,
        master: Tk,
        msg: Message,
        q: queue.Queue,
        sock: socket,
        all_points,
        logger: Logger,
        localhost: bool = False
    ):
        super().__init__(master)
        self.pack()
        self.move_id = "0"
        self.master: Tk = master
        self.game_logic = GameLogic(
            q,
            msg,
            sock,
            all_points,
            logger,
            self,  # GameUI
        )
        self.master.protocol("WM_DELETE_WINDOW", self.game_logic.send_bye_and_exit)

        self.init_ui_elements(msg, localhost)

    def init_ui_elements(self, msg: Message, localhost: bool = False):
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

        if msg.current_player == self.game_logic.game_state.identity:
            self.name_lbl.config(bg="green")
            self.childframes[self.game_logic.game_state.identity].set_color(TURN_COLOR)
        else:
            self.name_lbl.config(bg="red")
            self.childframes[self.game_logic.game_state.identity].set_color(BACKGROUND_COLOR)
        self.set_label_next(msg.current_player)
        if not localhost:
            self.show_enabled_modes()

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
        if self.game_logic.game_state.num_players == 2:
            # Only return the top center frame
            return [frames[1]]
        # Return as many frames as there are other players
        return frames[0:self.game_logic.game_state.num_players - 1]

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
        self.put_other_cards(person, self.game_logic.turn_state.all_nums_of_cards[person])

    def put_other_cards(self, who: str, num_cards: int):
        frame = self.childframes[who]
        self.other_cards_imgs[who] = []
        frame_width = frame["width"]
        frame_height = frame["height"]
        photo = ImageTk.PhotoImage(self.game_logic.game_state.deck.smallback)
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

    def set_up_central_frame(self, msg: Message) -> Frame:
        assert msg.played is not None
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
            text=f"{STACK_LABEL_TEXT}{self.game_logic.turn_state.stack_counter}",
            bg="PeachPuff",
            width=10,
            height=3
        )

        self.direction_l = Label(
            frame,
            image=self.revdir if self.game_logic.turn_state.is_reversed else self.fordir,
            width=93,
            height=93,
        )

        if self.game_logic.game_state.modes.stack:
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
        self.setup_pile(msg.played, frame)

        return frame

    def set_up_card_frame(self, msg: Message):
        assert msg.played is not None
        frame_width = self.screen_width
        frame_height = 0.4 * self.screen_height
        self.card_frame = Frame(
            parent=self.master,
            width=frame_width,
            height=frame_height,
            bg=BACKGROUND_COLOR,
        )
        self.card_frame.place(x=0, y=0.6 * self.screen_height)
        self.childframes[self.game_logic.game_state.identity] = self.card_frame

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
            command=self.game_logic.send_debug)
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

        if msg.current_player == self.game_logic.game_state.identity:
            if msg.played.type_is(CardType.PLUSTWO) and \
                    (not self.game_logic.turn_state.can_stack or
                     not self.game_logic.game_state.modes.stack):
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

    def set_anim(self):
        self.animated = not self.animated

    def show_enabled_modes(self):
        txt_modes = ""
        if self.game_logic.game_state.modes.is_regular():
            txt_modes = "\nRegular"
        else:
            txt_modes = "\n".join(self.game_logic.game_state.modes.enabled_strings())
        # InfoPop(self, "Modes", txt_modes)
        self.show_information("Modes", txt_modes, default=True)

    # Create a menu bar, configure to add to master (which is the root window)
    def setup_menu(self):
        menubar = Menu(self)

        menu = Menu(menubar)
        menu.add_command(label="Rules", command=show_rules)
        menu.add_command(label="Points", command=self.show_points)
        menu.add_command(label="Toggle animation", command=self.set_anim)
        menubar.add_cascade(label="Menu", menu=menu)
        mode = Menu(menubar)
        if self.game_logic.game_state.modes.is_regular():
            mode.add_command(label="Regular enabled")
        else:
            for mode_str in self.game_logic.game_state.modes.enabled_strings():
                mode.add_command(
                    label=f"{mode_str} enabled",
                    command=lambda mode_type=mode_str: show_mode(mode_type)
                )
        menubar.add_cascade(label="Game mode rules", menu=mode)

        self.master["menu"] = menubar

    # Add the pile and last played buttons
    def setup_pile(self, last_played_card: Card, parent_frame: Frame):
        # Button to take a card (so a pile)
        frame_width = parent_frame["width"]
        frame_height = parent_frame["height"]

        self.new_card = TakeCardButton(
            image=self.game_logic.game_state.deck.backofcard,
            method=self.handle_take_card,
            parent_frame=parent_frame
        )
        self.new_card.place(x=0.6 * frame_width, y=0.07 * frame_height)
        # Last is a disabled button with the last played card (from the message) shown
        self.last = PileButton(last_played_card, parent_frame)
        self.last.place(x=0.4 * frame_width, y=0.07 * frame_height)

    def setup_hand(self):
        # Setup a fresh hand, deleting anything that was there before (either on new game or card
        # swap)
        if len(self.hand_btns) > 0:
            for i in self.hand_btns:
                self.hand_btns[i].destroy()
        self.hand_btns: dict[int, HandCardButton] = {}
        dealt_cards = self.game_logic.turn_state.hand_cards
        n = self.game_logic.turn_state.num_cards_left
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

    def set_up_other_players(self, frames: list[Frame]):
        for i in range(len(frames)):
            frame = frames[i]
            person_index = (self.game_logic.game_state.index + i + 1) % \
                self.game_logic.game_state.num_players
            person = self.game_logic.game_state.peeps[person_index]
            self.childframes[person] = frame
            self.set_up_opponent_info(person, frame)

    def set_label_next(self, current_player: str):
        for player, label in self.other_names_lbls.items():
            label.config(bg="green" if player == current_player else "red")
            self.childframes[player].config(
                bg=TURN_COLOR if player == current_player else BACKGROUND_COLOR)

    # Change the button color and enable/disable the parameter
    def toggle_uno(self):
        self.toggle_uno_button_color()
        # todo can we avoid setting a turn state from the ui?
        self.game_logic.turn_state.set_uno(not self.game_logic.turn_state.uno)

    def toggle_uno_button_color(self):
        if self.game_logic.turn_state.uno:
            self.uno_but["bg"] = BACKGROUND_COLOR
            self.uno_but["bg"] = "light sky blue"

        else:
            self.uno_but["bg"] = "lime green"

    def configure_stack_label(self, counter: int):
        self.stack_label.config(text=f"{STACK_LABEL_TEXT}{counter}")

    def update_labels_buttons_card_taken(self, new_card: Card, index: int, move_is_possible: bool):
        if self.game_logic.turn_state.stack_counter >= 0 and \
                self.game_logic.turn_state.last_played.type_is(CardType.PLUSTWO):
            # or Card.card_is(self.game_logic.turn_state.last_played, CardType.PLUSFOUR)
            self.configure_stack_label(self.game_logic.turn_state.stack_counter)
        self.cards_left.config(
            text=self.game_logic.turn_state.all_nums_of_cards[self.game_logic.game_state.identity]
        )

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
            (self.game_logic.turn_state.card_counter == 0 or
                (self.game_logic.game_state.modes.mult and
                    self.game_logic.turn_state.card_counter > 6)) and \
                self.game_logic.turn_state.stack_counter == 0:
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
        card_indices = self.game_logic.turn_state.sort_cards()
        old_buttons = copy.copy(self.hand_btns)
        # Get buttons from the sorted indices, but move indices to start from 0 again for an
        # increasing list
        self.hand_btns = {i: old_buttons[k] for (i, k) in enumerate(card_indices)}

        self.move_buttons()

    def show_information(self, title: str, information: str, default: bool):
        if default:
            messagebox.showinfo(title, information)
        else:
            InfoPop(self, title, information)

    def enable_taking_for_final_plus(self, counter: int):
        self.turn_need_taking.config(text="Take cards!", bg="orange")
        self.name_lbl.config(bg="green")
        self.childframes[self.game_logic.game_state.identity].set_color(TURN_COLOR)
        self.new_card.set_enabled(True)
        if self.game_logic.game_state.modes.stack and counter > 0:
            self.configure_stack_label(self.game_logic.turn_state.stack_counter)

    def show_temp_banner(self, text: str, ttl: int = 5000):
        frame_width = self.card_frame.width
        temp_banner = Label(self.card_frame, text=text, bg="blue", fg="white", width=40, height=1)
        temp_banner.place(x=0.4 * frame_width, y=1)
        self.master.after(ttl, temp_banner.destroy)

    def inform_about_sevenzero(
            self,
            from_player: str,
            number: str,
            old_hand_size: int,
            new_hand_size: int
    ):
        self.update_btns(from_player, old_hand_size, new_hand_size)
        self.show_temp_banner("You got cards from " + from_player, 10000)
        self.show_information(
            f"A {number} was played",
            f"{number} was played.\n You got cards from\n {from_player}",
            default=False
        )

    def update_other_nums_of_cards(self, num_cards_per_person: dict[str, int]):
        self.game_logic.log.info("Updating the number of remaining cards for others")
        for person, label in self.other_cards_lbls.items():
            card_word = "cards" if not num_cards_per_person[person] == 1 else "card"
            label.config(text=f"{num_cards_per_person[person]} {card_word}")
            o_cards = self.other_cards_imgs[person]
            for car in o_cards:
                car.destroy()

            self.put_other_cards(person, num_cards_per_person[person])

    # Another player either took a card, or placed a seven-zero, mostly
    def process_design_update(self, message: Message):
        self.game_logic.log.info("A player has taken or placed a card")
        who_updated = message.from_player
        card_word = "card" if message.num_left == 1 else "cards"
        self.other_cards_lbls[who_updated].config(text=f"{message.num_left} {card_word}")
        o_cards = self.other_cards_imgs[who_updated]
        for car in o_cards:
            car.destroy()
        self.put_other_cards(who_updated, message.num_left)

        if message.played:
            self.game_logic.log.info("A new card was placed, updating")
            self.set_last_played(message.played)

    # Show the points that you have with your cards right now (option in menu)
    def show_points(self):
        points = self.game_logic.game_state.all_points[self.game_logic.game_state.identity]
        text = f"Your points this session: {points}\n"
        for player, pts in self.game_logic.game_state.all_points.items():
            if player == self.game_logic.game_state.identity:
                text += "(You) "
            text += f"{player}: {pts} points\n"
        self.show_information("Points", text, default=True)

    def update_btns(self, player: str, old_hand_size: int, new_hand_size: int):
        self.sevenzero_update_buttons(player, old_hand_size, new_hand_size)

    def sevenzero_update_buttons(self, player: str, old_hand_size: int, new_hand_size: int):
        self.setup_hand()
        for j in self.hand_btns:
            self.hand_btns[j].set_enabled(False)

        card_word = "card" if old_hand_size == 1 else "cards"
        self.other_cards_lbls[player].config(text=f"{old_hand_size} {card_word}")
        self.cards_left.config(text=f"{new_hand_size}")

    def update_next_lbl(self, sent_message: Message):
        assert sent_message.played is not None
        skip_player: bool = sent_message.played.type_is(CardType.STOP) and not sent_message.taken
        difference = 2 if skip_player else 1
        # Take all players and move them up by 1/2 when turn finished
        if not self.game_logic.turn_state.is_reversed:
            next_index = (self.game_logic.game_state.index + difference) % \
                self.game_logic.game_state.num_players
        else:
            next_index = (self.game_logic.game_state.index - difference) % \
                self.game_logic.game_state.num_players
        next_player = self.game_logic.game_state.peeps[next_index]
        if next_player in self.other_names_lbls.keys():
            self.other_names_lbls[next_player].config(bg="green")
            self.childframes[next_player].set_color(TURN_COLOR)

    def set_last_played(self, last_played: Card):
        self.update_last_played_img(last_played)

    def update_last_played_img(self, card: Card):
        self.last.update_card(card)

    def check_periodically(self):
        self.game_logic.incoming()
        if not self.game_logic.turn_state.quit_game:
            self.after(100, self.check_periodically)

    def start_new(self, message: Message):

        self.game_logic.log.info("Destroying old game...")
        self.master.destroy()

        root = Tk()
        root.configure(bg="white")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry("{}x{}".format(screen_width, screen_height))
        utils.title_window(root, message.whoami, message.players)
        root.protocol("WM_DELETE_WINDOW", self.game_logic.send_bye_and_exit)
        new = GameUI(
            master=root,
            msg=message,
            q=self.game_logic.q,
            sock=self.game_logic.sock,
            # todo all_points part of game_state
            all_points=self.game_logic.game_state.all_points,
            logger=self.game_logic.log,
            # localhost=self.localhost
        )

        new.start_config(message)
        new.check_periodically()
        new.mainloop()

    def start_config(self, message: Message):
        assert message.played is not None
        self.game_logic.turn_state.configure_counters_uno_on_start(
            message.played,
            message.current_player
        )
        self.config_start_buttons(message)

    def config_start_buttons(self, message: Message):
        assert message.played is not None
        current = message.current_player == self.game_logic.game_state.identity
        played_plus = message.played.is_plus
        stack_possible = self.game_logic.game_state.modes.stack and \
            self.game_logic.turn_state.can_stack
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
        elif self.game_logic.turn_state.possible_move:
            self.new_card.set_enabled(False)

    # Move card to the pile in an animation
    def move(self, origx: int, origy: int, dx: int, dy: int, i: int, binst, img, ind: int):
        card = self.game_logic.turn_state.hand_cards[ind]
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
            self.game_logic.complete_placement(card, ind)

    def place_card(self, ind: int, binst: HandCardButton):
        new_card = self.game_logic.turn_state.hand_cards[ind]
        old_card = self.game_logic.turn_state.last_played
        same_color = new_card.color == old_card.color
        same_symbol = new_card.symbol == old_card.symbol
        is_black = new_card.type_is(CardType.BLACK)
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
                self.game_logic.complete_placement(new_card, ind)

    def update_labels_buttons_card_placed(self, placed_card: Card, ind: int):
        if placed_card.type_is(CardType.REVERSE):
            self.direction_l.set_image(
                self.revdir if self.game_logic.turn_state.is_reversed else self.fordir)
        self.hand_btns.pop(ind)
        self.cards_left.config(
            text=self.game_logic.turn_state.all_nums_of_cards[self.game_logic.game_state.identity])
        self.move_buttons()
        if placed_card.type_is(CardType.PLUSTWO) and self.game_logic.game_state.modes.stack:
            self.configure_stack_label(self.game_logic.turn_state.stack_counter + 2)

    def pick_option(self, title: str, question: str, options: Optional[list[str]]) -> str:
        if options:
            picker = Picker(self.master, title, question, options)
            return picker.result
        else:
            response = simpledialog.askstring(title, question)
            return response if response else "0"

    def update_labels_new_turn(self, played_card: Card, msg: Message):
        self.set_label_next(msg.current_player)
        self.direction_l.set_image(
            self.revdir if self.game_logic.turn_state.is_reversed else self.fordir)
        if played_card.type_is(CardType.PLUSTWO) and not msg.taken:
            if self.game_logic.game_state.modes.stack:
                self.configure_stack_label(self.game_logic.turn_state.stack_counter)
            self.taken_label.config(text="")
        elif msg.taken:
            self.configure_stack_label(0)
            self.taken_label.config(text="Other player took cards!")
        else:
            self.taken_label.config(text="")

    def enable_buttons_regular_turn(self, card: Card, msg: Message):
        self.name_lbl.config(bg="green")
        self.childframes[self.game_logic.game_state.identity].set_color(TURN_COLOR)
        if card.type_is(CardType.PLUSFOUR) and not msg.taken:
            # Show "challenge +4" button
            self.handle_wild_button(validity=msg.wild)
        # No moves possible, or move possible but need to take cards
        if not self.game_logic.turn_state.possible_move or \
            (self.game_logic.turn_state.card_counter == 2 or
                self.game_logic.turn_state.card_counter == 4):
            self.new_card.set_enabled(True)
        # Say your turn if either mode is normal, or take forever and not plus
        if (self.game_logic.turn_state.card_counter < 2 and not
            self.game_logic.game_state.modes.mult) or \
            (self.game_logic.game_state.modes.mult and not
                self.game_logic.turn_state.card_counter == 4 and not
                self.game_logic.turn_state.card_counter == 2) or \
                (self.game_logic.game_state.modes.stack and self.game_logic.turn_state.can_stack and
                    card.type_is(CardType.PLUSTWO)):
            self.turn_need_taking.config(text="", bg=TURN_COLOR)
            for i in self.hand_btns:
                self.hand_btns[i].set_enabled(True)
            if self.game_logic.game_state.modes.stack and self.game_logic.turn_state.can_stack and \
                    card.type_is(CardType.PLUSTWO) and not msg.taken and \
                    self.game_logic.turn_state.stack_counter > 0:
                for i in self.hand_btns:
                    # Go through cards on buttons and enable only +2s
                    if not self.hand_btns[i].card.type_is(CardType.PLUSTWO):
                        self.hand_btns[i].set_enabled(False)
        else:
            self.turn_need_taking.config(text="Take cards!", bg="orange")

    def ask_yes_no(self, title: str, question: str) -> int:
        return messagebox.askyesno(title, question)

    def enable_taking_for_challenge(self, reason: ChallengeReason):
        self.new_card.set_enabled(True)
        if reason == ChallengeReason.MISSING_UNO:
            self.show_information(
                "UNO not said!",
                "You forgot to click UNO, \nso take 2 cards!",
                default=True
            )
            self.turn_need_taking.config(text="Take 2 cards!", bg="orange")
        else:
            self.show_information(
                "Illegal +4!",
                "You can't put +4 when you \nhave other cards, so take 4!",
                default=True
            )
            self.turn_need_taking.config(text="Take 4 cards!", bg="orange")
        self.name_lbl.config(bg="orange")

    def disable_buttons(self, sent_message: Message):
        self.new_card.set_enabled(False)
        self.uno_but["bg"] = "light sky blue"
        self.handle_challenge_button(destroy=True)
        self.handle_wild_button(destroy=True)
        go_or_debug = sent_message.stage == Stage.GO or sent_message.stage == Stage.DEBUG
        if go_or_debug:
            self.update_next_lbl(sent_message)

        elif sent_message.stage == Stage.ZEROCARDS:
            self.turn_need_taking.config(text="Getting results!", bg=BACKGROUND_COLOR, fg="blue")
        else:
            self.turn_need_taking.config(text="", bg=BACKGROUND_COLOR)

        for i in self.hand_btns:
            self.hand_btns[i].set_enabled(False)
        self.name_lbl.config(bg="red")
        self.childframes[self.game_logic.game_state.identity].set_color(BACKGROUND_COLOR)
        self.taken_label.config(text="")

    def handle_challenge_button(self, player: Optional[str] = "", destroy: bool = False):
        if destroy:
            if self.challenge:
                self.challenge.destroy()
        else:
            self.challenge = ColorfulButton(
                parent_frame=self.central_frame,
                text="UNO not said!", bg="red", fg="white",
                width=150, height=30, command=self.handle_uno_challenge)
            if player == self.game_logic.game_state.identity:
                frame_width = self.central_frame["width"]
                frame_height = self.central_frame["height"]
                self.challenge.place(x=0.07 * frame_width, y=0.63 * frame_height)
        self.update_idletasks()

    def handle_wild_button(self, validity: bool = False, destroy: bool = False):
        if destroy:
            if self.valid_wild:
                self.valid_wild.destroy()
        else:
            self.valid_wild = ColorfulButton(
                parent_frame=self.central_frame,
                text="Illegal +4?", bg="HotPink",
                width=150, height=30,
                command=lambda valid=validity: self.handle_plus_challenge(valid))
            frame_width = self.central_frame["width"]
            frame_height = self.central_frame["height"]
            self.valid_wild.place(x=0.07 * frame_width, y=0.83 * frame_height)
        self.update_idletasks()

    def close_window(self):
        try:
            self.master.destroy()
        except TclError:
            self.game_logic.log.warning("The window seems to have been destroyed already")
            pass
        self.game_logic.log.info("Bye")

    # logicky bits

    def handle_uno_challenge(self):
        self.game_logic.challenge_uno()
        self.handle_challenge_button(destroy=True)

    def handle_plus_challenge(self, valid: bool):
        self.game_logic.challenge_plus(valid)
        if valid:
            self.show_information("Legal move", "The player was honest,\nso take 6 cards!", True)
        self.handle_wild_button(destroy=True)

    def handle_take_card(self):
        # Remove the "uno not placed" button as was ignored
        self.handle_challenge_button(destroy=True)
        self.handle_wild_button(destroy=True)
        new, ind, possible_move = self.game_logic.take_card()
        # Create and enable a new button for the card + update labels
        self.update_labels_buttons_card_taken(new, ind, possible_move)


# ######################################## SHOW FUNCTIONS #######################################
def show_rules():
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
