import numpy as np
from qubits.qubit_func import *
simulator = CPUQVM()
number_of_qubits = 2
shots = 10000

#Создаем приватные кубиты
privateQbitsArray = generate_random_private_qbits(number_of_qbits_in_token=number_of_qubits)
print("Приватные кубиты:")
for el in privateQbitsArray:
    print("*********************")
    print("Кубит №", str(el.id))
    print("  Тета:", str(el.theta))
    print("  Фи:", str(el.phi))
    print("  Id дочернего публичного кубита:", str(el.publicQbit.id))
    print(measure_qbit(simulator, el, number_of_measures_of_single_qbit=shots))
    print("*********************")
print("")
