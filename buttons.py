from tkinter import Button, Frame
from PIL import ImageTk, Image
from typing import Callable, Optional
from card import Card
from tkmacosx import Button as ColorButton

DEFAULT_WIDTH = 117
DEFAULT_HEIGHT = 183


class CardButton(Button):
    def coords(self) -> tuple[int, int]:
        return self.winfo_x(), self.winfo_y()

    def set_enabled(self, yes: bool = True):
        state = "normal" if yes else "disabled"
        self.config(state=state)


class HandCardButton(CardButton):
    def __init__(
        self,
        card: Card,
        index: int,
        method: Callable,
        parent_frame: Frame,
        bg: str = "",
        enabled: bool = True,
    ):
        image = ImageTk.PhotoImage(card.card_pic)
        super().__init__(
            master=parent_frame,
            text=card.name,
            image=image,
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            border=0,
            # pady=0,
            # padx=0,
            bg=bg,
        )
        self.card = card
        self.set_command(method, index)
        self.set_enabled(enabled)
        # Need an extra command as otherwise there's no image
        self.__setattr__("image", image)

    def set_command(self, method: Callable, index: int):
        self["command"] = lambda ind=index, binst=self: method(ind, binst)


class PileButton(CardButton):
    def __init__(self, card: Card, parent_frame: Frame):
        image = ImageTk.PhotoImage(card.card_pic)
        super().__init__(
            master=parent_frame,
            text=card.name,
            image=image,
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            border=0,
            state="disabled",
        )
        # Need an extra command as otherwise there's no image
        self.__setattr__("image", image)

    def update_card(self, card: Card):
        image = ImageTk.PhotoImage(card.card_pic)
        self["image"] = image
        self.__setattr__("image", image)
        self["text"] = card.name

    def get_image(self) -> ImageTk.PhotoImage:
        return self["image"]


class TakeCardButton(CardButton):
    def __init__(self, image: Image.Image, method: Callable, parent_frame: Frame):
        photo_image = ImageTk.PhotoImage(image)
        super().__init__(
            parent_frame,
            image=photo_image,
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            border=0,
        )
        self.set_command(method)
        # Need an extra command as otherwise there's no image
        self.__setattr__("image", photo_image)

    def set_command(self, method: Callable):
        self["command"] = method


class ColorfulButton(ColorButton):
    def __init__(
        self,
        parent_frame: Optional[Frame] = None,
        text: str = "",
        fg: str = "",
        bg: str = "",
        width: int = 0,
        height: int = 0,
        command: Callable = ...,
    ):
        if not text:
            super().__init__()
            return
        super().__init__(
            master=parent_frame,
            text=text,
            fg=fg,
            bg=bg,
            width=width,
            height=height,
            borderless=1,
            borderwidth=0,
            border=0,
            command=command,
        )
