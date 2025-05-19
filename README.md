# Quantum Algorithms Collection

A collection of Jupyter notebooks and Python modules implementing a range of key quantum algorithms using [Qiskit](https://www.ibm.com/quantum/qiskit).

---

## Overview

This repository is designed as a hands-on exploration of quantum computation, combining foundational protocols and algorithms.  
It showcases how quantum algorithms can solve a variety of problems—ranging from simple logical tasks and cryptography, to combinatorial optimization and simulation of physical systems. The largest project focuses on an instance of the Grover's algorithm to solve an $n*n$ Latin Square (simplified Sudoku).

---

## Algorithms Included

- **Deutsch, Deutsch–Jozsa:**  
  Distinguishing function types and extracting hidden strings using quantum parallelism.

- **BB84, E91 (Quantum Key Distribution):**  
  Protocols for secure cryptographic key sharing using quantum states and entanglement.

- **Grover’s Search (single & multiple marked elements):**  
  Quadratic speedup for unstructured search, including both textbook and generalized cases.

- **Quantum Fourier Transform (QFT) & Phase Estimation:**  
  Core subroutines for eigenvalue extraction and period finding.

- **Shor’s Algorithm:**  
  Quantum factoring using phase estimation and the QFT.

- **Variational Algorithms:**  
  - **VQE (Variational Quantum Eigensolver):** Hybrid quantum/classical algorithm for estimating ground state energies.
  - **VQD, SSVQE:** Extensions of VQE for excited states and subspace optimization.
  - **QSR (Quantum Sampling Regression):** Variant of VQE

- **QAOA (Quantum Approximate Optimization Algorithm):**  
  Example application to the Max-Cut problem.

---

## Spotlight: Latin Square Solver (Grover’s Algorithm for Constraint Satisfaction)

The **Latin Square solver** is the main and most original project in this collection.  
It demonstrates a fully quantum-enhanced approach to solving Latin squares—grids using Grover's algorithm where each number appears exactly once in every row and column.
The oracle here is built from constraints, and valid solutions emerge from the structure of the problem.  
All key modules are reusable for other constraint-satisfaction problems.

- See [`latin_square/`](./latin_square) for code, detailed documentation, and an end-to-end demo.

---

## Repository Structure

```
early_algorithms/         # Deutsch, Deutsch–Jozsa, Teleportation
key_distribution/         # BB84 and E91 QKD protocols
grover_search/            # Grover’s search for single/multiple solutions
latin_square/             # Main project: Grover’s algorithm for Latin squares (modular, with oracles and utilities)
QFT_PE_Shor/              # QFT, Phase Estimation, Shor’s algorithm
variational/              # VQE, VQD, SSVQE, QSR
QAOA_IBM_tutorial/        # QAOA Max-Cut notebook
```

---


## Requirements

This repository was developed and tested with the following Python packages and versions:

- qiskit == 2.0.0
- qiskit-aer == 0.17.0
- matplotlib == 3.10.1
- numpy == 2.2.5
- scipy == 1.15.2
- rustworkx == 0.16.0

Optional/recommended for notebook use:
- ipykernel
- notebook or jupyterlab
- pandas == 1.5.2     # (if you work with tables/dataframes)
- seaborn == 0.13.2   # (for additional plotting)

To install the core requirements, run:

```bash
pip install qiskit==2.0.0 qiskit-aer==0.17.0 matplotlib==3.10.1 numpy==2.2.5 scipy==1.15.2 rustworkx==0.16.0
```

---


## References & Further Reading

- [Qiskit Documentation](https://quantum.cloud.ibm.com/)
- Algorithm-specific references and papers are cited within notebooks.