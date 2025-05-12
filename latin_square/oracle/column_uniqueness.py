import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import (
    comparator_equal,
    column_pair_flags,
    Indexer
)

from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister


def column_uniqueness_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer
):
    """
    Appends to `qc` the circuit that:
      • flips a per‐column flag for each column iff any two cells in that column are equal,
      • then flips the single col_constraints_flag iff any column flag is set.
    All ancillas are borrowed from `idx` and released; the only qubits left
    possibly set are the constraint flags in qr.
    """
    k = idx.k
    n = idx.n

    # 1) Borrow ancillas: k for XNOR scratch + 1 for per‐pair target
    comp_anc_inds = idx.reserve_ancilla(k + 1)
    comp_anc = [qr[i] for i in comp_anc_inds]

    # 2) Borrow n qubits for the per‐column flags
    col_flag_inds = idx.reserve_ancilla(n)
    col_flags = [qr[i] for i in col_flag_inds]

    # 3) Identify the single global column‐constraints flag
    final_flag = qr[idx.col_flag()]

    # --- First sweep: compute each column's flag ---
    for j in range(n):
        column_pair_flags(qc,
                          data=qr,         # flat QR
                          anc=comp_anc,    # length = k+1
                          cflag=col_flags[j],
                          idx=idx,
                          col=j)

    # --- OR all col_flags into final_flag ---
    qc.mcx(col_flags, final_flag, ctrl_state='0'*n)
    qc.x(final_flag)

    # --- Second sweep: uncompute col_flags ---
    for j in range(n):
        column_pair_flags(qc,
                          data=qr,
                          anc=comp_anc,
                          cflag=col_flags[j],
                          idx=idx,
                          col=j)

    # 5) Release all borrowed ancillas
    idx.release_ancilla(comp_anc_inds + col_flag_inds)
