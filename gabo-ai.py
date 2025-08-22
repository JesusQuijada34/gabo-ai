import customtkinter as ctk
import threading
import time
import requests
import json
import markdown
import os
from PIL import Image, ImageTk

# Configuración de la API
API_KEY = "AIzaSyDD8X1GvPm6j3axGaWz-pmjKSQXdP8eci4"
MODEL = "gemini-2.0-flash"

# Configuración de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modo oscuro estilo GitHub
ctk.set_default_color_theme("blue")  # Tema azul

# Colores estilo GitHub
GITHUB_DARK = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "border": "#30363d",
    "text_primary": "#f0f6fc",
    "text_secondary": "#c9d1d9",
    "accent": "#58a6ff",
    "success": "#3fb950"
}

class GaboAIChat(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gabo AI - Asistente con Estilo GitHub")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Configurar grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Historial de conversación
        self.conversation_history = []

        # Inicializar UI
        self.init_ui()

        # Añadir mensaje de bienvenida
        self.add_message("¡Hola! Soy Gabo AI, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?", False)

    def init_ui(self):
        # Crear sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Gabo AI",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # Botones de acción
        self.new_chat_button = ctk.CTkButton(
            self.sidebar,
            text="Nueva Conversación",
            command=self.new_conversation,
            fg_color=GITHUB_DARK["bg_secondary"],
            text_color=GITHUB_DARK["text_primary"],
            border_color=GITHUB_DARK["border"],
            border_width=1
        )
        self.new_chat_button.grid(row=1, column=0, padx=20, pady=10)

        self.save_button = ctk.CTkButton(
            self.sidebar,
            text="Guardar Chat",
            command=self.save_conversation,
            fg_color=GITHUB_DARK["bg_secondary"],
            text_color=GITHUB_DARK["text_primary"],
            border_color=GITHUB_DARK["border"],
            border_width=1
        )
        self.save_button.grid(row=2, column=0, padx=20, pady=10)

        # Tema
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar,
            text="Tema:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.appearance_mode_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")

        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light"],
            command=self.change_appearance_mode,
            fg_color=GITHUB_DARK["bg_secondary"],
            button_color=GITHUB_DARK["border"],
            button_hover_color=GITHUB_DARK["accent"]
        )
        self.appearance_mode_optionemenu.grid(row=4, column=0, padx=20, pady=(0, 10))

        # Área principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Área de chat con scroll - ¡ESTA ES LA PARTE IMPORTANTE!
        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Área de entrada - SIEMPRE EN LA PARTE INFERIOR
        self.input_frame = ctk.CTkFrame(self.main_frame, height=80)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_rowconfigure(0, weight=1)

        # Asegurar que el área de entrada siempre esté abajo
        self.main_frame.grid_rowconfigure(0, weight=10)  # Chat ocupa la mayor parte
        self.main_frame.grid_rowconfigure(1, weight=1)   # Input ocupa poco espacio

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
            command=self.send_message,
            fg_color=GITHUB_DARK["success"]
        )
        self.send_button.grid(row=0, column=1, padx=10, pady=10)

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def new_conversation(self):
        if len(self.conversation_history) > 0:
            # Limpiar área de chat
            for widget in self.chat_frame.winfo_children():
                widget.destroy()

            self.conversation_history = []

            # Añadir mensaje de bienvenida
            self.add_message("¡Hola! Soy Gabo AI, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?", False)

    def save_conversation(self):
        # Aquí iría la lógica para guardar la conversación
        print("Función de guardado implementada aquí")

    def add_message(self, text, is_user=True):
        # Determinar color según el remitente
        bg_color = GITHUB_DARK["success"] if is_user else GITHUB_DARK["bg_secondary"]
        text_color = "#FFFFFF" if is_user else GITHUB_DARK["text_primary"]

        # Crear frame para el mensaje
        message_frame = ctk.CTkFrame(
            self.chat_frame,
            corner_radius=8,
            fg_color=bg_color,
            border_color=GITHUB_DARK["border"],
            border_width=1
        )

        # Alinear a la derecha si es usuario, a la izquierda si es AI
        if is_user:
            message_frame.grid(row=len(self.conversation_history), column=0, sticky="e", pady=5, padx=(100, 10))
        else:
            message_frame.grid(row=len(self.conversation_history), column=0, sticky="w", pady=5, padx=(10, 100))

        # Limitar el ancho máximo del mensaje
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame._max_width = 500  # Ancho máximo para no romper el diseño

        # Procesar markdown a HTML simple
        html_content = self.markdown_to_html(text)

        # Añadir texto del mensaje
        message_text = ctk.CTkLabel(
            message_frame,
            text=html_content,  # Usamos texto plano por simplicidad
            wraplength=450,  # Ancho máximo para el texto
            justify="left",
            text_color=text_color,
            font=ctk.CTkFont(size=14)
        )
        message_text.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Añadir información del remitente y hora
        sender = "Tú" if is_user else "Gabo AI"
        timestamp = time.strftime("%H:%M")

        info_text = ctk.CTkLabel(
            message_frame,
            text=f"{sender} • {timestamp}",
            text_color=text_color,
            font=ctk.CTkFont(size=11),
            opacity=0.7
        )
        info_text.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Guardar en historial
        self.conversation_history.append({
            "text": text,
            "is_user": is_user,
            "time": timestamp
        })

        # Auto-scroll al final
        self.after(100, self.scroll_to_bottom)

    def markdown_to_html(self, text):
        # Reemplazar Gemini por Gabo AI
        text = text.replace("Gemini", "Gabo AI").replace("gemini", "Gabo AI")

        # Convertir markdown a texto simple (sin HTML)
        # Para una implementación más completa, podrías usar un widget de texto con formato
        text = text.replace("**", "").replace("__", "").replace("`", "")

        # Limitar longitud para evitar mensajes demasiado largos
        if len(text) > 1000:
            text = text[:1000] + "..."

        return text

    def scroll_to_bottom(self):
        # Scroll al final del área de chat
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self, event=None):
        message = self.input_entry.get().strip()
        if not message:
            return

        # Añadir mensaje del usuario
        self.add_message(message, True)
        self.input_entry.delete(0, ctk.END)

        # Mostrar indicador de typing
        typing_frame = ctk.CTkFrame(
            self.chat_frame,
            corner_radius=8,
            fg_color=GITHUB_DARK["bg_secondary"],
            border_color=GITHUB_DARK["border"],
            border_width=1
        )
        typing_frame.grid(row=len(self.conversation_history), column=0, sticky="w", pady=5, padx=(10, 100))

        typing_label = ctk.CTkLabel(
            typing_frame,
            text="Gabo AI está escribiendo...",
            text_color=GITHUB_DARK["text_primary"]
        )
        typing_label.grid(row=0, column=0, padx=15, pady=10)

        # Obtener respuesta en un hilo separado
        threading.Thread(target=self.get_ai_response, args=(message, typing_frame), daemon=True).start()

    def get_ai_response(self, message, typing_frame):
        # Simular tiempo de escritura
        time.sleep(1.5)

        try:
            response = self.send_to_gemini(message)

            # Eliminar indicador de typing
            self.after(0, typing_frame.destroy)

            # Añadir respuesta
            self.after(0, self.add_message, response, False)
        except Exception as e:
            self.after(0, typing_frame.destroy)
            self.after(0, self.add_message, f"Error: {str(e)}", False)

    def send_to_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
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
        self.mainloop()

# Ejecutar la aplicación
if __name__ == "__main__":
    app = GaboAIChat()
    app.run()
