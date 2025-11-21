from math import sqrt

from pyqpanda3.core import QCircuit, QProg, H, measure, CPUQVM, draw_qprog, I, CNOT


def generate_quantum():
    prog = QProg(1)
    prog << H(0)
    prog << measure(0, 0)
    prog << CNOT(0,1)
    prog << measure(1, 1)
    return prog


print(draw_qprog(generate_quantum()))

qvm = CPUQVM()
qvm.run(generate_quantum(), 1024)
rez = qvm.result().get_prob_dict()
print(rez)
print(f'{sqrt(rez["0"])} ∣0⟩ + {sqrt(rez["1"])} ∣1⟩')
assert rez["0"] + rez["1"] == 1




