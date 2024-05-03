from socket import socket, AF_INET, SOCK_STREAM
import sys
import logging
from logmanager import setup_logger
from deck import Deck
from typing import Any
from random import shuffle
from copy import deepcopy
from card import Card
from message_utils import recover
from game_classes import Stage, Modes
import json
from json import JSONDecodeError
import utils

log = logging.getLogger(__name__)


def pretty_print_message(message: dict[str, Any]):
    new_msg = deepcopy(message)
    new_msg.pop("padding", "")
    log.debug(new_msg)


class Server():

    def __init__(self):
        setup_logger(log, "server")
        self.sock: socket = socket(AF_INET, SOCK_STREAM)
        self.num_players: int
        self.modes = Modes()
        self.local_address: tuple[str, int]  # (ip, port)
        self.peeps: list[str] = []  # Names of players
        self.socks: dict[str, socket] = {}  # Socket information per player
        self.addresses: dict[str, tuple[str, int]] = {}  # Each player's address
        self.current_player = ""
        self.stack_counter = 0
        self.total_games_played = 0
        self.parse_server_arguments(sys.argv)
        self.all_players_points: dict[str, int]
        self.sock.bind(self.local_address)
        self.sock.listen(128)

    def parse_server_arguments(self, args: list[str]):
        if len(args) < 4:
            log.critical(
                "Please provide four space-separated arguments: the local ip address, the port"
                " to connect to, the number of players and any game modes without spaces."
                "(Input 0 for a regular game, or 1 for 7/0, 2 for stacking and 3 for taking "
                "multiple cards)"
            )
            sys.exit(1)

        # Get the local address
        ip = args[1]
        try:
            port = int(args[2])
        except ValueError:
            log.critical(f"Unable to convert port {args[2]} to an integer!")
            sys.exit(1)
        self.local_address = (ip, port)
        # Get the number of players
        try:
            self.num_players = int(args[3])
        except ValueError:
            log.critical(f"Unable to convert the number of players ({args[3]}) to an integer!")
            sys.exit(1)
        # Get modes
        # [0] = 7/0, [1] = stack, [2] = take forever
        if "0" not in args[4]:
            self.modes = self.get_modes(args[4])

    def get_modes(self, mode_string: str) -> Modes:
        modes = Modes.from_string(mode_string)
        for mode in modes.enabled_strings():
            log.info(f"{mode} enabled")
        return modes

    def connect_clients(self):
        player_counter = 0
        # Wait for clients to connect and save their information
        while player_counter < self.num_players:
            player_socket, addr = self.sock.accept()
            byte_name, _ = player_socket.recvfrom(200)
            name = byte_name.decode("utf-8")
            self.peeps.append(name)
            self.socks[name] = player_socket
            self.addresses[name] = addr
            log.info(f"Connected player {player_counter} - {name}")
            player_counter += 1
            n = self.num_players - player_counter
            log.info(f"Waiting for {n} more players")
        self.all_players_points = {
            p: number for p, number in zip(self.peeps, [0] * self.num_players)
        }

    def init_deck(self):
        # Deck initialisation
        deck_placeholder: list[Card] = Deck().deck
        self.pile: list[str] = [c.name for c in deck_placeholder]
        self.all_played = []
        self.is_reversed = False
        self.first_card = self.pop_first_card()
        self.left_cards: dict[str, int] = {
            p: number for p, number in zip(self.peeps, [7] * self.num_players)
        }
        self.resulting_points = 0
        self.previous_message = {}

    # If too few cards left, shuffle all played cards and add to the end of the pile.
    # Reset all played afterwards as they're now a part of the pile
    def fit_pile_to_size(self):
        if len(self.pile) < 20:
            shuffle(self.all_played)
            self.pile += self.all_played
            self.all_played = []

    def pop_first_card(self) -> str:
        # Usually the first card is placed after cards are dealt (so e.g. it's the 15th card for 2
        # players). Pretend it's the same here
        first_card: str = self.pile.pop(7 * self.num_players)

        # Black cards will not be played first. If popped, reshuffle and get a new one
        while "bla" in first_card:
            self.pile.append(first_card)
            shuffle(self.pile)
            first_card = self.pile.pop(7 * self.num_players)
        return first_card

    def reverse_players(self):
        self.peeps.reverse()
        self.is_reversed = not self.is_reversed

    def send_initial_pile(self, first_game: bool = False):
        # Skeleton of json to be sent
        data_to_send = {
            "stage": Stage.INIT,
            "modes": self.modes.to_json(),
            "played": self.first_card,
            "pile": self.pile[0:7],
            "num_left": 7,
            "other_left": self.left_cards,
            # The card name is 3 chars of color + the number/other properties
            "color": self.first_card[0:3],
            "player": False
        }
        self.previous_message = data_to_send
        # End of initialisation

        log.info(self.peeps)
        data_to_send["peeps"] = deepcopy(self.peeps)
        if "reverse" in self.first_card:
            self.reverse_players()

        if first_game:
            self.current_player = self.peeps[0] if "stop" not in self.first_card else self.peeps[1]
        else:
            # On consequent games we start from the players after the winner, not player 0
            # (either the next one, or the one after if a stop is played)
            self.current_player = utils.get_next_player(
                self.current_player, self.peeps, self.first_card
            )
        self.prev_player = utils.get_prev_player(self.current_player, self.peeps, self.first_card)

        data_to_send["dir"] = self.is_reversed

        for player in self.peeps:
            player_index = self.peeps.index(player)
            data_to_send["pile"] = self.pile[0:7] + \
                self.pile[
                    7 * (self.num_players - player_index):7 * (self.num_players - player_index) + 20
            ]
            data_to_send["whoami"] = player

            # todo replace player with is_current. or curr and player can be combined
            data_to_send["player"] = player == self.current_player
            if not data_to_send["player"]:
                data_to_send["curr"] = self.current_player

            self.send_message(data_to_send, player)
            log.info(f"Sent initial cards to player {player}")
            pretty_print_message(data_to_send)
            self.pile = self.pile[7:]

    def send_to_all_players(self, message: dict[str, Any], skip_current: bool = False):
        for player in self.peeps:
            # Send a message if we don't skip any players,
            # or we DO skip and we're not looking at the current player
            sending = (player != self.current_player and skip_current) or not skip_current
            if sending:
                self.send_message(message, player)

    def send_message(self, message: dict[str, Any], destination_player: str):
        msg_copy = deepcopy(message)
        msg_copy.pop("padding", "")
        msg_copy["padding"] = "a" * (685 - len(json.dumps(msg_copy)))
        encoded_msg = json.dumps(msg_copy).encode("utf-8")
        self.socks[destination_player].sendto(encoded_msg, self.addresses[destination_player])

    def receive_message(self, from_player: str, buffer_size: int = 700) -> dict[str, Any]:
        json_msg, _ = self.socks[from_player].recvfrom(buffer_size)
        try:
            dec_json = json_msg.decode("utf-8")
            message = json.loads(dec_json)
            message.pop("padding", "")
            log.debug(message)
        except JSONDecodeError as e:
            log.critical(f"Error decoding response from a player: {e}")
            log.critical(json_msg)
            log.warning("Trying to recover")
            message = recover(dec_json)
        return message

    def process_received_challenge(self, message: dict[str, Any]):
        # From a current player to the previous player; need to send to previous player only
        self.fit_pile_to_size()
        data = message
        # This makes data longer than 700 characters, but that's fine. We're trimming padding later
        data["pile"] = self.pile[:20]
        rulebreaker = self.prev_player
        self.send_message(data, rulebreaker)
        # We sent a challenge to the previous player, so now expect a response from them
        self.prev_player = self.current_player
        self.current_player = rulebreaker

    def process_completed_challenge(self, message: dict[str, Any]):
        # Swap the current and previous player
        old = self.current_player
        self.current_player = self.prev_player
        self.prev_player = old

        # Update the now previous player's card number, as well as what the pile looks like
        self.left_cards[self.prev_player] = message["num_left"]
        self.pile.pop(0)
        self.pile.pop(0)
        if "why" in message and message["why"] == 4:
            self.pile.pop(0)
            self.pile.pop(0)

        self.fit_pile_to_size()

        data = {
            "pile": self.pile[:20],
            "num_left": message["num_left"],
            "played": message["played"],
            "other_left": self.left_cards,
            "stage": Stage.GO,
            "player": True,
            "color": message["color"]
        }

        if "why" in message and message["why"] == 4:
            data["taken"] = True
        data["dir"] = self.is_reversed
        data["counter"] = self.stack_counter

        for player in self.peeps:
            if player != self.prev_player:
                data["player"] = player == self.current_player
                if not data["player"]:
                    data["curr"] = self.current_player
                self.send_message(data, player)

    def process_and_show_points(self, message: dict[str, Any]):
        taking_cards = "plus" in message["played"]
        self.fit_pile_to_size()

        data = {
            "pile": self.pile[0:20],
            "played": message["played"],
            "stage": Stage.ZEROCARDS,
            "player": True,
            "color": message["color"],
            "to_take": taking_cards
        }
        # If stacking is enabled, someone may need to take many cards first
        if "counter" in message and self.modes.stack:
            data["counter"] = message["counter"]
            self.stack_counter = message["counter"]
        # Either: next takes cards, then all send. Or: all send

        # We only care about the next player if they have to take cards. They'll always be +1 so no
        # need to specify a played card
        next_player = utils.get_next_player(self.current_player, self.peeps, "")
        for player in self.peeps:
            if player != self.current_player:
                # Only the next player needs to take cards
                data["to_take"] = taking_cards and player == next_player

                # Send the request for points and syncronously receive the response
                self.send_message(data, player)
                result = self.receive_message(player, 1000)
                self.resulting_points += result["points"]

        self.all_players_points[self.current_player] += self.resulting_points

        # Send a points update to all players
        msg = {
            "stage": Stage.CALC,
            "points": self.resulting_points,
            "total": self.all_players_points,
            "winner": self.current_player
        }
        self.send_to_all_players(msg)

    def pop_pile_until_equivalent(self, player_cards_left: int):
        # Find the difference between how many cards a player has vs how many we reported for them
        # before their move
        num_taken = player_cards_left - self.left_cards[self.current_player]
        for _ in range(num_taken):
            self.pile.pop(0)

    def swap_after_seven(self, message: dict[str, Any]):
        swapped_player = message["swapwith"]
        hand = message["hand"]
        ask = {
            "stage": Stage.SEVEN,
            "hand": hand,
            "from": self.current_player
        }
        # Ask cards from the swapped player, send those to current,
        # msg["cards"] to swapped
        decoded_response = self.swap_hands(ask, to_whom=swapped_player)
        other_hand = decoded_response["hand"]
        log.info(
            f"Player {swapped_player} has {other_hand}. Will go to {self.current_player}"
        )
        decoded_response["end"] = True
        self.send_message(decoded_response, self.current_player)
        # Swap number of cards
        self.left_cards[swapped_player] = message["num_left"]
        self.left_cards[self.current_player] = len(other_hand)

    def swap_hands(
            self, swapping_message: dict[str, Any], to_whom: str
    ) -> dict[str, Any]:
        # Add padding to message
        from_whom = swapping_message["from"]
        log.info(f"Player {from_whom} has {swapping_message['hand']} - sending to player {to_whom}")
        self.send_message(swapping_message, to_whom)
        decoded_response = self.receive_message(to_whom, 2000)
        return decoded_response

    def swap_after_zero(self, message: dict[str, Any]):
        hand = message["hand"]
        # Go through the indices of players and swap cards
        i = self.peeps.index(self.current_player)
        swap = {
            "stage": Stage.ZERO,
            "hand": hand,
            "from": self.current_player
        }
        next_player = utils.get_next_player(self.current_player, self.peeps, "zero")
        self.left_cards[next_player] = len(hand)
        response = self.swap_hands(swap, to_whom=next_player)
        hand = response["hand"]
        i = (i + 1) % self.num_players
        next_player = utils.get_next_player(next_player, self.peeps, "zero")
        while not (i == self.peeps.index(self.current_player)):
            swap = {
                "stage": Stage.ZERO,
                "hand": hand,
                "from": self.peeps[i]
            }
            self.left_cards[next_player] = len(hand)
            response = self.swap_hands(swap, to_whom=next_player)
            # bug response has no hand for a third player when 4 play. could not reproduce tho
            hand = response["hand"]
            i = (i + 1) % self.num_players
            next_player = utils.get_next_player(next_player, self.peeps, "zero")

    def relay_and_change_turns(self, card: str, message: dict[str, Any]):
        # If the last played card is stop
        if "stop" in card and "taken" not in message:  # todo this could probably be combined
            next_player = utils.get_next_player(self.current_player, self.peeps, card)
            for player in self.peeps:
                message["player"] = player == next_player
                if not message["player"]:
                    message["curr"] = next_player
                message["num_left"] = self.previous_message["num_left"]
                self.send_message(message, player)
                log.info(f"Message about a stop card forwarded to player {player}")

        # Not stop, so just relay info
        else:
            # The next player is +1. Either on a refular turn, or on a stop + taken combination
            next_player = utils.get_next_player(self.current_player, self.peeps, "")
            for player in self.peeps:
                if player != self.current_player:
                    message["player"] = player == next_player
                    if not message["player"]:
                        message["curr"] = next_player
                    self.send_message(message, player)
                    log.info(f"Regular message forwarded to player {player}")
                else:
                    left = {"stage": Stage.NUMUPDATE, "other_left": self.left_cards}
                    self.send_message(left, player)
                    log.info(f"Number update sent to current player {player}")
        self.prev_player = self.current_player
        self.current_player = next_player

    def process_regular_message(self, message: dict[str, Any]):  # refactor
        card = message["played"]

        log.info(f"Player {self.current_player} played {card}")

        data = {
            "pile": self.pile,
            "num_left": message["num_left"],
            "played": message["played"],
            "other_left": self.left_cards,
            "stage": Stage.GO,
            "player": True,
            "color": message["color"]
        }
        if "plusfour" in card and "taken" not in message:
            data["wild"] = message["wild"]
        if "taken" not in message:
            self.all_played.append(card)
            # Compare the pile on the server with the client's one to see if the player took cards
            if not (self.pile[0:5] == message["pile"][0:5]):
                self.pile.pop(0)
            # If taking multiple cards is enabled, make the server and client piles eqivalent
            if self.modes.mult:
                self.pop_pile_until_equivalent(message["num_left"])
        else:
            # The player took cards after a +2/+4 and reported it
            self.stack_counter = 0
            data["taken"] = message["taken"]
            self.pop_pile_until_equivalent(message["num_left"])
        self.fit_pile_to_size()
        data["pile"] = self.pile[:20]
        self.left_cards[self.current_player] = message["num_left"]

        if "7" in card and self.modes.sevenzero and "taken" not in message:
            # A seven was placed right now, not that it was placed before but someone else took
            # cards afterwards
            self.swap_after_seven(message)

        if "0" in card and self.modes.sevenzero and "taken" not in message:
            self.swap_after_zero(message)

        data["other_left"] = self.left_cards

        if self.modes.stack and "counter" in message:
            data["counter"] = message["counter"]
            self.stack_counter = message["counter"]

        if "reverse" in card and "taken" not in message:
            self.reverse_players()
        data["dir"] = self.is_reversed

        if message["num_left"] == 1 and "said_uno" not in message.keys():
            data["said_uno"] = False
        elif "said_uno" in message.keys() and message["said_uno"]:
            data["said_uno"] = True
            data["from"] = self.current_player

        self.relay_and_change_turns(card, data)

        if "stop" not in message["played"]:
            self.previous_message = message

    def process_messages_forever(self):
        # Go - regular play, regular relay
        # Debug - change turn, regular play, print data
        # Challenge - only send packet to make player take two cards
        # Zerocards - one player is out of cards, forward to the other who will either take cards or
        # send points
        # Calc - other player sends points

        while True:
            log.info(f"Waiting for player {self.current_player}")
            message = self.receive_message(self.current_player)
            if message["stage"] == Stage.GO or message["stage"] == Stage.DEBUG:
                self.process_regular_message(message)

            elif message["stage"] == Stage.CHALLENGE:
                log.info("Received a challenge - Uno wasn't said, or an illegal +4 was placed")
                self.process_received_challenge(message)

            elif message["stage"] == Stage.SHOWCHALLENGE:
                log.info("Someone clicked on \"Illegal +4\" but it was legal! Forwarding")
                self.send_message(message, self.prev_player)

            elif message["stage"] == Stage.CHALLENGE_TAKEN:
                log.info("The previous player took cards after forgetting Uno or placing a bad +4")
                self.process_completed_challenge(message)

            elif message["stage"] == Stage.ZEROCARDS:
                log.info("A player has finished - tallying up the points")
                self.process_and_show_points(message)

            elif message["stage"] == Stage.INIT:
                self.total_games_played += 1
                log.info(f"New game! Total played: {self.total_games_played}")
                # Restore the player list to its original form
                if self.is_reversed:
                    self.reverse_players()
                self.init_deck()
                self.modes = Modes.from_json(message.get("modes", {}))
                self.send_initial_pile()

            elif message["stage"] == Stage.DESIGNUPD:
                log.info("Received a design update")
                # Forward the update to every player except the one we got it from
                self.send_to_all_players(message, skip_current=True)

            else:
                # Try and get the stage - either it's a new one, or the key doesn't exist
                msg_stage = message.get("stage", "")
                log.info(
                    f"Received a BYE message or an unknown stage: {msg_stage}."
                    " Forwarding and shutting down"
                )
                # Don't send to the current player as they sent it to us in the first place
                self.send_to_all_players(message, skip_current=True)
                break

    def exit(self):
        for player in self.peeps:
            self.socks[player].close()
        self.sock.close()


if __name__ == "__main__":

    server = Server()
    server.connect_clients()

    server.init_deck()
    server.send_initial_pile(first_game=True)

    server.process_messages_forever()

    server.exit()
