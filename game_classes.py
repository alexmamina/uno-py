from enum import IntEnum
from dataclasses import dataclass
from deck import Deck

# Go - regular play, regular relay
# Debug - change turn, regular play, print data
# Challenge - only send packet to make player take two cards
# Challenge taken - confirmation of challenge complete
# Zerocards - one player is out of cards, forward to the other who will either take cards or send
# points
# Takecards - send back to player out of cards while waiting for the other to take more
# Calc - other player sends points
# Bye - a player said no new games, or an error occurred at one player
# Init - send initial information to setup a new game
# Seven - the 7 part of 7/0
# Zero - the 0 part of 7/0
# Numupdate - the finale of 7/0 to update all cards left
# Designupd - relay to all just to see cards move on screen
# Showchallenge - if player was honest, tell them someone else checked their cards


class Stage(IntEnum):
    INIT = -1
    GO = 0
    CHALLENGE = 1
    CHALLENGE_TAKEN = 6
    SHOWCHALLENGE = 810
    ZEROCARDS = 2
    DEBUG = 3
    TAKECARDS = 4
    CALC = 5
    SEVEN = 7
    ZERO = 70
    NUMUPDATE = 705
    BYE = 10
    DESIGNUPD = 123


@dataclass
class Modes:
    sevenzero: bool = False
    stack: bool = False
    mult: bool = False

    SEVENZERO_STRING = "7/0"
    STACK_STRING = "Stacking"
    MULT_STRING = "Taking multiple cards"

    def enabled_strings(self) -> list[str]:
        strings = []
        if self.sevenzero:
            strings.append(self.SEVENZERO_STRING)
        if self.stack:
            strings.append(self.STACK_STRING)
        if self.mult:
            strings.append(self.MULT_STRING)
        return strings

    def is_regular(self) -> bool:
        # If it's none of the other modes, it's regular
        return not (self.sevenzero or self.stack or self.mult)

    def to_json(self) -> dict[str, bool]:
        return {
            self.SEVENZERO_STRING: self.sevenzero,
            self.STACK_STRING: self.stack,
            self.MULT_STRING: self.mult,
        }

    @classmethod
    def from_json(cls, json_modes: dict[str, bool]) -> "Modes":
        return Modes(
            sevenzero=json_modes[cls.SEVENZERO_STRING],
            stack=json_modes[cls.STACK_STRING],
            mult=json_modes[cls.MULT_STRING],
        )

    @classmethod
    def from_string(cls, mode_string: str) -> "Modes":
        modes = Modes()
        if "0" not in mode_string:
            modes = Modes(
                sevenzero="1" in mode_string, stack="2" in mode_string, mult="3" in mode_string
            )
        return modes


@dataclass
class GameState:
    identity: str  # Current player's name
    peeps: list[str]  # Players' names
    deck: Deck  # The deck where cards are defined
    all_points: dict[str, int]  # All players' points throughout games
    modes: Modes  # Currently enabled modes

    @property
    def index(self) -> int:
        return self.peeps.index(self.identity)

    @property
    def num_players(self) -> int:
        return len(self.peeps)
