# From a Pygame experiment to a checked game engine

The starting point was my earlier single-file `TicTacToe.py`: a 1,145-line Pygame project with a graphical board, scorekeeping, local multiplayer, several computer difficulty modes and experiments with game-tree evaluation.

Revisiting it exposed a useful engineering problem. Rendering, mutable board state and search were tightly coupled, making it difficult to establish that every search branch followed the rules or that a difficulty setting was making the intended decision. The original computer player had not been verified as unbeatable.

This repository contains a maintained rewrite of that idea, rather than presenting the historical implementation as a finished solver. The original archive remains unchanged.

| Earlier experiment | Current edition |
|---|---|
| Shared mutable state across UI and search | Frozen board values and legal transitions |
| Difficulty modes intertwined with rendering | Exact search and relaxed randomness behind the same interface |
| Search could continue past some winning positions | Terminal wins stop every branch immediately |
| Manual play as the main correctness check | Independent oracle over the entire legal state space |
| Pygame menus and a graphical board | Tkinter desktop game plus a display-free CLI |
| Heuristic scoring experiments | Explicit win/draw/loss contract and measured search variants |

The redesign keeps the part I enjoyed: a familiar game where a small move can create a fork, force a block or turn into another draw. It also makes the algorithm explainable. Every legal move has a solved outcome, and the displayed counters reveal how much work each search strategy performed.

No historical usage, award, deployment or external evaluation is claimed for this game. The test results and measurements in this repository describe the current implementation.
