from deck import Deck
from card import Card, CardType, BLACK_PLUSFOUR_CARD_NAME, BLACK_CARD_NAME
from message_processor import Message
from typing import Optional
from game_classes import Modes, Stage
import utils
from random import shuffle
import server_utils
from server_session_data import Session


DEFAULT_PILE_SIZE = 20


class GameData:
    players: list[str]
    player_cards_left: dict[str, int]
    current_player: str
    prev_player: str
    modes: Modes
    stack_counter: int
    pile: list[str]
    all_played: list[str]
    is_reversed: bool
    first_card: Card
    previous_message: Optional[Message]

    def __init__(self, session: Session, modes: Modes, first_game: bool = False):
        self.players = []
        self.modes = modes
        self.player_cards_left = {}
        self.is_reversed = False
        deck_placeholder: list[Card] = Deck().deck
        temp_pile: list[str] = [c.name for c in deck_placeholder]
        self.first_card, self.pile = server_utils.pop_first_card(temp_pile, session.num_players)
        for p in session.players:
            self.players.append(p)
            self.player_cards_left[p] = 7
        if self.first_card.type_is(CardType.REVERSE):
            self.reverse_players()
        if first_game:
            self.current_player = (
                self.players[0]
                if not self.first_card.type_is(CardType.STOP)
                # 1 in every case except for testing 1 player
                else self.players[1 % session.num_players]
            )
        else:
            # On consequent games we start from the player after the winner, not player 0
            # (either the next one, or the one after if a stop is played)
            self.current_player = utils.get_next_player(
                session.last_winner, self.players, self.first_card
            )
        self.prev_player = utils.get_prev_player(
            self.current_player, self.players, self.first_card)
        self.stack_counter = 0
        self.all_played = []
        self.previous_message = None

    def generate_initial_message(self, ind: int, player: str, num_players: int) -> Message:
        # Message skeleton that will be populated with player-specific data below
        data_to_send = Message(
            stage=Stage.INIT,
            modes=self.modes,
            played=self.first_card,
            num_left=7,
            other_left=self.player_cards_left,
            players=self.players,
            is_reversed=self.is_reversed
        )
        self.previous_message = data_to_send

        # The first 7 cards are for the hand + the rest (default size) represent a pile
        start_pile_index = 7 * (num_players - ind)
        end_pile_index = start_pile_index + DEFAULT_PILE_SIZE
        data_to_send.pile = self.pile[:7] + self.pile[start_pile_index:end_pile_index]
        data_to_send.whoami = player
        data_to_send.current_player = self.current_player

        self.pile = self.pile[7:]
        return data_to_send

    def reverse_players(self):
        self.players.reverse()
        self.is_reversed = not self.is_reversed

    def get_top_of_pile(self) -> list[str]:
        return self.pile[:DEFAULT_PILE_SIZE]

    # If too few cards left, shuffle all played cards and add to the end of the pile.
    # Reset all played afterwards as they're now a part of the pile
    def fit_pile_to_size(self):
        if len(self.pile) < 20:
            shuffle(self.all_played)
            self.pile += self.all_played
            self.all_played = []

    def add_played_card(self, card: Card):
        # Played black cards are coloured; when adding them back to the pile, add their original
        # versions
        if card.type_is(CardType.PLUSFOUR):
            self.all_played.append(BLACK_PLUSFOUR_CARD_NAME)
        elif card.type_is(CardType.BLACK):
            self.all_played.append(BLACK_CARD_NAME)
        else:
            self.all_played.append(card.name)
        # Check what the played card was
        if card.type_is(CardType.REVERSE):
            self.reverse_players()

    def update_pile(self, num_taken: int):
        for _ in range(num_taken):
            self.pile.pop(0)
        self.fit_pile_to_size()

    def __str__(self) -> str:
        return str(self.__dict__)
