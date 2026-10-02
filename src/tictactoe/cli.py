"""Terminal play, inspection and a deterministic demo. No GUI import at startup."""

import argparse
from dataclasses import asdict
import json
import random

from .game import Game, bot_move
from .model import Board
from .search import STRATEGIES, solve


def self_play(strategy: str = "symmetry") -> dict:
    board = Board()
    moves = []
    while not board.result:
        analysis = solve(board, strategy)
        assert analysis.move is not None
        moves.append({"player": board.turn, "cell": analysis.move + 1,
                      "nodes": analysis.stats.nodes})
        board = board.play(analysis.move)
    return {"strategy": strategy, "moves": moves, "board": "".join(board.cells),
            "result": board.result}


def play(mode: str, side: str, seed: int) -> None:
    game, rng = Game(), random.Random(seed)
    print("Nine squares. Your move.\nCells are 1-9, left to right, top to bottom.")
    print("Enter h for a hint, or q to leave. X always starts.\n")
    while not game.board.result:
        print(game.board, "\n")
        if mode != "local" and game.board.turn != side:
            move = bot_move(game.board, mode, rng)
            print(f"Computer chooses {move + 1}.\n")
        else:
            try:
                answer = input(f"{game.board.turn}, choose a cell: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSee you next round.")
                return
            if answer == "q":
                return
            if answer == "h":
                analysis = solve(game.board)
                print("Best cells:", ", ".join(str(m + 1) for m in analysis.best_moves))
                print("Outcome assumes both players play perfectly.\n")
                continue
            try:
                move = int(answer) - 1
                if move not in game.board.legal_moves:
                    raise ValueError
            except ValueError:
                print("Choose an empty cell from 1 to 9.\n")
                continue
        game.play(move)
    print(game.board, "\n")
    print("A well-earned draw." if game.board.result == "D" else f"{game.board.result} wins!")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play a little. Inspect the search.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("gui", help="Open the desktop game (requires Tk).")
    terminal = commands.add_parser("play", help="Play in your terminal.")
    terminal.add_argument("--mode", choices=("perfect", "relaxed", "local"), default="perfect")
    terminal.add_argument("--side", choices=("X", "O"), default="X")
    terminal.add_argument("--seed", type=int, default=7)
    demo = commands.add_parser("self-play", help="Run two perfect players, without a display.")
    demo.add_argument("--strategy", choices=STRATEGIES, default="symmetry")
    demo.add_argument("--json", action="store_true")
    inspect = commands.add_parser("analyze", help="Show exact move outcomes for a board.")
    inspect.add_argument("board", help="Nine cells such as XO..X.O..; dot means empty.")
    inspect.add_argument("--strategy", choices=STRATEGIES, default="symmetry")
    args = parser.parse_args(argv)
    if args.command == "gui":
        try:
            from .gui import launch
            launch()
        except ImportError:
            parser.exit(2, "Tk is unavailable. Use 'play' or 'self-play', or install Tk for your Python.\n")
        except RuntimeError as exc:
            parser.exit(2, f"{exc}\n")
    elif args.command == "play":
        play(args.mode, args.side, args.seed)
    elif args.command == "self-play":
        result = self_play(args.strategy)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Two perfect players walk onto a board...")
            for move in result["moves"]:
                print(f"{move['player']} -> cell {move['cell']} ({move['nodes']:,} search calls)")
            print("\n" + str(Board.parse(result["board"])))
            print("\nA draw. Naturally.")
    elif args.command == "analyze":
        try:
            analysis = solve(Board.parse(args.board), args.strategy)
        except ValueError as exc:
            parser.error(str(exc))
        result = asdict(analysis)
        result["move"] = None if analysis.move is None else analysis.move + 1
        result["move_scores"] = {str(move + 1): score for move, score in analysis.move_scores}
        result["perspective"] = "player to move; -1 loss, 0 draw, +1 win with perfect play"
        print(json.dumps(result, indent=2))
    return 0
