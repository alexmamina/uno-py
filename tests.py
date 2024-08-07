import unittest
from tkinter import Tk
from game_classes import Modes
from deck import Deck
from socket import socket
from gameanim import Game
from logging import Logger
from card import Card, CardType
from utils import get_next_player, get_prev_player


def get_modes(mode_string: str) -> Modes:
    modes = Modes(
        sevenzero="1" in mode_string, stack="2" in mode_string, mult="3" in mode_string
    )
    return modes


class FakeGame:
    d = Deck().deck
    hand_cards = {
        i: Card(v)
        for i, v in enumerate(
            ["gre8", "blackplusfour", "blu5", "blu2", "gre5", "yel6", "yel2"]
        )
    }
    # hand_cards = {i: v for i, v in enumerate(d[:7])}
    last_played: str


def possible_move(self) -> bool:
    for hand_card in self.hand_cards.values():
        is_black = hand_card.type_is(CardType.BLACK)
        same_color = self.last_played[0:3] in hand_card.name
        same_symbol = self.last_played[3:] in hand_card.name
        if is_black or same_color or same_symbol:
            return True
    return False


# Non-UI settings
def can_put_plusfour(self) -> bool:
    last_played_color = self.last_played[0:3]
    for hand_card in self.hand_cards.values():
        if last_played_color in hand_card.name:  # Color
            return False
    return True


# Non-UI settings
def can_stack(self) -> bool:
    for hand_card in self.hand_cards.values():
        if hand_card.type_is(CardType.PLUSTWO):
            return True
    return False


class Tests(unittest.TestCase):

    all_args = ["0", "1", "2", "3", "12", "13", "23", "123"]

    @classmethod
    def setUpClass(cls) -> None:
        m = {
            "stage": -1,
            "modes": {"7/0": False, "Stacking": True, "Taking multiple cards": True},
            "played": "gre0",
            "pile": [
                "gre2",
                "redstop",
                "gre3",
                "red8",
                "yel4",
                "red5",
                "yel3"
            ],
            "num_left": 7,
            "other_left": {x: 7 for x in ["default-925", "one"]},
            "player": "default-925",
            "peeps": ["default-925", "one"],
            "dir": False,
            "whoami": "one",
            "padding": "a",
        }
        a: dict[str, int] = {p: 0 for p in m["peeps"]}
        cls.m = m
        cls.game = Game(Tk(), None, m, socket(), a, Logger(__name__))

    @unittest.skip("modes too old")
    def test_pretty_modes(self):
        # Get modes
        # [0] = 7/0, [1] = stack, [2] = take forever

        for args in self.all_args:
            modes = [False] * 3
            text = []
            ttest_modes = [False] * 3
            ttest_text = []
            with self.subTest(params=args, msg=str(args)):
                if "0" not in args:
                    modes[0] = "1" in args
                    if modes[0]:
                        text.append("7/0 enabled")
                    modes[1] = "2" in args
                    if modes[1]:
                        text.append("Stacking enabled")
                    modes[2] = "3" in args
                    if modes[2]:
                        text.append("Taking many cards enabled")

                    mode_types = ["7/0", "Stacking", "Taking many cards"]
                    for i in range(1, 4):
                        ttest_modes[i - 1] = str(i) in args
                        if str(i) in args:
                            ttest_text.append(f"{mode_types[i - 1]} enabled")
                self.assertEqual(modes, ttest_modes, args)
                self.assertEqual(text, ttest_text)

    def test_card_type(self):
        import random
        cards = [
            "red5", "blureverse", "greplustwo",
            "yelstop", "black", "blackplusfour", "yelblack",
            "bluplusfour", "greblack", "yelplusfour"]
        for _ in range(200):
            for type in [CardType.BLACK,
                         CardType.PLUSFOUR, CardType.PLUSTWO, CardType.REVERSE,
                         CardType.STOP]:
                card = cards[random.randint(0, len(cards) - 1)]
                with self.subTest(params=type, msg=f"{type} - {card}"):

                    self.assertEqual(
                        Card(card).type_is(type), type in card
                    )

    def test_sort_cards(self):
        cards = [
            "red5", "red4", "blureverse", "greplustwo",
            "yelstop", "black", "blackplusfour", "black",
            "blustop", "gre0", "yel6", "yelreverse"]
        self.game.turn_state.hand_cards = {i: Card(card) for i, card in enumerate(cards)}
        indices = self.game.turn_state.sort_cards()
        solution = {0: Card("red4"), 1: Card("red5"), 2: Card("yel6"), 3: Card("yelreverse"),
                    4: Card("yelstop"), 5: Card("gre0"), 6: Card("greplustwo"),
                    7: Card("blureverse"), 8: Card("blustop"), 9: Card("black"), 10: Card("black"),
                    11: Card("blackplusfour")}
        sol_indices = [1, 0, 10, 11, 4, 9, 3, 2, 8, 5, 7, 6]
        self.assertEqual(self.game.turn_state.hand_cards, solution)
        self.assertEqual(indices, sol_indices)

    @unittest.skip("too general test")
    def test_mode_class(self):
        for args in self.all_args:
            with self.subTest(params=args, msg=str(args)):
                text = []
                modes = [False] * 3
                if "0" not in args:
                    modes[0] = "1" in args
                    if modes[0]:
                        text.append("7/0")
                    modes[1] = "2" in args
                    if modes[1]:
                        text.append("Stacking")
                    modes[2] = "3" in args
                    if modes[2]:
                        text.append("Taking multiple cards")
                modes = get_modes(args)
                strlist = modes.enabled_strings()

                self.assertEqual(strlist, text)

    def test_game_modes(self):
        actual_strings = ["Stacking", "Taking multiple cards"]
        self.assertEqual(actual_strings, self.game.game_state.modes.enabled_strings())

    def test_possible_move_color(self):
        self.game.turn_state.last_played = "gre0"
        self.assertTrue(self.game.turn_state.possible_move)

    def test_possible_move_number(self):
        self.game.turn_state.last_played = "blu5"
        self.assertTrue(self.game.turn_state.possible_move)

    def test_possible_move_black(self):
        self.game.turn_state.hand_cards[10] = Card("black")
        self.assertTrue(self.game.turn_state.possible_move)
        self.game.turn_state.hand_cards.pop(10)

    def test_no_possible_move(self):
        self.game.turn_state.last_played = "blu7"
        self.assertFalse(self.game.turn_state.possible_move)

    def test_can_plusfour(self):
        self.game.turn_state.last_played = "blu6"
        self.game.turn_state.hand_cards[10] = Card("blackplusfour")
        self.assertTrue(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)

    def test_cannot_plusfour_color(self):
        self.game.turn_state.last_played = "gre1"
        self.game.turn_state.hand_cards[10] = Card("blackplusfour")
        self.assertFalse(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)

    def test_can_plusfour_number_black(self):
        self.game.turn_state.last_played = "blu2"
        self.game.turn_state.hand_cards[10] = Card("blackplusfour")
        self.game.turn_state.hand_cards[11] = Card("black")
        self.assertTrue(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)
        self.game.turn_state.hand_cards.pop(11)

    def test_can_put_plustwo(self):
        self.game.turn_state.last_played = "redplustwo"
        self.game.turn_state.hand_cards[12] = Card("greplustwo")
        self.assertTrue(self.game.turn_state.possible_move)
        self.game.turn_state.hand_cards.pop(12)

    @unittest.skip("stashed")
    def test_config_start(self):
        # self.game.message["player"] = 0
        self.game.turn_state.last_played = "yelplustwo"
        # self.game.pile.append("yelplustwo")
        # self.game.game_state.modes = Modes()
        new_card_1 = True
        hand_btns_1: dict[int, tuple[bool, str]]
        hand_btns_2: dict[int, tuple[bool, str]]
        hand_btns_1 = {i: (True, "a") for i in range(7)}
        hand_btns_1[3] = (True, "two")
        new_card_2 = True
        hand_btns_2 = {i: (True, "a") for i in range(7)}
        hand_btns_2[3] = (True, "two")
        if Tests.m["player"] != self.game.game_state.identity:
            new_card_1 = False
            for i in hand_btns_1:
                hand_btns_1[i] = (False, "b")
        elif Card(self.game.turn_state.last_played).is_plus() and (
            not self.game.turn_state.can_stack or not self.game.game_state.modes.stack
        ):
            for i in hand_btns_1:
                hand_btns_1[i] = (False, "b")
        elif (
            Card(self.game.turn_state.last_played).is_plus() and
            self.game.game_state.modes.stack and
            self.game.turn_state.can_stack
        ):
            for i in hand_btns_1:
                if not Card(hand_btns_1[i][1]).type_is(CardType.PLUSTWO):
                    hand_btns_1[i] = (False, "two")
        elif self.game.turn_state.possible_move:
            new_card_1 = False
        not_current = Tests.m["player"] != self.game.game_state.identity
        played_plus = Card(self.game.turn_state.last_played).is_plus()
        no_stack = not self.game.turn_state.can_stack or not self.game.game_state.modes.stack
        stack_possible = self.game.game_state.modes.stack and self.game.turn_state.can_stack
        if not_current or self.game.turn_state.possible_move:
            new_card_2 = False
        if not_current or (no_stack and played_plus):
            for i in hand_btns_2:
                hand_btns_2[i] = (False, "b")
        if stack_possible and played_plus:
            for i in hand_btns_2:
                if not Card(hand_btns_2[i][1]).type_is(CardType.PLUSTWO):
                    hand_btns_2[i] = (False, "two")
        self.assertEqual(new_card_1, new_card_2)
        self.assertEqual(hand_btns_1, hand_btns_2)

    def test_init_msg(self):
        data_to_send_1 = {}
        data_to_send_2 = {}
        self.pile = ["blu5"] * 50
        self.num_players = 3
        self.list_of_players = [0, 1, 2]
        self.first_card = "red5"
        # self.first_card = "yelstop"
        # self.first_card = "blureverse"
        first_game = True

        self.current_player, self.curr_list_index, self.prev_player = self.get_player_order(
            self.list_of_players, self.first_card
        )

        for i in self.list_of_players:
            # Get the first 7 cards + the pile of twenty that comes after everyone has taken
            # (7*numplayers)
            data_to_send_1["pile"] = self.pile[0:7] + \
                self.pile[7 * (self.num_players - i):7 * (self.num_players - i) + 20]
            data_to_send_1["whoami"] = i
            data_to_send_1["player"] = self.current_player
            self.pile = self.pile[7:]

        self.pile = ["blu5"] * 50
        for i in self.list_of_players:
            # Get the first 7 cards + the pile of twenty that comes after everyone has taken
            # (7*numplayers)
            data_to_send_2["pile"] = self.pile[0:7] + \
                self.pile[7 * (self.num_players - i):7 * (self.num_players - i) + 20]
            data_to_send_2["whoami"] = i
            if (i == self.list_of_players[0] and
                not Card(self.first_card).type_is(CardType.STOP)) or \
                    (i == 1 and Card(self.first_card).type_is(CardType.STOP)):
                data_to_send_2["player"] = i
                self.current_player = i
                self.curr_list_index = \
                    1 if (i == 1 and Card(self.first_card).type_is(CardType.STOP)) else 0
                self.prev_player = self.list_of_players[self.num_players - 1]
            else:
                # Only on the first game start from player 0 and consider stop
                if i == self.list_of_players[0] and \
                        Card(self.first_card).type_is(CardType.STOP) and first_game:
                    data_to_send_2["player"] = (self.current_player + 1) % self.num_players
                else:
                    data_to_send_2["player"] = self.current_player

            self.pile = self.pile[7:]
        self.assertEqual(data_to_send_1, data_to_send_2)

    def get_player_order(self, list_of_players: list[int], first_card: str) -> tuple[int, int, int]:
        # list of players. either reversed or not. either normal card, or stop. on normal, first
        # is current, last is prev. on stop second is current, first is prev
        first_stop = Card(first_card).type_is(CardType.STOP)
        current_player = list_of_players[1] if first_stop else list_of_players[0]
        curr_list_index = list_of_players.index(current_player)
        prev_player = list_of_players[(curr_list_index - 1) % len(list_of_players)]
        return current_player, curr_list_index, prev_player

    def test_next_player_forward_4(self):
        played_cards = ["redstop", "bluplustwo", "blu5"]
        solution = {
            "0": ["2", "1", "1"],
            "1": ["3", "2", "2"],
            "2": ["0", "3", "3"],
            "3": ["1", "0", "0"]
        }
        # for num_players in range(2, 5):
        players = [str(x) for x in range(4)]
        for current_player in players:
            for card in played_cards:
                with self.subTest(f"{current_player} played {card}"):
                    next = get_next_player(current_player, players, card)
                    proper_next = solution[current_player][played_cards.index(card)]
                    self.assertEqual(next, proper_next)

    def test_next_player_forward_2(self):
        played_cards = ["redstop", "bluplustwo", "blu5"]
        solution = {
            "0": ["0", "1", "1"],
            "1": ["1", "0", "0"],
        }
        # for num_players in range(2, 5):
        players = [str(x) for x in range(2)]
        for current_player in players:
            for card in played_cards:
                with self.subTest(f"{current_player} played {card}"):
                    next = get_next_player(current_player, players, card)
                    proper_next = solution[current_player][played_cards.index(card)]
                    self.assertEqual(next, proper_next)

    def test_prev_player_forward_2(self):
        played_cards = ["redstop", "bluplustwo", "blu5"]
        solution = {
            "0": ["0", "1", "1"],
            "1": ["1", "0", "0"],
        }
        players = [str(x) for x in range(2)]
        for current_player in players:
            for card in played_cards:
                with self.subTest(f"{current_player} has to follow up {card}"):
                    next = get_prev_player(current_player, players, card)
                    proper_next = solution[current_player][played_cards.index(card)]
                    self.assertEqual(next, proper_next)

    def test_prev_player_forward_4(self):
        played_cards = ["redstop", "bluplustwo", "blu5"]
        solution = {
            "0": ["2", "3", "3"],
            "1": ["3", "0", "0"],
            "2": ["0", "1", "1"],
            "3": ["1", "2", "2"]
        }
        # for num_players in range(2, 5):
        players = [str(x) for x in range(4)]
        for current_player in players:
            for card in played_cards:
                with self.subTest(f"{current_player} has to follow up {card}"):
                    next = get_prev_player(current_player, players, card)
                    proper_next = solution[current_player][played_cards.index(card)]
                    self.assertEqual(next, proper_next)


if __name__ == "__main__":
    unittest.main()
