from contextlib import redirect_stdout, redirect_stderr
import io
import json
import random
import unittest
from unittest.mock import patch

from tictactoe.cli import main, self_play
from tictactoe.game import Game, bot_move
from tictactoe.model import Board
from tictactoe.search import STRATEGIES


class InterfaceTests(unittest.TestCase):
    def test_round_scoring_reset_and_illegal_move_are_atomic(self):
        game = Game()
        for move in (0, 3, 1, 4, 2):
            game.play(move)
        self.assertEqual(game.scores, {"X": 1, "O": 0, "D": 0})
        before = game.board
        with self.assertRaises(ValueError):
            game.play(5)
        self.assertEqual(game.board, before)
        self.assertEqual(game.scores["X"], 1)
        game.new_round()
        self.assertEqual(game.board, Board())
        self.assertEqual(game.scores["X"], 1)
        game.reset_scores()
        self.assertEqual(sum(game.scores.values()), 0)

    def test_seeded_casual_opponent_and_validation(self):
        a, b = random.Random(27), random.Random(27)
        self.assertEqual([bot_move(Board(), "relaxed", a) for _ in range(20)],
                         [bot_move(Board(), "relaxed", b) for _ in range(20)])
        self.assertEqual(bot_move(Board(), "perfect", a), 4)
        with self.assertRaises(ValueError):
            bot_move(Board(), "unknown", a)
        with self.assertRaises(ValueError):
            bot_move(Board.parse("XXXOO...."), "perfect", a)

    def test_all_variants_self_play_to_a_legal_draw(self):
        for strategy in STRATEGIES:
            record = self_play(strategy)
            self.assertEqual(record["result"], "D")
            board = Board()
            for move in record["moves"]:
                self.assertEqual(move["player"], board.turn)
                board = board.play(move["cell"] - 1)
            self.assertEqual("".join(board.cells), record["board"])

    def test_json_commands(self):
        for args in (["self-play", "--json"], ["analyze", "XX.OO...."]):
            stream = io.StringIO()
            with redirect_stdout(stream):
                self.assertEqual(main(args), 0)
            parsed = json.loads(stream.getvalue())
            self.assertIsInstance(parsed, dict)

    def test_invalid_board_returns_cli_error(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["analyze", "OO......."])
        self.assertEqual(error.exception.code, 2)

    def test_terminal_input_hint_invalid_and_quit(self):
        stream = io.StringIO()
        with patch("builtins.input", side_effect=["h", "wrong", "q"]), redirect_stdout(stream):
            main(["play"])
        self.assertIn("Best cells:", stream.getvalue())
        self.assertIn("Choose an empty cell", stream.getvalue())

    def test_terminal_local_win_and_eof(self):
        stream = io.StringIO()
        with patch("builtins.input", side_effect=["1", "4", "2", "5", "3"]), redirect_stdout(stream):
            main(["play", "--mode", "local"])
        self.assertIn("X wins!", stream.getvalue())
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(stream):
            main(["play", "--side", "O"])
        self.assertIn("See you next round.", stream.getvalue())
