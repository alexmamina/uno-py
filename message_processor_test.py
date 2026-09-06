import unittest
from game_classes import Stage
from message_processor import Message
from card import Card
from typing import Any
import json


class Tests(unittest.TestCase):

    def test_skip_empty_fields(self):
        msg = Message(
            stage=Stage.INIT,
            current_player="me",
            padding="a",
            played=Card("blu1"),
            players=["me", "someone else"],
        )
        json_blob = msg.to_json()
        try:
            encoded = json.dumps(json_blob)
        except Exception:
            self.fail("Could not encode message")
        try:
            decoded: dict[str, Any] = json.loads(encoded)
        except Exception:
            self.fail("Could not decode message")
        final_message = Message.from_dict(decoded)
        expected_message = Message(
            stage=Stage.INIT,
            current_player="me",
            padding="a",
            played=Card("blu1"),
            players=["me", "someone else"]
        )
        self.assertEqual(
            final_message,
            expected_message,
            f"{final_message} is different from {expected_message}"
        )
