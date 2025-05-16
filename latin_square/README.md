# Latin Square Solver with Grover’s Algorithm

A quantum-enhanced approach to finding Latin squares using Grover’s search algorithm. This repository provides tools to construct the necessary quantum circuits, define constraint oracles, and simulate the end-to-end solution process.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Usage](#usage)  
3. [Project Structure](#project-structure)  
4. [Module Reference](#module-reference)  
5. [Testing](#testing)  


---

## Project Overview

A *Latin square* of order *N* is an *N×N* grid filled with the numbers 1 through *N* such that each number appears exactly once in each row and each column. This project demonstrates a concrete application of **Grover’s quantum search algorithm** to find valid Latin squares (and, more generally, *N×M* rectangular grids with the same uniqueness constraints).

The inspiration came from Avery Parkinson’s “Solving Sudoku Using Quantum Computing” example, which applies Grover’s algorithm to the Sudoku problem. Here, we generalize that idea: instead of fixing a classic 9×9 Sudoku, our code generates a flexible **oracle gate** for any *n×m* grid. That oracle marks assignments satisfying three key constraints:
1. **Cell validity** – each cell’s value lies in the allowed range.  
2. **Row uniqueness** – no duplicate values in any row.  
3. **Column uniqueness** – no duplicate values in any column.  

We encode the entire grid in a register of qubits by mapping each cell’s value to a binary bit-string. The oracle then flips the phase of those basis states representing grids that satisfy all constraints. By repeating Grover iterations (oracle + diffusion), we amplify the amplitudes of valid solutions and use Qiskit-based simulation to extract and visualize them.

**Key features**:
- **Flexible oracle generation** for arbitrary *n×m* Latin-square-style constraints  
- **Quantum circuit construction** including parameter calculation and diffusion operator  
- **End-to-end simulation** with Qiskit, producing solution counts and histograms  
- **Modular design** separating Grover logic, constraint oracles, and utility routines  

This approach both illustrates the power of quantum search in combinatorial problems and provides a reusable framework for exploring similar constraint-satisfaction tasks on near-term quantum hardware.


## Usage - Interactive Notebook

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

