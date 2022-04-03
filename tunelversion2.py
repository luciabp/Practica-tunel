"""
VERSIÓN 2: Túnel de Kiyotaki (Versión 2)

Esta versión del problema consiste en adjudicar un tiempo máximo TIME a 
los turnos, de manera que si un coche que ha entrado en el túnel sale de
este en tiempo mayor que TIME, entonces no se admite que entren más coches en ese
sentido en el túnel y los coches del sentido opuesto comienzan a entrar una vez
hayan salido todos los coches que habían entrado en el túnel.
"""


import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = "south"
NORTH = "north"
TIME = 0.1 # tiempo máximo adjudicado a cada turno

NCARS = 10

"""
Variables condición:
    turn: natural \in {0,1}
    north_inside: natural
    south_inside: natural
    
Invariante:
    turn = 0 y south_inside = 0 -> north_inside >= 0
    turn = 1 y north_inside = 0 -> south_inside >= 0
"""

class Monitor():
    
   def __init__(self):
       # Variable compartida para guardar el número de coches dentro del túnel que salen del norte
       self.ncars_north_inside = Value('i',0)
       # Variable compartida para guardar el número de coches dentro del túnel que salen del sur
       self.ncars_south_inside = Value('i',0)
       # Variable compartida para guardar el tiempo en el que empieza un turno
       self.time = Value('d',0)
       # Variable compartida = 0, si es el turno de los coches en el norte y =1, si es el turno de los coches en el sur
       self.turn = Value('i',0)
       # Semáforo binario para garantizar la exclusión mutua
       self.mutex = Lock()
       # Variable condición para controlar la salida y entrada al túnel
       self.turnosem = Condition(self.mutex)

    # Función para comprobarsi un coche del norte puede entrar en el túnel
   def es_turno_norte(self):
       return self.turn.value == 0 and self.ncars_south_inside.value == 0
   
    # Función para comprobarsi un coche del sur puede entrar en el túnel
   def es_turno_sur(self):
       return self.turn.value == 1 and self.ncars_north_inside.value == 0
   
    # Función para controlar la entrada de coches en el túnel dada su dirección inicial
   def wants_enter(self,direction):
       #{INV}
       self.mutex.acquire() # Para garantizar exclusión mutua con semáforo binario
       if direction == NORTH:
           # Espera a que sea su turno y no haya coches del sur dentro
           self.turnosem.wait_for(self.es_turno_norte) 
           #{INV y turn = 0 y south_inside = 0}
           if self.time.value == 0: # si no hemos inicializado el tiempo de este turno
               self.time.value = time.time() # guardamos el tiempo de inicio del turno
           self.ncars_north_inside.value += 1 # entra en el túnel
           # {INV}
       else: 
           # Espera a que sea su turno y no haya coches del norte dentro
           self.turnosem.wait_for(self.es_turno_sur)
           #{INV y turn = 1 y north_inside = 0}
           if self.time.value == 0: # si no hemos inicializado el tiempo de ese turno
               self.time.value = time.time() # guardamos el tiempo de inicio del turno
           self.ncars_south_inside.value += 1 # entra en el túnel
           # {INV}
       self.mutex.release()

   def leaves_tunnel(self, direction):
       # {INV}
       self.mutex.acquire() # Para garantizar exclusión mutua con un semáforo binario
       if direction == NORTH:
           self.ncars_north_inside.value -= 1 # Sale del túnel
           if time.time() - self.time.value > TIME: # si se supera el tiempo máximo del turno
               self.turn.value = 1 # cambio de turno
               self.time.value = 0 # inicializo nuevo cambio de tiempo
               self.turnosem.notify_all() # aviso a los waits

       else:
           self.ncars_south_inside.value -= 1 # Sale del túnel
           if time.time() - self.time.value > TIME: # si se supera el tiempo máximo por turno
               self.turn.value = 0 # cambio de turno
               self.time.value = 0 # inicializo nuevo cambio de tiempo
               self.turnosem.notify_all() # aviso a los waits
       self.mutex.release()
       # {INV}

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

