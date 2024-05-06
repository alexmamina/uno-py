from tkinter import Tk
from socket import socket, AF_INET, SOCK_STREAM
import json
from json import JSONDecodeError
from threading import Thread
import queue
import logging
import sys
from logmanager import setup_logger
# from player import Player
import gameanim
from random import randint
from tkinter.simpledialog import askstring
import argparse
import utils

parser = argparse.ArgumentParser(
    usage="No flags - play multiplayer. Add flags to play alone (temporarily deprecated)"
)
parser.add_argument("--sentient", action="store_true",
                    help="add this flag to start a robot's side client")
parser.add_argument("--human", type=str,
                    help="use this flag followed by your name to start a game against a robot")

log = logging.getLogger(__name__)


def get_player_info(conditions: argparse.Namespace) -> tuple[str, int, str]:
    if not conditions.sentient:
        # Create and hide a tiny root for the popup to appear properly
        small_window = Tk()
        small_window.withdraw()
        address = None
        if not conditions.human:
            address = askstring(
                "Address",
                "Paste the \"CONNECT TO\" information you see on the server:"
            )
            name = askstring("Name", "What's your name?")
        else:
            name = conditions.human
        small_window.destroy()
        if address:
            host, port = address.split()
        else:
            # If the address is empty, just use defaults. Useful for local testing
            host, port = "localhost", 44444

        if not name:
            name = f"default-{randint(0, 1000)}"
    else:
        host, port = "localhost", 44444
        name = "Not-a-robot"
    try:
        port = int(port)
    except ValueError:
        log.critical(f"Couldn't convert port {port} to an integer - please try again!")
        sys.exit(1)
    return host, port, name


def connect_to_server(sock: socket, host: str, port: int, name: str):
    try:
        sock.connect((host, port))
        sock.send(name.encode("utf-8"))
        log.info(
            "Connected to server. Waiting for other players to connect before we can show you "
            "your cards!"
        )
    except Exception as e:
        log.critical(f"Error connecting to server: {e}")
        sys.exit(1)


def start_game(sock: socket, conditions: argparse.Namespace):
    init, _ = sock.recvfrom(1000)
    try:
        data = init.decode("utf-8")
        message = json.loads(data)
        message.pop("padding")
        log.debug(f"Received initial message: {message}")
        utils.title_window(root, message["whoami"], message["peeps"])
        q = queue.Queue()
        all_points: dict[str, int] = {
            p: number for p, number in zip(message["peeps"], [0] * len(message["other_left"]))
        }
        if conditions.sentient:
            log.critical("Currently not supported")
            sys.exit(1)
            # window = Player(root, q, message, sock, all_points)
            # root.withdraw()
        else:
            window = gameanim.Game(root, q, message, sock, all_points, log)
            # window = Game(root, q, message, sock, all_points)
        window.start_config(message)
        thread = Thread(target=window.receive)
        thread.start()
        window.check_periodically()
        window.mainloop()
    except JSONDecodeError as e:
        log.critical(f"Error decoding the response from the server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    conditions = parser.parse_args()

    # Get the player's name and connection information
    host, port, name = get_player_info(conditions)

    setup_logger(log, name.lower())
    log.info(f"Host: {host}, port: {port}, name: {name}")

    # Create the main window
    root = Tk()
    root.configure(bg="white")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")

    # Connect to the server and get initial game information
    sock = socket(AF_INET, SOCK_STREAM)
    connect_to_server(sock, host, port, name)

    start_game(sock, conditions)
