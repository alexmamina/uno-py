from abc import ABC
from dataclasses import dataclass
from game_classes import Stage
from typing import Optional


@dataclass
class Message(ABC):
    stage: Stage
    player: int
    padding: str

    # def receive and parse
    # def send
    def test(self):
        print("test")


@dataclass
class InitMessage(Message):
    modes: list[bool]
    played: str
    peeps: list[str]
    pile: list[str]
    num_left: int
    other_left: list[int]
    color: str

    def test(self):
        super().test()
        print("init")


a = InitMessage(Stage.INIT, 0, '', [], 'p', ['z'], [], 2, [], 'bla')
a.test()


@dataclass
class GoMessage(Message):
    # make same as debug?
    played: str
    pile: list[str]
    color: str
    num_left: int
    wild: Optional[bool]  # if +4
    counter: Optional[int]  # if stack
    hand: Optional[list[str]]  # if 7/0
    said_uno: Optional[bool]  # if uno
    swapwith: Optional[int]  # if 7 in 7/0


@dataclass
class ChallengeMessage(Message):
    why: int
    counter: Optional[int]  # for stacking??
    # no player tho?


@dataclass
class ChallengeTakenMessage(Message):
    played: str
    pile: list[str]
    color: str
    num_left: int
    why: int


@dataclass
class ZeroCardsMessage(Message):
    played: str
    pile: list[str]
    color: str
    num_left: int
    counter: Optional[int]
    to_take: Optional[bool]
