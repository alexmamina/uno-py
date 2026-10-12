import copy
import unittest
from unittest import mock
from unittest.mock import patch
from server_game_data import GameData
from game_classes import Modes, Stage
from card import Card, CardType
from server_session_data import Session, PlayerInfo


class Tests(unittest.TestCase):
    def setUp(self):
        local = ("localhost", 12345)
        self.players = [f"p-{i}" for i in range(3)]
        self.player_info = {p: PlayerInfo(mock.Mock(), local) for p in self.players}
        self.session = Session(
            local,
            3,
            mock.Mock(),
            self.player_info)
        self.modes = Modes(sevenzero=True, mult=True)

    def test_init_first_regular(self):
        custom_deck = [Card("blu1")] * 21 + [Card("red3")]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            actual = GameData(self.session, self.modes, first_game=True)
            self.assertEqual(actual.players, self.players)
            self.assertEqual(actual.player_cards_left, {p: 7 for p in self.players})
            self.assertEqual(actual.current_player, self.players[0])
            self.assertEqual(actual.prev_player, self.players[-1])
            self.assertEqual(actual.modes, Modes(sevenzero=True, mult=True))
            self.assertEqual(actual.stack_counter, 0)
            self.assertEqual(actual.all_played, [])
            self.assertFalse(actual.is_reversed)
            self.assertEqual(actual.first_card, Card("red3"))
            self.assertIsNone(actual.previous_message)

    def test_init_first_reverse(self):
        custom_deck = [Card("blu1")] * 21 + [Card("blureverse")]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            actual = GameData(self.session, self.modes, first_game=True)
            self.players.reverse()
            self.assertEqual(actual.players, self.players)
            self.assertEqual(actual.player_cards_left, {p: 7 for p in self.players})
            self.assertEqual(actual.current_player, self.players[0])
            self.assertEqual(actual.prev_player, self.players[-1])
            self.assertEqual(actual.modes, Modes(sevenzero=True, mult=True))
            self.assertEqual(actual.stack_counter, 0)
            self.assertEqual(actual.all_played, [])
            self.assertTrue(actual.is_reversed)
            self.assertEqual(actual.first_card, Card("blureverse"))
            self.assertIsNone(actual.previous_message)

    def test_init_first_stop(self):

        custom_deck = [Card("blu1")] * 21 + [Card("blustop")]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            actual = GameData(self.session, self.modes, first_game=True)
            self.assertEqual(actual.players, self.players)
            self.assertEqual(actual.player_cards_left, {p: 7 for p in self.players})
            # On start player 0 is first unless the played card is a stop, in which case the current
            # player is 1 instead. Previous player is the one before the one we skipped, so -1
            self.assertEqual(actual.current_player, self.players[1])
            self.assertEqual(actual.prev_player, self.players[-1])
            self.assertEqual(actual.modes, Modes(sevenzero=True, mult=True))
            self.assertEqual(actual.stack_counter, 0)
            self.assertEqual(actual.all_played, [])
            self.assertFalse(actual.is_reversed)
            self.assertEqual(actual.first_card, Card("blustop"))
            self.assertIsNone(actual.previous_message)

    def test_init_consequent_game(self):
        custom_deck = [Card("blu1")] * 21 + [Card("red3")]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            self.session.last_winner = self.players[2]
            self.session.player_points[self.players[2]] = 150
            self.modes = Modes()
            actual = GameData(self.session, self.modes, first_game=False)
            self.assertEqual(actual.players, self.players)
            self.assertEqual(actual.player_cards_left, {p: 7 for p in self.players})
            self.assertEqual(actual.current_player, self.players[0])
            self.assertEqual(actual.prev_player, self.players[-1])
            self.assertEqual(actual.modes, Modes())
            self.assertEqual(actual.stack_counter, 0)
            self.assertEqual(actual.all_played, [])
            self.assertFalse(actual.is_reversed)
            self.assertEqual(actual.first_card, Card("red3"))
            self.assertIsNone(actual.previous_message)

    def test_generate_initial_message(self):

        # First hand is blue, second is red, third is green. The rest is a yellow stop
        # which is the first card + 20 yellows which are the actual rest of the pile
        custom_deck_names = [f"blu{i}" for i in range(1, 8)] + [f"red{i}" for i in range(1, 8)] + \
            [f"gre{i}" for i in range(1, 8)] + ["yelstop"] + ["yel1" for _ in range(20)]
        custom_deck = [Card(n) for n in custom_deck_names]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            data = GameData(self.session, self.modes, first_game=True)
            # Check the message for the 3rd player; we'd have already sent msgs for the first two
            data.pile = data.pile[14:]
            message = data.generate_initial_message(2, self.players[2], len(self.players))
            self.assertEqual(message.stage, Stage.INIT)
            self.assertEqual(
                message.pile,
                [f"gre{i}" for i in range(1, 8)] + ["yel1" for _ in range(20)]
            )
            self.assertEqual(message.played, Card("yelstop"))
            self.assertEqual(message.other_left, {p: 7 for p in self.players})

    def test_add_played_card(self):
        cards_to_add = [Card("red5"), Card("blureverse"), Card("redplusfour"), Card("black")]
        expected_cards = [Card("red5"), Card("blureverse"), Card("blackplusfour"), Card("black")]
        custom_deck_names = [f"blu{i}" for i in range(1, 8)] + [f"red{i}" for i in range(1, 8)] + \
            [f"gre{i}" for i in range(1, 8)] + ["yelstop"] + ["yel1" for _ in range(20)]
        custom_deck = [Card(n) for n in custom_deck_names]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            data = GameData(self.session, self.modes, first_game=True)
            for i, card in enumerate(cards_to_add):
                with self.subTest(card=card):
                    data.add_played_card(card)
                    self.assertEqual(data.all_played, [c.name for c in expected_cards[:i + 1]])
                    if card.type_is(CardType.REVERSE):
                        self.assertEqual(data.players, self.players[::-1])

    def test_update_pile(self):
        custom_deck_names = [f"blu{i}" for i in range(1, 8)] + [f"red{i}" for i in range(1, 8)] + \
            [f"gre{i}" for i in range(1, 8)] + ["yelstop"] + ["yel1" for _ in range(20)]
        custom_deck = [Card(n) for n in custom_deck_names]
        with patch('server_game_data.Deck') as mock_deck:
            mock_deck.return_value.deck = custom_deck
            data = GameData(self.session, self.modes, first_game=True)
            # Override pile with whatever cards we had to fill in some data. 42 cards
            data.pile = copy.deepcopy(custom_deck_names)
            data.all_played = ["blackplusfour"] * 3
            data.update_pile(10)  # 32 remain, > 20
            self.assertEqual(data.pile, custom_deck_names[10:])
            self.assertEqual(data.all_played, ["blackplusfour"] * 3)
            data.update_pile(14)  # 18 remain, < 20
            self.assertEqual(data.all_played, [])
            self.assertIn("blackplusfour", data.pile)  # Pile includes played cards now

# server test
# process and show points if can mock a response. ensure game data correct and session
#   winner/points correct
# swap after seven expect hands to have swapped
# swap after zero expect hands to have swapped
# process regular message updates num left + pile
# process regular message reverse
#  process regular message skip player
# process received challenge updates game data
# process completed challenge updates game data
