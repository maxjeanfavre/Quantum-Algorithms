from math import ceil, floor, log2, pi, sqrt
from typing import List, Tuple
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from utils.helpers import Indexer
from oracle.oracle import oracle  # your combined row/col/cell + global‐flag oracle


def create_circuit(grid: List[int], n: int) -> Tuple[QuantumCircuit, QuantumRegister, Indexer]:
    """
    1) Build Indexer(n, num_anc) with enough ancilla for all sub-oracles.
    2) Allocate one flat QuantumRegister of size idx.total_qubits.
    3) Load `grid` (row-major, length n*n) into the first n*n*idx.k qubits.
    Returns (qc, qr, idx).
    """
    # bits per cell
    k = max(1, ceil(log2(n)))
    # need ancilla = 2*n + k + 2  (peak ancilla for cell_validity)
    #num_anc = 2*n + k + 2
    num_anc = n + k + 2
    idx = Indexer(n, num_anc)

    qr = QuantumRegister(idx.total_qubits, name="q")
    qc = QuantumCircuit(qr, name="grover_sudoku")

    # load grid values (grid is a flat list of length n*n)
    for i in range(n):
        for j in range(n):
            val = grid[i*n + j]
            for b in range(idx.k):
                if (val >> b) & 1:
                    qc.x(qr[idx.data(i, j, b)])

    return qc, qr, idx


def implement_grover(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    iterations: int
) -> None:
    """
    Appends `iterations` rounds of:
      1) phase‐oracle via `oracle(qc, qr, idx, threshold_n)`
      2) phase‐kickback on idx.global_flag()
      3) uncompute oracle
      4) diffusion on data qubits
    """
    # diffusion helper
    def diffuser(qc: QuantumCircuit, qubits: List[int]):
        qc.h(qubits)
        qc.x(qubits)
        qc.h(qubits[-1])
        qc.mcx(qubits[:-1], qubits[-1])
        qc.h(qubits[-1])
        qc.x(qubits)
        qc.h(qubits)

    # collect data‐qubit indices
    data_qubits = [
        qr[idx.data(i, j, b)]
        for i in range(idx.n)
        for j in range(idx.n)
        for b in range(idx.k)
    ]
    gf = qr[idx.global_flag()]

    for _ in range(iterations):
        # --- phase‐oracle ---
        oracle(qc, qr, idx)
        qc.x(gf); qc.z(gf); qc.x(gf)       # phase‐flip on valid states
        oracle(qc, qr, idx)   # uncompute

        # --- diffuser ---
        diffuser(qc, data_qubits)


def simulate_all_and_extract(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    sim_type: str,
    shots: int = 1024
) -> dict[tuple[int, ...], int]:
    """
    Measure *all* qubits, simulate on Aer, and extract only the grid configurations.
    Returns a dict mapping tuple(grid_values) -> count.
    """
    # 1) Copy & measure everything
    circ = qc.copy()
    circ.measure_all()

    # 2) Simulate on statevector for speed
    sim = AerSimulator(method=sim_type,enable_truncation=True)
    tcirc = transpile(circ, sim, optimization_level=3)
    raw_counts = sim.run(tcirc, shots=shots).result().get_counts()

    # 3) Aggregate counts by grid alone
    out: dict[tuple[int, ...], int] = {}
    n = idx.n
    k = idx.k

    for bitstr, cnt in raw_counts.items():
        # reverse so bit i corresponds to qubit i
        bits = [int(b) for b in bitstr[::-1]]

        # rebuild the n×n grid values
        grid_vals = []
        for i in range(n):
            for j in range(n):
                v = 0
                base = (i * n + j) * k
                for b in range(k):
                    v |= (bits[base + b] << b)
                grid_vals.append(v)

        key = tuple(grid_vals)
        out[key] = out.get(key, 0) + cnt

    return out


def optimal_grover_iterations(n: int, num_solutions: int = 1) -> int:
    # k = bits per cell
    k = max(1, ceil(log2(n)))
    # total data qubits
    num_data_qubits = n * n * k
    # size of search space
    N = 2**num_data_qubits
    # optimal iterations
    return floor((pi / 4) * sqrt(N / num_solutions))