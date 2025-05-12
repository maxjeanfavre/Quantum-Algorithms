import math
from typing import List, Iterable, Sequence
from contextlib import contextmanager

from qiskit import QuantumCircuit
from qiskit.circuit import Qubit


###############################################################################

#####   Indexer

###############################################################################


class Indexer:
    """
    Flat‑index manager for Grover‑style Latin‑square (or Sudoku) oracles.

    Segment order
    -------------
      1. DATA qubits           – n² · k       (k = ⌈log₂ n⌉)
      2. ROW‑constraint flag   – 1
      3. COL‑constraint flag   – 1
      4. CELL‑VALIDITY flag    – 1
      5. GLOBAL flag           – 1
      6. ANCILLA pool          – num_anc (supplied at construction)

    Only **one** flag per constraint family.
    """

    # ───────────────────────────── construction ───────────────────────────── #

    def __init__(self, n: int, num_anc: int = 0):
        """
        Parameters
        ----------
        n : int
            Order of the Latin square (grid size n × n).
        num_anc : int, optional
            How many ancilla qubits to pre‑allocate.  Default: 0.
        """
        self.n = n
        self.k = math.ceil(math.log2(n))
        self.num_anc = max(0, int(num_anc))

        # segment lengths
        len_data = n * n * self.k

        # segment bases
        self._base_data = 0
        self._base_row_flag = self._base_data + len_data
        self._base_col_flag = self._base_row_flag + 1
        self._base_cell_flag = self._base_col_flag + 1
        self._index_global = self._base_cell_flag + 1
        self._base_ancilla = self._index_global + 1

        # ancilla bookkeeping
        self._ancilla_free: List[int] = list(
            range(self._base_ancilla, self._base_ancilla + self.num_anc)
        )
        self._total_qubits = self._base_ancilla + self.num_anc

    # ───────────────────────────── data helpers ───────────────────────────── #

    def data(self, i: int, j: int, bit: int) -> int:
        self._chk_cell(i, j)
        self._chk_bit(bit)
        return (i * self.n + j) * self.k + bit + self._base_data

    def data_bits(self, i: int, j: int) -> List[int]:
        self._chk_cell(i, j)
        base = (i * self.n + j) * self.k + self._base_data
        return list(range(base, base + self.k))

    # ───────────────────── constraint‑flag accessors ──────────────────────── #

    def row_flag(self) -> int:
        return self._base_row_flag

    def col_flag(self) -> int:
        return self._base_col_flag

    def cell_valid_flag(self) -> int:
        return self._base_cell_flag

    def global_flag(self) -> int:
        return self._index_global

    # ───────────────────────── ancilla management ─────────────────────────── #

    def reserve_ancilla(self, n: int = 1) -> List[int]:
        """
        Reserve `n` ancillas and return their indices.
        Raises RuntimeError if not enough free ancillas remain.
        """
        if n <= 0:
            raise ValueError("Number of ancillas to reserve must be positive.")
        if len(self._ancilla_free) < n:
            raise RuntimeError(
                f"Requested {n} ancillas, but only {len(self._ancilla_free)} available."
            )
        out, self._ancilla_free = self._ancilla_free[:n], self._ancilla_free[n:]
        return out

    def release_ancilla(self, qubits: List[int] | int):
        """
        Mark one or multiple ancilla indices as free again.
        """
        if isinstance(qubits, int):
            qubits = [qubits]
        for q in qubits:
            if q < self._base_ancilla or q >= self._total_qubits:
                raise ValueError(f"Qubit {q} is not an ancilla managed by this indexer.")
            if q in self._ancilla_free:
                raise ValueError(f"Ancilla {q} already free.")
            self._ancilla_free.append(q)

    def add_ancillas(self, count: int):
        """
        Permanently extend the ancilla pool by `count` new qubits.
        """
        if count <= 0:
            return
        start = self._total_qubits
        new = list(range(start, start + count))
        self._ancilla_free.extend(new)
        self._total_qubits += count

    # ───────────────────────── diagnostics/debug ──────────────────────────── #

    @property
    def total_qubits(self) -> int:
        return self._total_qubits

    def pretty(self, q: int) -> str:
        if q < 0 or q >= self._total_qubits:
            return f"<out‑of‑range {q}>"

        if q < self._base_row_flag:  # data region
            cell, bit = divmod(q - self._base_data, self.k)
            i, j = divmod(cell, self.n)
            return f"data({i},{j},{bit})"

        if q == self._base_row_flag:
            return "row_flag"
        if q == self._base_col_flag:
            return "col_flag"
        if q == self._base_cell_flag:
            return "cell_valid_flag"
        if q == self._index_global:
            return "global_flag"

        return f"ancilla({q - self._base_ancilla})"

    # ────────────────────────────── internals ─────────────────────────────── #

    def _chk_cell(self, i: int, j: int):
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise IndexError("cell index out of range")

    def _chk_bit(self, b: int):
        if not (0 <= b < self.k):
            raise IndexError("bit position out of range")


# ────────────────────────────── smoke test ──────────────────────────────── #
if __name__ == "__main__":
    idx = Indexer(n=4, num_anc=3)

    print("Total qubits:", idx.total_qubits)
    print("  data(2,3,1):", idx.data(2, 3, 1))
    print("  row_flag:    ", idx.row_flag())
    print("  col_flag:    ", idx.col_flag())
    print("  cell_valid:  ", idx.cell_valid_flag())
    print("  global_flag: ", idx.global_flag())
    print("  ancillas free:", idx._ancilla_free)

    # quick reserve / release demo
    a = idx.reserve_ancilla(2)
    print("Reserved:", a, "remaining pool:", idx._ancilla_free)
    idx.release_ancilla(a[0])
    print("Released one, pool:", idx._ancilla_free)



###############################################################################

#####   tiny quantum macros helpers

###############################################################################


# C1 ────────────────────────────────────────────────────────────────────
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CDKMRippleCarryAdder


def prepare_ancilla_cell_validity(qc, anc, n, k):
    """Write 2^k−n into anc[0..k-1], leave anc[k] and anc[k+1] in |0⟩."""
    const = (1 << k) - n
    for i in range(k):
        if (const >> i) & 1:
            qc.x(anc[i])


def comparator_less(qc, dataQ, anc, target, k):
    """
    Flip `target` iff dataQ ≥ n, using anc[0..k-1]=2^k−n, anc[k]=helper.
    Leaves dataQ and anc restored.
    """
    gate = CDKMRippleCarryAdder(k, kind="half").to_gate(label="ADD")
    qubits = list(dataQ) + list(anc)        # must be length 2k+2
    qc.append(gate, qubits)                 # compute sum & carry
    qc.cx(anc[k], target)                   # copy carry-out (overflow)
    qc.append(gate.inverse(), qubits)       # uncompute


from qiskit.circuit.library import IntegerComparator

def comparator_less2(
    qc,            # QuantumCircuit
    dataQ,         # list or QuantumRegister of k state qubits
    anc,           # list or QuantumRegister of ancillas (we’ll use anc[0])
    target,        # Qubit to flip when data < threshold
    threshold      # integer n to compare against
):
    """
    Flip `target` iff int(dataQ) < threshold,
    using exactly 1 ancilla qubit (anc[0]).
    Leaves dataQ and anc clean.
    """
    k = len(dataQ)
    # Build the comparator: flips target when data < threshold
    cmp = IntegerComparator(
        num_state_qubits=k,
        value=threshold,
        geq=False,        # False => “< threshold”
        name="lt_cmp"
    )
    # Append: k data qubits + 1 target + 1 ancilla
    qc.append(cmp, list(dataQ) + list(anc))
    qc.cx(anc[0],target)



def comparator_equal(
    qc: QuantumCircuit,
    q1: list[Qubit],
    q2: list[Qubit],
    anc: list[Qubit],
    target: Qubit,
    k: int
):
    """
    Flip `target` iff q1 == q2 (both length k).
    Uses anc[0..k-1] as scratch XNOR bits, then MCX, then uncompute.
    """
    # 1) XNOR each bit into anc[i]
    for i in range(k):
        qc.cx(q1[i], anc[i])
        qc.cx(q2[i], anc[i])
        qc.x(anc[i])
    # 2) MCX on all k ancillas
    qc.mcx(anc[:k], target)
    # 3) Uncompute XNOR
    for i in reversed(range(k)):
        qc.x(anc[i])
        qc.cx(q2[i], anc[i])
        qc.cx(q1[i], anc[i])


def row_pair_flags(
    qc: QuantumCircuit,
    data: QuantumRegister,
    anc: QuantumRegister,
    rflag: Qubit,
    idx: Indexer,
    row: int
):
    """
    For a single `row`, compare every (c1<c2) pair.  Each time cells match,
    flip the single-qubit `rflag`.  All ancilla and data qubits are clean on exit.
    """
    k = idx.k
    n = idx.n

    # We'll use anc[0..k-1] for each comparator, and anc[k] as the per-pair 'target'
    if len(anc) < k+1:
        raise ValueError("anc register must have at least k+1 qubits")

    scratch = anc[k]  # one extra ancilla to act as 'target' for each comparator

    for c1 in range(n-1):
        for c2 in range(c1+1, n):
            # slice out the two k-qubit cells
            q1 = [ data[idx.data(row, c1, b)] for b in range(k) ]
            q2 = [ data[idx.data(row, c2, b)] for b in range(k) ]

            # compute equality into scratch, OR into rflag, then uncompute
            comparator_equal(qc, q1, q2, anc[:k], scratch, k)
            qc.cx(scratch, rflag)
            comparator_equal(qc, q1, q2, anc[:k], scratch, k)



def column_pair_flags(
    qc: QuantumCircuit,
    data: QuantumRegister,
    anc: QuantumRegister,
    cflag: Qubit,
    idx: Indexer,
    col: int
):
    """
    For a single `col`, compare every (r1<r2) pair of rows. Each time cells
    match in column `col`, flip the single-qubit `cflag`. All ancilla and
    data qubits are clean on exit.
    """
    k = idx.k
    n = idx.n

    # We use anc[0..k-1] for each comparator’s XNOR scratch, and anc[k] for the per-pair target
    if len(anc) < k+1:
        raise ValueError("anc register must have at least k+1 qubits")

    scratch = anc[k]  # extra ancilla for each comparator’s output

    for r1 in range(n-1):
        for r2 in range(r1+1, n):
            # slice out the two k-qubit cells at (r1, col) and (r2, col)
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]

            # compute equality into scratch, OR into cflag, then uncompute
            comparator_equal(qc, q1, q2, anc[:k], scratch, k)
            qc.cx(scratch, cflag)
            comparator_equal(qc, q1, q2, anc[:k], scratch, k)
