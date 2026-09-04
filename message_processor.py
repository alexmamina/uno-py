from game_classes import ChallengeReason, Stage, Modes
from typing import Any, Optional
from card import Card
from dataclasses import dataclass, field


@dataclass
class Message:
    stage: Stage
    player: str = ""
    padding: str = ""
    modes: Modes = Modes()
    played: Optional[Card] = None
    players: list[str] = field(default_factory=lambda: [])
    pile: list[str] = field(default_factory=lambda: [])
    num_left: int = 0
    other_left: dict[str, int] = field(default_factory=lambda: {})
    is_reversed: bool = False
    whoami: str = ""
    wild: bool = False
    counter: int = 0
    hand: list[str] = field(default_factory=lambda: [])
    said_uno: bool = False
    swapwith: str = ""
    challenge_reason: Optional[ChallengeReason] = None
    to_take: bool = False
    taken: bool = False
    points: int = 0
    total: dict[str, int] = field(default_factory=lambda: {})
    winner: str = ""
    end: bool = False
    from_player: str = ""

    def converted_type(self, obj: Any) -> Any:
        # Custom types or lists of custom types: return to_json(), otherwise the object itself
        if type(obj) in [Modes, Card]:
            return obj.to_json()
        return obj

    def to_json(self) -> dict[str, Any]:
        dict_self = self.__dict__
        # Only construct a message with filled in parameters
        non_empty_values = {k: v for k, v in dict_self.items() if v}
        encoded_values = {k: self.converted_type(v) for k, v in non_empty_values.items()}
        return encoded_values

    @classmethod
    def from_dict(cls, message: dict[str, Any]) -> "Message":
        if isinstance(message.get("modes", ""), str):
            modes = Modes.from_string(message.get("modes", ""))
        else:
            modes = Modes.from_json(message.get("modes", '{}'))
        return Message(
            stage=Stage(int(message["stage"])),
            player=message.get("player", ""),
            padding=message["padding"],
            modes=modes,
            played=Card(message.get("played", "")) if message.get("played") else None,
            players=message.get("players", []),
            pile=message.get("pile", []),
            num_left=message.get("num_left", 0),
            other_left=message.get("other_left", {}),
            is_reversed=message.get("is_reversed", False),
            whoami=message.get("whoami", ""),
            wild=message.get("wild", False),
            counter=message.get("counter", 0),
            hand=message.get("hand", []),
            said_uno=message.get("said_uno", False),
            swapwith=message.get("swapwith", ""),
            challenge_reason=message.get("challenge_reason"),
            to_take=message.get("to_take", False),
            taken=message.get("taken", False),
            points=message.get("points", 0),
            total=message.get("total", {}),
            winner=message.get("winner", ""),
            end=message.get("end", False),
            from_player=message.get("from_player", "")
        )
