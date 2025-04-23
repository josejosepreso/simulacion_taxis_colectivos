from simpy import Environment, Container, Resource
import random

NUM_VEHICULOS = 5
NUM_ASIENTOS_VEHICULO = 4

class Colonia:
    def __init__(self, nombre: str, distancia_absoluta: int):
        self.nombre = nombre
        self.distancia_absoluta = distancia_absoluta
        
class Destino:
    def __init__(self, colonia: Colonia, punto: int):
        self.colonia = colonia
        self.punto = punto
        self.distancia_absoluta = self.colonia.distancia_absoluta * (self.punto / 5)

class PuntoTaxi:
    def __init__(self, env: Environment, colonias: [Colonia]):
        self.env = env
        self.vehiculos = Resource(
            env
            , capacity = NUM_VEHICULOS
        )
        self.colas_pasajeros: dict = { c.nombre: [] for c in colonias }
        self.cola_vehiculos: [Vehiculo] = [ Vehiculo(env, i) for i in range(NUM_VEHICULOS) ]
        
class Pasajero:
    def __init__(self, env: Environment, id: int, destino: Destino, punto_taxi: PuntoTaxi):
        self.env = env
        self.id = id
        self.destino = destino
        self.punto_taxi = punto_taxi
        self.env.process(self.start())

    def start(self):
        print(f"{self.env.now}: pasajero con id {self.id} llega al punto con destino: colonia {self.destino.colonia.nombre}, punto {self.destino.punto}")

        with self.punto_taxi.vehiculos.request() as req:
            colonia = self.destino.colonia.nombre
            cola_pasajeros = self.punto_taxi.colas_pasajeros[colonia]
            
            if len(cola_pasajeros) < NUM_ASIENTOS_VEHICULO:
                return
            
            siguientes_pasajeros = sorted([ cola_pasajeros.pop(0) for _ in range(NUM_ASIENTOS_VEHICULO) ], key = lambda p: p.destino.punto)
            # siguientes_pasajeros = [ cola_pasajeros.pop(0) for _ in range(NUM_ASIENTOS_VEHICULO) ]
            ids_pasajeros = [ p.id for p in siguientes_pasajeros ]
            
            print(f"{self.env.now}: pasajeros {ids_pasajeros} con destino a colonia {colonia} listos para subir a taxi")
            
            yield req

            vehiculo: Vehiculo = self.punto_taxi.cola_vehiculos.pop(0)
            
            print(f"{self.env.now}: pasajeros {ids_pasajeros} subieron a vehiculo con id {vehiculo.id}")

            # self.env.process(vehiculo.start(siguientes_pasajeros))

            # Pasajeros estan dentro del vehiculo

            velocidad = random.randint(15, 25)
            
            t_abs = [ int(60 * p.destino.distancia_absoluta / velocidad) for p in siguientes_pasajeros ]
            t_relat = [t_abs[0]] + [ t_abs[i] - t_abs[i - 1] for i in range(1, len(t_abs)) ]

            now = self.env.now

            for pasajero, tiempo in zip(siguientes_pasajeros, t_relat):
                yield self.env.timeout(tiempo)
                print(f"{self.env.now}: pasajero con id {pasajero.id} llego a su destino: colonia {colonia}, punto {pasajero.destino.punto}")

            print(f"{self.env.now}: vehiculo con id {vehiculo.id} volviendo al punto de taxi...")
                
            yield self.env.timeout(max(t_abs))
            
            print(f"{self.env.now}: vehiculo con id {vehiculo.id} volvio al punto de taxi. Tiempo del viaje: {self.env.now - now}")

            self.punto_taxi.cola_vehiculos.append(vehiculo)

class Vehiculo:
    def __init__(self, env: Environment, id: int):
        self.env = env
        self.id = id
        self.asientos = Container(
            env
            , init = NUM_ASIENTOS_VEHICULO
            , capacity = NUM_ASIENTOS_VEHICULO
        )

    def start(self, pasajeros: [Pasajero]):
        pass
            
class Simulacion:
    def __init__(self, env: Environment, colonias_settings: [dict]):
        self.env = env
        self.colonias: [Colonia] = [ Colonia(s["nombre"], s["distancia"]) for s in colonias_settings ]
        self.punto_taxi = PuntoTaxi(env, self.colonias)
        self.pasajeros = []
        self.env.process(self.start())

    def start(self):
        while True:
            # Pasajero(s) llegan cada 1-5 minutos
            yield self.env.timeout(random.randint(1, 5))

            for _ in range(random.randint(1, 3)):
                colonia: Colonia = random.choice(self.colonias)                
                destino = Destino(colonia, random.randint(1, 10))
                
                pasajero = Pasajero(
                    self.env
                    , len(self.pasajeros) + 1
                    , destino
                    , self.punto_taxi
                )

                self.pasajeros.append(pasajero)
                self.punto_taxi.colas_pasajeros[colonia.nombre].append(pasajero)
        
def main():
    random.seed(333)
    
    colonias_settings = [
        { "nombre": "A", "distancia": 1 }
        , { "nombre": "B", "distancia": 3 }
        , { "nombre": "C", "distancia": 2 }
    ]

    env = Environment()

    s = Simulacion(env, colonias_settings)

    env.run( until = 120 )

if __name__ == "__main__":
    main()
