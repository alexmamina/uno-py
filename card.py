from PIL import Image
from dataclasses import dataclass
from os import listdir

CARD_IMAGE_PATH = "Images/Cards/"
SPECIAL_FOLDER = "Special"
CARD_FOLDER = "UNO"


@dataclass
class CardType:
    BLACK = "bla"
    PLUS = "plus"
    PLUSTWO = "plustwo"
    PLUSFOUR = "plusfour"
    REVERSE = "reverse"
    STOP = "stop"
    SEVEN = "7"
    ZERO = "0"

    ALL = [BLACK, PLUSTWO, PLUSFOUR, REVERSE, STOP, SEVEN, ZERO]

    @classmethod
    def get_type(cls, card_name: str) -> str:
        for type in cls.ALL:
            if type in card_name:
                return type
        return ""


class Card:
    card_pic: Image.Image
    name: str
    card_type: str

    def __init__(self, name: str):
        special = Card.is_special(name)
        if special:
            folder = SPECIAL_FOLDER
            extension = ".jpeg"
        else:
            folder = CARD_FOLDER
            extension = ".png"
        # The name is either the file name, or just the card name. Process accordingly
        if "." in name:
            filename = name
            self.name = name.split(".")[0]
        else:
            filename = name + extension
            self.name = name
        card_pic = Image.open(f"{CARD_IMAGE_PATH}{folder}/" + filename)
        self.card_pic = card_pic.resize((117, 183), Image.LANCZOS)
        self.card_type = CardType.get_type(name)

    def __str__(self) -> str:
        return "Card: " + self.name

    def __repr__(self) -> str:
        return self.name

    # We have a plustwo or a plusfour, both of which are also plus.
    # Black is assigned first as a type, so this is an additional check
    def is_plus(self) -> bool:
        return CardType.PLUS in self.name

    def type_is(self, type: str) -> bool:
        if type == CardType.PLUSFOUR:
            return self.card_type == CardType.BLACK and self.is_plus()
        return self.card_type == type

    @classmethod
    def is_special(cls, name: str) -> bool:
        # If an image with this name exists in the special folder, it's a special card
        # Assume all special cards are jpegs
        files = listdir(f"{CARD_IMAGE_PATH}{SPECIAL_FOLDER}")
        return f"{name}.jpeg" in files
