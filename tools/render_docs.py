"""Generate diagrams and render the real CLI transcript. Pillow is docs-only."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tictactoe import Board, solve
from tictactoe.cli import main

OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
BG, PANEL, INK, MUTED, TEAL, CORAL = "#101c30", "#1b2e49", "#f0f4fb", "#aec0d6", "#70e2cc", "#ffaf94"


def font(size: int, mono: bool = False, bold: bool = False):
    candidates = (["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"] if mono else
                  ["C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def canvas(w: int, h: int):
    image = Image.new("RGB", (w, h), BG)
    return image, ImageDraw.Draw(image)


def hero() -> None:
    image, draw = canvas(1440, 830)
    draw.text((64, 38), "TIC TAC TOE", fill=TEAL, font=font(23, bold=True))
    draw.text((60, 77), "Nine squares. Your move.", fill=INK, font=font(56, bold=True))
    draw.text((64, 155), "A playable game with a stubborn opponent and a search you can inspect.", fill=MUTED, font=font(25))
    board = Board.parse("X...O...X")
    analysis = solve(board)
    for i, mark in enumerate(board.cells):
        x, y = 66 + 155 * (i % 3), 228 + 155 * (i // 3)
        fill = "#2b515b" if i in analysis.best_moves else PANEL
        draw.rounded_rectangle((x, y, x + 143, y + 143), radius=16, fill=fill)
        if mark != ".":
            draw.text((x + 71, y + 68), mark, anchor="mm", fill=TEAL if mark == "X" else CORAL, font=font(76, bold=True))
        else:
            draw.text((x + 71, y + 59), str(i + 1), anchor="mm", fill=MUTED, font=font(31))
            draw.text((x + 71, y + 110), "DRAW" if i in analysis.best_moves else "LOSS", anchor="mm", fill=TEAL if i in analysis.best_moves else MUTED, font=font(17, bold=True))
    draw.text((66, 719), "O to move. Edge squares prevent X's fork.", fill=INK, font=font(23))
    draw.text((66, 756), "Board diagram generated from the actual solver; not a UI screenshot.", fill=MUTED, font=font(17))
    cards = [("PLAY", "Desktop or terminal", "Perfect, relaxed, or local two-player."),
             ("INSPECT", "Four ways to search", "Minimax, pruning, caching, symmetry."),
             ("VERIFY", "Every reachable board", "5,478 positions checked against an independent oracle.")]
    for j, (label, title, detail) in enumerate(cards):
        y = 229 + 165 * j
        draw.rounded_rectangle((585, y, 1370, y + 144), radius=16, fill=PANEL)
        draw.text((611, y + 18), label, fill=TEAL, font=font(17, bold=True))
        draw.text((611, y + 47), title, fill=INK, font=font(31, bold=True))
        draw.text((611, y + 98), detail, fill=MUTED, font=font(22))
    image.save(OUT / "game-diagram.png")


def chart() -> None:
    data = json.loads((ROOT / "benchmarks/search.json").read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if r["position"] == "opening"]
    image, draw = canvas(1440, 830)
    draw.text((64, 40), "ONE EMPTY BOARD. FOUR EXACT ANSWERS.", fill=TEAL, font=font(23, bold=True))
    draw.text((60, 84), "Same draw. Less search.", fill=INK, font=font(52, bold=True))
    draw.text((64, 160), "Recursive calls, including cache hits. Fresh table for each decision.", fill=MUTED, font=font(25))
    max_nodes = max(r["nodes"] for r in rows)
    names = {"minimax": "Plain minimax", "alpha-beta": "Alpha-beta", "memo": "Memoisation", "symmetry": "Symmetry + memo"}
    for j, row in enumerate(rows):
        y = 244 + j * 105
        draw.text((64, y), names[row["strategy"]], fill=INK, font=font(27, bold=True))
        draw.rounded_rectangle((385, y, 1190, y + 41), radius=7, fill=PANEL)
        width = max(4, 805 * row["nodes"] / max_nodes)
        draw.rounded_rectangle((385, y, 385 + width, y + 41), radius=min(7, width / 2), fill=CORAL if j == 0 else TEAL)
        draw.text((1220, y + 1), f"{row['nodes']:,}", fill=INK, font=font(26, bold=True))
    reduction = (1 - rows[-1]["nodes"] / rows[0]["nodes"]) * 100
    draw.text((64, 707), f"{reduction:.2f}% fewer calls with symmetry caching on this opening.", fill=TEAL, font=font(28, bold=True))
    draw.text((64, 761), "Linear scale. Call counts measure search work, not wall-clock speed. Source: benchmarks/search.json", fill=MUTED, font=font(20))
    image.save(OUT / "search-calls.png")


def transcript() -> None:
    stream = io.StringIO()
    with redirect_stdout(stream):
        main(["self-play"])
    text = "$ python -m tictactoe self-play\n\n" + stream.getvalue()
    (ROOT / "docs/self-play.txt").write_text(text, encoding="utf-8")
    lines = text.splitlines()
    image, draw = canvas(1220, 115 + 35 * len(lines))
    draw.text((44, 24), "ACTUAL CLI OUTPUT / DETERMINISTIC SELF-PLAY", fill=TEAL, font=font(19, bold=True))
    for i, line in enumerate(lines):
        draw.text((44, 77 + i * 35), line, fill=INK, font=font(25, mono=True))
    image.save(OUT / "self-play.png")


def architecture() -> None:
    image, draw = canvas(1440, 520)
    draw.text((64, 35), "SMALL PIECES, CLEAR RESPONSIBILITIES", fill=TEAL, font=font(22, bold=True))
    draw.text((60, 76), "Play and proof share one rules engine.", fill=INK, font=font(45, bold=True))
    boxes = [(60, "Interfaces", "Tkinter / terminal", "Input, display, hints"),
             (530, "Game + Board", "Immutable positions", "Legal moves, rounds, score"),
             (1000, "Exact search", "Negamax + variants", "Move values and call counts")]
    for x, title, sub, detail in boxes:
        draw.rounded_rectangle((x, 196, x + 380, 375), radius=15, fill=PANEL)
        draw.text((x + 22, 220), title, fill=TEAL, font=font(29, bold=True))
        draw.text((x + 22, 280), sub, fill=INK, font=font(22))
        draw.text((x + 22, 325), detail, fill=MUTED, font=font(18))
    for x in (450, 920):
        draw.line((x, 285, x + 65, 285), fill=MUTED, width=3)
        draw.polygon(((x + 65, 285), (x + 56, 279), (x + 56, 291)), fill=MUTED)
    draw.text((60, 422), "Independent bitboard oracle checks every accepted board, every legal transition and every move outcome.", fill=MUTED, font=font(24))
    image.save(OUT / "architecture.png")


if __name__ == "__main__":
    hero()
    chart()
    transcript()
    architecture()
    print("Rendered four documentation visuals and a real CLI transcript.")
