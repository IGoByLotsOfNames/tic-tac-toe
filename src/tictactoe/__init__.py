"""Rules and search for ordinary 3-by-3 tic-tac-toe."""

from .model import Board
from .search import Analysis, solve

__all__ = ["Analysis", "Board", "solve"]
