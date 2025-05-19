# Oracle Module

## Purpose & Role

The `oracle/` package defines the phase‐inversion “black box” that identifies valid Latin‐square assignments. In Grover’s algorithm, this oracle flips the phase of basis states corresponding to grids that satisfy all constraints, enabling amplitude amplification of only those solutions.

## Row and Column Uniqueness (`row_uniqueness.py` and `column_uniqueness.py`)

We take row uniqueness as example, however, the same approach applies for column. To enforce that no two cells in the same row contain the same value, we process each row independently:

1. **Pairwise comparisons**  
   - In a row of *m* cells, there are $\tfrac{m(m-1)}{2}$ unique pairs of cells.  
   - For each pair $(c_1, c_2)$, we use `comparator_equal` on their *k*-qubit registers.  
   - If the two *k*-bit values are equal, the comparator flips a dedicated “pair‐flag” qubit for that pair.

2. **Row‐level aggregation**  
   - After all pairwise comparisons, we have up to $\tfrac{m(m-1)}{2}$ pair‐flag qubits.  
   - We merge these with a multi‐controlled OR:  
     - First, a multi-control on all pair-flag qubits in the “0” state (via `mcx` + X) sets a single per-row “column‐violation” flag if *any* pair matched.  
   - We then uncompute (reverse) all comparators to reset the pair‐flag qubits and free ancillas.

3. **Global row‐uniqueness flag**  
   - We repeat the above for each of the *n* rows, producing *n* per-row flags.  
   - A final multi-controlled OR across those *n* flags sets the `row_flag` qubit if *any* row contains a duplicate.  
   - Again, we uncompute the per-row aggregation to leave only the single `row_flag` set.

Column uniqueness follows the exact same pattern—processing each column instead of each row, with $\tfrac{n(n-1)}{2}$ pairwise checks per column and a final `col_flag` qubit aggregating all column violations.


### Cell Validity (`cell_validity.py`)

Because we encode each cell in $k = \lceil\log_2(\max(n,m))\rceil$ qubits, the binary register can represent values $0$ through $2^k - 1$, which may exceed the needed symbol set. In an $n\times m$ grid you must use exactly $\max(n,m)$ distinct symbols (indexed $0$ through $\max(n,m)-1$) to avoid repeats in every row and column.

For example, a $3\times 2$ grid has $\max(3,2)=3$ symbols $\{0,1,2\}$. We need $k=\lceil\log_2(3)\rceil=2$ qubits per cell, which can encode values $0$–$3$. The cell-validity oracle therefore compares each 2-qubit value against the threshold 3, marking—and later rejecting—any cell that encodes “3,” since it lies outside the intended symbol range.

The cell‐validity oracle ensures every filled cell holds a value within the allowed range $[0,\,\text{max(n,m)}-1]$. It works as follows:

1. **Prepare threshold ancillas**  
   - Compute the constant $(2^k - \max(n,m))$ in $k$ ancilla qubits (one bit per qubit) using `prepare_ancilla_cell_validity`.  
   - These ancillas encode the comparator’s “minus threshold” constant.

2. **Per‐cell comparison**  
   - For each of the $n\times m$ cells:
     - Extract the cell’s $k$ data qubits.
     - Run `comparator_less` against the threshold ancillas, flipping a dedicated “cell‐flag” qubit if the cell value ≥ symbol_max (i.e., out of range).
   - After this pass, each cell‐flag qubit indicates whether its corresponding cell violated the range check.

3. **Global validity aggregation**  
   - Use a multi‐controlled OR (`mcx` + X) across all $n\times m$ cell‐flag qubits to set a single `cell_valid_flag` qubit if **any** cell is invalid.
   - This single flag now represents “the grid has at least one out‐of‐range cell.”

4. **Uncompute and cleanup**  
   - Reverse all `comparator_less` calls on every cell to reset the individual cell‐flag qubits and restore ancillas to $\ket{0}$.
   - Reverse the initial threshold preparation to return those ancillas to $\ket{0}$.
   - At the end, only the single `cell_valid_flag` may remain set, with all other ancillas and intermediate flags clean.

Column and row‐validity follow the same compute–aggregate–uncompute pattern, but since symbol range is global, cell‐validity only needs one level of aggregation.



## Composition (`oracle.py`)

The top‐level `oracle()` function stitches the sub-oracles into a single multi-condition gate:

1. **Compute**  
   - Run **Cell Validity**, **Row Uniqueness**, and **Column Uniqueness** in sequence, setting their respective flag qubits.  
2. **Global Phase Flip**  
   - Multi-control on the three flag qubits → flip the **global_flag** qubit for valid grids.  
3. **Uncompute**  
   - Reverse the three sub-oracles to reset all ancilla and flag qubits, leaving only the **global_flag** flipped.

This compute–phase flip–uncompute pattern ensures a “clean” oracle that doesn’t leave residual garbage.
