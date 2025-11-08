from pyqpanda3.core import QCircuit, QProg, H, measure, CPUQVM

# Функция для генерации случайного 64-битного токена с помощью квантового симулятора
def generate_quantum_random_token():
    qvm = CPUQVM()
    circuit = QCircuit()
    for i in range(2):
        circuit << H(i)   # Применяем H-гейт к кубиту i (равные вероятности 0 и 1)
        print(circuit)

    prog = QProg()
    prog << circuit

    # Выполняем измерение каждого кубита в базисе Z, результаты сохраняем в классический бит с тем же индексом:contentReference[oaicite:3]{index=3}
    for i in range(2):
        prog << measure(i, i)  # Измеряем кубит i и сохраняем бит в память i

    # Инициализируем QPanda3 симулятор на CPU и выполняем программу один раз (single shot):contentReference[oaicite:4]{index=4}

    qvm.run(prog, 5)  # Запускаем программу на 1 повтор (количество шотов = 1)

    # Получаем результаты: словарь, где ключ — 64-битная строка результатов измерений, значение — число выпадений
    result = qvm.result().get_counts()

    # Извлекаем единственную 64-битную строку (токен) из результатов
    bitstring = list(result.keys())[0]
    return bitstring


token = generate_quantum_random_token()
print("Сгенерированный 64-битный токен:", token)
