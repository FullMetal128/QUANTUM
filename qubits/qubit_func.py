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
        self.publicQbit = PublicQbit(self.id)

#Класс, содержащий только суперпозицию. Набор объектов данного класса будут составлять токен
class PublicQbit:
    def __init__(self, id, tag=None):
        self.id = id
        self.tag = tag
        self.circuit = QCircuit()

    def makeSpin(self, theta, phi):
        self.circuit << RY(self.id, math.radians(theta)) # θ влияет на P(0)/P(1) в Z
        self.circuit << RZ(self.id, math.radians(phi))   # φ задаёт фазу, в Z не видно
        print("Выполнен спин на публичном кубите с id: "+str(self.id))

    def makeReverseSpin(self, theta, phi):
        self.circuit << RZ(self.id, math.radians(-phi))   # φ задаёт фазу, в Z не видно
        self.circuit << RY(self.id, math.radians(-theta)) # θ влияет на P(0)/P(1) в Z
        print("Выполнен обратный спин на публичном кубите с id: "+str(self.id))

#Создание массива приватных кубитов с рандомными углами
def generate_random_private_qbits(number_of_qbits_in_token):
    resultArray = []
    for i in range(number_of_qbits_in_token):
        privateQbit = PrivateQbit(i+1, get_random_theta(), get_random_phi())
        resultArray.append(privateQbit)
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
def make_public_qbits_array(private_qbits_array):
    public_qbits_array = []
    for privateQbit in private_qbits_array:
        public_qbits_array.append(privateQbit.publicQbit)
    return public_qbits_array

#Функция для измерения состояния кубита
def measureQbit(simulator, qbit, numberOfMeasuresOfSingleQbit):
    programm = QProg() << qbit.circuit << measure(qbit.id, 0)    #qbit.id)
    simulator.run(programm, numberOfMeasuresOfSingleQbit)
    result = simulator.result().get_counts()
    #print("Кубит с id "+str(qbit.id))
    #print(result)
    ones = result.get('1', 0)
    #print("Количество единиц:", ones)
    return result