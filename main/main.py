import time

import numpy as np
from qubits.qubit_func import *
simulator = CPUQVM()
number_of_qubits = 2
shots = 10000
numberOfMeasuresOfSingleQbit = 10000
permissibleNumberOfones = 50

#Создаем приватные кубиты
privateQbitsArray = generate_random_private_qbits(number_of_qbits_in_token=number_of_qubits)
print("Приватные кубиты:")
for el in privateQbitsArray:
    print("*********************")
    print("Кубит №", str(el.id))
    print("  Тета:", str(el.theta))
    print("  Фи:", str(el.phi))
    print("  Id дочернего публичного кубита:", str(el.public_qbit.id))
    print(measure_qbit(simulator, el, number_of_measures_of_single_qbit=shots))
    print("*********************")
print("")

#Создаем массив публичных кубитов на основе приватных
publicQbitsArray = make_public_qbits_array(private_qbits_array=privateQbitsArray)
print("\nПубличные кубиты:")
for el in publicQbitsArray:
    print("___________")
    print("Кубит №", str(el.id))

    print(measureQbit(simulator, el, numberOfMeasuresOfSingleQbit))
    print("___________")
print("")

#Создаем токен на основе публичных кубитов
token = Token(1, publicQbitsArray)

#Делаем спины на всех кубитах
make_spin_for_all_qbits_in_token(token, privateQbitsArray)
print("\n")

print("Публичные кубиты внутри токена после спина:")
for el in token.array_of_public_qbits:
    print("___________")
    print("Кубит №", str(el.id))
    print(measureQbit(simulator, el, numberOfMeasuresOfSingleQbit))
    print("___________")
print("")

time.sleep(1)

#Разворачиваем все кубиты в токене
reverse_qbits_in_token(token, privateQbitsArray)

print("Публичные кубиты внутри токена после обратного спина:")
for el in token.array_of_public_qbits:
    print("___________")
    print("Кубит №", str(el.id))
    print(measureQbit(simulator, el, numberOfMeasuresOfSingleQbit))
    print("___________")
print("")

#Замеряем все кубиты в нашем токене(для наглядности)
resultOfTokenMeasure = measure_token(simulator, token, numberOfMeasuresOfSingleQbit, permissibleNumberOfones)
print("Результат проверки: "+str(resultOfTokenMeasure))