from tkinter import Toplevel, Label, TOP, BOTTOM
from tkmacosx import Button as but


class InfoPop(Toplevel):
    def __init__(self, parent, title: str, text: str):
        Toplevel.__init__(self, parent)
        self.title(title)
        self.config(bg="Ivory")
        self.geometry("200x150+%d+%d" % (500, 250))
        self.text = text
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.create_widgets()
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus_set()
        self.focus()
        # wait.window ensures that calling function waits for the window to
        # close before the result is returned.
        # self.wait_window()

    def create_widgets(self):
        # frmL = Frame(self)
        # Label(frmL, text=self.text, font=("TkDefaultFont", 20), bg="Ivory").pack(side=TOP)
        Label(self, text=self.text, font=("TkDefaultFont", 20), bg="Ivory").pack(side=TOP)
        # frmButton = Frame(self)
        btn = but(
            self,
            text="OK",
            width=180,
            height=40,
            bg="light blue",
            command=self.cancel,
            borderless=1
        )
        btn.focus_set()
        self.bind("<Return>", self.cancel)

        btn.pack(side=BOTTOM)

    def cancel(self, *args):
        self.destroy()
