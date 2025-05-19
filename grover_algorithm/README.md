# Grover Search Algorithm

This folder contains two Jupyter notebooks demonstrating **Grover's algorithm** on classic textbook search problems:

- **Grover_single.ipynb**  
  Demonstrates Grover's search for a single marked element in an unsorted dataset.  
  For example, given a database of size $ N $, we search for an index $ n $ such that $ n = n_{\text{target}} $.  
  This is the standard use-case described in most quantum computing textbooks and tutorials.

- **Grover_multiple.ipynb**  
  Extends the algorithm to the case where multiple marked elements are present.  
  Here, we search for any $ n $ in a set of marked values $ \{n_1, n_2, \ldots, n_m\} $.

A more complex application—where the solution is not given directly as input to build the oracle, but instead is defined only through problem constraints—can be found in the `latin_square` folder, where Grover's algorithm is used to solve a Latin square as a constraint satisfaction problem.


## References

- [Qiskit Documentation](https://qiskit.org/documentation/)
- [Grover, L. K. (1996). A fast quantum mechanical algorithm for database search.](https://arxiv.org/abs/quant-ph/9605043)
