"""
VERSIÓN 3: Túnel de Kiyotaki (Versión tiempo 2)

Esta versión del problema consiste en adjudicar un tiempo máximo TIME a 
los turnos, de manera que si un coche que ha entrado en el túnel sale de
este en tiempo mayor que TIME, entonces, si alguno del otro sentido ha solicitado
entrar, no se admite que entren más coches en ese sentido en el túnel y, si han
solicitado entrar, los coches del sentido opuesto comienzan a entrar una vez 
hayan salido todos los coches que habían entrado en el túnel. 
Además, aunque un turno esté en su rango de tiempo, si ningún coche
en dicho turno solicita entrar en el túnel y sí hay solicitudes del sentido 
opuesto, se cambia el turno al sentido opuesto.
"""

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = "south"
NORTH = "north"
TIME = 0.000000000001 # tiempo máximo del turno

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
       # Variable compartida para guardar el tiempo en el que empieza un turno
       self.time = Value('d',0)
       # Variable compartida = 0, si es el turno de los coches en el norte y =1, si es el turno de los coches en el sur
       self.turn = Value('i',0)
       # Semáforo binario para garantizar la exclusión mutua
       self.mutex = Lock()
       # Variable condición para controlar la salida y entrada al túnel
       self.turnosem = Condition(self.mutex)
   
   def es_turno_norte(self): # El turno es del norte si turn = 0
       return self.turn.value == 0 and self.ncars_south_inside.value == 0
   
   def es_turno_sur(self): # El turno es del sur si turn = 1
       return self.turn.value == 1 and self.ncars_north_inside.value == 0
   
   def tunel_libre(self): # El túnel está libre si no hay nadie dentro
       return self.ncars_north_inside.value == 0 and self.ncars_south_inside.value == 0

   # Para controlar el acceso al túnel
   def wants_enter(self,direction):
       self.mutex.acquire() # Garantizamos exclusión mutua
       if direction == NORTH:
           self.ncars_north_wants_enter.value += 1 # Para guardar el número de coches que solicitan entrar
           self.turnosem.wait_for(self.es_turno_norte) # Espera a que sea su turno
           self.ncars_north_wants_enter.value -= 1 # Para guardar el número de coches que solicitan entrar
           if self.time.value == 0: # Inicializamos el tiempo de inicio del turno si no está inicializado
               self.time.value = time.time() 
           self.ncars_north_inside.value += 1  # Entra en el túnel
       else: 
           self.ncars_south_wants_enter.value += 1 # Para guardar el número de coches que solicitan entrar
           self.turnosem.wait_for(self.es_turno_sur) # Espera a que sea su turno
           self.ncars_south_wants_enter.value -= 1
           if self.time.value == 0: # Inicializamos el tiempo de inicio del turno si no está inicializado
               self.time.value = time.time()
           self.ncars_south_inside.value += 1 # Entra en el túnel
       self.mutex.release()

    # Para controlar la salida del túnel
   def leaves_tunnel(self, direction):
       self.mutex.acquire() # Garantizamos exclusión mutua
       if direction == NORTH:
           if (self.ncars_north_wants_enter.value == 0 or time.time() - self.time.value > TIME) and self.ncars_south_wants_enter.value > 0:
               self.turn.value = 1 # para que no sigan entrando más del norte
               self.time.value = 0 # inicializamos tiempo
           self.ncars_north_inside.value -= 1 # sale del túnel
           # si ha pasado el tiempo máximo o ninguno más del turno quiere entrar:
           if self.tunel_libre(): # cuando el último sale del túnel
               self.turnosem.notify_all() # aviso

       else:
           if (self.ncars_south_wants_enter.value == 0 or time.time() - self.time.value > TIME) and self.ncars_north_wants_enter.value > 0:
               self.turn.value = 0 # para que no entren más del norte
               self.time.value = 0 # inicializamos tiempo
           self.ncars_south_inside.value -= 1 # sale del túnel
           # si ha pasado el tiempo máximo o ninguno más del turno quiere entrar:
           if self.tunel_libre(): # cuando el último sale del túnel
               self.turnosem.notify_all() # aviso
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

