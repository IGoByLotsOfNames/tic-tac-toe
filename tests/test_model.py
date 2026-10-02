from dataclasses import FrozenInstanceError
from itertools import product
import unittest

from oracle import states, terminal
from tictactoe.model import Board

STATES = states()


class BoardTests(unittest.TestCase):
    def test_exactly_all_reachable_positions_are_accepted(self):
        accepted = set()
        for cells in product(".XO", repeat=9):
            try:
                board = Board(cells)
            except ValueError:
                continue
            accepted.add("".join(board.cells))
        self.assertEqual(accepted, set(STATES))
        self.assertEqual(len(accepted), 5478)

    def test_every_legal_transition_and_terminal(self):
        terminals = 0
        for text, (x, o) in STATES.items():
            board = Board.parse(text)
            expected = terminal(x, o)
            if expected is not None:
                terminals += 1
                self.assertEqual(board.result, {1: "X", -1: "O", 0: "D"}[expected])
                self.assertEqual(board.legal_moves, ())
                for i in range(9):
                    with self.assertRaises(ValueError):
                        board.play(i)
            else:
                self.assertIsNone(board.result)
                self.assertEqual(board.legal_moves, tuple(i for i, c in enumerate(text) if c == "."))
                for move in board.legal_moves:
                    child = board.play(move)
                    self.assertIn("".join(child.cells), STATES)
                    self.assertEqual(child.cells[move], board.turn)
                    self.assertEqual(sum(a != b for a, b in zip(board.cells, child.cells)), 1)
        self.assertEqual(terminals, 958)

    def test_rejects_malformed_mutable_and_invalid_moves(self):
        for cells in ([], ["."] * 9, (), (".",) * 10, ("Q",) * 9):
            with self.assertRaises(ValueError):
                Board(cells)
        for move in (-1, 9, True, False, "1", 1.0, None):
            with self.assertRaises(ValueError):
                Board().play(move)
        with self.assertRaises(ValueError):
            Board().play(0).play(0)

    def test_immutable_and_parse(self):
        board = Board()
        with self.assertRaises(FrozenInstanceError):
            board.cells = ("X",) * 9
        self.assertEqual(Board.parse("xo..x.o..").cells, tuple("XO..X.O.."))
        board.play(4)
        self.assertEqual(board, Board())

    def test_win_with_empty_cells_stops_immediately(self):
        board = Board.parse("XXXOO....")
        self.assertEqual(board.winning_line, (0, 1, 2))
        self.assertEqual(board.legal_moves, ())
        with self.assertRaises(ValueError):
            board.play(5)
