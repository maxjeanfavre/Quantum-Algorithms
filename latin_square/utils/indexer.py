"""
indexer.py

Provides the Indexer class for flat-index management of an n*m grid
encoded into qubits, plus ancilla tracking and convenience methods.
"""

import math
from typing import List, Sequence, Optional

from qiskit import QuantumCircuit


class Indexer:
    """
    Manages qubit indices for:
      • data region: n·m cells * k bits each
      • row-, col-, cell-validity, and global flags
      • a pool of ancilla qubits
    """
    def __init__(
        self,
        grid: Sequence[Sequence[Optional[int]]],
        num_anc: int = 0,
    ):
        """
        Parameters
        ----------
        grid : rows*cols array of
            None        (empty cell)
            integer     (fixed symbol in [0..max(n,m)-1])
        num_anc : int, optional
            How many ancilla qubits to pre-allocate. Default: 0.
        """
        # infer dimensions
        self.n = len(grid)              # number of rows
        if self.n == 0:
            raise ValueError("grid must have at least one row")
        self.m = len(grid[0])           # number of columns

        # bit-width to encode symbols 0..max(n,m)-1
        self.k = math.ceil(math.log2(max(self.n, self.m)))

        # validate rectangular shape
        lengths = [len(r) for r in grid]
        if any(L != self.m for L in lengths):
            raise ValueError(f"all rows must have length {self.m}, got {lengths}")

        # store grid and ancilla count
        self.grid = grid
        self.num_anc = max(0, int(num_anc))

        # compute base offsets for each segment
        len_data = self.n * self.m * self.k
        self._base_data       = 0
        self._base_row_flag   = len_data
        self._base_col_flag   = self._base_row_flag + 1
        self._base_cell_flag  = self._base_col_flag + 1
        self._index_global    = self._base_cell_flag + 1
        self._base_ancilla    = self._index_global + 1

        # ancilla bookkeeping
        self._ancilla_free = list(range(
            self._base_ancilla,
            self._base_ancilla + self.num_anc
        ))
        self._total_qubits = self._base_ancilla + self.num_anc

    # ──────────────── data-qubit helpers ────────────────── #

    def prepare_cell(self, qc: QuantumCircuit, i: int, j: int):
        """
        For cell (i,j): if grid[i][j] is None apply H to each bit-qubit,
        otherwise X-prepare the fixed integer value in binary.
        """
        qubits = self.cell_qubits(i, j)
        val = self.grid[i][j]
        if val is None:
            for q in qubits:
                qc.h(q)
        else:
            for b, q in enumerate(qubits):
                if (val >> b) & 1:
                    qc.x(q)

    def initialize_grid(self, qc: QuantumCircuit):
        """Apply prepare_cell to every (i,j) in the grid."""
        for i in range(self.n):
            for j in range(self.m):
                self.prepare_cell(qc, i, j)

    # ────────────────── flat-index accessors ─────────────────── #

    def data(self, i: int, j: int, bit: int) -> int:
        """Return the qubit index for the given cell-bit."""
        self._chk_cell(i, j)
        self._chk_bit(bit)
        return (i * self.m + j) * self.k + bit + self._base_data

    def cell_qubits(self, i: int, j: int) -> List[int]:
        """Return the k contiguous qubit indices for cell (i,j)."""
        self._chk_cell(i, j)
        base = (i * self.m + j) * self.k + self._base_data
        return list(range(base, base + self.k))

    # ─────────── constraint-flag indices ──────────────── #

    def row_flag(self) -> int:        return self._base_row_flag
    def col_flag(self) -> int:        return self._base_col_flag
    def cell_valid_flag(self) -> int: return self._base_cell_flag
    def global_flag(self) -> int:     return self._index_global

    # ─────────────── ancilla management ────────────────── #

    def reserve_ancilla(self, n: int = 1) -> List[int]:
        """
        Reserve `n` ancilla qubits and return their indices.
        Raises if not enough remain.
        """
        if n < 0:
            raise ValueError("Cannot reserve a negative number of ancillas.")
        if len(self._ancilla_free) < n:
            raise RuntimeError(
                f"Requested {n} ancillas, but only {len(self._ancilla_free)} available."
            )
        out, self._ancilla_free = self._ancilla_free[:n], self._ancilla_free[n:]
        return out

    def release_ancilla(self, qubits: int | List[int]):
        """Return previously reserved ancillas back to the pool."""
        if isinstance(qubits, int):
            qubits = [qubits]
        for q in qubits:
            if q < self._base_ancilla or q >= self._total_qubits:
                raise ValueError(f"Qubit {q} is not managed by this Indexer.")
            if q in self._ancilla_free:
                raise ValueError(f"Ancilla {q} already free.")
            self._ancilla_free.append(q)

    # ────────────── diagnostics & pretty-printing ─────────── #

    @property
    def total_qubits(self) -> int:
        return self._total_qubits

    def pretty(self, q: int) -> str:
        """Human-readable name for qubit index `q`."""
        if q < 0 or q >= self._total_qubits:
            return f"<out-of-range {q}>"
        if q < self._base_row_flag:
            cell, bit = divmod(q - self._base_data, self.k)
            i, j = divmod(cell, self.m)
            return f"data({i},{j},{bit})"
        if q == self._base_row_flag:   return "row_flag"
        if q == self._base_col_flag:   return "col_flag"
        if q == self._base_cell_flag:  return "cell_valid_flag"
        if q == self._index_global:    return "global_flag"
        return f"ancilla({q - self._base_ancilla})"

    # ───────────────────────── internals ────────────────────────── #

    def _chk_cell(self, i: int, j: int):
        """Raise if (i,j) is out of the grid bounds."""
        if not (0 <= i < self.n and 0 <= j < self.m):
            raise IndexError(f"cell index ({i},{j}) out of range")

    def _chk_bit(self, b: int):
        """Raise if bit index b is outside [0..k-1]."""
        if not (0 <= b < self.k):
            raise IndexError(f"bit index {b} out of range")
