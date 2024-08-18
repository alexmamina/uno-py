from tkinter import Toplevel, Frame, Label, Button, Tk
from tkmacosx import Button as ColorfulButton


class Picker(Toplevel):
    def __init__(self, parent: Tk, title: str, question: str, options: list[str]):
        Toplevel.__init__(self, master=parent)
        self.title(title)
        x = parent.winfo_rootx()
        y = parent.winfo_rooty()
        self.geometry("+%d+%d" % (x - 150, y + 150))
        # self.geometry("385x50+%d+%d" % (x - 150, y + 150))
        self.question = question
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.options = options
        self.result = "_"
        self.attributes("-topmost", "true")
        self.create_widgets(title)
        self.grab_set()
        # wait.window ensures that calling function waits for the window to
        # close before the result is returned.
        self.wait_window()

    def create_widgets(self, title: str):
        frm_question = Frame(self)
        Label(frm_question, text=self.question).grid()
        frm_question.grid(row=1)
        frm_buttons = Frame(self)
        frm_buttons.grid(row=2)
        column = 0
        for option in self.options:
            if "color" in title:
                btn = ColorfulButton(
                    frm_buttons,
                    text=option,
                    command=lambda x=option: self.set_option(x),
                    bg=option,
                    borderless=1
                )

            else:
                btn = Button(frm_buttons, text=option, command=lambda x=option: self.set_option(x))
            btn.grid(column=column, row=0)
            column += 1

    def set_option(self, option_selected: str):
        self.result = option_selected
        self.destroy()

    def cancel(self):
        self.result = self.options[0]
        self.destroy()
