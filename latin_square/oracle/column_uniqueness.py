import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import comparator_equal
from utils.indexer import Indexer

from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Qubit


def column_pair_flags(
    qc: QuantumCircuit,
    data: QuantumRegister,
    anc: QuantumRegister,
    flag1: QuantumRegister,
    flag2: QuantumRegister,
    cflag: Qubit,
    idx: Indexer,
    col: int
):
    """
    For a single column `col`, compare every pair of rows (r1 < r2).
    If any two cells in that column are equal, flip the violation flag `cflag`.
    Leaves all ancilla and data qubits restored to their original state.

    Parameters:
        qc:     The QuantumCircuit to modify.
        data:   QuantumRegister holding the grid data (n × m × k qubits).
        anc:    QuantumRegister providing k scratch qubits for XNOR operations.
        flag1:  QuantumRegister of length n for per-row OR results.
        flag2:  QuantumRegister of length n-1 for per-pair equality flags.
        cflag:  Single-qubit flag for any equality violation in this column.
        idx:    Indexer instance for qubit indexing and metadata.
        col:    Column index to check.
    """
    n, m, k = idx.n, idx.m, idx.k

    # Validate ancilla register sizes
    if len(anc) < k:
        raise ValueError(f"anc register must have at least {k} qubits for scratch")
    if len(flag1) < n:
        raise ValueError(f"flag1 register must have at least {n} qubits for row flags")
    if len(flag2) < n-1:
        raise ValueError(f"flag2 register must have at least {n-1} qubits for pair flags")

    # Compute equality flags for each row pair
    for r1 in range(n-1):
        for r2 in range(r1+1, n):
            # Extract k-bit cell values for rows r1 and r2
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            # Flip flag2[r2-1] if q1 == q2
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)

        # OR the pair-wise flags into a row-level flag
        qc.mcx(flag2, flag1[r1], ctrl_state='0'*(n-1))  # multi-control on all zeros
        qc.x(flag1[r1])  # invert to record if any equality occurred

        # Uncompute pair flags to reset ancillas
        for r2 in range(r1+1, n):
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)

    # OR all row-level flags into the column-level violation flag
    qc.mcx(flag1, cflag, ctrl_state='0'*n)
    qc.x(cflag)

    # Final cleanup: uncompute all intermediate flags
    for r1 in range(n-1):
        for r2 in range(r1+1, n):
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)
        qc.mcx(flag2, flag1[r1], ctrl_state='0'*(n-1))
        qc.x(flag1[r1])
        for r2 in range(r1+1, n):
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)


def column_uniqueness_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer
):
    """
    Appends column-uniqueness checks:
      1. Compute a per-column flag if any two cells in that column match.
      2. OR all per-column flags into a single global constraint flag.
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

    flag1_inds = idx.reserve_ancilla(n)
    flag1 = [qr[i] for i in flag1_inds]

    flag2_inds = idx.reserve_ancilla(n-1)
    flag2 = [qr[i] for i in flag2_inds]

    col_flag_inds = idx.reserve_ancilla(m)
    col_flags = [qr[i] for i in col_flag_inds]

    final_flag = qr[idx.col_flag()]

    # First pass: compute each per-column violation flag
    for j in range(m):
        column_pair_flags(
            qc, qr, comp_anc, flag1, flag2, col_flags[j], idx, j
        )

    # Aggregate per-column flags into the final flag
    qc.mcx(col_flags, final_flag, ctrl_state='0'*m)
    qc.x(final_flag)

    # Second pass: uncompute per-column flags to release ancillas
    for j in range(m):
        column_pair_flags(
            qc, qr, comp_anc, flag1, flag2, col_flags[j], idx, j
        )

    # Release all borrowed ancillas
    idx.release_ancilla(comp_anc_inds + flag1_inds + flag2_inds + col_flag_inds)
