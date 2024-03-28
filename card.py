from PIL import Image


class Card():
    def __init__(self, card_pic: Image.Image, name: str):
        self.card_pic = card_pic.resize((117, 183), Image.LANCZOS)
        # The name is contents.png so get rid of the .png part
        self.name = name.split(".")[0]

    def __str__(self) -> str:
        return "Card: " + self.name

    def __repr__(self) -> str:
        return self.name
