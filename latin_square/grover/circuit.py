"""
Circuit construction for the Grover-based Latin-square solver.

This module provides:
  • create_circuit: build and initialize the quantum circuit for a given grid.
"""
from math import ceil, log2
from typing import List, Tuple

from qiskit import QuantumCircuit, QuantumRegister

from utils.indexer import Indexer
from utils.grid import verify_grid


def create_circuit(
    grid: List[List[int]]
) -> Tuple[QuantumCircuit, QuantumRegister, Indexer]:
    """
    Construct and initialize the quantum circuit for solving a partially filled Latin square.

    Steps:
      1. Determine grid dimensions n (rows) and m (columns) and bit-width k = ceil(log2(max(n,m))).
      2. Validate the input grid structure and pre-filled values via verify_grid.
      3. Compute the number of ancilla qubits needed to implement the cell-validity and uniqueness oracles.
      4. Instantiate an Indexer for qubit indexing and metadata.
      5. Allocate a flat QuantumRegister of size idx.total_qubits.
      6. Load the pre-filled grid into data qubits (and apply Hadamard on empty cells).

    Parameters:
        grid: 2D list representing the Latin square pre-fill (integers in [0..symbol_max) or None).

    Returns:
        qc:  QuantumCircuit containing the initialized data + ancilla register.
        qr:  QuantumRegister of size idx.total_qubits.
        idx: Indexer for qubit-mapping and ancilla management.
    """
    # 1) Grid dimensions and bit-width
    n = len(grid)
    m = len(grid[0]) if n > 0 else 0
    k = max(1, int(ceil(log2(max(n, m)))))

    # 2) Validate grid pre-fills
    verify_grid(grid, max(n, m))

    # 3) Estimate ancilla count for all sub-oracles
    num_anc = max(
        k + 2 + n + m,      # cell-validity: k+2 constant + n row-flags + m column-flags
        k + 2*m + n - 1,    # row-uniqueness: k scratch + 2m window flags + n−1 row flags
        k + 2*n + m - 1     # column-uniqueness: k scratch + 2n window flags + m−1 col flags
    )

    # 4) Create Indexer and registers
    idx = Indexer(grid, num_anc)
    qr  = QuantumRegister(idx.total_qubits, name="q")
    qc  = QuantumCircuit(qr, name="grover_circuit")

    # 5) Load grid into circuit
    idx.initialize_grid(qc)

    return qc, qr, idx
