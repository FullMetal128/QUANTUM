from pyqpanda3.core import QCircuit, QProg, H, CNOT, measure, CPUQVM

# Create a quantum circuit
circuit = QCircuit()

# Construct GHZ state
circuit << H(0)  # Apply Hadamard gate on qubit 0
circuit << CNOT(0, 1)  # Apply CNOT gate with control 0 and target 1
circuit << CNOT(1, 2)  # Apply CNOT gate with control 1 and target 2

# Create a quantum prog and compose the circuit
prog = QProg()
prog << circuit

# Add measure operation
prog << measure(0, 0) << measure(1, 1) << measure(2, 2)

# Create a QVM
qvm = CPUQVM()

# Execute the prog and obtain the result
qvm.run(prog, 1000)
result = qvm.result().get_counts()

# Print qprog and result
print(prog)
print(result)