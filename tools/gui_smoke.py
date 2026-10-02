"""Exercise actual Tk widgets without showing a window; requires Tk and a display."""

from pathlib import Path
import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tictactoe.gui import App


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    app = App(root)
    root.update_idletasks()
    app.hint()
    assert len(app.hints) == 9
    app.click(4)
    assert app.pending is not None
    app.new_round()  # An old scheduled response must not enter a new round.
    assert app.pending is None
    assert app.game.board.cells.count(".") == 9
    app.mode.set("Local two-player")
    app.new_round()
    for move in (0, 3, 1, 4, 2):
        app.buttons[move].invoke()
    assert app.game.board.result == "X" and app.game.scores["X"] == 1
    app.buttons[8].invoke()
    assert app.game.board.cells[8] == "."
    app.reset_scores()
    assert sum(app.game.scores.values()) == 0
    app.mode.set("Perfect")
    app.side.set("O")
    app.new_round()
    assert app.pending is not None
    app.cancel_pending()
    app.computer_turn()
    assert app.game.board.cells[4] == "X"
    app.mode.set("Relaxed")
    app.new_round()
    app.cancel_pending()
    app.computer_turn()
    assert app.game.board.cells.count("X") == 1
    app.close()
    print("Tk smoke passed: hints, reset/cancellation, local win, terminal lock, score reset, both bot modes.")


if __name__ == "__main__":
    main()
