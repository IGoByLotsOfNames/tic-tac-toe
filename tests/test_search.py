import unittest

from oracle import states, x_value
from tictactoe.model import Board
from tictactoe.search import STRATEGIES, TRANSFORMS, canonical, solve

STATES = states()


class SearchTests(unittest.TestCase):
    def test_every_variant_and_move_score_against_independent_oracle(self):
        # All 5,478 states, including 958 terminal positions. The oracle uses
        # integer bitboards and X-max/O-min backup rather than tuple negamax.
        for text, (x, o) in STATES.items():
            board = Board.parse(text)
            expected = x_value(x, o) * (1 if board.turn == "X" else -1)
            expected_moves = {}
            for move in board.legal_moves:
                value = x_value(x | (1 << move), o) if board.turn == "X" else x_value(x, o | (1 << move))
                expected_moves[move] = value * (1 if board.turn == "X" else -1)
            for strategy in STRATEGIES:
                analysis = solve(board, strategy)
                if analysis.score != expected or dict(analysis.move_scores) != expected_moves:
                    self.fail(f"{strategy}: {text}: {analysis} != {expected}, {expected_moves}")
                if expected_moves:
                    self.assertIn(analysis.move, analysis.best_moves)
                    self.assertEqual(set(analysis.best_moves), {m for m, v in expected_moves.items() if v == expected})
                else:
                    self.assertIsNone(analysis.move)

    def test_perfect_player_cannot_lose_to_any_human_continuation(self):
        # Visit every complete human move sequence, not a sampled opponent.
        for bot in ("X", "O"):
            finished = 0

            def walk(board):
                nonlocal finished
                if board.result:
                    finished += 1
                    self.assertIn(board.result, (bot, "D"))
                    return
                moves = (solve(board).move,) if board.turn == bot else board.legal_moves
                for move in moves:
                    walk(board.play(move))

            walk(Board())
            self.assertGreater(finished, 0)

    def test_symmetry_keys_preserve_rules_and_values(self):
        self.assertEqual(len(TRANSFORMS), 8)
        keys = set()
        for text, (x, o) in STATES.items():
            cells = tuple(text)
            key = canonical(cells)
            keys.add(key)
            for transform in TRANSFORMS:
                image = tuple(cells[i] for i in transform)
                self.assertEqual(canonical(image), key)
                self.assertEqual(Board(image).result, Board(cells).result)
        self.assertEqual(len(keys), 765)

    def test_cold_search_is_repeatable_and_variants_save_calls(self):
        plain = solve(Board(), "minimax")
        alpha = solve(Board(), "alpha-beta")
        memo = solve(Board(), "memo")
        symmetry = solve(Board(), "symmetry")
        self.assertEqual(plain.stats.nodes, 549946)
        self.assertLess(alpha.stats.nodes, plain.stats.nodes)
        self.assertLess(memo.stats.nodes, plain.stats.nodes)
        self.assertLess(symmetry.stats.nodes, memo.stats.nodes)
        self.assertGreater(alpha.stats.cutoffs, 0)
        self.assertGreater(symmetry.stats.cache_hits, 0)
        self.assertEqual(symmetry, solve(Board(), "symmetry"))
        self.assertEqual((plain.move, alpha.move, memo.move, symmetry.move), (4, 4, 4, 4))

    def test_unknown_strategy_and_terminal(self):
        with self.assertRaises(ValueError):
            solve(Board(), "lucky")
        for strategy in STRATEGIES:
            result = solve(Board.parse("XXXOO...."), strategy)
            self.assertEqual(result.score, -1)
            self.assertIsNone(result.move)
