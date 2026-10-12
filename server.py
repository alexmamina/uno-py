import sys
import logging
from logmanager import setup_logger
from copy import deepcopy
from card import Card, CardType
from message_processor import Message
from message_utils import recover
from game_classes import ChallengeReason, Stage, Modes
import json
from json import JSONDecodeError
import utils
import server_utils
from server_game_data import Session, GameData

DEFAULT_BUFFER_SIZE = 700
BUFFER_CAP = 685
PADDING_CHAR = "a"
log = logging.getLogger(__name__)


class Server:
    session: Session
    game_data: GameData

    def __init__(self, args: list[str]):
        setup_logger(log, "server")
        session, modes = self.parse_server_arguments(args)
        self.session = session
        self.session.connect(log)
        self.game_data = GameData(self.session, modes, first_game=True)

    def parse_server_arguments(self, args: list[str]) -> tuple[Session, Modes]:
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

        local_address = (ip, port)
        # Get the number of players
        try:
            num_players = int(args[3])
        except ValueError:
            log.critical(f"Unable to convert the number of players ({args[3]}) to an integer!")
            sys.exit(1)
        # Get modes
        if "0" not in args[4]:
            modes = server_utils.get_modes(args[4], log)
        return Session(local_address=local_address, num_players=num_players), modes

    def send_to_all_players(self, message: Message, skip_current: bool = False):
        for player in self.session.players:
            # Send a message if we don't skip any players,
            # or we DO skip and we're not looking at the current player
            sending = (player != self.game_data.current_player and skip_current) or not skip_current
            if sending:
                self.send_message(message, player)

    def send_message(self, message: Message, destination_player: str):
        msg_copy = deepcopy(message)
        msg_copy.padding = PADDING_CHAR * (BUFFER_CAP - len(json.dumps(msg_copy.to_json())))
        encoded_msg = json.dumps(msg_copy.to_json()).encode("utf-8")
        self.session.players[destination_player].send_message(encoded_msg)

    def receive_message(self, from_player: str, buffer_size: int = DEFAULT_BUFFER_SIZE) -> Message:
        json_msg, _ = self.session.players[from_player].socket.recvfrom(buffer_size)
        try:
            dec_json = json_msg.decode("utf-8")
            message = Message.from_dict(json.loads(dec_json))
            message.padding = ""
        except JSONDecodeError as e:
            log.error(f"Error decoding response: {e}. Message: {json_msg}. Will try to recover")
            message = recover(dec_json)
        return message

    def send_initial_pile(self):
        num_players = self.session.num_players
        for ind, player in enumerate(self.game_data.players):
            data_to_send = self.game_data.generate_initial_message(ind, player, num_players)
            self.send_message(data_to_send, player)

    def process_received_challenge(self, message: Message):
        # From a current player to the previous player; need to send to previous player only
        self.game_data.fit_pile_to_size()
        message.pile = self.game_data.get_top_of_pile()
        rulebreaker = self.game_data.prev_player
        self.send_message(message, rulebreaker)
        # We sent a challenge to the previous player, so now expect a response from them
        self.game_data.prev_player = self.game_data.current_player
        self.game_data.current_player = rulebreaker

    def process_completed_challenge(self, message: Message):
        # Swap the current and previous player
        old = self.game_data.current_player
        self.game_data.current_player = self.game_data.prev_player
        self.game_data.prev_player = old

        self.game_data.player_cards_left[self.game_data.prev_player] = message.num_left

        self.game_data.update_pile(message.num_taken_from_pile)

        data = Message(
            stage=Stage.GO,
            pile=self.game_data.get_top_of_pile(),
            num_left=message.num_left,
            played=message.played,
            other_left=self.game_data.player_cards_left,
            is_reversed=self.game_data.is_reversed,
            counter=self.game_data.stack_counter,
            current_player=self.game_data.current_player,
            from_player=message.from_player,
            # Only mark cards as taken for illegal +4 as 'Uno not said' can still be played on a
            # valid +2/stack
            taken=message.challenge_reason == ChallengeReason.ILLEGAL_PLUSFOUR,
        )

        for player in self.session.players:
            if player != self.game_data.prev_player:
                self.send_message(data, player)

    def process_and_show_points(self, message: Message):
        # The message should always have 'played' here but adding the assertion for linting purposes
        assert message.played is not None
        taking_cards = message.played.is_plus
        self.game_data.fit_pile_to_size()

        # We only care about the next player if they have to take cards. They'll always be +1 so no
        # need to specify a played card
        next_player = utils.get_next_player(self.game_data.current_player, self.game_data.players)
        data = Message(
            stage=Stage.ZEROCARDS,
            pile=self.game_data.get_top_of_pile(),
            played=message.played,
            from_player=message.from_player,
            counter=message.counter,
            current_player=next_player,
        )
        for player in self.session.players:
            if player != self.game_data.current_player:
                # Only the next player needs to take cards
                data.to_take = taking_cards and player == next_player
                # Send the request for points and syncronously receive the response
                self.send_message(data, player)
                # Receive a response with calculated points for each player, sum them up
                result = self.receive_message(player, 1000)
                self.session.player_points[self.game_data.current_player] += result.points
        self.session.last_winner = self.game_data.current_player
        # Send a points update to all players
        msg = Message(
            stage=Stage.CALC,
            points=result.points,
            total=self.session.player_points,
            winner=self.game_data.current_player,
            from_player=message.from_player,
        )
        self.send_to_all_players(msg)

    def swap_after_seven(self, message: Message):
        swap_with = message.swapwith
        ask = Message(
            stage=Stage.SEVEN,
            hand=message.hand,
            from_player=self.game_data.current_player,
        )
        # Ask cards from the swapped player, send those to current, own to swapped
        response = self.swap_hands(ask, to_whom=swap_with)
        other_hand = response.hand
        log.info(f"Player {swap_with} has {other_hand}. Will go to {self.game_data.current_player}")
        response.end = True
        self.send_message(response, self.game_data.current_player)
        # Swap numbers of cards
        self.game_data.player_cards_left[swap_with] = message.num_left
        self.game_data.player_cards_left[self.game_data.current_player] = len(other_hand)

    def swap_hands(self, swapping_message: Message, to_whom: str) -> Message:
        from_whom = swapping_message.from_player
        log.info(f"Player {from_whom} has {swapping_message.hand} - sending to player {to_whom}")
        self.send_message(swapping_message, to_whom)
        return self.receive_message(to_whom, 2000)

    def swap_after_zero(self, current_player_hand: list[str]):  # TODO: pull out into game_data
        swap = Message(
            stage=Stage.ZERO,
            hand=current_player_hand,
            from_player=self.game_data.current_player
        )
        # Record current player's index, find the next player, send current hand to next, retrieve
        # next's hand. Update index to point to next player, and get their next(-next) player.
        # Repeat until the current index points to the current player again.
        i = self.game_data.players.index(self.game_data.current_player)
        next_player = utils.get_next_player(self.game_data.current_player, self.game_data.players)
        self.game_data.player_cards_left[next_player] = len(current_player_hand)
        response = self.swap_hands(swap, to_whom=next_player)
        hand = response.hand
        i = (i + 1) % self.session.num_players
        next_player = utils.get_next_player(next_player, self.game_data.players)
        while i != self.game_data.players.index(self.game_data.current_player):
            swap = Message(
                stage=Stage.ZERO,
                hand=hand,
                from_player=self.game_data.players[i]
            )
            self.game_data.player_cards_left[next_player] = len(hand)
            response = self.swap_hands(swap, to_whom=next_player)
            hand = response.hand
            i = (i + 1) % self.session.num_players
            next_player = utils.get_next_player(next_player, self.game_data.players)

    def relay_and_change_turns(self, card: Card, message: Message):
        assert self.game_data.previous_message is not None
        skip_next_player = card.type_is(CardType.STOP) and not message.taken
        # If the last played card is stop
        next_player = utils.get_next_player(
            self.game_data.current_player,
            self.game_data.players,
            # Only provide a card if it's a valid stop that needs to be followed
            card if skip_next_player else None,
        )
        message.current_player = next_player
        message.num_left = self.game_data.previous_message.num_left
        # Forward message to all players with updated info about who's next
        if skip_next_player:
            self.send_to_all_players(message)
        # Forward message to all players except the one who just played
        # To the player who finished send an update of the number of cards per player
        else:
            self.send_to_all_players(message, skip_current=True)
            cards_left_msg = Message(
                stage=Stage.NUMUPDATE,
                other_left=self.game_data.player_cards_left,
                from_player=message.from_player
            )
            self.send_message(cards_left_msg, self.game_data.current_player)

        self.game_data.prev_player = self.game_data.current_player
        self.game_data.current_player = next_player

    def process_regular_message(self, message: Message):
        assert message.played is not None
        card = message.played

        log.info(f"{self.game_data.current_player} played {card.name} (type {card.card_type})")
        if not message.taken:  # TODO: pull this out into game_data.process msg
            self.game_data.add_played_card(card)
            if self.game_data.modes.stack and message.counter:
                self.game_data.stack_counter = message.counter
        else:
            # The player took cards after a +2/+4 and reported it
            self.game_data.stack_counter = 0
        self.game_data.update_pile(message.num_taken_from_pile)

        self.game_data.player_cards_left[self.game_data.current_player] = message.num_left

        if self.game_data.modes.sevenzero and not message.taken:
            if card.type_is(CardType.SEVEN):
                self.swap_after_seven(message)
            elif card.type_is(CardType.ZERO):
                self.swap_after_zero(message.hand)

        data = Message(
            num_left=message.num_left,
            played=card,
            pile=self.game_data.get_top_of_pile(),
            other_left=self.game_data.player_cards_left,
            stage=Stage.GO,
            said_uno=message.said_uno,
            from_player=message.from_player,
            wild=message.wild,  # TODO: ensure this is only set on not-taken=+4
            taken=message.taken,
            counter=message.counter,
            is_reversed=self.game_data.is_reversed,
        )

        self.relay_and_change_turns(card, data)

        if not message.played.type_is(CardType.STOP):
            self.game_data.previous_message = message

    def process_messages_forever(self):
        while True:
            log.info(f"Waiting for player {self.game_data.current_player}")
            message = self.receive_message(self.game_data.current_player)
            if message.stage == Stage.GO or message.stage == Stage.DEBUG:
                self.process_regular_message(message)

            elif message.stage == Stage.CHALLENGE:
                log.info("Received a challenge - Uno wasn't said, or an illegal +4 was placed")
                self.process_received_challenge(message)

            elif message.stage == Stage.SHOWCHALLENGE:
                log.info("Someone clicked on \"Illegal +4\" but it was legal! Forwarding")
                self.send_message(message, self.game_data.prev_player)

            elif message.stage == Stage.CHALLENGE_TAKEN:
                log.info("The previous player took cards after forgetting Uno or placing a bad +4")
                self.process_completed_challenge(message)

            elif message.stage == Stage.ZEROCARDS:
                log.info("A player has finished - tallying up the points")
                self.process_and_show_points(message)

            elif message.stage == Stage.INIT:
                self.session.total_games_played += 1
                log.info(f"New game! Total completed: {self.session.total_games_played}")
                self.game_data = GameData(self.session, self.game_data.modes)
                self.send_initial_pile()

            elif message.stage == Stage.DESIGNUPD:
                log.info("Received a design update")
                # Forward the update to every player except the one we got it from
                self.send_to_all_players(message, skip_current=True)
            elif message.stage == Stage.BYE:
                log.info("Goodbye received, shutting down")
                # Don't send to the current player as they sent it to us in the first place
                self.send_to_all_players(message, skip_current=True)
            else:
                log.critical(f"Unsupported stage: {message.stage}")
                break

    def exit(self):
        return self.session.exit()


if __name__ == "__main__":
    server = Server(sys.argv)
    server.send_initial_pile()
    server.process_messages_forever()
    server.exit()
