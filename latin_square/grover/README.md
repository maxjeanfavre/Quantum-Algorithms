# Grover Module

## Purpose & Scope

The `grover/` package implements Grover’s search algorithm specialized for finding *n×m* Latin‐square‐style solutions. It provides functions to build and initialize the quantum circuit, append Grover iterations (oracle + diffuser), calculate iteration parameters, and simulate on Qiskit backends.

## Key Components

- **`circuit.py`**  
  - `create_circuit(grid: List[List[int]]) → (QuantumCircuit, QuantumRegister, Indexer)`  
    Builds a `QuantumCircuit` for a partially filled grid:  
    1. Computes grid dimensions and bit-width per cell.  
    2. Validates pre-filled values with `verify_grid`.  
    3. Estimates ancilla count for all oracles.  
    4. Allocates qubits and initializes data registers (Hadamard on blanks).  
    Returns the circuit, its main register, and an `Indexer` to map grid cells and ancillas.

- **`algorithm.py`**  
  - `_diffuser`  
    Implements the inversion-about-the-mean operator on the list of data qubits.  
  - `implement_grover`  
    Appends “oracle → phase flip → uncompute oracle → diffuser” for the specified number of iterations. Uses `oracle.oracle` for marking valid solutions.

- **`params.py`**  
  - `count_blanks`  
    Counts how many cells are `None`.  
  - `total_possibilities`  
    Computes the search-space size.  
  - `optimal_grover_iterations`  
    Returns the optimal number of iterations $r$ given search size $N$ and known solution count $M$.

- **`simulation.py`**  
  - `simulate_counts`  
    Transpiles and runs the circuit on Qiskit’s `AerSimulator`, measures all qubits, and returns raw counts.  
  - `extract_grid_counts`  
    Converts bitstring counts into a mapping of flat grid-value tuples to occurrence counts, using `Indexer` to decode each cell’s bits.

