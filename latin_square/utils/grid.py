"""
grid.py

Utility functions for Latin-square grids:
  - verify_grid: ensure pre-filled grids are valid
  - pretty_print_grids: display result grids with counts
"""
from typing import List, Optional, Tuple, Dict


def verify_grid(
    grid: List[List[Optional[int]]],
    symbol_max: int
) -> bool:
    """
    Validate a partially filled grid for Latin-square constraints.

    Checks:
      1. Every non-None entry x satisfies 0 <= x < symbol_max.
      2. No row contains duplicate non-None symbols.
      3. No column contains duplicate non-None symbols.

    Parameters:
        grid:       2D list of integers or None.
        symbol_max: Upper bound on symbol values (exclusive).

    Returns:
        True if the grid is valid.

    Raises:
        ValueError: if the grid is empty, non-rectangular, has out-of-range symbols,
                    or contains duplicate symbols in any row or column.
    """
    n = len(grid)
    if n == 0:
        raise ValueError("Grid must have at least one row")
    m = len(grid[0])

    # Ensure all rows are the same length
    for i, row in enumerate(grid):
        if len(row) != m:
            raise ValueError(f"Row {i} has length {len(row)}, expected {m}")

    # Check cell values and row duplicates
    for i, row in enumerate(grid):
        seen_row = set()
        for j, v in enumerate(row):
            if v is not None:
                if not (0 <= v < symbol_max):
                    raise ValueError(f"Cell ({i},{j}) has invalid symbol {v}")
                if v in seen_row:
                    raise ValueError(f"Row {i} has duplicate symbol {v}")
                seen_row.add(v)

    # Check column duplicates
    for j in range(m):
        seen_col = set()
        for i in range(n):
            v = grid[i][j]
            if v is not None:
                if v in seen_col:
                    raise ValueError(f"Column {j} has duplicate symbol {v}")
                seen_col.add(v)

    return True


def pretty_print_grids(
    results: Dict[Tuple[int, ...], int],
    n: int,
    m: int
) -> None:
    """
    Print each grid configuration and its count in a formatted table.

    Parameters:
        results: Mapping from flat-state tuples (length n*m) to occurrence counts.
        n:       Number of rows in each grid.
        m:       Number of columns in each grid.
    """
    def format_grid(state: Tuple[int, ...]) -> str:
        # Break flat state into rows
        rows = [state[i*m:(i+1)*m] for i in range(n)]
        # Determine column width from the largest entry
        col_width = max(len(str(x)) for row in rows for x in row) + 2
        sep = "+" + "+".join("-" * col_width for _ in range(m)) + "+"

        lines = [sep]
        for row in rows:
            line = "|"
            for x in row:
                line += str(x).center(col_width) + "|"
            lines.append(line)
            lines.append(sep)
        return "\n".join(lines)

    # Display each grid and its count
    for state, count in results.items():
        print(f"Count = {count}")
        print(format_grid(state))
        print()
