"""
VERSIÓN 1: Túnel de Kiyotaki (Versión básica)

Esta versión consituye el caso básico en el que los turnos entre los sentidos se
establecen de manera que pasan todos los coches en un sentido que hayan 
solicitado entrar en el túnel. Cuando ya no queden más coches en ese sentido 
dentro del túnel, se cambia el turno al sentido contrario y se procede de
manera análoga.
"""

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = "south"
NORTH = "north"

NCARS = 10
"""
Variables condición:
    north_inside: natural
    south_inside: natural

INVARIANTE:
    north_inside, south_inside >= 0
    north_inside > 0 -> south_inside = 0
    south_inside > 0 -> north_inside = 0
"""
class Monitor():
    
   def __init__(self):
       # Variable compartida para guardar el número de coches dentro del túnel que salen del norte
       self.ncars_north_inside = Value('i',0)
       # Variable compartida para guardar el número de coches dentro del túnel que salen del sur
       self.ncars_south_inside = Value('i',0)
       # Semáforo binario para garantizar la exclusión mutua
       self.mutex = Lock()
       # Variable condición para controlar que no haya coches del norte dentro del túnel
       self.empty_north = Condition(self.mutex)
       # Variable condición para controlar que no haya coches del sur dentro del túnel
       self.empty_south = Condition(self.mutex)
       # {INV}

   # Función para comprobar que no hay coches del norte dentro del túnel
   def is_empty_north(self):
       return self.ncars_north_inside.value == 0
   # Función para comprobar que no hay coches del sur dentro del túnel
   def is_empty_south(self):
       return self.ncars_south_inside.value == 0
   
    # Función para controlar el acceso al túnel
   def wants_enter(self, direction):
       # {INV}
       self.mutex.acquire() # Garantizamos exclusión mutua
       if direction == NORTH: 
           # Para entrar en el túnel se espera a que no haya nadie del sentido opuesto dentro
           self.empty_south.wait_for(self.is_empty_south) 
           # {INV y ncars_south_inside = 0}
           self.ncars_north_inside.value += 1 # se entra en el túnel
           # {INV}
       else: 
           # Para entrar en el túnel se espera a que no haya nadie del sentido opuesto dentro
           self.empty_north.wait_for(self.is_empty_north) 
           # {INV y n_cars_north_inside = 0}
           self.ncars_south_inside.value += 1 # entra en el túnel
           # {INV}
       self.mutex.release()

   def leaves_tunnel(self, direction):
       # {INV}
       self.mutex.acquire() # Garantizamos exclusión mutua
       if direction == NORTH:
           self.ncars_north_inside.value -= 1 # sale del túnel
           if self.is_empty_north(): # si nadie más de su sentido está en el túnel
               # {INV y ncars_north_inside = 0}
               self.empty_north.notify_all() # se avisa
       else:
           self.ncars_south_inside.value -= 1 # sale del túnel
           if self.is_empty_south(): # si nadie más de su sentido está en el túnel
               # {INV y ncars_south_inside = 0}
               self.empty_south.notify_all()  # se avisa
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

