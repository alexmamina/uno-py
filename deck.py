from PIL import Image
from card import Card, CardType
from dataclasses import dataclass
from random import shuffle
from os import listdir

CARD_IMAGE_PATH = "Images/Cards/"


@dataclass
class Deck:
    backofcard = Image.open(f"{CARD_IMAGE_PATH}backofcard.jpeg")
    backofcard = backofcard.resize((117, 183), Image.LANCZOS)

    smallback = backofcard.resize((80, 125), Image.LANCZOS)

    # List of all Card objects
    def __init__(self):
        self.deck: list[Card] = []
        files = listdir(f"{CARD_IMAGE_PATH}UNO")
        if len(files) == 0:
            print("No files found")
            return
        for filename in files:
            if not filename.startswith("."):
                new_card = Card(filename)
                self.deck.append(new_card)
                if new_card.card_type != CardType.ZERO:
                    # Non-zero cards appear twice
                    self.deck.append(new_card)
                if new_card.card_type == CardType.BLACK:
                    # Black cards appear 4 times, so add 2 more
                    self.deck.append(new_card)
                    self.deck.append(new_card)

        # Shuffle the deck in place
        shuffle(self.deck)

    def __str__(self) -> str:
        string_like_deck = ""
        for c in self.deck:
            string_like_deck += c.name
            string_like_deck += ", "
        return string_like_deck

    def __repr__(self) -> str:
        proper_str_card = ""
        for c in self.deck:
            proper_str_card += c.name
            proper_str_card += ", "
        return proper_str_card
