from math import ceil, floor, log2, pi, sqrt
from typing import List, Tuple
from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

from utils.helpers import Indexer
from oracle.oracle import oracle   # your combined row/col/cell oracle

def create_circuit(
    grid: List[List[int]]
) -> Tuple[QuantumCircuit, QuantumRegister, Indexer]:
    """
    1) Build Indexer(grid, num_anc) with enough ancilla for all sub-oracles.
    2) Allocate one flat QuantumRegister of size idx.total_qubits.
    3) Load `grid` (row-major) into the first n*m*idx.k qubits.
    Returns (qc, qr, idx).
    """
    n = len(grid)         # # of rows
    m = len(grid[0])      # # of columns
    k = max(1, int(ceil(log2(max(n, m)))))
    # pick enough ancilla to cover cell‐validity, row/col‐uniqueness, etc.
    num_anc = max(
        k + 2 + n + m,      # cell‐validity needs k+2 + n + m
        k + 2*m + n - 1,    # row‐uniqueness
        k + 2*n + m - 1     # col‐uniqueness
    )

    idx = Indexer(grid, num_anc)
    qr  = QuantumRegister(idx.total_qubits, name="q")
    qc  = QuantumCircuit(qr, name="grover_general")

    # load the pre-filled cells / H on empty ones
    idx.initialize_grid(qc)
    return qc, qr, idx


def implement_grover(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    iterations: int
) -> None:
    """
    Appends `iterations` rounds of:
      1) phase‐oracle via `oracle(qc, qr, idx)`
      2) phase‐kickback on idx.global_flag()
      3) uncompute oracle
      4) diffusion on data qubits
    """
    # build diffuser on the data qubits
    def diffuser(qc, qubits):
        qc.h(qubits)
        qc.x(qubits)
        qc.h(qubits[-1])
        qc.mcx(qubits[:-1], qubits[-1])
        qc.h(qubits[-1])
        qc.x(qubits)
        qc.h(qubits)

    # collect data‐qubit indices in row-major order
    data_qubits = [
        qr[idx.data(i, j, b)]
        for i in range(idx.n)
        for j in range(idx.m)
        for b in range(idx.k)
    ]
    gf = qr[idx.global_flag()]

    for _ in range(iterations):
        oracle(qc, qr, idx)
        # phase‐flip on the “good” global flag
        qc.x(gf); qc.z(gf); qc.x(gf)
        oracle(qc, qr, idx)   # uncompute
        diffuser(qc, data_qubits)


def simulate_all_and_extract(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    sim_type: str,
    shots: int = 1024
) -> dict[tuple[int, ...], int]:
    """
    Measure *all* qubits, simulate on Aer, and aggregate counts by
    the grid configuration alone (ignoring flags).
    Returns a dict mapping tuple(grid_values) -> count.
    """
    circ = qc.copy()
    circ.measure_all()
    sim   = AerSimulator(method=sim_type, enable_truncation=True)
    tcirc = transpile(circ, sim, optimization_level=3)
    raw   = sim.run(tcirc, shots=shots).result().get_counts()

    n, m, k = idx.n, idx.m, idx.k
    out: dict[tuple[int, ...], int] = {}

    for bitstr, cnt in raw.items():
        bits = list(map(int, bitstr[::-1]))  # qubit 0 at bits[0]

        # rebuild the n×m grid
        flat = []
        for i in range(n):
            for j in range(m):
                v = 0
                for b in range(k):
                    v |= (bits[idx.data(i, j, b)] << b)
                flat.append(v)

        out[tuple(flat)] = out.get(tuple(flat), 0) + cnt

    return out


def optimal_grover_iterations(
    idx: Indexer,
    num_solutions: int = 1
) -> int:
    """
    Returns the usual floor((π/4)√(N/M)) for
    N = 2^(n*m*k) data states, M = num_solutions.
    """
    n, m, k = idx.n, idx.m, idx.k
    N = 2 ** (n * m * k)
    return floor((pi / 4) * sqrt(N / num_solutions))


import itertools

def count_possibilities_and_solutions(grid):
    """
    Given an n x m grid with entries either None or an integer in [0..n-1],
    returns (total_possibilities, total_solutions), where:
    - total_possibilities = n^(# of None cells)
    - total_solutions = number of completions satisfying row- and column-uniqueness
    """
    n = len(grid)           # number of rows
    m = len(grid[0]) if n > 0 else 0  # number of columns
    # Domain of symbols is 0..n-1
    domain = list(range(n))
    
    # Identify positions to fill
    blanks = [(i, j) for i in range(n) for j in range(m) if grid[i][j] is None]
    total_possibilities = len(domain) ** len(blanks)
    
    # Check function
    def is_valid_assignment(assignments):
        # Create filled grid
        filled = [row[:] for row in grid]
        for (i, j), val in zip(blanks, assignments):
            filled[i][j] = val
        # Check row uniqueness
        for row in filled:
            if len(set(row)) != len(row):
                return False
        # Check column uniqueness
        for j in range(m):
            col = [filled[i][j] for i in range(n)]
            if len(set(col)) != len(col):
                return False
        return True

    total_solutions = 0
    for assignment in itertools.product(domain, repeat=len(blanks)):
        if is_valid_assignment(assignment):
            total_solutions += 1

    r = floor((pi / 4) * sqrt(total_possibilities / total_solutions))

    return r, total_possibilities, total_solutions


