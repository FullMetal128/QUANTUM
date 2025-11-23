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

#Функции для генерации рандомных углов тета и фи
def getRandomTheta():
    return random.uniform(0, 180)

def getRandomPhi():
    return random.uniform(0, 360)