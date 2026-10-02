"""Immutable, validated board. X starts; play stops at the first win."""

from dataclasses import dataclass

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
         (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
EMPTY = "."
Cells = tuple[str, ...]


def winners(cells: Cells) -> frozenset[str]:
    return frozenset(cells[a] for a, b, c in LINES
                     if cells[a] != EMPTY and cells[a] == cells[b] == cells[c])


def outcome(cells: Cells) -> str | None:
    """Internal helper for already valid states; draw is D, ongoing is None."""
    for a, b, c in LINES:
        if cells[a] != EMPTY and cells[a] == cells[b] == cells[c]:
            return cells[a]
    return None if EMPTY in cells else "D"


@dataclass(frozen=True, slots=True)
class Board:
    cells: Cells = (EMPTY,) * 9

    def __post_init__(self) -> None:
        if not isinstance(self.cells, tuple) or len(self.cells) != 9:
            raise ValueError("Use an immutable tuple of nine cells.")
        if any(cell not in (EMPTY, "X", "O") for cell in self.cells):
            raise ValueError("Cells must be '.', 'X', or 'O'.")
        x, o = self.cells.count("X"), self.cells.count("O")
        won = winners(self.cells)
        if x not in (o, o + 1) or len(won) > 1:
            raise ValueError("Board cannot occur in a legal game.")
        if ("X" in won and x != o + 1) or ("O" in won and x != o):
            raise ValueError("A game must stop when a player wins.")

    @classmethod
    def parse(cls, text: str) -> "Board":
        """Read nine row-major cells, e.g. 'XO..X.O..'."""
        return cls(tuple(text.upper()))

    @property
    def turn(self) -> str:
        # At a terminal position this is the next hypothetical player. That
        # convention makes negamax's terminal score unambiguous.
        return "X" if self.cells.count("X") == self.cells.count("O") else "O"

    @property
    def result(self) -> str | None:
        return outcome(self.cells)

    @property
    def legal_moves(self) -> tuple[int, ...]:
        return () if self.result else tuple(i for i, c in enumerate(self.cells) if c == EMPTY)

    @property
    def winning_line(self) -> tuple[int, ...]:
        for line in LINES:
            a, b, c = line
            if self.cells[a] != EMPTY and self.cells[a] == self.cells[b] == self.cells[c]:
                return line
        return ()

    def play(self, move: int) -> "Board":
        if type(move) is not int or move not in self.legal_moves:
            raise ValueError("Choose an empty cell in an unfinished game.")
        return Board(self.cells[:move] + (self.turn,) + self.cells[move + 1:])

    def __str__(self) -> str:
        return "\n---+---+---\n".join(
            " " + " | ".join(self.cells[i:i + 3]) for i in (0, 3, 6))
