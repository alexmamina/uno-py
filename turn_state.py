from game_classes import GameState
import re
from card import Card


class TurnState():
    stack_counter: int
    all_nums_of_cards: dict[str, int]
    card_counter: int
    is_reversed: bool
    pile: list[str]
    uno: bool
    hand_cards: dict[int, Card]
    last_played: str

    def __init__(
        self,
        stack_counter: int,
        all_nums_of_cards: dict[str, int],
        card_counter: int,
        is_reversed: bool,
        pile: list[str],
        uno: bool,
        last_played: str,
        game_state: GameState
    ):
        self.stack_counter = stack_counter
        self.all_nums_of_cards = all_nums_of_cards
        self.card_counter = card_counter
        self.is_reversed = is_reversed
        self.pile = pile
        self.uno = uno
        self.hand_cards = self.deal_cards(game_state)
        self.last_played = last_played

    @property
    # Go through the hand and see if there are cards that could be played
    def possible_move(self) -> bool:
        for hand_card in self.hand_cards.values():
            is_black = "bla" in hand_card.name
            same_color = self.last_played[0:3] in hand_card.name
            same_symbol = self.last_played[3:] in hand_card.name
            if is_black or same_color or same_symbol:
                return True
        return False

    @property
    def can_put_plusfour(self) -> bool:
        last_played_color = self.last_played[0:3]
        for hand_card in self.hand_cards.values():
            if last_played_color in hand_card.name:  # Color
                return False
        return True

    @property
    def can_stack(self) -> bool:
        for hand_card in self.hand_cards.values():
            if "two" in hand_card.name:
                return True
        return False

    # Create a hand of 7 cards from pile from message. Return a dict as we want cards to have ids
    def deal_cards(self, game_state: GameState) -> dict[int, Card]:
        hand = {}
        for i in range(7):
            c = self.pile.pop(0)
            # Lookup the card name from pile to get card itself
            card = game_state.deck.get_card(c)
            hand[i] = card
        return hand

    def get_hand_card_names(self) -> list[str]:
        return [card.name for card in self.hand_cards.values()]

    def reset_card_counter(self, game_state: GameState):
        self.card_counter = 1 if not game_state.modes.mult else 500

    # Go through the hand and calculate points; regex is for finding numbers
    def calculate_points(self):
        result = 0
        for card in self.hand_cards.values():
            c = card.name
            regex_point = re.search(r"\d+", c)
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
