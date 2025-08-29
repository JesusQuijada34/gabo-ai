import customtkinter as ctk
import requests
import markdown
import re
import threading
import time
from datetime import datetime
import os
from PIL import Image, ImageTk
import sys

# Configuración de la API
API_KEY = ""
MODEL = ""

# Configurar apariencia de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Notification(ctk.CTkToplevel):
    def __init__(self, parent, message, code_content=None, filename=None):
        super().__init__(parent)

        self.code_content = code_content
        self.filename = filename

        # Configurar la ventana de notificación
        self.title("Notificación")
        self.geometry("400x150")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Centrar la ventana
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Configurar el layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Frame principal
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)

        # Mensaje
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=350,
            justify="left"
        )
        message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        # Botones
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        if code_content:
            save_button = ctk.CTkButton(
                button_frame,
                text="Guardar Código",
                command=self.save_code,
                width=120
            )
            save_button.pack(side="left", padx=(0, 10))

            copy_button = ctk.CTkButton(
                button_frame,
                text="Copiar Código",
                command=self.copy_code,
                width=120
            )
            copy_button.pack(side="left")

        # Botón de cerrar
        close_button = ctk.CTkButton(
            button_frame,
                text="X",
                command=self.destroy,
                width=40,
                fg_color="transparent",
                hover_color="#AA0000"
            )
        close_button.pack(side="right")

        # Auto-cerrar después de 5 segundos
        self.after(5000, self.destroy)

    def save_code(self):
        if self.code_content and self.filename:
            # Crear carpeta code si no existe
            os.makedirs("code", exist_ok=True)

            # Guardar archivo
            file_path = os.path.join("code", self.filename)
            with open(file_path, "w") as f:
                f.write(self.code_content)

            # Mostrar mensaje de éxito
            success_msg = f"Código guardado en: {file_path}"
            self.master.status_label.configure(text=success_msg, text_color="green")
            self.master.after(3000, lambda: self.master.status_label.configure(text="Conectado", text_color="green"))

            # Cerrar notificación
            self.destroy()

    def copy_code(self):
        if self.code_content:
            self.clipboard_clear()
            self.clipboard_append(self.code_content)

            # Mostrar mensaje de éxito
            self.master.status_label.configure(text="Código copiado al portapapeles", text_color="green")
            self.master.after(3000, lambda: self.master.status_label.configure(text="Conectado", text_color="green"))

            # Cerrar notificación
            self.destroy()

class GaboAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("INTELIGENCIA-ARTIFICIAL - Sala de Chat")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Variables de estado
        self.messages = []
        self.thinking = False
        self.current_response = ""

        # Configurar la interfaz
        self.setup_ui()

        # Mensaje de bienvenida
        self.add_message("¡Hola! Soy INTELIGENCIA-ARTIFIAL, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?", False)

    def setup_ui(self):
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Layout superior - Título y barra de estado
        top_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        top_frame.grid_propagate(False)

        # Título
        title_label = ctk.CTkLabel(
            top_frame,
            text="INTELIGENCIA-ARTIFICIAL - Sala de Chat",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=10)

        # Barra de estado
        self.status_label = ctk.CTkLabel(
            top_frame,
            text="Conectado",
            text_color="green",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="right", padx=20, pady=10)

        # Layout central - Historial de chat
        center_frame = ctk.CTkFrame(self, corner_radius=0)
        center_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_rowconfigure(0, weight=1)

        # Scrollable frame para el historial de chat
        self.chat_scrollable = ctk.CTkScrollableFrame(
            center_frame,
            corner_radius=0
        )
        self.chat_scrollable.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_scrollable.grid_columnconfigure(0, weight=1)

        # Layout inferior - Entrada de usuario
        bottom_frame = ctk.CTkFrame(self, height=100, corner_radius=0)
        bottom_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        bottom_frame.grid_propagate(False)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Frame de entrada
        input_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        input_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        input_frame.grid_columnconfigure(0, weight=1)

        # Campo de entrada
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Escribe tu mensaje aquí...",
            height=40
        )
        self.input_entry.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)

        # Botón de enviar
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Enviar",
            width=100,
            height=40,
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, sticky="nsew")

    def add_message(self, message, is_user=True):
        # Determinar alineación y color según el remitente
        alignment = "right" if is_user else "left"
        bg_color = ("#3B8ED0", "#1F6AA5") if is_user else ("#2B2B2B", "#252525")
        fg_color = "white" if is_user else ("#DCE4EE", "#DCE4EE")

        # Crear frame para el mensaje
        message_frame = ctk.CTkFrame(
            self.chat_scrollable,
            fg_color=bg_color,
            corner_radius=10
        )

        # Empacar según la alineación
        if alignment == "right":
            message_frame.pack(fill="x", padx=(100, 10), pady=5, anchor="e")
        else:
            message_frame.pack(fill="x", padx=(10, 100), pady=5, anchor="w")

        # Encabezado del mensaje (usuario + hora)
        header_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        user_label = ctk.CTkLabel(
            header_frame,
            text="Tú" if is_user else "INTELIGENCIA-ARTIFICIAL",
            font=ctk.CTkFont(weight="bold"),
            text_color=fg_color
        )

        if alignment == "right":
            user_label.pack(side="right")
        else:
            user_label.pack(side="left")

        time_label = ctk.CTkLabel(
            header_frame,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=12),
            text_color=fg_color
        )

        if alignment == "right":
            time_label.pack(side="left")
        else:
            time_label.pack(side="right")

        # Contenido del mensaje
        content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Procesar markdown y mostrar el mensaje
        formatted_text = self.format_message(message)
        message_label = ctk.CTkLabel(
            content_frame,
            text=formatted_text,
            justify="left",
            wraplength=600,
            text_color=fg_color
        )
        message_label.pack(fill="x")

        # Guardar el mensaje en el historial
        self.messages.append({
            "text": message,
            "user": is_user,
            "timestamp": datetime.now().strftime("%H:%M"),
            "frame": message_frame
        })

        # Scroll al final
        self.chat_scrollable._parent_canvas.yview_moveto(1.0)

        # Verificar si hay código en la respuesta de la IA
        if not is_user and self.has_code(message):
            self.show_code_notification(message)

    def format_message(self, text):
        # Convertir markdown a texto plano para la visualización
        # (CTkLabel no soporta markdown directamente)

        # Eliminar código entre ```
        text = re.sub(r'```.*?```', '[CÓDIGO]', text, flags=re.DOTALL)

        # Convertir negritas
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

        # Convertir cursivas
        text = re.sub(r'\*(.*?)\*', r'\1', text)

        # Convertir código en línea
        text = re.sub(r'`(.*?)`', r'\1', text)

        return text

    def has_code(self, text):
        # Verificar si el texto contiene código
        return "```" in text

    def extract_code(self, text):
        # Extraer código del texto
        code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', text, re.DOTALL)
        return code_blocks

    def generate_filename(self, prompt):
        # Generar nombre de archivo basado en las primeras 10 letras del prompt y la hora
        safe_prompt = re.sub(r'[^\w\s]', '', prompt)[:10]
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{safe_prompt}_{timestamp}.py"

    def show_code_notification(self, message):
        # Extraer código del mensaje
        code_blocks = self.extract_code(message)
        if not code_blocks:
            return

        # Obtener el prompt anterior
        prompt = ""
        for msg in reversed(self.messages):
            if msg["user"]:
                prompt = msg["text"]
                break

        # Generar nombre de archivo
        filename = self.generate_filename(prompt)

        # Mostrar notificación
        Notification(
            self,
            "Se ha detectado código en la respuesta. ¿Deseas guardarlo?",
            code_content="\n\n".join(code_blocks),
            filename=filename
        )

    def send_message(self, event=None):
        question = self.input_entry.get().strip()
        if not question or self.thinking:
            return

        self.input_entry.delete(0, "end")
        self.add_message(question, True)

        # Mostrar estado de pensamiento
        self.thinking = True
        self.send_button.configure(state="disabled", text="Pensando...")

        # Obtener respuesta en segundo plano
        threading.Thread(target=self.get_ai_response, args=(question,), daemon=True).start()

    def get_ai_response(self, question):
        try:
            # Llamar a la API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
            params = {"key": API_KEY}
            headers = {"Content-Type": "application/json"}

            data = {
                "contents": [{
                    "parts": [{"text": question}]
                }],
                "generationConfig": {
                    "temperature": 0.7
                }
            }

            response = requests.post(url, params=params, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            if "candidates" in result and result["candidates"]:
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                response_text = response_text.replace("Google", "Influent").replace("Gemini", "INTELIGENCIA-ARTIFICIAL")
            else:
                response_text = "Lo siento, no pude generar una respuesta."

        except Exception as e:
            response_text = f"Error: {str(e)}"

        # Actualizar la UI en el hilo principal
        self.after(0, self.show_response, response_text)

    def show_response(self, response_text):
        self.thinking = False
        self.send_button.configure(state="normal", text="Enviar")

        # Guardar la respuesta actual
        self.current_response = response_text

        # Añadir la respuesta al chat
        self.add_message(response_text, False)

if __name__ == "__main__":
    app = GaboAIApp()
    app.mainloop()
