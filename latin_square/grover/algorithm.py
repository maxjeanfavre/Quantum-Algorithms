"""
Core Grover search loop for the Latin-square problem.

This module provides:
  • implement_grover: append Grover iterations (oracle + phase-flip + diffuser).
"""
from typing import List
from qiskit import QuantumCircuit, QuantumRegister

from oracle.oracle import oracle
from utils.indexer import Indexer


def _diffuser(qc: QuantumCircuit, qubits: List[QuantumRegister]) -> None:
    """
    Apply the inversion-about-the-mean operator on the given data qubits.
    """
    qc.h(qubits)
    qc.x(qubits)
    qc.h(qubits[-1])
    qc.mcx(qubits[:-1], qubits[-1])
    qc.h(qubits[-1])
    qc.x(qubits)
    qc.h(qubits)


def implement_grover(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    iterations: int
) -> None:
    """
    Append the Grover search iterations to a circuit:

    Each iteration consists of:
      1. Oracle call to mark valid solutions via phase inversion.
      2. Phase-flip on the global constraint flag qubit.
      3. Oracle uncomputation to restore ancillas.
      4. Diffusion (_diffuser) on the data qubits to amplify amplitudes.

    Parameters:
        qc:         QuantumCircuit containing data + ancilla registers.
        qr:         QuantumRegister used in qc.
        idx:        Indexer for qubit mapping and metadata.
        iterations: Number of Grover iterations to apply.
    """
    # Collect all blanck data-qubit indices in row-major order
    data_blanck_qubits = [
        qr[idx.data(i, j, b)]
        for i in range(idx.n)
        for j in range(idx.m)
        if idx.grid[i][j] is None
        for b in range(idx.k)
    ]
    # Identify the global flag qubit
    global_flag = qr[idx.global_flag()]

    for _ in range(iterations):
        # 1) Apply the problem oracle
        oracle(qc, qr, idx)
        # 2) Phase-flip on the global flag qubit
        qc.x(global_flag)
        qc.z(global_flag)
        qc.x(global_flag)
        # 3) Uncompute the oracle to reset ancillas
        oracle(qc, qr, idx)
        # 4) Diffusion to amplify marked states
        _diffuser(qc, data_blanck_qubits)
