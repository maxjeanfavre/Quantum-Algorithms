import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import comparator_equal
from utils.indexer import Indexer

from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit


def row_pair_flags(
    qc: QuantumCircuit,
    data: QuantumRegister,
    anc: QuantumRegister,
    flag1: QuantumRegister,
    flag2: QuantumRegister,
    rflag: Qubit,
    idx: Indexer,
    row: int
):
    """
    For a single row `row`, compare every pair of columns (c1 < c2).
    If any two cells in that row are equal, flip the violation flag `rflag`.
    Leaves all ancilla and data qubits restored to their original state.

    Parameters:
        qc:     The QuantumCircuit to modify.
        data:   QuantumRegister holding the grid data (n * m * k qubits).
        anc:    QuantumRegister providing k scratch qubits for XNOR operations.
        flag1:  QuantumRegister of length m for per-column OR results.
        flag2:  QuantumRegister of length m-1 for per-pair equality flags.
        rflag:  Single-qubit flag for any equality violation in this row.
        idx:    Indexer instance for qubit indexing and metadata.
        row:    Row index to check.
    """
    n, m, k = idx.n, idx.m, idx.k

    # Validate ancilla register sizes
    if len(anc) < k:
        raise ValueError(f"anc register must have at least {k} qubits for scratch")
    if len(flag1) < m:
        raise ValueError(f"flag1 register must have at least {m} qubits for column flags")
    if len(flag2) < m-1:
        raise ValueError(f"flag2 register must have at least {m-1} qubits for pair flags")

    # Compute equality flags for each column pair
    for c1 in range(m-1):
        for c2 in range(c1+1, m):
            # Extract k-bit cell values for columns c1 and c2
            q1 = [data[idx.data(row, c1, b)] for b in range(k)]
            q2 = [data[idx.data(row, c2, b)] for b in range(k)]
            # Flip flag2[c2-1] if q1 == q2
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)

        # OR the pair-wise flags into a column-level flag
        qc.mcx(flag2, flag1[c1], ctrl_state='0'*(m-1))  # multi-control on all zeros
        qc.x(flag1[c1])  # record if any equality occurred

        # Uncompute pair flags to reset ancillas
        for c2 in range(c1+1, m):
            q1 = [data[idx.data(row, c1, b)] for b in range(k)]
            q2 = [data[idx.data(row, c2, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)

    # OR all column-level flags into the row-level violation flag
    qc.mcx(flag1, rflag, ctrl_state='0'*m)
    qc.x(rflag)

    # Final cleanup: uncompute all intermediate flags
    for c1 in range(m-1):
        for c2 in range(c1+1, m):
            q1 = [data[idx.data(row, c1, b)] for b in range(k)]
            q2 = [data[idx.data(row, c2, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)
        qc.mcx(flag2, flag1[c1], ctrl_state='0'*(m-1))
        qc.x(flag1[c1])
        for c2 in range(c1+1, m):
            q1 = [data[idx.data(row, c1, b)] for b in range(k)]
            q2 = [data[idx.data(row, c2, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)


def row_uniqueness_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer
):
    """
    Appends row-uniqueness checks:
      1. Compute a per-row flag if any two cells in that row match.
      2. OR all per-row flags into a single global constraint flag.
      3. Uncompute intermediate flags, leaving only the final constraint qubit set.

    All ancillas are managed and released via the Indexer.

    Parameters:
        qc:  QuantumCircuit to extend.
        qr:  Combined data and ancilla QuantumRegister.
        idx: Indexer for qubit allocation and grid dimensions (n, m, k).
    """
    n, m, k = idx.n, idx.m, idx.k

    # Reserve ancillas and flags from the Indexer
    comp_anc_inds = idx.reserve_ancilla(k)
    comp_anc = [qr[i] for i in comp_anc_inds]

    flag1_inds = idx.reserve_ancilla(m)
    flag1 = [qr[i] for i in flag1_inds]

    flag2_inds = idx.reserve_ancilla(m-1)
    flag2 = [qr[i] for i in flag2_inds]

    row_flag_inds = idx.reserve_ancilla(n)
    row_flags = [qr[i] for i in row_flag_inds]

    final_flag = qr[idx.row_flag()]

    # First pass: compute each per-row violation flag
    for i in range(n):
        row_pair_flags(
            qc, qr, comp_anc, flag1, flag2, row_flags[i], idx, i
        )

    # Aggregate per-row flags into the final flag
    qc.mcx(row_flags, final_flag, ctrl_state='0'*n)
    qc.x(final_flag)

    # Second pass: uncompute per-row flags to release ancillas
    for i in range(n):
        row_pair_flags(
            qc, qr, comp_anc, flag1, flag2, row_flags[i], idx, i
        )

    # Release all borrowed ancillas
    idx.release_ancilla(comp_anc_inds + flag1_inds + flag2_inds + row_flag_inds)