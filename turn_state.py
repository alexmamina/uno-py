from game_classes import ChallengeReason, GameState
import re
from card import Card, CardType
from typing import Optional
from game_classes import Stage
from message_processor import Message


class TurnState():
    stack_counter: int
    all_nums_of_cards: dict[str, int]
    card_counter: int
    is_reversed: bool
    pile: list[str]
    uno: bool
    hand_cards: dict[int, Card]
    last_played: Card
    game_state: GameState
    cards_taken_previously: bool
    stage: Stage
    why_challenge_in_progress: Optional[ChallengeReason] = None
    current_player: str
    quit_game: bool

    def __init__(
        self,
        stack_counter: int,
        all_nums_of_cards: dict[str, int],
        card_counter: int,
        is_reversed: bool,
        pile: list[str],
        last_played: Card,
        game_state: GameState,
        stage: Stage,
        uno: bool = False,
        quit_game: bool = False,
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
        self.quit_game = quit_game

    @property
    # Go through the hand and see if there are cards that could be played
    def possible_move(self) -> bool:
        for hand_card in self.hand_cards.values():
            is_black = hand_card.type_is(CardType.BLACK)
            same_color = self.last_played.color == hand_card.color
            same_symbol = self.last_played.symbol == hand_card.symbol
            if is_black or same_color or same_symbol:
                return True
        return False

    @property
    def can_put_plusfour(self) -> bool:
        last_played_color = self.last_played.color
        for hand_card in self.hand_cards.values():
            if last_played_color == hand_card.color:  # Color
                return False
        return True

    @property
    def can_stack(self) -> bool:
        for hand_card in self.hand_cards.values():
            if hand_card.type_is(CardType.PLUSTWO):
                return True
        return False

    @property
    def num_cards_left(self) -> int:
        return len(self.hand_cards)

    @property
    def is_current(self) -> bool:
        return self.current_player == self.game_state.identity

    def reverse_direction(self) -> None:
        self.is_reversed = not self.is_reversed

    def remove_card(self, card_index: int) -> None:
        self.hand_cards.pop(card_index)
        self.all_nums_of_cards[self.game_state.identity] -= 1

    def add_card(self, new_card: Card) -> int:
        # Since hand is a dict, the keys aren't in order.
        # Get the largest and add 1 for the next
        ind = max(list(self.hand_cards.keys())) + 1
        # Add new card to the "hand", create new button, update number
        self.hand_cards[ind] = new_card
        self.all_nums_of_cards[self.game_state.identity] += 1
        return ind

    def update_new_turn(self, message: Message) -> None:
        self.stage = message.stage
        self.cards_taken_previously = message.taken
        self.why_challenge_in_progress = message.challenge_reason

    def set_last_played(self, new_card: Card) -> None:
        self.last_played = new_card

    def decrease_counters(self) -> None:
        self.card_counter -= 1
        if self.stack_counter > 0 and self.last_played.type_is(CardType.PLUSTWO):
            # Card.card_is(self.turn_state.last_played, CardType.PLUSFOUR)
            self.stack_counter -= 1

    # Create a hand of 7 cards from pile from message. Return a dict as we want cards to have ids
    def deal_cards(self) -> dict[int, Card]:
        hand = {}
        for i in range(7):
            hand[i] = Card(self.pile.pop(0))
        return hand

    def get_hand_card_names(self) -> list[str]:
        return [card.name for card in self.hand_cards.values()]

    def reset_card_counter(self):
        self.card_counter = 1 if not self.game_state.modes.mult else 500

    def sort_cards(self) -> list[int]:
        # Sort in place
        cards = self.hand_cards
        # Sort in this order of colors
        area_colors = [CardType.RED, CardType.YELLOW, CardType.GREEN, CardType.BLUE, CardType.BLACK]
        resulting_cards = {}
        ctr = 0
        sorted_indices = []
        for area_color in area_colors:
            only_cols = {index: card for (index, card) in cards.items() if area_color in card.name}
            sorted_color_list = sorted(only_cols.items(), key=lambda card: card[1].name)
            # Convert sorted_color_list to dict with new indices from a list of sorted colors
            only_cols_final = {ctr + i: v for (i, (_, v)) in enumerate(sorted_color_list)}
            sorted_indices += [k for (k, _) in sorted_color_list]
            resulting_cards.update(only_cols_final)
            ctr += len(sorted_color_list)
        self.hand_cards = resulting_cards
        return sorted_indices

    # Go through the hand and calculate points; regex is for finding numbers
    def calculate_points(self) -> int:
        result = 0
        for card in self.hand_cards.values():
            c = card.name
            regex_point = re.search(r"\d+", c)
            if regex_point is not None:
                point = int(regex_point.group())
                result += point
            else:
                # non-numbers
                if (card.type_is(CardType.PLUSTWO) or
                    card.type_is(CardType.STOP) or
                        card.type_is(CardType.REVERSE)):
                    result += 20
                else:
                    result += 50
        return result

    def configure_counters_uno_on_start(self, last_played_card: Card, player: str):
        last_played_plus = last_played_card.is_plus
        if not player == self.game_state.identity:
            self.uno = False
        elif last_played_plus and \
                (not self.can_stack or not self.game_state.modes.stack):
            self.card_counter = 2
            self.uno = False
        elif last_played_plus and \
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
            self.hand_cards[i] = Card(c)
        self.all_nums_of_cards[self.game_state.identity] = new_hand_size
        self.all_nums_of_cards[player] = old_hand_size
        return old_hand_size, new_hand_size

    def update_last_played(self, message: Message) -> Card:
        played_card = message.played
        assert played_card is not None
        last_turn_cards_taken = message.taken
        # Set counters based on what the last played card was, or reset if nothing needs to be taken
        if not last_turn_cards_taken:
            if played_card.type_is(CardType.PLUSFOUR):
                self.update_card_counter(4)
            if played_card.type_is(CardType.PLUSTWO):
                self.update_card_counter(2)
                if self.game_state.modes.stack:
                    self.update_stack_counter(message.counter)
        else:
            self.reset_card_counter()
            self.update_stack_counter(0)

        self.last_played = played_card
        if message.pile:
            self.pile = message.pile

        return played_card

    def update_card_counter(self, num_to_take: int):
        self.card_counter = num_to_take

    def update_stack_counter(self, num_to_take: int):
        self.stack_counter = num_to_take

    def set_uno(self, uno_enabled: bool = True):
        self.uno = uno_enabled

    def can_send_points_after_taking(self) -> bool:
        return self.card_counter <= 0 and self.stack_counter == 0 and self.stage == Stage.ZEROCARDS

    def can_send_card_taken_update(self) -> bool:
        empty_counters = self.card_counter <= 0 and self.stack_counter == 0
        new_plus = not self.cards_taken_previously and self.last_played.is_plus
        return empty_counters and \
            (not self.possible_move or new_plus or self.stage == Stage.CHALLENGE)

    def set_quit_game(self):
        self.quit_game = True
