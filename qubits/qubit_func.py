from pyqpanda3.core import *
from datetime import datetime
import random
import math

#Приватный токен - класс, который содержит "инструкцию", как приготовить кубит.
class PrivateQbit:
    def __init__(self, id, theta, phi, tag=None): #Углы передаются в градусах
        self.id = id
        self.theta = theta
        self.phi = phi
        self.tag = tag
        self.circuit = QCircuit()
        self.public_qbit = PublicQbit(self.id)

#Класс, содержащий только суперпозицию. Набор объектов данного класса будут составлять токен
class PublicQbit:
    def __init__(self, id, tag=None):
        self.id = id
        self.tag = tag
        self.circuit = QCircuit()

    def make_spin(self, theta, phi):
        self.circuit << RY(self.id, math.radians(theta)) # θ влияет на P(0)/P(1) в Z
        self.circuit << RZ(self.id, math.radians(phi))   # φ задаёт фазу, в Z не видно
        print(theta, phi)
        print("Выполнен спин на публичном кубите с id: "+str(self.id))

    def make_reverse_spin(self, theta, phi):
        self.circuit << RZ(self.id, math.radians(-phi))   # φ задаёт фазу, в Z не видно
        self.circuit << RY(self.id, math.radians(-theta)) # θ влияет на P(0)/P(1) в Z
        print("Выполнен обратный спин на публичном кубите с id: "+str(self.id))

#Создание массива приватных кубитов с рандомными углами
def generate_random_private_qbits(number_of_qbits_in_token):
    resultArray = []
    for i in range(number_of_qbits_in_token):
        private_qbit = PrivateQbit(i+1, get_random_theta(), get_random_phi())
        resultArray.append(private_qbit)
    return resultArray

#Функции для генерации случайных углов тета и фи
def get_random_theta():
    return random.uniform(0, 180)

def get_random_phi():
    return random.uniform(0, 360)

#Функция для измерения состояния кубита
def measure_qbit(simulator, qbit, number_of_measures_of_single_qbit):
    program = QProg() << qbit.circuit << measure(qbit.id, 0)    #qbit.id)
    simulator.run(program, number_of_measures_of_single_qbit)
    result = simulator.result().get_counts()
    #print("Кубит с id "+str(qbit.id))
    #print(result)
    ones = result.get('1', 0)
    #print("Количество единиц:", ones)
    return result

#Создание массива публичных кубитов на основе приватных
def make_public_qbits_array(private_qbits_array: list):
    public_qbits_array = []
    for privateQbit in private_qbits_array:
        public_qbits_array.append(privateQbit.public_qbit)
    return public_qbits_array

#Функция для измерения состояния кубита
def measureQbit(simulator, qbit, number_of_measures_of_single_qbit):
    programm = QProg() << qbit.circuit << measure(qbit.id, 0)    #qbit.id)
    simulator.run(programm, number_of_measures_of_single_qbit)
    result = simulator.result().get_counts()
    print("Кубит с id "+str(qbit.id))
    ones = result.get('1', 0)
    print("Количество единиц:", ones)
    return result

#Функция для поиска приватного кубита в массиве по его айди(используется чтобы публичный кубит нашел свой приватный во время проверки токена)
def find_private_qbit_by_id(private_qbits, id):
    for el in private_qbits:
        if el.id == id:
            return el
    print("Кубит с таким айди не найден")
    return None

#Сделать спин/задать суперпозицию на всех кубитах в токене
def make_spin_for_all_qbits_in_token(token, private_qbits):
    for public_qbit in token.array_of_public_qbits:
        private_qbit = find_private_qbit_by_id(private_qbits, public_qbit.id)
        public_qbit.make_spin(private_qbit.theta, private_qbit.phi)

#Функция обратного спина для проверки токена
def reverse_qbits_in_token(token, private_qbits):
    for publicQbit in token.array_of_public_qbits:
        private_qbit = find_private_qbit_by_id(private_qbits, publicQbit.id)
        publicQbit.make_reverse_spin(private_qbit.theta, private_qbit.phi)

#Функция для измерения состояний кубитов токена
def measure_token(simulator, token, number_of_measures_of_single_qbit, permissible_number_of_ones):
    if((datetime.now() - token.time_of_creation).total_seconds() > token.ttl):
        return False
    success = True
    for qbit in token.array_of_public_qbits:
        programm = QProg() << qbit.circuit << measure(qbit.id, 0)    #qbit.id)
        simulator.run(programm, number_of_measures_of_single_qbit)
        result = simulator.result().get_counts()
        #print("Кубит с id "+str(qbit.id))
        #print(result)
        ones = result.get('1', 0)
        #print("Количество единиц:", ones)
        if ones > permissible_number_of_ones:
            success = False
    return success

#Класс, описывающий токен
class Token:
    def __init__(self, id, array_of_public_qbits, tag=None):
        self.time_of_creation = datetime.now()
        self.ttl = 5
        self.id = id
        self.array_of_public_qbits = array_of_public_qbits
        self.tag = tag

    def add_qbit(self, public_qbit):
        self.array_of_public_qbits.append(public_qbit)