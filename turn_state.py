from game_classes import GameState
import re
from card import Card
from typing import Any, Optional
from game_classes import Stage


class TurnState():
    stack_counter: int
    all_nums_of_cards: dict[str, int]
    card_counter: int
    is_reversed: bool
    pile: list[str]
    uno: bool
    hand_cards: dict[int, Card]
    last_played: str
    game_state: GameState
    cards_taken_previously: bool
    stage: Stage
    why_challenge_in_progress: Optional[int]

    def __init__(
        self,
        stack_counter: int,
        all_nums_of_cards: dict[str, int],
        card_counter: int,
        is_reversed: bool,
        pile: list[str],
        uno: bool,
        last_played: str,
        game_state: GameState,
        stage: Stage
    ):
        self.stack_counter = stack_counter
        self.all_nums_of_cards = all_nums_of_cards
        self.card_counter = card_counter
        self.is_reversed = is_reversed
        self.pile = pile
        self.uno = uno
        self.game_state = game_state
        self.hand_cards = self.deal_cards()
        self.last_played = last_played
        self.cards_taken_previously = False
        self.stage = stage

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

    @property
    def num_cards_left(self) -> int:
        return len(self.hand_cards)

    # Create a hand of 7 cards from pile from message. Return a dict as we want cards to have ids
    def deal_cards(self) -> dict[int, Card]:
        hand = {}
        for i in range(7):
            c = self.pile.pop(0)
            # Lookup the card name from pile to get card itself
            card = self.game_state.deck.get_card(c)
            hand[i] = card
        return hand

    def get_hand_card_names(self) -> list[str]:
        return [card.name for card in self.hand_cards.values()]

    def reset_card_counter(self):
        self.card_counter = 1 if not self.game_state.modes.mult else 500

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

    def configure_counters_uno_on_start(self, last_played_card: str, player: str):
        if not player:
            self.uno = False
        elif "plus" in last_played_card and \
                (not self.can_stack or not self.game_state.modes.stack):
            self.card_counter = 2
            self.uno = False
        elif "plus" in last_played_card and \
                self.game_state.modes.stack and self.can_stack:
            self.stack_counter = 2
            self.card_counter = 2

    # Save the new hand as the current one and update the numbers of cards per player after swap
    def replace_cards_after_swap(self, new_hand: list[str], player: str) -> tuple[int, int]:
        old_hand_size = len(self.hand_cards)
        new_hand_size = len(new_hand)
        self.hand_cards = {}
        for i in range(len(new_hand)):
            # Add new card
            c = new_hand[i]
            self.hand_cards[i] = self.game_state.deck.get_card(c)
        self.all_nums_of_cards[self.game_state.identity] = new_hand_size
        self.all_nums_of_cards[player] = old_hand_size
        return old_hand_size, new_hand_size

    def update_last_played(self, message: dict[str, Any]) -> str:
        played_card = message["played"]
        # if plus take cards else send points
        if "four" in played_card:
            played_card = message["color"][0:3] + "plusfour"
            if "taken" not in message:
                self.card_counter = 4
            else:
                self.reset_card_counter()
        elif "bla" in played_card:
            played_card = message["color"][0:3] + "black"
        else:
            self.reset_card_counter()
        self.last_played = played_card
        if "pile" in message.keys():
            self.pile = message["pile"]
        return played_card

    def update_card_counter(self, num_to_take: int):
        self.card_counter = num_to_take

    def update_stack_counter(self, num_to_take: int):
        self.stack_counter = num_to_take

    def set_uno(self, uno_enabled: bool = True):
        self.uno = uno_enabled
