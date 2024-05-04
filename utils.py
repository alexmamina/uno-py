from tkinter import Tk


def get_prev_player(current: str, all_players: list[str], last_played_card: str) -> str:
    diff = 1 if "stop" not in last_played_card else 2
    current_index = all_players.index(current)
    prev_index = (current_index - diff) % len(all_players)
    return all_players[prev_index]


def get_next_player(current: str, all_players: list[str], last_played_card: str) -> str:
    current_index = all_players.index(current)
    diff = 1 if "stop" not in last_played_card else 2
    next_index = (current_index + diff) % len(all_players)
    return all_players[next_index]


def title_window(window: Tk, player: str, all_players: list[str]):
    index = all_players.index(player)
    title = f"UNO - player {index} - {player}"
    window.title(title)
