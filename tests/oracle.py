"""Independent test oracle: bitboards, no imports from production code."""

from functools import lru_cache

MASKS = (7, 56, 448, 73, 146, 292, 273, 84)


def terminal(x: int, o: int) -> int | None:
    if any(x & mask == mask for mask in MASKS):
        return 1
    if any(o & mask == mask for mask in MASKS):
        return -1
    return 0 if x | o == 511 else None


def states() -> dict[str, tuple[int, int]]:
    seen: dict[str, tuple[int, int]] = {}

    def walk(x: int, o: int, turn_x: bool) -> None:
        key = "".join("X" if x & (1 << i) else "O" if o & (1 << i) else "." for i in range(9))
        if key in seen:
            return
        seen[key] = (x, o)
        if terminal(x, o) is not None:
            return
        for i in range(9):
            bit = 1 << i
            if (x | o) & bit == 0:
                walk(x | bit if turn_x else x, o if turn_x else o | bit, not turn_x)

    walk(0, 0, True)
    return seen


@lru_cache(maxsize=None)
def x_value(x: int, o: int) -> int:
    result = terminal(x, o)
    if result is not None:
        return result
    turn_x = x.bit_count() == o.bit_count()
    children = [x_value(x | (1 << i), o) if turn_x else x_value(x, o | (1 << i))
                for i in range(9) if (x | o) & (1 << i) == 0]
    return max(children) if turn_x else min(children)
