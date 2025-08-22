import random
import time
import os

# Definición de clases

class Personaje:
    def __init__(self, nombre, salud, ataque, defensa):
        self.nombre = nombre
        self.salud = salud
        self.ataque = ataque
        self.defensa = defensa
        self.inventario = []

    def atacar(self, objetivo):
        dano = max(0, self.ataque - objetivo.defensa) # Aseguramos que el daño no sea negativo
        objetivo.salud -= dano
        print(f"{self.nombre} ataca a {objetivo.nombre} y le inflige {dano} puntos de daño.")
        if objetivo.salud <= 0:
            print(f"{objetivo.nombre} ha sido derrotado.")

    def defender(self):
        print(f"{self.nombre} se prepara para defender.")
        # Implementación de lógica de defensa (opcional: aumentar temporalmente la defensa)

    def usar_item(self, item, objetivo=None):
        if item in self.inventario:
            item.usar(self, objetivo)
            self.inventario.remove(item)
        else:
            print(f"{self.nombre} no tiene {item.nombre} en su inventario.")

    def agregar_item(self, item):
        self.inventario.append(item)
        print(f"{self.nombre} ha recogido {item.nombre}.")

    def mostrar_inventario(self):
        if self.inventario:
            print(f"Inventario de {self.nombre}:")
            for item in self.inventario:
                print(f"- {item.nombre}: {item.descripcion}")
        else:
            print(f"{self.nombre} no tiene nada en su inventario.")

class Item:
    def __init__(self, nombre, descripcion):
        self.nombre = nombre
        self.descripcion = descripcion

    def usar(self, usuario, objetivo=None):
        print(f"{usuario.nombre} usa {self.nombre}.") # Acción por defecto

class PocionCurativa(Item):
    def __init__(self, cantidad_curacion):
        super().__init__("Poción Curativa", f"Cura {cantidad_curacion} puntos de salud.")
        self.cantidad_curacion = cantidad_curacion

    def usar(self, usuario, objetivo=None):
        super().usar(usuario)
        usuario.salud += self.cantidad_curacion
        print(f"{usuario.nombre} se cura {self.cantidad_curacion} puntos de salud. Salud actual: {usuario.salud}")

class Espada(Item):
    def __init__(self, dano_extra):
        super().__init__("Espada", f"Aumenta el daño de ataque en {dano_extra}.")
        self.dano_extra = dano_extra

    def usar(self, usuario, objetivo=None):
        super().usar(usuario)
        usuario.ataque += self.dano_extra
        print(f"{usuario.nombre} equipa la espada y aumenta su ataque en {self.dano_extra}. Ataque actual: {usuario.ataque}")

class Enemigo(Personaje):
    def __init__(self, nombre, salud, ataque, defensa, tipo):
        super().__init__(nombre, salud, ataque, defensa)
        self.tipo = tipo

    def elegir_accion(self, jugador):
        # IA básica del enemigo: ataca al jugador la mayoría de las veces
        if random.random() < 0.8:
            self.atacar(jugador)
        else:
            self.defender()

# Funciones auxiliares

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')  # Funciona en Windows y Linux/macOS

def pausa(segundos=1):
    time.sleep(segundos)

def mostrar_menu():
    print("\n--- Menú del Juego ---")
    print("1. Atacar")
    print("2. Defender")
    print("3. Usar Ítem")
    print("4. Mostrar Inventario")
    print("5. Huir (Termina el combate)")
    print("6. Salir del juego")
    print("-----------------------")

def crear_enemigo_aleatorio(nivel):
    tipos_enemigos = {
        "Goblin": {"salud": 20 + nivel * 5, "ataque": 5 + nivel * 2, "defensa": 1 + nivel},
        "Esqueleto": {"salud": 25 + nivel * 5, "ataque": 6 + nivel * 2, "defensa": 2 + nivel},
        "Araña Gigante": {"salud": 15 + nivel * 5, "ataque": 7 + nivel * 2, "defensa": 0 + nivel}
    }
    tipo_enemigo = random.choice(list(tipos_enemigos.keys()))
    datos_enemigo = tipos_enemigos[tipo_enemigo]
    nombre_enemigo = f"{tipo_enemigo} Nivel {nivel}"
    return Enemigo(nombre_enemigo, datos_enemigo["salud"], datos_enemigo["ataque"], datos_enemigo["defensa"], tipo_enemigo)

# Función principal del juego

def jugar():
    limpiar_pantalla()
    print("¡Bienvenido al Juego de Aventura!")

    nombre_jugador = input("Ingrese el nombre de su personaje: ")
    jugador = Personaje(nombre_jugador, 100, 10, 5)
    print(f"¡Bienvenido, {jugador.nombre}!")

    nivel = 1
    oro = 0

    while True:
        limpiar_pantalla()
        print(f"\n--- Nivel {nivel} ---")
        print(f"Oro: {oro}")

        # Evento aleatorio: Encuentro con un enemigo
        if random.random() < 0.7:  # 70% de probabilidad de encontrar un enemigo
            enemigo = crear_enemigo_aleatorio(nivel)
            print(f"\n¡Te encuentras con un {enemigo.nombre}!")

            # Combate
            while jugador.salud > 0 and enemigo.salud > 0:
                limpiar_pantalla()
                print(f"\n--- Combate contra {enemigo.nombre} ---")
                print(f"Salud de {jugador.nombre}: {jugador.salud}")
                print(f"Salud de {enemigo.nombre}: {enemigo.salud}")

                mostrar_menu()

                opcion = input("Elige una acción: ")

                if opcion == "1":
                    jugador.atacar(enemigo)
                    pausa(1)
                elif opcion == "2":
                    jugador.defender()
                    pausa(1)
                elif opcion == "3":
                    jugador.mostrar_inventario()
                    if jugador.inventario:
                        indice_item = input("Ingrese el número del ítem a usar: ")
                        try:
                            indice_item = int(indice_item) - 1
                            item_a_usar = jugador.inventario[indice_item]
                            jugador.usar_item(item_a_usar, enemigo)
                        except (ValueError, IndexError):
                            print("Selección inválida.")
                    pausa(1)
                elif opcion == "4":
                    jugador.mostrar_inventario()
                    pausa(2)
                elif opcion == "5":
                    print("¡Huyes del combate!")
                    break  # Sale del bucle de combate
                elif opcion == "6":
                    print("Gracias por jugar!")
                    return  # Sale del juego
                else:
                    print("Opción inválida.")
                    pausa(1)
                    continue # Vuelve al inicio del bucle

                # Turno del enemigo (si sigue vivo)
                if enemigo.salud > 0:
                    enemigo.elegir_accion(jugador)
                    pausa(1)

            # Fin del combate
            if jugador.salud <= 0:
                print("¡Has sido derrotado!")
                print("Game Over")
                return  # Termina el juego

            if enemigo.salud <= 0:
                print(f"¡Has derrotado al {enemigo.nombre}!")
                oro += 5 + nivel * 2 # Recompensa por derrotar al enemigo
                print(f"Recibes {5 + nivel * 2} de oro.")

                # Probabilidad de encontrar un item después del combate
                if random.random() < 0.3:
                    item_encontrado = random.choice([PocionCurativa(20), Espada(3)])
                    print(f"¡Encuentras un/una {item_encontrado.nombre}!")
                    jugador.agregar_item(item_encontrado)
                pausa(2)
        else:
            print("\nNo hay enemigos a la vista. Exploras la zona...")
            # Evento aleatorio: Encontrar oro
            if random.random() < 0.2:
                oro_encontrado = random.randint(1, 10)
                oro += oro_encontrado
                print(f("¡Encuentras {oro_encontrado} de oro!"))
                pausa(2)
            else:
                print("No encuentras nada interesante.")
                pausa(2)

        # Subir de nivel
        nivel += 1
        jugador.salud = 100 # Restablecer salud al subir de nivel
        print(f"¡Has subido al nivel {nivel}!")
        pausa(2)

# Iniciar el juego
jugar()

