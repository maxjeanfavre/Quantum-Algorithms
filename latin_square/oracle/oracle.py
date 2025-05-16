import sys, os
sys.path.append(os.path.dirname(os.getcwd()))

from qiskit import QuantumCircuit, QuantumRegister
from utils.indexer import Indexer
from oracle.row_uniqueness import row_uniqueness_circuit
from oracle.column_uniqueness import column_uniqueness_circuit
from oracle.cell_validity import cell_validity_circuit


def oracle(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
):
    """
    Appends to `qc` the full Latin-square validity oracle:
      1. Row-uniqueness → qr[idx.row_flag()]
      2. Column-uniqueness → qr[idx.col_flag()]
      3. Cell-validity      → qr[idx.cell_valid_flag()]
      4. Global flag = OR of the three above → qr[idx.global_flag()]

    All ancillas are borrowed and released inside the sub-circuits, and all
    intermediate flags are uncomputed at the end, leaving only the global flag.
    """
    # --- 1) Compute each constraint flag ---
    cell_validity_circuit(qc, qr, idx, max(idx.n, idx.m))
    row_uniqueness_circuit(qc, qr, idx)
    column_uniqueness_circuit(qc, qr, idx)


    # --- 2) Collapse into the single global flag ---
    controls = [
        qr[idx.cell_valid_flag()],
        qr[idx.row_flag()],
        qr[idx.col_flag()],
    ]
    global_q = qr[idx.global_flag()]
    ctrl_state = '0' * len(controls)
    qc.mcx(controls, global_q, ctrl_state=ctrl_state)
    qc.x(global_q)

    # --- 3) Uncompute the sub-oracles ---
    column_uniqueness_circuit(qc, qr, idx)
    row_uniqueness_circuit(qc, qr, idx)
    cell_validity_circuit(qc, qr, idx, max(idx.n, idx.m))
