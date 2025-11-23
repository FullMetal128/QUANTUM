import numpy as np
from qubits.qubit_func import *
simulator = CPUQVM()
#Создаем приватные кубиты
privateQbitsArray = generate_random_private_qbits(number_of_qbits_in_token=3)
print("Приватные кубиты:")
for el in privateQbitsArray:
    print("___________")
    print("Кубит №", str(el.id))
    print("  Тета:", str(el.theta))
    print("  Фи:", str(el.phi))
    print("  Id дочернего публичного кубита:", str(el.publicQbit.id))
    print(measure_qbit(simulator, el, number_of_measures_of_single_qbit=100))
    print("___________")
print("")
