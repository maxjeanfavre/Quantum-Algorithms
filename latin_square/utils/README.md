# Utils Module

## Purpose & Overview

The `utils/` package provides general helper routines for:

- Validating and pretty-printing Latin-square grids  
- Mapping between grid cells and qubit register indices  
- Building low-level quantum “macros” (comparators, adders, ancilla management)  
- Plotting measurement results as histograms  

These utilities support the `grover/` and `oracle/` packages by handling common tasks such as grid verification, qubit indexing, ancilla allocation, and result visualization.

## Key Modules

- **`indexer.py`**  
  The `Indexer` is your central tool for mapping the 2D grid logic onto a flat quantum register and orchestrating ancilla usage. With an `Indexer`, you can:

  - **Translate cells to qubits**:  
    Instantly find which qubits represent any cell’s bits, or grab all qubits for a given row, column, or individual cell.

  - **Initialize the grid**:  
    Automatically apply Hadamards to blank cells and X-gates to fixed values, so your circuit always starts in the correct superposition.

  - **Track special flags**:  
    Reserve dedicated qubits for row checks, column checks, cell-validity, and the global phase-flip, without manual index arithmetic.

  - **Manage ancillas**:  
    Dynamically reserve and release pools of scratch qubits for comparators and adders, ensuring no conflicts and easy uncomputation.

  - **Inspect and debug**:  
    Convert any flat qubit index into a human-readable label (e.g. `data(2,1,0)`, `row_flag`, `ancilla(4)`), making circuit diagrams and error messages clearer.

  - **Scale automatically**:  
    Adapts to any *n*m* grid size by calculating bit-width, total qubit count, and all required offsets under the hood.


- **`grid.py`**  
  - `verify_grid`  
    Ensures a partially filled grid is rectangular, values are in range, and no duplicates appear in any row or column.  
  - `pretty_print_grids`  
    Formats and prints each solution grid (from flat tuples) alongside its occurrence count.

- **`helpers.py`**  
  - `prepare_ancilla_cell_validity`  
    Initializes ancillas to encode the constant `(2**k - n)`.  
  - `comparator_less`  
    Uses a CDKM ripple-carry adder to flip `target` if a `k`-qubit register ≥ `n`.  
  - `comparator_equal`  
    Flips `target` if two `k`-qubit registers are equal, using bitwise XNOR and an `mcx`.  

- **`plotting.py`**  
  - `plot_grid_counts_histogram`  
    Displays a bar chart of solution configurations. Each bar is labeled with a one-line “row0,row1|row2,row3…” representation of the grid, and its height corresponds to the measurement count.

 
