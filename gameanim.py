import copy
import json
import queue

from logging import Logger
from typing import Any, TYPE_CHECKING

from game_classes import Stage, Modes, GameState
from turn_state import TurnState
from card import Card, CardType
from socket import socket

from deck import Deck
from json import JSONDecodeError
from message_utils import recover
if TYPE_CHECKING:
    from game_ui import GameUI


class GameLogic():

    # Initialise a logic engine
    def __init__(
        self,
        queue,  #: queue.Queue,
        msg: dict[str, Any],
        sock: socket,
        all_points,
        logger: Logger,
        game_ui: "GameUI",
    ):
        self.log = logger
        self.sock = sock
        self.q = queue
        self.game_ui = game_ui

        self.game_state = GameState(
            msg["whoami"],
            msg["peeps"],
            Deck(),
            all_points,
            Modes.from_json(msg["modes"])
        )

        other_players: list[str] = copy.deepcopy(self.game_state.peeps)
        other_players.pop(self.game_state.index)
        self.log.info(f"I am {self.game_state.identity}, playing against {other_players}")

        self.turn_state = TurnState(
            stack_counter=0 if not Card(msg["played"]).type_is(CardType.PLUSTWO) else 2,
            all_nums_of_cards=msg["other_left"],
            card_counter=1 if not self.game_state.modes.mult else 500,
            is_reversed=msg["dir"],
            pile=msg["pile"],
            last_played=msg["played"],
            game_state=self.game_state,
            stage=msg["stage"]
        )

    # #################################### EVENTS ##################################
    # Set new card on pile, send information, update hand - after animation or straight away
    def complete_placement(self, card: str, card_index: int):
        proper_card = Card(card)
        if proper_card.type_is(CardType.REVERSE):
            self.turn_state.is_reversed = not self.turn_state.is_reversed
        # Changes the black card to black with a color to show which one to play next
        if proper_card.type_is(CardType.BLACK):
            new_color = self.game_ui.pick_option(
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
        self.turn_state.hand_cards.pop(card_index)
        self.turn_state.all_nums_of_cards[self.game_state.identity] -= 1

        self.game_ui.update_labels_buttons_card_placed(special_card, card_index)

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
            swap_with = self.game_ui.pick_option(
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

        self.game_ui.update_last_played_img(special_card)

    def take_card(self):
        # Take new card
        new = Card(self.turn_state.pile.pop(0))
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
        return new, ind, possible_move

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
                    self.game_ui.enable_taking_for_challenge(msg["why"])

                elif msg["stage"] == Stage.SHOWCHALLENGE:
                    self.log.info("Another player tried to check you for illegal +4")
                    self.game_ui.show_temp_banner("Someone checked if +4 was illegal!", 5000)

                # Another player has finished the game; you either take cards if last is a plus,
                # or automatically send the remaining points for the other player
                elif msg["stage"] == Stage.ZEROCARDS:
                    self.game_ui.set_last_played(msg)
                    if msg["to_take"]:
                        # Enable taking cards
                        self.game_ui.enable_taking_for_final_plus(msg)

                        self.turn_state.update_card_counter(
                            2 if Card(msg["played"]).type_is(CardType.PLUSTWO) else 4
                        )
                        if self.game_state.modes.stack and "counter" in msg:
                            self.turn_state.update_stack_counter(msg["counter"])
                            self.game_ui.configure_stack_label(self.turn_state.stack_counter)

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
                        self.game_ui.show_information(
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

                    self.game_ui.inform_about_sevenzero(msg, what)

                elif msg["stage"] == Stage.NUMUPDATE:
                    self.game_ui.update_other_nums_of_cards(msg)

                elif msg["stage"] == Stage.DESIGNUPD:
                    self.game_ui.process_design_update(msg)

                elif msg["stage"] == Stage.INIT:
                    self.log.info("New game!")
                    self.game_ui.start_new(msg)
                elif msg["stage"] == Stage.BYE:
                    self.log.info("Received a BYE message, closing (someone exited?)")
                    self.turn_state.set_quit_game()
                    break

            except queue.Empty:
                pass
        if self.turn_state.quit_game:
            self.log.info("Loop ended")
            self.send_bye_and_exit()

    def process_regular_message(self, msg: dict[str, Any]):
        # todo some of this could be turn_state methods
        # Set the last played card and configure the pile + card counter
        self.game_ui.set_last_played(msg)
        newly_played = msg["played"]
        self.log.info(f"Played: {newly_played}")
        if Card(newly_played).type_is(CardType.PLUSTWO) and "taken" not in msg:
            self.turn_state.update_card_counter(2)
            if self.game_state.modes.stack:
                self.turn_state.update_stack_counter(msg["counter"])
        elif "taken" in msg:
            self.turn_state.update_stack_counter(0)
        self.game_ui.update_labels_new_turn(newly_played, msg)
        self.game_ui.update_other_nums_of_cards(msg)
        # Check if other player said UNO; place the challenge button if not said
        if "said_uno" in msg.keys() and not msg["said_uno"]:
            self.game_ui.handle_challenge_button(msg["player"])
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
                self.game_ui.show_information(
                    "UNO",
                    f"{from_player}\n has only 1 card left!",
                    default=False
                )

        self.turn_state.all_nums_of_cards = msg["other_left"]

        # Enable buttons for cards if your turn; make UNO show if necessary
        if msg["player"] == self.game_state.identity:
            self.log.info("Your turn, enabling buttons")
            self.game_ui.enable_buttons_regular_turn(newly_played, msg)

    def process_winning(self, points: int, table_of_points: str) -> bool:
        self.game_ui.show_information(
            "Win",
            f"You won {points} points!\n\n Total this session: \n" +
            table_of_points,
            default=True)
        ans = self.game_ui.ask_yes_no("New", "Would you like to continue\n with a new game?")
        if ans == 1:
            modes_response = self.game_ui.pick_option(
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
            self.turn_state.set_quit_game()
        return ans == 1

    # Put received message in queue for async processing
    def receive(self):
        while not self.turn_state.quit_game:
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
                    self.turn_state.set_quit_game()
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
                    self.turn_state.set_quit_game()
                    raise
                # break
            except OSError as o:
                if o.errno == 9:
                    self.log.info("Tried to receive a message, but the socket has closed")
                    break
                else:
                    self.log.error(o)
                    self.turn_state.set_quit_game()
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

        self.game_ui.disable_buttons(data_to_send)
        self.log.info("Not your turn anymore")

    # Notify opponent that they forgot to say UNO; when clicking button
    def challenge_uno(self):
        data = {"stage": Stage.CHALLENGE, "why": 1}
        if self.game_state.modes.stack and self.turn_state.stack_counter > 0:
            data["counter"] = self.turn_state.stack_counter
        self.send_info(data)

    def challenge_plus(self, is_valid: bool):
        data = {"stage": Stage.CHALLENGE, "why": 4}
        # If true that can't put +4, so it was illegal, send it
        if not is_valid:
            self.send_info(data)
        else:
            self.turn_state.update_card_counter(6)
            data = {"stage": Stage.SHOWCHALLENGE, "from": self.game_state.identity}
            self.send_message(data)

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
        self.game_ui.configure_stack_label(0)

    # Send all the final information with 0 cards left to end/finalise the game
    def send_final(self, data_to_send: dict[str, Any]):
        self.log.info("END")
        data_to_send["stage"] = Stage.ZEROCARDS
        self.turn_state.set_uno(False)
        self.turn_state.reset_card_counter()
        self.send_message(data_to_send)

        self.game_ui.disable_buttons(data_to_send)
        self.log.info("Not your turn anymore")

    def send_bye_and_exit(self):
        try:
            bye: dict[str, Any] = {"stage": Stage.BYE}
            self.send_message(bye)
            self.sock.close()
        except OSError:
            pass
        self.turn_state.set_quit_game()

        self.log.info("I am closing")
        self.game_ui.close_window()

    def send_message(self, message: dict[str, Any]):
        message["padding"] = "a" * (685 - len(json.dumps(message)))
        # todo remove for message class
        # with open("gamemsgs.txt", "a") as f:
        #     f.write(f"{list(message.keys())}stage: {message['stage']}")
        #     f.write("\n")
        self.sock.send(json.dumps(message).encode("utf-8"))
