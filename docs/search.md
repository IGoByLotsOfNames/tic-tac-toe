# A complete search, small enough to inspect

The rules are ordinary tic-tac-toe: X moves first, players alternate, and a row, column or diagonal of three ends the game immediately. A full board with no winner is a draw.

## The board is a value

`Board` stores a tuple of nine cells. A move returns a new board; it cannot mutate a sibling branch of the search tree. Construction validates cell contents, move counts, simultaneous winners and whether the winning side could have moved last.

For 3×3 tic-tac-toe these checks exactly match the reachable positions. This is verified by comparing all `3^9 = 19,683` encodings with an independently generated game graph. It is not a general claim about larger games.

Terminal boards have no legal moves, even if some cells are empty. The `turn` property on a terminal board denotes the next *hypothetical* player. A won terminal position therefore has score −1 for that player; a draw has score 0. This keeps the negamax recurrence consistent at the boundary.

## Negamax

Let `V(board, player)` be the eventual outcome from the player-to-move's perspective: −1, 0 or +1. The value of an unfinished board is:

```text
V(board, player) = max(-V(child, other_player))
```

The sign changes because what is good for one player is bad for the other. Search continues to a terminal position; it does not use a learned model or a heuristic evaluation of unfinished boards.

The implementation intentionally scores only the outcome. It does not prefer a win in fewer moves. Moves with equal values follow this stable order, using the user-facing cell numbers:

```text
5, 1, 3, 7, 9, 2, 4, 6, 8
```

## Four strategies, one contract

**Plain minimax** evaluates every legal continuation. A state reached by different histories is searched again.

**Alpha-beta** carries a window of outcomes that can still matter to the parent. Once `alpha >= beta`, another child cannot improve the parent's decision, so the rest of that branch can be skipped. It has no transposition table. At the root, every candidate receives a full window (`-2` to `+2`). This costs more work than narrowing a shared root window, but gives the interface an exact outcome for *each* candidate rather than a mixture of exact answers and bounds.

**Memoisation** stores exact board values for the duration of one call to `solve`. It does not prune, so every cached result is exact. The side to move is implied by the board's X/O counts and need not be a separate key field.

**Symmetry-aware memoisation** uses the lexicographically smallest of the board's eight rotations/reflections as its key. Only values are cached, not moves. Therefore the engine never has to mistake a move in canonical coordinates for one on the player's actual board. Candidate moves are still evaluated in the original orientation.

Keeping pruning and exact-value caching separate avoids a subtle failure mode: caching an alpha-beta cut-off as though it were a fully evaluated score.

## What the counters mean

- `nodes`: one for the root, plus every recursive function call, including calls answered from a cache.
- `terminals`: terminal positions evaluated after cache lookup. A cached terminal answer does not add another terminal evaluation.
- `cache_hits`: calls answered by an existing exact value.
- `cutoffs`: branches where alpha-beta stops iterating remaining children.
- `cache_entries`: exact values stored at the end of that decision; the root is not stored.

Each `solve` call starts from an empty cache. There is no warmed global table making a later benchmark appear cheaper.

## Complexity

With branching factor `b` and remaining depth `d`, plain minimax takes `O(b^d)` time in the usual game-tree bound and `O(d)` recursion space. Tic-tac-toe's branching factor shrinks after every move and its maximum depth is nine. Alpha-beta has the same worst-case bound; the benefit depends on move ordering and available cut-offs.

Memoisation evaluates a state graph rather than repeating its whole history tree. With `V` reachable states and `E` legal transitions, it takes `O(V + E)` work and `O(V + d)` storage when board size is fixed. Symmetry canonicalisation examines eight transforms of nine cells per key, adding overhead while reducing the number of distinct cached states. Here there are 5,478 reachable boards and 765 symmetry classes, including the empty board.

Call-count reduction is not automatically equal to elapsed-time reduction. The committed benchmark deliberately reports deterministic counts; it makes no hardware-independent speed claim.
