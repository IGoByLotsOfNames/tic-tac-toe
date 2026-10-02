"""Reproduce cold per-decision search work. No timing-based assertions."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tictactoe import Board, solve
from tictactoe.search import STRATEGIES

POSITIONS = {"opening": ".........", "after_corner": "X........",
             "opposite_corners": "X...O...X", "immediate_threat": "XX.OO...."}


def measure() -> dict:
    rows = []
    for label, text in POSITIONS.items():
        for strategy in STRATEGIES:
            result = solve(Board.parse(text), strategy)
            rows.append({"position": label, "board": text, "strategy": strategy,
                         "move": result.move + 1, "score": result.score, **asdict(result.stats)})
    return {"definition": "Nodes count root plus recursive calls, including cache hits. Each solve uses a fresh table.",
            "root_policy": "Each candidate has a full search window; every displayed move outcome is exact.",
            "move_order": [5, 1, 3, 7, 9, 2, 4, 6, 8], "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    result = measure()
    if args.check:
        if json.loads(args.check.read_text(encoding="utf-8")) != result:
            raise SystemExit("Search results differ from the checked-in measurement.")
        print("All 16 search measurements reproduce exactly.")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(result['rows'])} search measurements to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
