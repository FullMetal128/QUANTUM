from pyqpanda3.core import QCircuit, QProg, H, CNOT, measure, CPUQVM
import random
# good
# Initialize quantum virtual machine (CPU simulator)
qvm = CPUQVM()

# Step 1: Prepare GHZ state on qubits 0,1,2
circuit = QCircuit()
circuit << H(0)              # Hadamard on qubit 0 to create superposition (|0> + |1>)
circuit << CNOT(0, 1)        # Entangle qubit 0 with qubit 1
circuit << CNOT(1, 2)        # Entangle qubit 1 with qubit 2 (now qubits 0,1,2 in GHZ state)
prog = QProg() << circuit

# Step 2: Issuer chooses a random measurement basis for verification
basis_is_Z = (random.random() < 0.5)  # True = Z-basis, False = X-basis

# Step 3: Apply measurement instructions to the token
if basis_is_Z:
    # Measure all qubits in Z-basis
    prog << measure(0, 0) << measure(1, 1) << measure(2, 2)
else:
    # Measure all qubits in X-basis: apply H then measure in Z-basis
    prog << H(0) << H(1) << H(2)
    prog << measure(0, 0) << measure(1, 1) << measure(2, 2)

# Step 4: Run the program on the simulator for one shot and get result
qvm.run(prog, shots=10)
result_bits = list(qvm.result().get_counts().keys())[0]  # e.g., "000" or "111"
print(f"Measurement result = {result_bits} (basis = {'Z' if basis_is_Z else 'X'})")

# Step 5: Verify the measurement outcomes against expected GHZ behavior
def all_bits_same(bitstring):
    return bitstring.count(bitstring[0]) == len(bitstring)

def even_parity(bitstring):
    return bitstring.count('1') % 2 == 0

if basis_is_Z:
    valid = all_bits_same(result_bits)
    expected_pattern = "all 0s or all 1s"
else:
    valid = even_parity(result_bits)
    expected_pattern = "an even number of 1s"

print(f"Expected pattern: {expected_pattern}. Token {'VALID' if valid else 'INVALID'}.")

# (For testing only) Verify distribution of outcomes for genuine GHZ token
for basis in ['Z', 'X']:
    # Prepare fresh GHZ state program
    circuit = QCircuit() << H(0) << CNOT(0,1) << CNOT(1,2)
    prog = QProg() << circuit
    if basis == 'X':
        prog << H(0) << H(1) << H(2)
    prog << measure(0, 0) << measure(1, 1) << measure(2, 2)
    qvm.run(prog, shots=1000)
    counts = qvm.result().get_counts()
    print(f"\nBasis {basis} measurement distribution:")
    for outcome, count in counts.items():
        print(f"  {outcome}: {count}")