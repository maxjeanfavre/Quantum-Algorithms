import math
from typing import List, Iterable, Sequence, Optional, Tuple
from contextlib import contextmanager

from qiskit import QuantumCircuit
from qiskit.circuit import Qubit


###############################################################################

#####   Indexer

###############################################################################

class Indexer:
    def __init__(self,   
        grid: Sequence[Sequence[Optional[int]]],
        num_anc: int = 0,
        ):
        """
        Parameters
        ----------
            How many ancilla qubits to pre-allocate.  Default: 0.
+       grid : n×n array of either None (free cell) or int in [0..n-1] (fixed)
        """
        self.n = len(grid)        # number of rows
        self.m = len(grid[0])     # number of columns
        self.k = math.ceil(math.log2(max(self.n,self.m)))

        # ensure rectangular
        lengths = [len(r) for r in grid]
        if any(L != self.m for L in lengths):
            raise ValueError(f"all rows must have length {self.m}, got {lengths}")
        
        # store grid & ancilla count
        self.grid = grid
        self.num_anc = max(0, int(num_anc))

        # segment lengths
        len_data = self.n * self.m * self.k

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

    # ────────────────── data qubits preparation helpers ─────────────────── #

    def prepare_cell(self, qc: QuantumCircuit, i: int, j: int):
        qubits = self.cell_qubits(i, j)
        val = self.grid[i][j]
        if val is None:
            for q in qubits:
                qc.h(q)
        else:
            for b, q in enumerate(qubits):
                if (val >> b) & 1:
                    qc.x(q)

    # Since H and X are their own inverses, unprepare is identical

    def initialize_grid(self, qc: QuantumCircuit):
        for i in range(self.n):
            for j in range(self.m):
                self.prepare_cell(qc, i, j)

    # ───────────────────────────── data helpers ───────────────────────────── #

    def data(self, i: int, j: int, bit: int) -> int:
        self._chk_cell(i, j)
        self._chk_bit(bit)
        return (i * self.m + j) * self.k + bit + self._base_data

    def cell_qubits(self, i: int, j: int) -> List[int]:
        self._chk_cell(i, j)
        base = (i * self.m + j) * self.k + self._base_data
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
        if n < 0:
            raise ValueError("Number of ancillas can't be negative.")
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
            i, j = divmod(cell, self.m)
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
        if not (0 <= i < self.n and 0 <= j < self.m):
            raise IndexError("cell index out of range")

    def _chk_bit(self, b: int):
        if not (0 <= b < self.k):
            raise IndexError("bit position out of range")



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
    flag1: QuantumRegister,
    flag2: QuantumRegister,
    rflag: Qubit,
    idx: Indexer,
    row: int
):
    """
    For a single `row`, compare every (c1<c2) pair.  Each time cells match,
    flip the single-qubit `rflag`.  All ancilla and data qubits are clean on exit.
    """
    n, m, k = idx.n, idx.m, idx.k

    # We'll use anc[0..k-1] for each comparator, and anc[k] as the per-pair 'target'
    if len(anc) < k:
        raise ValueError("anc register must have at least k qubits")
    
    if len(flag1) < m:
        raise ValueError("flag1 register must have at least m qubits")
    
    if len(flag2) < m-1:
        raise ValueError("flag2 register must have at least m-1 qubits")

    for c1 in range(m-1):
        for c2 in range(c1+1, m):
            # slice out the two k-qubit cells
            q1 = [ data[idx.data(row, c1, b)] for b in range(k) ]
            q2 = [ data[idx.data(row, c2, b)] for b in range(k) ]

            # compute equality into flag2
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)
        
        # OR that window flag2 into flag1
        qc.mcx(flag2, flag1[c1], ctrl_state='0'*(m-1))
        qc.x(flag1[c1])

        for c2 in range(c1+1, m):
            # slice out the two k-qubit cells
            q1 = [ data[idx.data(row, c1, b)] for b in range(k) ]
            q2 = [ data[idx.data(row, c2, b)] for b in range(k) ]

            # compute equality into flag2
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)

    qc.mcx(flag1, rflag, ctrl_state='0'*m)
    qc.x(rflag)

    for c1 in range(m-1):
        for c2 in range(c1+1, m):
            # slice out the two k-qubit cells
            q1 = [ data[idx.data(row, c1, b)] for b in range(k) ]
            q2 = [ data[idx.data(row, c2, b)] for b in range(k) ]

            # compute equality into flag2
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)
        
        # OR that window flag2 into flag1
        qc.mcx(flag2, flag1[c1], ctrl_state='0'*(m-1))
        qc.x(flag1[c1])

        for c2 in range(c1+1, m):
            # slice out the two k-qubit cells
            q1 = [ data[idx.data(row, c1, b)] for b in range(k) ]
            q2 = [ data[idx.data(row, c2, b)] for b in range(k) ]

            # compute equality into flag2
            comparator_equal(qc, q1, q2, anc, flag2[c2-1], k)


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
    For a single `column`, compare every (r1<r2) pair of rows.  Each time cells
    match in column `col`, flip the single‐qubit `cflag`.  All ancilla and
    data qubits are clean on exit.
    """
    n, m, k = idx.n, idx.m, idx.k

    # anc must supply k scratch qubits
    if len(anc) < k:
        raise ValueError("anc register must have at least k qubits")
    # flag1 needs one bit per row
    if len(flag1) < n:
        raise ValueError(f"flag1 register must have at least {n} qubits")
    # flag2 needs one bit per pair slot (n-1)
    if len(flag2) < n-1:
        raise ValueError(f"flag2 register must have at least {n-1} qubits")

    # loop over every pair of rows
    for r1 in range(n-1):
        for r2 in range(r1+1, n):
            # extract the k data qubits for (r1,col) and (r2,col)
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            # compute equality into flag2[r2-1]
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)

        # OR that window of flag2 bits into flag1[r1]
        qc.mcx(flag2, flag1[r1], ctrl_state='0'*(n-1))
        qc.x(flag1[r1])

        # uncompute the flag2 window
        for r2 in range(r1+1, n):
            q1 = [data[idx.data(r1, col, b)] for b in range(k)]
            q2 = [data[idx.data(r2, col, b)] for b in range(k)]
            comparator_equal(qc, q1, q2, anc, flag2[r2-1], k)

    # finally OR all flag1 bits into the column‐constraint flag
    qc.mcx(flag1, cflag, ctrl_state='0'*n)
    qc.x(cflag)

    # uncompute all flag2 and flag1 for clean ancilla
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
