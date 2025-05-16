import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from utils.helpers import comparator_less, prepare_ancilla_cell_validity
from utils.indexer import Indexer

from qiskit import QuantumCircuit, QuantumRegister


def cell_validity_circuit(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    idx: Indexer,
    threshold_n: int
):
    """
    Check each cell against a threshold and flag if any value exceeds it.
    Processes the grid row by row:
      1. Prepare constant ancillas for comparison (2**k - threshold_n).
      2. For each row, compare each of its m cells to the threshold, recording results in cell_flags.
      3. Aggregate per-cell flags into a per-row flag if any cell in the row is above the threshold.
      4. Combine all per-row flags into the final validity flag.
    All ancillas are restored to |0> when complete.

    Parameters:
        qc:           The QuantumCircuit to modify.
        qr:           QuantumRegister containing data and ancillas.
        idx:          Indexer for qubit allocation and grid dimensions (n, m, k).
        threshold_n:  Integer threshold for cell values.
    """
    k = idx.k             # bit-width for cell values
    n = idx.n             # number of rows
    m = idx.m             # number of columns

    # Reserve ancillas: k for comparator plus 2 for threshold constant storage
    const_ancilla_inds = idx.reserve_ancilla(k + 2)
    const_ancilla = [qr[i] for i in const_ancilla_inds]

    # Per-cell comparison flags for each row
    cell_flag_inds = idx.reserve_ancilla(m)
    cell_flags = [qr[i] for i in cell_flag_inds]

    # Per-row aggregation flags
    row_flag_inds = idx.reserve_ancilla(n)
    row_flags = [qr[i] for i in row_flag_inds]

    # Final validity flag for the entire grid
    validity_flag = qr[idx.cell_valid_flag()]

    # Initialize ancillas to represent (2**k - threshold_n)
    prepare_ancilla_cell_validity(qc, const_ancilla, threshold_n, k)

    # Process each row in the grid
    for i in range(n):
        # Compare each cell in row i to the threshold
        for j in range(m):
            data_qubits = [qr[q] for q in idx.cell_qubits(i, j)]
            comparator_less(qc, data_qubits, const_ancilla, cell_flags[j], k)

        # If any cell flag is set, mark the entire row
        qc.mcx(cell_flags, row_flags[i], ctrl_state='0'*m)
        qc.x(row_flags[i])

        # Uncompute cell comparison flags for this row
        for j in reversed(range(m)):
            data_qubits = [qr[q] for q in idx.cell_qubits(i, j)]
            comparator_less(qc, data_qubits, const_ancilla, cell_flags[j], k)

    # Combine all row flags into the final validity flag
    qc.mcx(row_flags, validity_flag, ctrl_state='0'*n)
    qc.x(validity_flag)

    # Restore per-row flags to |0> by recomputing and uncomputing
    for i in range(n):
        for j in range(m):
            data_qubits = [qr[q] for q in idx.cell_qubits(i, j)]
            comparator_less(qc, data_qubits, const_ancilla, cell_flags[j], k)
        qc.mcx(cell_flags, row_flags[i], ctrl_state='0'*m)
        qc.x(row_flags[i])
        for j in reversed(range(m)):
            data_qubits = [qr[q] for q in idx.cell_qubits(i, j)]
            comparator_less(qc, data_qubits, const_ancilla, cell_flags[j], k)

    # Restore constant ancillas
    prepare_ancilla_cell_validity(qc, const_ancilla, threshold_n, k)

    # Release all ancillas
    idx.release_ancilla(const_ancilla_inds + cell_flag_inds + row_flag_inds)
