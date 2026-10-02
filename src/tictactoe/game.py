"""Interface-independent round state, scoring and seeded casual opponent."""

from dataclasses import dataclass, field
import random

from .model import Board
from .search import solve


@dataclass
class Game:
    board: Board = field(default_factory=Board)
    scores: dict[str, int] = field(default_factory=lambda: {"X": 0, "O": 0, "D": 0})

    def play(self, move: int) -> None:
        self.board = self.board.play(move)
        if self.board.result:
            self.scores[self.board.result] += 1

    def new_round(self) -> None:
        self.board = Board()

    def reset_scores(self) -> None:
        self.scores = {"X": 0, "O": 0, "D": 0}


def bot_move(board: Board, difficulty: str, rng: random.Random) -> int:
    if not board.legal_moves:
        raise ValueError("The round is already over.")
    if difficulty == "relaxed":
        return rng.choice(board.legal_moves)
    if difficulty == "perfect":
        move = solve(board).move
        assert move is not None
        return move
    raise ValueError(f"Unknown difficulty: {difficulty}")
