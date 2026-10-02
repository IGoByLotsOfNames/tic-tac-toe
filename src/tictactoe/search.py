"""Exact outcome search with four deliberately separate optimisation choices."""

from dataclasses import dataclass

from .model import Board, Cells, EMPTY, outcome

STRATEGIES = ("minimax", "alpha-beta", "memo", "symmetry")
# Tie breaking is deterministic, not an extra strength claim.
MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _maps() -> tuple[tuple[int, ...], ...]:
    transforms = set()
    for mirror in (False, True):
        for turns in range(4):
            mapping = []
            for i in range(9):
                r, c = divmod(i, 3)
                if mirror:
                    c = 2 - c
                for _ in range(turns):
                    r, c = c, 2 - r
                mapping.append(3 * r + c)
            transforms.add(tuple(mapping))
    return tuple(sorted(transforms))


TRANSFORMS = _maps()


def canonical(cells: Cells) -> Cells:
    """One key for all eight rotations/reflections, keeping X and O distinct."""
    return min(tuple(cells[i] for i in mapping) for mapping in TRANSFORMS)


@dataclass(frozen=True, slots=True)
class SearchStats:
    nodes: int
    terminals: int
    cache_hits: int
    cutoffs: int
    cache_entries: int


@dataclass(frozen=True, slots=True)
class Analysis:
    move: int | None
    score: int
    move_scores: tuple[tuple[int, int], ...]
    stats: SearchStats

    @property
    def best_moves(self) -> tuple[int, ...]:
        return tuple(move for move, score in self.move_scores if score == self.score)


def solve(board: Board, strategy: str = "symmetry") -> Analysis:
    """Return exact -1/0/+1 outcomes from the current player's perspective.

    Each invocation starts with an empty table. All root children receive a
    full search window, so *every* displayed move score is exact. A cache is
    never combined with alpha-beta bounds: the memo variants store only exact
    values, and the pruning variant has no transposition table.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    nodes, terminals, hits, cutoffs = 1, 0, 0, 0
    table: dict[Cells, int] = {}
    use_cache = strategy in ("memo", "symmetry")

    def value(cells: Cells, player: str, alpha: int = -2, beta: int = 2) -> int:
        nonlocal nodes, terminals, hits, cutoffs
        nodes += 1
        key = canonical(cells) if strategy == "symmetry" else cells
        if use_cache and key in table:
            hits += 1
            return table[key]
        result = outcome(cells)
        if result:
            terminals += 1
            answer = 0 if result == "D" else (1 if result == player else -1)
        else:
            answer = -2
            other = "O" if player == "X" else "X"
            for move in MOVE_ORDER:
                if cells[move] != EMPTY:
                    continue
                child = cells[:move] + (player,) + cells[move + 1:]
                score = -value(child, other, -beta, -alpha)
                answer = max(answer, score)
                if strategy == "alpha-beta":
                    alpha = max(alpha, score)
                    if alpha >= beta:
                        cutoffs += 1
                        break
        if use_cache:
            table[key] = answer
        return answer

    if board.result:
        score = 0 if board.result == "D" else -1
        return Analysis(None, score, (), SearchStats(1, 1, 0, 0, 0))
    other = "O" if board.turn == "X" else "X"
    scores = tuple((move, -value(board.cells[:move] + (board.turn,) + board.cells[move + 1:], other))
                   for move in MOVE_ORDER if board.cells[move] == EMPTY)
    best_score = max(score for _, score in scores)
    best_move = next(move for move, score in scores if score == best_score)
    return Analysis(best_move, best_score, scores,
                    SearchStats(nodes, terminals, hits, cutoffs, len(table)))
