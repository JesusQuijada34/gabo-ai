import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import requests
import json
from PIL import Image, ImageTk
import pygame
import math
import random
import sys
import os

# Configuración de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema azul

# Configuración de la API
API_KEY = "AIzaSyDD8X1GvPm6j3axGaWz-pmjKSQXdP8eci4"
MODELS = {
    "flash": {"name": "Gabo AI Flash", "model": "gemini-2.0-flash", "color": "#3B8ED0"},
    "pro": {"name": "Gabo AI Pro", "model": "gemini-1.5-pro-latest", "color": "#FF4B4B"},
    "classic": {"name": "Gabo AI Classic", "model": "gemini-1.0-pro", "color": "#9370DB"}
}
current_model = MODELS["flash"]

# Clase para los efectos de PyGame
class OrbEffect:
    def __init__(self):
        self.width, self.height = 100, 100
        self.orb_radius = 4
        self.orb_count = 8
        self.orbs = []
        self.last_mouse_pos = (0, 0)
        self.initialize_orbs()

        # Inicializar PyGame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption("Orb Effect")

        # Hacer la ventana transparente
        self.screen.set_colorkey((0, 0, 0))
        self.screen.fill((0, 0, 0))

        # Ocultar el cursor de PyGame
        pygame.mouse.set_visible(False)

        # Posicionar la ventana en la esquina inferior derecha
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{ctk.winfo_screenwidth()-self.width-50},{ctk.winfo_screenheight()-self.height-50}"

    def initialize_orbs(self):
        # Crear orbes iniciales
        for i in range(self.orb_count):
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
            self.orbs.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'color': color,
                'size': random.randint(2, 5),
                'speed': random.uniform(0.05, 0.1),
                'delay': i * 3
            })

    def update(self):
        # Obtener la posición actual del mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.last_mouse_pos = (mouse_x, mouse_y)

        # Actualizar la posición de cada orb
        for orb in self.orbs:
            if orb['delay'] > 0:
                orb['delay'] -= 1
                continue

            dx = mouse_x - orb['x']
            dy = mouse_y - orb['y']
            distance = max(1, math.sqrt(dx*dx + dy*dy))

            # Mover el orb hacia el cursor
            orb['x'] += dx * orb['speed']
            orb['y'] += dy * orb['speed']

            # Mantener los orbes dentro de la ventana
            orb['x'] = max(0, min(self.width, orb['x']))
            orb['y'] = max(0, min(self.height, orb['y']))

    def draw(self):
        # Limpiar la pantalla
        self.screen.fill((0, 0, 0))

        # Dibujar cada orb
        for orb in self.orbs:
            if orb['delay'] > 0:
                continue

            pygame.draw.circle(
                self.screen,
                orb['color'],
                (int(orb['x']), int(orb['y'])),
                orb['size']
            )

        # Actualizar la pantalla
        pygame.display.update()

    def run(self):
        # Bucle principal de PyGame
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()

# Clase principal de la aplicación
class GaboAIApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Gabo AI - Asistente Inteligente")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Configurar icono
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # Historial de conversación
        self.conversation_history = []

        # Inicializar la interfaz
        self.setup_ui()

        # Iniciar efectos de orbes en un hilo separado
        self.orb_thread = threading.Thread(target=self.start_orb_effect, daemon=True)
        self.orb_thread.start()

    def start_orb_effect(self):
        orb_effect = OrbEffect()
        orb_effect.run()

    def setup_ui(self):
        # Configurar grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Crear sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Gabo AI",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # Selector de modelo
        self.model_label = ctk.CTkLabel(
            self.sidebar,
            text="Modelo:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.model_label.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        self.model_var = ctk.StringVar(value="flash")
        self.model_optionmenu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["flash", "pro", "classic"],
            variable=self.model_var,
            command=self.change_model
        )
        self.model_optionmenu.grid(row=2, column=0, padx=20, pady=(0, 10))

        # Botones de acción
        self.new_chat_button = ctk.CTkButton(
            self.sidebar,
            text="Nueva Conversación",
            command=self.new_conversation
        )
        self.new_chat_button.grid(row=3, column=0, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            self.sidebar,
            text="Guardar Chat",
            command=self.save_conversation
        )
        self.save_button.grid(row=4, column=0, padx=20, pady=10)

        # Tema
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar,
            text="Tema:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="w")

        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(0, 10))

        # Área principal
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Área de chat
        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Área de entrada
        self.input_frame = ctk.CTkFrame(self.main_frame, height=80)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Escribe tu mensaje aquí...",
            height=40
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.input_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Enviar",
            width=80,
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=10, pady=10)

        # Añadir mensaje de bienvenida
        self.add_message("¡Hola! Soy Gabo AI, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?", False)

    def change_model(self, choice):
        global current_model
        current_model = MODELS[choice]

        # Actualizar color del botón de enviar
        self.send_button.configure(fg_color=current_model["color"])

        # Añadir mensaje de cambio de modelo
        self.add_message(f"Modelo cambiado a: {current_model['name']}", False)

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def new_conversation(self):
        if len(self.conversation_history) > 0:
            if messagebox.askyesno("Nueva Conversación", "¿Estás seguro de que quieres comenzar una nueva conversación? Se borrará el historial actual."):
                self.conversation_history = []

                # Limpiar área de chat
                for widget in self.chat_frame.winfo_children():
                    widget.destroy()

                # Añadir mensaje de bienvenida
                self.add_message("¡Hola! Soy Gabo AI, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?", False)

    def save_conversation(self):
        # Aquí iría la lógica para guardar la conversación
        messagebox.showinfo("Guardar Conversación", "Función de guardado implementada aquí.")

    def add_message(self, text, is_user=True):
        # Crear frame para el mensaje
        message_frame = ctk.CTkFrame(
            self.chat_frame,
            corner_radius=10,
            fg_color=current_model["color"] if not is_user else "#2B2B2B"
        )
        message_frame.grid(row=len(self.conversation_history), column=0, sticky="ew", pady=5)
        message_frame.grid_columnconfigure(0, weight=1)

        # Añadir texto del mensaje
        message_text = ctk.CTkLabel(
            message_frame,
            text=text,
            wraplength=700,
            justify="left"
        )
        message_text.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Añadir información del remitente y hora
        sender = "Tú" if is_user else current_model["name"]
        timestamp = time.strftime("%H:%M")

        info_text = ctk.CTkLabel(
            message_frame,
            text=f"{sender} • {timestamp}",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        info_text.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")

        # Guardar en historial
        self.conversation_history.append({
            "text": text,
            "is_user": is_user,
            "time": timestamp
        })

        # Auto-scroll al final
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self, event=None):
        message = self.input_entry.get().strip()
        if not message:
            return

        # Añadir mensaje del usuario
        self.add_message(message, True)
        self.input_entry.delete(0, tk.END)

        # Mostrar indicador de typing
        typing_frame = ctk.CTkFrame(self.chat_frame, corner_radius=10, fg_color=current_model["color"])
        typing_frame.grid(row=len(self.conversation_history), column=0, sticky="ew", pady=5)

        typing_label = ctk.CTkLabel(
            typing_frame,
            text="Gabo AI está escribiendo...",
            text_color="white"
        )
        typing_label.grid(row=0, column=0, padx=10, pady=10)

        # Obtener respuesta en un hilo separado
        threading.Thread(target=self.get_ai_response, args=(message, typing_frame), daemon=True).start()

    def get_ai_response(self, message, typing_frame):
        # Simular tiempo de escritura
        time.sleep(1.5)

        # Obtener respuesta de la API
        try:
            response = self.send_to_gemini(message)

            # Eliminar indicador de typing
            self.root.after(0, typing_frame.destroy)

            # Añadir respuesta
            self.root.after(0, self.add_message, response, False)
        except Exception as e:
            self.root.after(0, typing_frame.destroy)
            self.root.after(0, self.add_message, f"Error: {str(e)}", False)

    def send_to_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model['model']}:generateContent"
        params = {"key": API_KEY}

        headers = {"Content-Type": "application/json"}

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7
            }
        }

        response = requests.post(url, params=params, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text.replace("Gemini", "Gabo AI").replace("gemini", "Gabo AI")
        else:
            return "Lo siento, no pude generar una respuesta. Por favor intenta nuevamente."

    def run(self):
        self.root.mainloop()

# Ejecutar la aplicación
if __name__ == "__main__":
    app = GaboAIApp()
    app.run()
