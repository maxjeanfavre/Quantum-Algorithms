"""
Simulation and result processing for Grover-based Latin-square solver.

This module provides:
  • simulate_counts: run an Aer simulation, measure all qubits, and return raw bitstring counts
  • extract_grid_counts: aggregate raw counts into grid-value counts
"""
from typing import Dict, Tuple

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

from utils.indexer import Indexer


def simulate_counts(
    qc: QuantumCircuit,
    sim_type: str,
    shots: int = 1024
) -> Dict[str, int]:
    """
    Execute the given circuit on AerSimulator, measuring all qubits.

    Parameters:
        qc:        QuantumCircuit (should have measurements appended internally).
        sim_type:  Simulation method (e.g. 'matrix_product_state').
        shots:     Number of simulation shots.

    Returns:
        Raw counts mapping bitstring keys to occurrence counts.
    """
    # Copy circuit and ensure all qubits are measured
    circ = qc.copy()
    circ.measure_all()

    # Set up simulator and transpile
    sim = AerSimulator(method=sim_type, enable_truncation=True)
    tcirc = transpile(circ, sim, optimization_level=3)

    # Run simulation and return raw counts
    result = sim.run(tcirc, shots=shots).result()
    return result.get_counts()


def extract_grid_counts(
    raw_counts: Dict[str, int],
    idx: Indexer
) -> Dict[Tuple[int, ...], int]:
    """
    Transform raw bitstring counts into counts by grid configurations.

    Parameters:
        raw_counts: Mapping from bitstring (MSB->LSB) to counts.
        idx:        Indexer for qubit mapping (n, m, k, data qubits).

    Returns:
        Mapping from flat grid-value tuples to aggregated counts.
    """
    n, m, k = idx.n, idx.m, idx.k
    aggregated: Dict[Tuple[int, ...], int] = {}

    for bitstr, cnt in raw_counts.items():
        # Reverse bitstring to have index match qubit index
        bits = list(map(int, bitstr[::-1]))

        # Reconstruct flat grid values
        flat = []
        for i in range(n):
            for j in range(m):
                v = 0
                for b in range(k):
                    v |= bits[idx.data(i, j, b)] << b
                flat.append(v)

        key = tuple(flat)
        aggregated[key] = aggregated.get(key, 0) + cnt

    return aggregated
