"""A small Tk front end; all rules and search live outside the UI."""

import random
import tkinter as tk
from tkinter import ttk

from .game import Game, bot_move
from .search import solve

BG, PANEL, TILE = "#101c30", "#192a43", "#223955"
INK, MUTED, TEAL, CORAL = "#f0f4fb", "#aabbd0", "#70e2cc", "#ffaf94"


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root, self.game, self.rng = root, Game(), random.Random()
        self.pending: str | None = None
        self.hints: tuple[int, ...] = ()
        self.mode, self.side = tk.StringVar(value="Perfect"), tk.StringVar(value="X")
        self.status, self.detail, self.score = tk.StringVar(), tk.StringVar(), tk.StringVar()
        root.title("Tic Tac Toe - Your move")
        root.configure(bg=BG)
        root.geometry("880x675")
        root.minsize(820, 650)
        root.protocol("WM_DELETE_WINDOW", self.close)
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 20))
        tk.Label(header, text="TIC TAC TOE", font=("Segoe UI", 12, "bold"),
                 bg=BG, fg=TEAL).pack(anchor="w")
        tk.Label(header, textvariable=self.status, font=("Segoe UI", 27, "bold"),
                 bg=BG, fg=INK).pack(anchor="w", pady=(5, 0))
        tk.Label(header, text="Nine squares. One more round?", font=("Segoe UI", 12),
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 0))
        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=30)
        grid = tk.Frame(content, bg=BG, width=420, height=420)
        grid.pack(side="left", anchor="n")
        grid.grid_propagate(False)
        self.buttons = []
        for i in range(9):
            grid.rowconfigure(i // 3, weight=1, uniform="cells")
            grid.columnconfigure(i % 3, weight=1, uniform="cells")
            button = tk.Button(grid, text=str(i + 1), font=("Segoe UI", 36, "bold"),
                               bg=TILE, fg=MUTED, disabledforeground=MUTED,
                               activebackground="#315573", activeforeground=INK,
                               relief="flat", borderwidth=0, highlightthickness=2,
                               highlightbackground=BG, highlightcolor=TEAL,
                               command=lambda cell=i: self.click(cell))
            button.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            self.buttons.append(button)
        panel = tk.Frame(content, bg=PANEL, padx=20, pady=18)
        panel.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=(4, 4))
        self.label(panel, "THE MATCH", 11, TEAL, True).pack(anchor="w")
        self.label(panel, "Opponent", 11).pack(anchor="w", pady=(15, 4))
        modes = ttk.Combobox(panel, textvariable=self.mode, state="readonly",
                             values=("Perfect", "Relaxed", "Local two-player"), width=22)
        modes.pack(fill="x")
        modes.bind("<<ComboboxSelected>>", lambda event: self.new_round())
        self.label(panel, "Play as (X starts)", 11).pack(anchor="w", pady=(12, 4))
        sides = ttk.Combobox(panel, textvariable=self.side, state="readonly", values=("X", "O"), width=22)
        sides.pack(fill="x")
        sides.bind("<<ComboboxSelected>>", lambda event: self.new_round())
        self.label(panel, "ROUND SCORE", 11, TEAL, True).pack(anchor="w", pady=(22, 5))
        tk.Label(panel, textvariable=self.score, bg=PANEL, fg=INK,
                 font=("Segoe UI", 12)).pack(anchor="w")
        self.label(panel, "BEHIND THE MOVE", 11, TEAL, True).pack(anchor="w", pady=(22, 6))
        tk.Label(panel, textvariable=self.detail, bg=PANEL, fg=MUTED, justify="left",
                 wraplength=245, font=("Segoe UI", 11)).pack(anchor="w")
        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", padx=34, pady=(18, 22))
        self.action(footer, "New round", self.new_round, TEAL, BG).pack(side="left")
        self.action(footer, "Show a hint", self.hint).pack(side="left", padx=10)
        self.action(footer, "Reset score", self.reset_scores).pack(side="right")
        root.bind("<Key>", self.key)
        self.new_round()

    @staticmethod
    def label(parent: tk.Widget, text: str, size: int, color: str = MUTED,
              bold: bool = False) -> tk.Label:
        return tk.Label(parent, text=text, bg=PANEL, fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    @staticmethod
    def action(parent: tk.Widget, text: str, command, bg: str = TILE, fg: str = INK) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground="#315573", activeforeground=INK, relief="flat",
                         padx=16, pady=10, font=("Segoe UI", 11, "bold"))

    def is_bot_turn(self) -> bool:
        return self.mode.get() != "Local two-player" and self.game.board.turn != self.side.get()

    def cancel_pending(self) -> None:
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None

    def new_round(self) -> None:
        self.cancel_pending()
        self.game.new_round()
        self.hints = ()
        self.detail.set("Perfect sees the whole game.\nRelaxed picks an empty square.\n\nUse keys 1-9 or click a tile.")
        self.render()
        self.schedule_bot()

    def reset_scores(self) -> None:
        self.game.reset_scores()
        self.render()

    def key(self, event: tk.Event) -> None:
        if event.char in "123456789" and event.char:
            self.click(int(event.char) - 1)

    def click(self, move: int) -> None:
        if self.is_bot_turn() or move not in self.game.board.legal_moves:
            return
        self.hints = ()
        self.game.play(move)
        self.render()
        self.schedule_bot()

    def schedule_bot(self) -> None:
        if not self.game.board.result and self.is_bot_turn():
            self.pending = self.root.after(240, self.computer_turn)

    def computer_turn(self) -> None:
        self.pending = None
        if self.game.board.result or not self.is_bot_turn():
            return
        difficulty = self.mode.get().lower()
        if difficulty == "perfect":
            analysis = solve(self.game.board)
            move = analysis.move
            self.detail.set(f"Last search\n{analysis.stats.nodes:,} calls\n"
                            f"{analysis.stats.cache_hits:,} cached answers\n\n"
                            "Rotations and reflections share an answer.")
        else:
            move = bot_move(self.game.board, difficulty, self.rng)
            self.detail.set("Relaxed chose a random empty square.\n\nA little room for surprises.")
        assert move is not None
        self.game.play(move)
        self.render()

    def hint(self) -> None:
        if self.game.board.result or self.is_bot_turn():
            return
        analysis = solve(self.game.board)
        self.hints = analysis.best_moves
        word = {-1: "a loss", 0: "a draw", 1: "a win"}[analysis.score]
        self.detail.set(f"Highlighted cells preserve {word} with perfect play from both sides.\n\n"
                        f"{analysis.stats.nodes:,} search calls.\nA hint, not a promise about your next move.")
        self.render()

    def render(self) -> None:
        board = self.game.board
        if board.result == "D":
            status = "A well-earned draw."
        elif board.result:
            status = f"{board.result} takes the round!"
        elif self.is_bot_turn():
            status = "The computer is thinking..."
        elif self.mode.get() == "Local two-player":
            status = f"{board.turn}, your move."
        else:
            status = "Your move."
        self.status.set(status)
        self.score.set(f"X  {self.game.scores['X']}     O  {self.game.scores['O']}     Draws  {self.game.scores['D']}")
        for i, button in enumerate(self.buttons):
            mark = board.cells[i]
            color = TEAL if mark == "X" else CORAL if mark == "O" else MUTED
            bg = "#345c5c" if i in board.winning_line else "#284e57" if i in self.hints else TILE
            button.configure(text=str(i + 1) if mark == "." else mark, bg=bg,
                             fg=color, disabledforeground=color,
                             state="normal" if i in board.legal_moves and not self.is_bot_turn() else "disabled")

    def close(self) -> None:
        self.cancel_pending()
        self.root.destroy()


def launch() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError("A graphical display is unavailable. Try 'play' or 'self-play'.") from exc
    App(root)
    root.mainloop()
