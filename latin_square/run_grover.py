"""
run.py

End-to-end runner for the Grover-based Latin-square solver.
This script defines a function `run_grover` that takes a grid and expected
solution count, then builds the circuit, runs Grover iterations, simulates,
and prints intermediate and final results. It is intended to be called
from a notebook or other driver code that defines the grid.
"""
import sys, os
sys.path.append(os.path.dirname(__file__))

from typing import List, Optional
from math import ceil, log2
from utils.grid import pretty_print_grids
from grover.circuit import create_circuit
from grover.algorithm import implement_grover
from grover.simulation import simulate_counts, extract_grid_counts
from grover.params import total_possibilities, optimal_grover_iterations
from utils.plotting import plot_grid_counts_histogram


def run_grover(
    grid: List[List[Optional[int]]],
    num_solutions: int,
    sim_type: str = "statevector",
    shots: int = 1024
) -> None:
    """
    Execute the full Grover-based search on a given partially filled grid.

    Parameters
    ----------
    grid : List[List[Optional[int]]]
        2D grid where None indicates an empty cell.
    num_solutions : int
        Known or assumed number of valid completions (M).
    sim_type : str, optional
        AerSimulator method, by default "matrix_product_state".
    shots : int, optional
        Number of simulation shots, by default 1024.

    Prints
    ------
    - Initial grid
    - Total possibility count N
    - Number of solutions M
    - Optimal iteration count r
    - Raw measurement counts
    - Aggregated final grid counts
    """
    # Derive dimensions
    n = len(grid)
    m = len(grid[0]) if n > 0 else 0
    k = ceil(log2(max(n,m)))

    # 1) Display the input grid
    flat = tuple(x for row in grid for x in row)
    print("Initial grid:")
    pretty_print_grids({flat: 1}, n, m)

    # 2) Compute search-space size and iteration count
    N = total_possibilities(grid, k)
    M = num_solutions
    print(f"Total possibilities N = {N}")
    print(f"Number of solutions M = {M}")
    r = optimal_grover_iterations(N, M)
    print(f"Optimal Grover iterations r = {r}\n")

    # 3) Build and initialize the quantum circuit
    qc, qr, idx = create_circuit(grid)

    # 4) Append Grover iterations
    implement_grover(qc, qr, idx, r)
    # Resource metrics: report qubit count, circuit depth, and total gates
    print(f"Total qubits used: {qc.num_qubits}")
    print(f"Circuit depth: {qc.depth()}")
    print(f"Total gates: {qc.size()}\n")

    # 5) Simulate and collect raw counts
    raw_counts = simulate_counts(qc, sim_type, shots)

    # 6) Aggregate counts by final grid configurations
    grid_counts = extract_grid_counts(raw_counts, idx)
    print("Aggregated grid counts:")
    pretty_print_grids(grid_counts, n, m)

    # 7) Plot histogram of final grid counts
    plot_grid_counts_histogram(grid_counts, n, m)
