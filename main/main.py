import numpy as np

from qubits.qubit_func import *

qubit = PublicQbit
r = qubit(id=12, tag=12)
print(r.circuit)
a = qubit(id=12, tag=12)
print(a.makeSpin(12,21))
print(a.circuit)


print(r.circuit)