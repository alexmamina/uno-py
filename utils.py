from tkinter import Tk
from card import Card, CardType
from typing import Optional


def get_prev_player(
        current: str,
        all_players: list[str],
        last_played_card: Optional[Card] = None
) -> str:
    # If the card isn't given, it's definitely not a stop
    is_stop = last_played_card and last_played_card.type_is(CardType.STOP)
    diff = 1 if not is_stop else 2
    current_index = all_players.index(current)
    prev_index = (current_index - diff) % len(all_players)
    return all_players[prev_index]


def get_next_player(
        current: str,
        all_players: list[str],
        last_played_card: Optional[Card] = None
) -> str:
    current_index = all_players.index(current)
    is_stop = last_played_card and last_played_card.type_is(CardType.STOP)
    diff = 1 if not is_stop else 2
    next_index = (current_index + diff) % len(all_players)
    return all_players[next_index]


def title_window(window: Tk, player: str, all_players: list[str]):
    index = all_players.index(player)
    title = f"UNO - player {index} - {player}"
    window.title(title)
