import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import (
    comparator_less,
    prepare_ancilla_cell_validity,
    Indexer
)

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from math import ceil, log2


# Assumes prepare_ancilla and comparator are already in scope


def cell_validity_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    threshold_n: int
):
    """
    On `qc` (using the flat register `qr` of size idx.total_qubits), flip
    qr[idx.cell_valid_flag()] iff any of the n×n cells ≥ threshold_n.
    Uses Bennett windows of size w = n (so n_win = n), and returns ALL
    ancillas to |0> on exit.
    """
    # 1) parameters
    k   = idx.k         # = ceil(log2(threshold_n))
    n   = idx.n         # grid dimension
    m   = n * n         # total cells
    # w = n, n_win = n

    # 2) reserve & slice your ancilla pools
    comp_anc = idx.reserve_ancilla(k + 2)
    comp_anc_q = [qr[q] for q in comp_anc]

    wflag = idx.reserve_ancilla(n)
    wflag_q = [qr[q] for q in wflag]

    iflag = idx.reserve_ancilla(n)
    iflag_q = [qr[q] for q in iflag]

    fin_q = qr[idx.cell_valid_flag()]

    # 3) prepare the shared constant ancilla
    prepare_ancilla_cell_validity(qc, comp_anc_q, threshold_n, k)

    # 4) first Bennett sweep (n windows of size n)
    for win in range(n):
        first = win * n
        # compute each cell’s flag into wflag_q[j]
        for j in range(n):
            cell_idx = first + j
            i, jcell = divmod(cell_idx, n)
            data_q = [qr[q] for q in idx.data_bits(i, jcell)]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

        # OR that window into iflag_q[win]
        qc.mcx(wflag_q, iflag_q[win], ctrl_state='0'*n)
        qc.x(iflag_q[win])

        # uncompute the per‐cell flags
        for j in reversed(range(n)):
            cell_idx = first + j
            i, jcell = divmod(cell_idx, n)
            data_q = [qr[q] for q in idx.data_bits(i, jcell)]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

    # 5) OR all iflag_q bits into fin_q
    qc.mcx(iflag_q, fin_q, ctrl_state='0'*n)
    qc.x(fin_q)

    # 6) second Bennett sweep (restore iflag_q & wflag_q)
    for win in range(n):
        first = win * n
        for j in range(n):
            cell_idx = first + j
            i, jcell = divmod(cell_idx, n)
            data_q = [qr[q] for q in idx.data_bits(i, jcell)]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

        qc.mcx(wflag_q, iflag_q[win], ctrl_state='0'*n)
        qc.x(iflag_q[win])

        for j in reversed(range(n)):
            cell_idx = first + j
            i, jcell = divmod(cell_idx, n)
            data_q = [qr[q] for q in idx.data_bits(i, jcell)]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

    # 7) unprepare the shared constant ancilla
    prepare_ancilla_cell_validity(qc, comp_anc_q, threshold_n, k)

    # 8) release all ancillas back to the pool
    idx.release_ancilla(comp_anc + wflag + iflag)