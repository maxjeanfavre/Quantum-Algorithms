# grover/params.py

from typing import List, Optional
from math import floor, pi, sqrt

def count_blanks(grid: List[List[Optional[int]]]) -> int:
    """
    Count how many entries in the grid are None (i.e. need to be filled).
    """
    return sum(1 for row in grid for cell in row if cell is None)

def total_possibilities(
    grid: List[List[Optional[int]]],
    bit_width: int
) -> int:
    """
    Compute the size of the quantum superposition search space for blank cells.

    Each blank cell is encoded in `bit_width` qubits, giving 2**bit_width states per cell.
    For B blank cells, total possibilities:
        N = 2**(B * bit_width)

    Parameters:
        grid:       Partially filled grid with None for blanks.
        bit_width:  Number of qubits used per cell.

    Returns:
        Total number of basis states over all blank cells.
    """
    blanks = count_blanks(grid)
    return 2 ** (blanks * bit_width)

def optimal_grover_iterations(
    N: int,
    M: int
) -> int:
    """
    Given search-space size N and known number of solutions M,
    return the standard Grover iteration count floor((π/4) * sqrt(N/M)).
    """
    return floor((pi / 4) * sqrt(N / M))
