# Latin Square Solver with Grover’s Algorithm

A quantum-enhanced approach to finding Latin squares using Grover’s search algorithm. This repository provides tools to construct the necessary quantum circuits, define constraint oracles, and simulate the end-to-end solution process.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Usage](#usage)  
3. [Project Structure](#project-structure)  
4. [Module Reference](#module-reference)  
5. [Limitations & Future Work](#limitations)  


---

## Project Overview

A *Latin square* of order *N* is an *N×N* grid filled with the numbers 1 through *N* such that each number appears exactly once in each row and each column. This project demonstrates a concrete application of **Grover’s quantum search algorithm** to find valid Latin squares (and, more generally, *N×M* rectangular grids with the same uniqueness constraints).

The idea was first to solve a problem using Grover's algorithm for a problem where we do not give the solution explicity. Unlike common textbook examples (such as finding a specific $n$ where $n=6$), where the solution is explicitly defined, here the set of solutions emerges from the problem’s constraints and must be verified by the oracle. The inspiration came from Avery Parkinson’s “Solving Sudoku Using Quantum Computing” example, which applies Grover’s algorithm to the Sudoku problem. Here, we generalize that idea: instead of fixing a classic 9×9 Sudoku, our code generates a flexible **oracle gate** for any *n×m* grid. That oracle marks assignments satisfying three key constraints:
1. **Cell validity** – each cell’s value lies in the allowed range.  
2. **Row uniqueness** – no duplicate values in any row.  
3. **Column uniqueness** – no duplicate values in any column.  

We encode the entire grid in a register of qubits by mapping each cell’s value to a binary bit-string. The oracle then flips the phase of those basis states representing grids that satisfy all constraints. By repeating Grover iterations (oracle + diffusion), we amplify the amplitudes of valid solutions and use Qiskit-based simulation to extract and visualize them.

**Key features**:
- **Flexible grid generation** for arbitrary *n×m* Latin-square-style constraints  
- **Quantum circuit construction** including parameter calculation and diffusion operator  
- **End-to-end simulation** with Qiskit, producing solution counts and histograms  
- **Modular design** separating Grover logic, constraint oracles, and utility routines  

This approach both illustrates the power of quantum search in combinatorial problems and provides a reusable framework for exploring similar constraint-satisfaction tasks on near-term quantum hardware.


## Usage

Open and execute the `grover_solver.ipynb` notebook in JupyterLab or Jupyter Notebook.

Within the notebook:

- **Grid definition**
  - Specify the dimensions *n×m*.
  - Optionally prefill some cells (leave blank cells as variables to solve).

- **Number of solutions**
  - Manually enter the known or expected number of valid Latin-square fillings.  
  > _Note: supplying the solution count by hand isn’t ideal; future releases may automate this step._

- **Run all cells**
  1. The notebook builds the Grover oracle and diffusion circuits.  
  2. It runs a Qiskit simulator to perform the search iterations.  
  3. A histogram of measurement results highlights the valid solutions.

- The notebook includes several **example grids** (with precomputed solution counts) so you can see end-to-end demos without computing the solution count yourself.



## Project Structure

```plaintext

latin_square/
├── grover/                   # Grover-search core
│   ├── algorithm.py          
│   ├── circuit.py            
│   ├── params.py                     
│   └── simulation.py 
├── oracle/                   # Constraint oracles
│   ├── cell_validity.py      
│   ├── row_uniqueness.py     
│   ├── column_uniqueness.py  
│   └── oracle.py        
├── utils/                    # Helper routines
│   ├── grid.py               
│   ├── indexer.py            
│   ├── helpers.py            
│   └── plotting.py           
├── tests/                    # Constraint-validation notebooks
│   ├── test_cell_validity.ipynb
│   ├── test_row_uniqueness.ipynb
│   ├── test_column_uniqueness.ipynb
│   └── test_oracle.ipynb
├── grover_solver.ipynb       # End-to-end demo notebook
└── run_grover.py             # Command-line driver

```plaintext




## Module Reference

- **`grover/`**  
  Core implementation of Grover’s search:  
  - `algorithm.py`: Grover iteration logic and oracle integration  
  - `circuit.py`: Quantum circuit construction and grid initialization  
  - `params.py`: Calculation of optimal iteration counts and qubit requirements  
  - `simulation.py`: Qiskit-based simulator wrappers and result extraction  

  See [`grover/README.md`](grover/README.md) for more details.

- **`oracle/`**  
  Definition and composition of constraint oracles:  
  - `cell_validity.py`: Checks that each cell’s value is within the allowed range  
  - `row_uniqueness.py`: Ensures no duplicate values in any row  
  - `column_uniqueness.py`: Ensures no duplicate values in any column  
  - `oracle.py`: Combines sub-oracles into a single phase-flip gate  

  See [`oracle/README.md`](oracle/README.md) for more details.

- **`utils/`**  
  Helper routines and utilities:  
  - `grid.py`: Grid validation, conversion, and pretty-printing  
  - `indexer.py`: Mapping between grid cells and qubit register indices, ancilla management  
  - `helpers.py`: Comparators, and other low-level ops  
  - `plotting.py`: Histogram and result visualization helpers  

  See [`utils/README.md`](utils/README.md) for more details.


  - **`tests/`**  
  Notebooks for validating individual components:  
  - `test_cell_validity.ipynb`, `test_row_uniqueness.ipynb`, `test_column_uniqueness.ipynb`, `test_oracle.ipynb`  
  Use these to verify each oracle and utility behaves as expected.



## Limitations & Future Work

- **Simulator limits**:  
  Qiskit’s classical simulators can handle quantum registers of up to around 25 qubits, which restricts us to testing small grids—typically up to about **3×2**. To make the most of available resources, we have designed the circuits to minimize the number of qubits used, even if this sometimes increases circuit depth.

- **Automating solution-count estimation**:  
  At present, the number of valid solutions must be provided manually. In future versions, we might automate this step, either via classical preprocessing or by using adaptive Grover search techniques.

- **Real-device execution**:  
  Currently, the circuits are not suitable for real quantum devices due to noise and limited qubit counts. As hardware improves (with ~30 or more low-noise qubits), we plan to adapt the implementation for real-device runs. In particular, we may revisit the tradeoff between ancilla count and circuit depth—allocating more ancillas could reduce depth and help mitigate noise.

- **Extending to other CSPs**:  
  The oracle framework can be extended to support a broader class of constraint-satisfaction problems (CSPs), such as partial Sudoku, magic squares, or graph coloring. This can be achieved by adding new circuits that check additional constraints and produce flag qubits, which are then incorporated into the global constraint flag.

