#!/usr/bin/env python
# coding: utf-8

# ### Variational Quantum Eigensolver for the lowest eigenvalue $\lambda_0$

# Variational quantum eigensolver, design to find the lowest eigenvalue for a given observables.
#  ...
# 
# Only the cost function and variational part is there. Reference + ansatz might be given as argument ???

# ### Cost Function

# In[ ]:


from qiskit import QuantumCircuit
import numpy as np

from qiskit.primitives import StatevectorEstimator
estimator = StatevectorEstimator()

def cost_func_vqe(parameters, ansatz, observable, estimator):
    """Return estimate of energy from estimator

    Parameters:
        params (ndarray): Array of ansatz parameters
        ansatz (QuantumCircuit): Parameterized ansatz circuit
        hamiltonian (SparsePauliOp): Operator representation of Hamiltonian
        estimator (Estimator): Estimator primitive instance

    Returns:
        float: Energy estimate
    """

    estimator_job = estimator.run([(ansatz, observable, [parameters])])
    estimator_result = estimator_job.result()[0]

    cost = estimator_result.data.evs[0]
    return cost


# ### Optimization loop

# In[17]:


# SciPy minimizer routine
from scipy.optimize import minimize

def opti_loop_vqe(cost_func_vqe, x0, ansatz, observable, estimator, method="COBYLA"):
    return minimize(cost_func_vqe, x0, args=(ansatz, observable, estimator), method=method)


# ### Test 
# 
# In this section, we validate the VQE module by running it on multiple small test cases, varying the ansatz and the observables.
# Each test case is designed to check correctness, flexibility, and robustness of the VQE setup.

# ### Test Case 1 — 2-Qubit Ansatz and Non-Degenerate Integer Hamiltonian
# 
# **Objective**  
# Find the minimum eigenvalue of the Hamiltonian:
# \begin{equation*}
# H = Z \otimes Z + 2 \, X \otimes X
# \end{equation*}
# 
# **Observable**  
# This Hamiltonian mixes $Z$ and $X$ interactions across two qubits.
# 
# **Eigenvalues and Eigenvectors**  
# After exact diagonalization, the eigenvalues and corresponding eigenvectors are:
# 
# - Eigenvalue: $-3$
# \begin{equation*}
# \ket{\psi_0} = \frac{1}{\sqrt{2}} \left( \ket{01} + \ket{10} \right)
# \end{equation*}
# - Eigenvalue: $-1$
# \begin{equation*}
# \ket{\psi_1} = \frac{1}{\sqrt{2}} \left( \ket{00} + \ket{11} \right)
# \end{equation*}
# - Eigenvalue: $+1$
# \begin{equation*}
# \ket{\psi_2} = \frac{1}{\sqrt{2}} \left( \ket{00} - \ket{11} \right)
# \end{equation*}
# - Eigenvalue: $+3$
# \begin{equation*}
# \ket{\psi_3} = \frac{1}{\sqrt{2}} \left( \ket{01} - \ket{10} \right)
# \end{equation*}
# 
# **Expected Results**  
# - Minimal eigenvalue: $-3$,
# - The ground state is **non-degenerate** (unique),
# - The optimizer should converge to a variational state close to:
# \begin{equation*}
# \ket{\psi_0} = \frac{1}{\sqrt{2}} \left( \ket{01} + \ket{10} \right)
# \end{equation*}
# achieving an expectation value near $-3$.
# 

# In[44]:


from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp, Statevector
import numpy as np

# Define parameters
theta0 = Parameter('θ0')
theta1 = Parameter('θ1')

# Define ansatz
ansatz_case1 = QuantumCircuit(2)
ansatz_case1.ry(theta0, 0)
ansatz_case1.ry(theta1, 1)
ansatz_case1.cx(0, 1)

# Optional: visualize ansatz
#display(ansatz_case1.decompose().draw('mpl'))


# Define observable H = ZZ + 2*XX
observable_case1 = SparsePauliOp.from_list([
    ("ZZ", 1.0),
    ("XX", 2.0)
])


# Initial parameters
x0_case1 = np.random.uniform(0, 2*np.pi, size=len(ansatz_case1.parameters))

# Run optimization
results_case1 = opti_loop_vqe(cost_func_vqe, x0_case1, ansatz_case1, observable_case1, estimator)

# Display the Minimal eigenvalue
#print("Optimal parameters:", results_case1.x)
print("\nMinimal eigenvalue found:", results_case1.fun)

# =========================================================
# Display the final statevector found by VQE

# Assign optimal parameters to the ansatz
param_dict = dict(zip(ansatz_case1.parameters, results_case1.x))
optimized_circuit_case1 = ansatz_case1.assign_parameters(param_dict)

# Generate the final quantum state
final_state_case1 = Statevector(optimized_circuit_case1)

# Build the single-line sum
terms = []
for idx, amplitude in enumerate(final_state_case1.data):
    if np.abs(amplitude) > 1e-3:  # only significant amplitudes
        bstr = format(idx, '02b')  # 2 qubits = 2 binary digits
        terms.append(f"({amplitude:.5f})|{bstr}⟩")

# Join and print the sum
statevector_str = " + ".join(terms)
print("Final statevector:", statevector_str)


# ### Test Case 2 — 3-Qubit Ansatz and Ground State Observable
# 
# **Objective**  
# Find the minimum eigenvalue of the Hamiltonian:
# \begin{equation*}
# H = X \otimes X \otimes Z + Y \otimes Y \otimes Z + Z \otimes Z \otimes Z
# \end{equation*}
# 
# **Observable**  
# This Hamiltonian couples all three qubits through mixed $ X $, $ Y $, and $ Z $ interactions.
# 
# **Eigenvalues and Eigenvectors**  
# After exact diagonalization, the eigenvalues and corresponding eigenvectors are:
# 
# - Eigenvalue: $ -3 $ : 
#   \begin{equation*}
#   \frac{1}{\sqrt{2}}\left( \ket{001} - \ket{011} \right)
#   \end{equation*}
# - Eigenvalue: $ -1 $ : 
#   \begin{equation*}
#   \ket{001}
#   \end{equation*}
# - Eigenvalue: $ -1 $ : 
#   \begin{equation*}
#   \frac{1}{\sqrt{2}}\left( \ket{000} - \ket{110} \right)
#   \end{equation*}
# - Eigenvalue: $ -1 $ : 
#   \begin{equation*}
#   \frac{1}{\sqrt{2}}\left( \ket{010} - \ket{111} \right)
#   \end{equation*}
# - Eigenvalue: $ +1 $ : 
#   \begin{equation*}
#   -\frac{1}{\sqrt{2}}\left( \ket{000} + \ket{110} \right)
#   \end{equation*}
# - Eigenvalue: $ +1 $ : 
#   \begin{equation*}
#   \frac{1}{\sqrt{2}}\left( \ket{010} + \ket{111} \right)
#   \end{equation*}
# - Eigenvalue: $ +1 $ : 
#   \begin{equation*}
#   \ket{101}
#   \end{equation*}
# - Eigenvalue: $ +3 $ : 
#   \begin{equation*}
#   \ket{011}
#   \end{equation*}
# 
# **Expected Results**  
# - We are seeking the ground state corresponding to the minimal eigenvalue $ -3 $.
# - The ground state is:
# \begin{equation*}
# \ket{\psi_0} = \frac{1}{\sqrt{2}}\left( \ket{001} - \ket{011} \right)
# \end{equation*}
# Thus, the optimizer should ideally converge to this superposition, achieving an expectation value near $ -3 $.
# 

# In[ ]:


# Test Case 2 — 3-Qubit VQE with Integer Hamiltonian

from qiskit import QuantumCircuit
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp, Statevector
import numpy as np

# Build the TwoLocal ansatz
ansatz_case2 = TwoLocal(
    num_qubits=3,
    rotation_blocks=["rz", "ry"],
    entanglement_blocks="cx",
    entanglement="linear",
    reps=1
)

# Optional: visualize the ansatz
display(ansatz_case2.decompose().draw('mpl'))

# Define the observable H = XXZ + YYZ + ZZZ
observable_case2 = SparsePauliOp.from_list([
    ("XXZ", 1.0),
    ("YYZ", 1.0),
    ("ZZZ", 1.0)
])

# Initial parameters
x0_case2 = np.random.uniform(0, 2*np.pi, size=len(ansatz_case2.parameters))

# Run the optimization
results_case2 = opti_loop_vqe(cost_func_vqe, x0_case2, ansatz_case2, observable_case2, estimator)

# Display the Minimal eigenvalue
#print("Optimal parameters:", results_case2.x)
print("Minimal eigenvalue found:", results_case2.fun)

# =========================================================
# Display the final statevector found by VQE

# Assign optimal parameters to the ansatz
param_dict = dict(zip(ansatz_case2.parameters, results_case2.x))
optimized_circuit_case2 = ansatz_case2.assign_parameters(param_dict)
final_state_case2 = Statevector(optimized_circuit_case2)



# Build the single-line sum
terms = []
for idx, amplitude in enumerate(final_state_case2.data):
    phase = 0
    if np.abs(amplitude) > 1e-3:  # only significant amplitudes
        bstr = format(idx, '03b')  # 3 qubits = 3 binary digits
        phase = np.angle(amplitude)
        terms.append(f"({amplitude*np.exp(-1j*phase):.5f})|{bstr}⟩")

# Join and print the sum
statevector_str = " + ".join(terms)
print("Final statevector:", statevector_str)


# ### Test case 3 - Random Hermitian matrix

# In[79]:


def random_hermitian_matrix(n):
    """
    Generate a random Hermitian matrix of size (2^n)x(2^n).
    """    
    dim = 2**n
    A = np.random.rand(dim, dim) + 1j*np.random.rand(dim, dim)
    H = (A + A.conj().T) / 2  # Make it Hermitian
    return H


# In[ ]:


import numpy as np
import itertools

def pauli_decomposition(A):
    """
    Compute the Pauli decomposition of a Hermitian matrix A (size 2^n x 2^n).
    
    Returns a dictionary with keys as tuples (i,j,k,...) and values as coefficients h_{ijkl...}.
    """
    # Define Pauli matrices
    I = np.array([[1, 0], [0, 1]], dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    paulis = [I, X, Y, Z]
    
    # Check that A is square and size 2^n x 2^n
    d = A.shape[0]
    assert A.shape == (d, d), "Matrix A must be square"
    n = int(np.log2(d))
    assert 2**n == d, "Matrix size must be a power of 2"
    
    coeffs = {}

    # Loop over all n-tuples of Pauli matrices
    for pauli_indices in itertools.product(range(4), repeat=n):
        # Build the tensor product
        op = paulis[pauli_indices[0]]
        for idx in pauli_indices[1:]:
            op = np.kron(op, paulis[idx])
        
        # Compute the coefficient
        h = np.trace(op @ A) / (2**n)
    
    return coeffs



# In[92]:


def pauli_expression(coeffs, threshold=1e-10):
    """
    Returns a string representing the Hermitian matrix as a sum of Pauli tensor products.
    
    coeffs: dictionary from pauli_decomposition().
    threshold: minimum absolute value to keep a term.
    """
    pauli_labels = ['I', 'X', 'Y', 'Z']
    terms = []
    
    for pauli_indices, coeff in coeffs.items():
        if abs(coeff) > threshold:
            label = ' ⊗ '.join([pauli_labels[i] for i in pauli_indices])
            terms.append(f"({coeff.real:.4f} + {coeff.imag:.4f}j) * ({label})")
    
    return ' +\n'.join(terms) if terms else "0"


# In[96]:


H = random_hermitian_matrix(2)

h = pauli_decomposition(H)

print(h)

print(pauli_expression(h))


# In[ ]:





# In[ ]:




