from PIL import Image
from card import Card
from dataclasses import dataclass
from random import shuffle
from os import listdir

CARD_IMAGE_PATH = "Images/Cards/"


@dataclass
class Deck:
    # backofcard: Image.Image
    # special_blacks: dict[str, Image.Image]
    # smallback: Image.Image

    backofcard = Image.open(f"{CARD_IMAGE_PATH}backofcard.jpg")
    backofcard = backofcard.resize((117, 183), Image.LANCZOS)

    smallback = backofcard.resize((80, 125), Image.LANCZOS)

    redplus = Image.open(f"{CARD_IMAGE_PATH}redplusfour.jpeg")
    redplus = redplus.resize((117, 183), Image.LANCZOS)
    redblack = Image.open(f"{CARD_IMAGE_PATH}redblack.jpeg")
    redblack = redblack.resize((117, 183), Image.LANCZOS)
    bluplus = Image.open(f"{CARD_IMAGE_PATH}bluplusfour.jpeg")
    bluplus = bluplus.resize((117, 183), Image.LANCZOS)
    blublack = Image.open(f"{CARD_IMAGE_PATH}blublack.jpeg")
    blublack = blublack.resize((117, 183), Image.LANCZOS)
    greplus = Image.open(f"{CARD_IMAGE_PATH}greplusfour.jpeg")
    greplus = greplus.resize((117, 183), Image.LANCZOS)
    greblack = Image.open(f"{CARD_IMAGE_PATH}greblack.jpeg")
    greblack = greblack.resize((117, 183), Image.LANCZOS)
    yelplus = Image.open(f"{CARD_IMAGE_PATH}yelplusfour.jpeg")
    yelplus = yelplus.resize((117, 183), Image.LANCZOS)
    yelblack = Image.open(f"{CARD_IMAGE_PATH}yelblack.jpeg")
    yelblack = yelblack.resize((117, 183), Image.LANCZOS)

    special_blacks = {
        "redplus": redplus, "greplus": greplus, "bluplus": bluplus,
        "yelplus": yelplus, "redblack": redblack, "blublack": blublack,
        "yelblack": yelblack, "greblack": greblack
    }

    # List of all Card objects
    def __init__(self):
        self.deck: list[Card] = []
        files = listdir(f"{CARD_IMAGE_PATH}UNO")
        if len(files) == 0:
            print("No files found")
            return
        for filename in files:
            if (filename != ".DS_Store") and (filename != ".idea"):
                card_pic = Image.open(f"{CARD_IMAGE_PATH}UNO/" + filename)
                new_card = Card(card_pic, filename)
                self.deck.append(new_card)
                if "0" not in filename:
                    # Non-zero cards appear twice
                    self.deck.append(new_card)
                if "black" in filename:
                    # Black cards appear 4 times, so add 2 more
                    self.deck.append(new_card)
                    self.deck.append(new_card)
        # Shuffle the deck in place
        shuffle(self.deck)

    def get_card(self, name: str) -> Card:
        for c in self.deck:
            if c.name == name:
                return c
        # Return an empty card if no matches
        return Card(Image.Image(), "")

    def get_special(self, name: str) -> Image.Image:
        for i in self.special_blacks:
            if i in name:
                return self.special_blacks[i]
        return Image.Image()

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
