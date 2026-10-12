from game_classes import Modes
from card import Card, CardType
from logging import Logger
from random import shuffle


def get_modes(mode_string: str, log: Logger) -> Modes:
    modes = Modes.from_string(mode_string)
    for mode in modes.enabled_strings():
        log.info(f"{mode} enabled")
    return modes


def pop_first_card(pile: list[str], num_players) -> tuple[Card, list[str]]:
    # Usually the first card is placed after cards are dealt (so e.g. it's the 15th card for 2
    # players). Pretend it's the same here
    first_card: Card = Card(pile.pop(7 * num_players))

    # Black cards will not be played first. If popped, reshuffle and get a new one
    while first_card.type_is(CardType.BLACK):
        pile.append(first_card.name)
        shuffle(pile)
        first_card = Card(pile.pop(7 * num_players))
    return first_card, pile
