import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import (
    comparator_less,
    prepare_ancilla_cell_validity,
    Indexer
)

from qiskit import QuantumCircuit, QuantumRegister
from math import ceil, log2

def cell_validity_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    threshold_n: int
):
    """
    On `qc` (using the flat register `qr` of size idx.total_qubits), flip
    qr[idx.cell_valid_flag()] iff any of the n×m cells ≥ threshold_n.
    Uses Bennett windows of size w = m (columns), one window per row,
    and returns ALL ancillas to |0> on exit.
    """
    k = idx.k             # bits to encode 0..threshold_n-1
    n = idx.n             # number of rows
    m = idx.m             # number of columns

    # 2) reserve ancilla: k for comparator, plus 2 for prepare/unprepare
    comp_anc_inds = idx.reserve_ancilla(k + 2)
    comp_anc_q = [qr[i] for i in comp_anc_inds]

    # wflag: one bit per column in a row
    wflag_inds = idx.reserve_ancilla(m)
    wflag_q = [qr[i] for i in wflag_inds]

    # iflag: one bit per row (one result per window)
    iflag_inds = idx.reserve_ancilla(n)
    iflag_q = [qr[i] for i in iflag_inds]

    fin_q = qr[idx.cell_valid_flag()]

    # 3) prepare the shared constant ancilla (2^k - threshold_n)
    prepare_ancilla_cell_validity(qc, comp_anc_q, threshold_n, k)

    # 4) first Bennett sweep: one window per row
    for i in range(n):
        # compute each cell ≥ threshold into wflag_q[j]
        for j in range(m):
            data_q = [ qr[q] for q in idx.cell_qubits(i, j) ]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

        # OR the m per-cell bits into iflag_q[i]
        qc.mcx(wflag_q, iflag_q[i], ctrl_state='0'*m)
        qc.x(iflag_q[i])

        # uncompute the per-cell flags
        for j in reversed(range(m)):
            data_q = [ qr[q] for q in idx.cell_qubits(i, j) ]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

    # 5) OR all row‐window bits into the final cell_valid_flag
    qc.mcx(iflag_q, fin_q, ctrl_state='0'*n)
    qc.x(fin_q)

    # 6) second Bennett sweep: restore iflag_q & wflag_q
    for i in range(n):
        for j in range(m):
            data_q = [ qr[q] for q in idx.cell_qubits(i, j) ]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

        qc.mcx(wflag_q, iflag_q[i], ctrl_state='0'*m)
        qc.x(iflag_q[i])

        for j in reversed(range(m)):
            data_q = [ qr[q] for q in idx.cell_qubits(i, j) ]
            comparator_less(qc, data_q, comp_anc_q, wflag_q[j], k)

    # 7) unprepare the shared constant ancilla
    prepare_ancilla_cell_validity(qc, comp_anc_q, threshold_n, k)

    # 8) release all ancillas
    idx.release_ancilla(comp_anc_inds + wflag_inds + iflag_inds)
