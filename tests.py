import unittest
from tkinter import Tk
from game_classes import Modes
from deck import Deck
from socket import socket
from gameanim import Game
from logging import Logger


def get_modes(mode_string: str) -> Modes:
    modes = Modes(
        sevenzero="1" in mode_string, stack="2" in mode_string, mult="3" in mode_string
    )
    return modes


class FakeGame:
    d = Deck().deck
    hand_cards = {
        i: Deck().get_card(v)
        for i, v in enumerate(
            ["gre8", "blackplusfour", "blu5", "blu2", "gre5", "yel6", "yel2"]
        )
    }
    # hand_cards = {i: v for i, v in enumerate(d[:7])}
    last_played: str


def possible_move(self) -> bool:
    for hand_card in self.hand_cards.values():
        is_black = "bla" in hand_card.name
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
        if "two" in hand_card.name:
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
            "color": "gre",
            "player": True,
            "peeps": ["default-925", "one"],
            "dir": False,
            "whoami": "one",
            "padding": "a",
        }
        a: dict[str, int] = {p: 0 for p in m["peeps"]}
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
                print(args)
                self.assertEqual(modes, ttest_modes, args)
                self.assertEqual(text, ttest_text)

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
        self.game.turn_state.hand_cards[10] = self.game.game_state.deck.get_card("black")
        self.assertTrue(self.game.turn_state.possible_move)
        self.game.turn_state.hand_cards.pop(10)

    def test_no_possible_move(self):
        self.game.turn_state.last_played = "blu7"
        self.assertFalse(self.game.turn_state.possible_move)

    def test_can_plusfour(self):
        self.game.turn_state.last_played = "blu6"
        self.game.turn_state.hand_cards[10] = self.game.game_state.deck.get_card("blackplusfour")
        self.assertTrue(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)

    def test_cannot_plusfour_color(self):
        self.game.turn_state.last_played = "gre1"
        self.game.turn_state.hand_cards[10] = self.game.game_state.deck.get_card("blackplusfour")
        self.assertFalse(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)

    def test_can_plusfour_number_black(self):
        self.game.turn_state.last_played = "blu2"
        self.game.turn_state.hand_cards[10] = self.game.game_state.deck.get_card("blackplusfour")
        self.game.turn_state.hand_cards[11] = self.game.game_state.deck.get_card("black")
        self.assertTrue(self.game.turn_state.can_put_plusfour)
        self.game.turn_state.hand_cards.pop(10)
        self.game.turn_state.hand_cards.pop(11)

    def test_can_put_plustwo(self):
        self.game.turn_state.last_played = "redplustwo"
        self.game.turn_state.hand_cards[12] = self.game.game_state.deck.get_card("greplustwo")
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
        if not self.game.message["player"]:
            new_card_1 = False
            for i in hand_btns_1:
                hand_btns_1[i] = (False, "b")
        elif "plus" in self.game.message["played"] and (
            not self.game.turn_state.can_stack or not self.game.game_state.modes.stack
        ):
            for i in hand_btns_1:
                hand_btns_1[i] = (False, "b")
        elif (
            "plus" in self.game.message["played"] and
            self.game.game_state.modes.stack and
            self.game.turn_state.can_stack
        ):
            for i in hand_btns_1:
                if "two" not in hand_btns_1[i][1]:
                    hand_btns_1[i] = (False, "two")
        elif self.game.turn_state.possible_move:
            new_card_1 = False
        not_current = not self.game.message["player"]
        played_plus = "plus" in self.game.message["played"]
        no_stack = not self.game.turn_state.can_stack or not self.game.game_state.modes.stack
        stack_possible = self.game.game_state.modes.stack and self.game.turn_state.can_stack
        if not_current or self.game.turn_state.possible_move:
            new_card_2 = False
        if not_current or (no_stack and played_plus):
            for i in hand_btns_2:
                hand_btns_2[i] = (False, "b")
        if stack_possible and played_plus:
            for i in hand_btns_2:
                if "two" not in hand_btns_2[i][1]:
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
        print(self.current_player, self.curr_list_index, self.prev_player)

        for i in self.list_of_players:
            # Get the first 7 cards + the pile of twenty that comes after everyone has taken
            # (7*numplayers)
            data_to_send_1["pile"] = self.pile[0:7] + \
                self.pile[7 * (self.num_players - i):7 * (self.num_players - i) + 20]
            data_to_send_1["whoami"] = i
            # if (i == self.list_of_players[0] and "stop" not in self.first_card) or \
            #         (i == 1 and "stop" in self.first_card):
            #     data_to_send["player"] = 1
            #     self.current_player = i
            #     self.curr_list_index = 1 if (i == 1 and "stop" in self.first_card) else 0
            #     self.prev_player = self.list_of_players[self.num_players - 1]
            # else:
            #     data_to_send["player"] = 0
            #     # Only on the first game start from player 0 and consider stop
            #     # refactor: why
            #     if i == self.list_of_players[0] and "stop" in self.first_card and first_game:
            #         data_to_send["curr"] = (self.current_player + 1) % self.num_players
            #     else:
            #         data_to_send["curr"] = self.current_player
            data_to_send_1["player"] = i == self.current_player
            data_to_send_1["curr"] = self.current_player
            self.pile = self.pile[7:]

        self.pile = ["blu5"] * 50
        for i in self.list_of_players:
            # Get the first 7 cards + the pile of twenty that comes after everyone has taken
            # (7*numplayers)
            data_to_send_2["pile"] = self.pile[0:7] + \
                self.pile[7 * (self.num_players - i):7 * (self.num_players - i) + 20]
            data_to_send_2["whoami"] = i
            if (i == self.list_of_players[0] and "stop" not in self.first_card) or \
                    (i == 1 and "stop" in self.first_card):
                data_to_send_2["player"] = True
                self.current_player = i
                self.curr_list_index = 1 if (i == 1 and "stop" in self.first_card) else 0
                self.prev_player = self.list_of_players[self.num_players - 1]
            else:
                data_to_send_2["player"] = False
                # Only on the first game start from player 0 and consider stop
                # refactor: why
                if i == self.list_of_players[0] and "stop" in self.first_card and first_game:
                    data_to_send_2["curr"] = (self.current_player + 1) % self.num_players
                else:
                    data_to_send_2["curr"] = self.current_player

            self.pile = self.pile[7:]
        self.assertEqual(data_to_send_1, data_to_send_2)

    def get_player_order(self, list_of_players: list[int], first_card: str) -> tuple[int, int, int]:
        # list of players. either reversed or not. either normal card, or stop. on normal, first
        # is current, last is prev. on stop second is current, first is prev
        first_stop = "stop" in first_card
        current_player = list_of_players[1] if first_stop else list_of_players[0]
        curr_list_index = list_of_players.index(current_player)
        prev_player = list_of_players[(curr_list_index - 1) % len(list_of_players)]
        return current_player, curr_list_index, prev_player


if __name__ == "__main__":
    unittest.main()
