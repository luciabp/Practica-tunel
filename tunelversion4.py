"""
VERSIÓN 4: Túnel de Kiyotaki (versión contador de coches)

Esta versión del problema consiste en establecer turnos de manera que en cada turno
pasen a lo sumo MAX coches (pueden ser menos si no tantos solicitan entrar) 
cuando algún coche del otro sentido haya solicitado entrar.
"""

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = "south"
NORTH = "north"
TIME = 0.0000000001
MAX = 2

NCARS = 10

class Monitor():
    
   def __init__(self):
       # Variable compartida para guardar el número de coches del norte esperando a entrar
       self.ncars_north_wants_enter= Value('i',0)
       # Variable compartida para guardar el número de coches del sur esperando a entrar
       self.ncars_south_wants_enter = Value('i',0)
       # Variable compartida para guardar el número de coches dentro del túnel que salen del norte
       self.ncars_north_inside = Value('i',0)
       # Variable compartida para guardar el número de coches dentro del túnel que salen del sur
       self.ncars_south_inside = Value('i',0)
       # Variable compartida para guardar el número de coches del norte que han entrado en el túnel en un turno
       self.ncars_north_entered = Value('i',0)
       # Variable compartida para guardar el número de coches del sur que han entrado en el túnel en un turno
       self.ncars_south_entered = Value('i',0)
       # Variable compartida para guardar el tiempo en el que empieza un turno
       self.time = Value('d',0)
       # Variable compartida turno: 0 si es el turno del sur, 1 si es el del norte
       self.turn = Value('i',0)
       # Semáforo binario para garantizar la exclusión mutua
       self.mutex = Lock()
       # Variable condición para controlar la salida y entrada al túnel
       self.turnosem = Condition(self.mutex)
       # Variable condición para comprobar que no hay coches en el túnel
       self.freetunnel = Condition(self.mutex)
   
   def es_turno_norte(self):
       return self.turn.value == 0 and self.ncars_south_inside.value == 0 and self.ncars_north_entered.value < MAX
   
   def es_turno_sur(self):
       return self.turn.value == 1 and self.ncars_north_inside.value == 0 and self.ncars_south_entered.value < MAX
   
   def todossalen(self):
       return self.ncars_north_inside.value == 0 and self.ncars_south_inside.value == 0
    
   def wants_enter(self,direction):
       self.mutex.acquire()
       if direction == NORTH:
           self.ncars_north_wants_enter.value += 1 # para contar número de solicitudes para entrar
           self.turnosem.wait_for(self.es_turno_norte) # espera su turno
           self.ncars_north_wants_enter.value -= 1
           self.ncars_north_inside.value += 1 # entra dentro del túnel
           self.ncars_north_entered.value += 1 # aumentamos el contador de los que han entrado
       else: 
           self.ncars_south_wants_enter.value += 1 # para contar las solicitudes de entrada
           self.turnosem.wait_for(self.es_turno_sur) # espera su turno
           self.ncars_south_wants_enter.value -= 1
           self.ncars_south_inside.value += 1 # entra dentro del túnel
           self.ncars_south_entered.value +=1 # aumentamos el contador de los que han entrado
       self.mutex.release()

   def leaves_tunnel(self, direction):
       self.mutex.acquire()
       if direction == NORTH:
           # si se llega al número máximo de coches por turno o nadie solicita entrar, se cambiará el turno
           if (self.ncars_north_entered.value == MAX or self.ncars_north_wants_enter.value == 0) and self.ncars_south_wants_enter.value > 0:
               self.turn.value = 1 # para que no entren más coches del norte
           self.ncars_north_inside.value -= 1 # sale del túnel
           if self.todossalen(): # es cierto para el último del turno que salga
               self.ncars_north_entered.value = 0 # vuelta a inicializar
               self.turnosem.notify_all()
          
       else:
           if (self.ncars_south_entered.value == MAX or self.ncars_south_wants_enter.value == 0) and self.ncars_north_wants_enter.value > 0:
               self.turn.value = 0 # para que no entren más coches del sur
           self.ncars_south_inside.value -= 1 # sale del túnel
           if self.todossalen(): # es cierto para el último del turno que salga
               self.ncars_south_entered.value = 0 # vuelta a inicializar
               self.turnosem.notify_all()
       self.mutex.release()


def delay(n=3):
    time.sleep(random.random()*n)

def car(cid, direction, monitor):
    print(f"car {cid} direction {direction} created")
    delay(6)
    print(f"car {cid} from {direction} wants to enter")
    monitor.wants_enter(direction)
    print(f"car {cid} from {direction} enters the tunnel")
    delay(3)
    print(f"car {cid} from {direction} leaving the tunnel")
    monitor.leaves_tunnel(direction)
    print(f"car {cid} from {direction} out of the tunnel")



def main():
    monitor = Monitor()
    cid = 0
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        time.sleep(random.expovariate(1/0.5)) # a new car enters each 0.5s

if __name__ == '__main__':
    main()
