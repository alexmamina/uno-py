from tkinter import Frame as TFrame, Label as TLabel
from PIL import ImageTk
from typing import Any, Optional


class Frame(TFrame):
    def __init__(
            self,
            parent: Any = None,
            width: float = 0,
            height: float = 0,
            bg: str = "white",
            border_width: int = 1,
            border_color: str = "black"
    ):
        super().__init__(
            master=parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=border_width,
            highlightbackground=border_color
        )

    @property
    def width(self):
        return self["width"]

    @property
    def height(self):
        return self["height"]

    def set_color(self, color: str):
        self.config(bg=color)


class Label(TLabel):
    def __init__(
            self,
            parent: Any = None,
            text: str = "",
            fg: str = "black",
            bg: str = "white",
            image: Optional[ImageTk.PhotoImage] = None,
            width: int = 0,
            height: int = 0,
            font: tuple[str, int] = ("TkDefaultFont", 15),
    ):
        super().__init__(
            master=parent,
            text=text,
            fg=fg,
            bg=bg,
            width=width,
            height=height,
            font=font,
            border=0,
        )
        if image:
            self.set_image(image)

    def set_image(self, image: ImageTk.PhotoImage):
        self.image = image
        self["image"] = image
        self.__setattr__("image", image)

    # .config does things fine by itself?
    # def config(self, **kwargs):
    #     pass
