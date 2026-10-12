from socket import socket, AF_INET, SOCK_STREAM
from message_processor import Message
from typing import Any
from logging import Logger
from dataclasses import dataclass, field


@dataclass
class PlayerInfo:
    socket: socket
    address: tuple[str, int]

    def send_message(self, message: Any):
        self.socket.sendto(message, self.address)


@dataclass
class Session:
    local_address: tuple[str, int]  # (ip, port)
    num_players: int
    sock: socket = socket(AF_INET, SOCK_STREAM)
    players: dict[str, PlayerInfo] = field(default_factory=lambda: {})
    player_points: dict[str, int] = field(default_factory=lambda: {})
    total_games_played = 0
    last_winner: str = ""

    def connect(self, log: Logger):
        self.sock.bind(self.local_address)
        self.sock.listen(128)
        self.connect_clients(log)

    def connect_clients(self, log: Logger):
        player_counter = 0
        # Wait for clients to connect and save their information
        while player_counter < self.num_players:
            player_socket, addr = self.sock.accept()
            byte_name, _ = player_socket.recvfrom(200)
            name = byte_name.decode("utf-8")
            player_details = PlayerInfo(
                socket=player_socket,
                address=addr,
            )
            self.players[name] = player_details
            # Instantiate points total for each new player
            self.player_points[name] = 0
            log.info(f"Connected player {player_counter} - {name}")
            player_counter += 1
            n = self.num_players - player_counter
            log.info(f"Waiting for {n} more players")

    def send_message(self, player: str, message: Message):
        self.players[player].send_message(message)

    def exit(self):
        for info in self.players.values():
            info.socket.close()
        self.sock.close()
