"""
Helper routines and “quantum macros” for building and composing small Qiskit circuits.
Includes ancilla preparation, comparators, and context-manager utilities.
"""

import math
from typing import List, Iterable, Sequence, Optional, Tuple, ContextManager
from contextlib import contextmanager

from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit
from qiskit.circuit.library import CDKMRippleCarryAdder


def prepare_ancilla_cell_validity(qc: QuantumCircuit, anc: QuantumRegister, n: int, k: int) -> None:
    """
    Initialize ancillas such that anc[0..k-1] store the bitwise representation of (2**k - n),
    and anc[k], anc[k+1] remain in |0⟩.
    """
    const = (1 << k) - n
    for i in range(k):
        if (const >> i) & 1:
            qc.x(anc[i])


def comparator_less(
    qc: QuantumCircuit,
    dataQ: Sequence[Qubit],
    anc: Sequence[Qubit],
    target: Qubit,
    k: int
) -> None:
    """
    Compare dataQ (k qubits) against a stored constant in anc[0..k-1], flipping `target` if dataQ ≥ n.
    Uses CDKM ripple-carry adder: computes sum+carry, copies overflow, then uncomputes.
    """
    gate = CDKMRippleCarryAdder(k, kind="half").to_gate(label="ADD")
    qubits = list(dataQ) + list(anc)
    qc.append(gate, qubits)
    qc.cx(anc[k], target)
    qc.append(gate.inverse(), qubits)


def comparator_equal(
    qc: QuantumCircuit,
    q1: List[Qubit],
    q2: List[Qubit],
    anc: List[Qubit],
    target: Qubit,
    k: int
) -> None:
    """
    Flip `target` if and only if the two k-qubit registers q1 and q2 are equal.
    Implements bitwise XNOR into anc[0..k-1], then an MCX, then uncomputes.
    """
    for i in range(k):
        qc.cx(q1[i], anc[i])
        qc.cx(q2[i], anc[i])
        qc.x(anc[i])

    qc.mcx(anc[:k], target)

    for i in reversed(range(k)):
        qc.x(anc[i])
        qc.cx(q2[i], anc[i])
        qc.cx(q1[i], anc[i])
