from tkinter import Frame, Button, Tk, Label

from PIL import ImageTk
from deck import Deck
from tkmacosx import Button as but
# import time
import logging
from random import randint

log = logging.getLogger(__name__)


class Img(Frame):
    # Initialise a frame. Setup the pile, hand, last played card and all gui
    def __init__(self, master: Tk):
        log.setLevel(logging.DEBUG)
        format = logging.Formatter("%(asctime)s:%(funcName)s:%(lineno)d:%(levelname)s: %(message)s")
        logging_handler = logging.StreamHandler()
        logging_handler.setFormatter(format)
        log.addHandler(logging_handler)
        super().__init__(master)
        self.deck = Deck()
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.master.destroy)
        # Take one card only
        self.last: Button
        self.challenge = but()
        self.valid_wild: but
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight() - 100
        self.create_buttons()

    def create_buttons(self):
        photo = ImageTk.PhotoImage(self.deck.backofcard)

        # Button to take a card (so a pile)
        self.new_card = Button(
            text="new",
            image=photo,
            width=117,
            height=183,
            border=0,
            command=self.update_chal,
        )
        # print(self.new_card.image)
        print(self.new_card["image"])
        log.info("created buttons")
        log.critical("crit")
        log.error("err")
        log.warning("warn")
        log.debug("debug")
        self.new_card.place(x=10, y=10)

        self.challenge = but(
            text="challenge",
            image=photo,
            width=117,
            height=183,
            border=0,
            command=self.update_new,
        )
        # self.challenge["image"] = photo
        self.challenge.__setitem__("image", photo)
        self.challenge.place(x=200, y=200)
        print("buttons")

        cardback = Label(text="lbl", image=photo, width=80, height=125, border=0)
        cardback["image"] = photo
        # cardback.image = photo
        cardback.place(x=200, y=50)
        print(log.getEffectiveLevel())
        print(log.isEnabledFor(logging.INFO))

    def update_chal(self):  # but
        print("chal")
        photo2 = ImageTk.PhotoImage(self.deck.redplus)
        photo3 = ImageTk.PhotoImage(self.deck.blublack)
        photo4 = ImageTk.PhotoImage(self.deck.greplus)
        ll = [photo2, photo3, photo4]
        i = ll[randint(0, 2)]
        print(str(i))

        self.challenge["image"] = i
        self.challenge.__setitem__("image", i)
        self.update_idletasks()

    def update_new(self):  # Button
        print("new")
        photo2 = ImageTk.PhotoImage(self.deck.redplus)
        photo3 = ImageTk.PhotoImage(self.deck.blublack)
        photo4 = ImageTk.PhotoImage(self.deck.greplus)
        ll = [photo2, photo3, photo4]
        i = ll[randint(0, 2)]
        print(str(i))

        self.new_card["image"] = i
        self.new_card.__setattr__("image", i)

        self.update_idletasks()

    def destroy(self) -> None:
        self.destroy
        super().destroy()


if __name__ == "__main__":

    root = Tk()
    root.geometry("700x553+250+120")
    window = Img(root)
    window.mainloop()
