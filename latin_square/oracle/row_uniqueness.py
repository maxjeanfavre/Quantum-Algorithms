import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import (
    comparator_equal,
    row_pair_flags,
    Indexer
)

from math import ceil, log2
from qiskit import QuantumCircuit, QuantumRegister
from utils.helpers import comparator_equal
from utils.helpers import Indexer  # or wherever your Indexer lives


def row_uniqueness_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer
):
    """
    Appends to `qc` the circuit that:
      • flips a per‐row flag for each row iff any two cells in that row are equal,
      • then flips the single row_constraints_flag iff any row flag is set.
    All ancillas are borrowed from `idx` and released; the only qubits left
    possibly set are the constraint flags in qr.
    """
    n, m, k = idx.n, idx.m, idx.k

    # 1) Borrow ancillas: k for XNOR scratch + 1 for per‐pair target
    comp_anc_inds = idx.reserve_ancilla(k)
    comp_anc = [qr[i] for i in comp_anc_inds]

    # 2) Borrow m-1 qubits for the flag1 needed in row_pair_flags
    flag1_inds = idx.reserve_ancilla(m)
    flag1 = [qr[i] for i in flag1_inds]

    # 3) Borrow m qubits for the flag2 needed in row_pair_flags
    flag2_inds = idx.reserve_ancilla(m-1)
    flag2 = [qr[i] for i in flag2_inds]

    # 4) Borrow n qubits for the per‐row flags
    row_flag_inds = idx.reserve_ancilla(n)
    row_flags = [qr[i] for i in row_flag_inds]

    # 5) Identify the single global row‐constraints flag
    final_flag = qr[idx.row_flag()]

    # --- First sweep: compute each row's flag ---
    for i in range(n):
        row_pair_flags(qc,
                       data=qr,          # flat QR
                       anc=comp_anc,     # is length
                       flag1=flag1,
                       flag2=flag2,
                       rflag=row_flags[i],
                       idx=idx,
                       row=i)

    # --- OR all row_flags into final_flag ---
    qc.mcx(row_flags, final_flag, ctrl_state='0'*n)
    qc.x(final_flag)

    # --- Second sweep: uncompute row_flags ---
    for i in range(n):
        row_pair_flags(qc,
                       data=qr,          # flat QR
                       anc=comp_anc,     # is length
                       flag1=flag1,
                       flag2=flag2,
                       rflag=row_flags[i],
                       idx=idx,
                       row=i)

    # 5) Release all borrowed ancillas
    idx.release_ancilla(comp_anc_inds + flag1_inds + flag2_inds + row_flag_inds)
