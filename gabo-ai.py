import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import threading
import markdown2
import time
import subprocess

# 🎨 Colores ANSI
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# API DeepSeek (ajusta el key si lo cambias)
API_URL = "https://api.together.xyz/v1/chat/completions"
API_KEY = "97301d064786753021066a79298e18af22d5d545140f99994373bf3ac82c1210"
MODEL = "deepseek-ai/DeepSeek-V3"

def getversion():
    newversion = time.strftime("%y.%m-%H.%M")
    newversion = f"1-{newversion}-danenone"
    return newversion

class GaboAIApp(ctk.CTk):
    def __init__(self):
        newversion = getversion()
        """
        errory = f"{RED}═══ screen mode ════════════════════════════════════════════\n"
        errory = f"{errory} Disculpa pero no colocastes ningún valor\n {CYAN}Ajustando a 600x600 (Perfomance DPI)...\n{errory}"
        
        banner = f"{GREEN}═══ screen mode ════════════════════════════════════════════\n"
        banner = f"{banner} Hola👋, escoje un dispositivo de emulación:\n {CYAN}1 Android Mode (600x700)\n {RED}2 Tablet Mode (1200x700)\n{banner}"
        print(banner)
        frameselector = input(f"{GREEN}flatr_gaboai-v{newversion}{MAGENTA}@{CYAN}:").strip()
        if frameselector == "1":
            frameselector = "600x700"
        elif frameselector == "2":
            frameselector = "1200x700"
        elif frameselector == "3":
            frameselector = input(f"{YELLOW}Necesitamos sus medidas, empecemos por el {GREEN}Ancho x Alto")
        else:
            subprocess.run(['clear'])
            print(errory)
            frameselector = "600x600"
        """
        super().__init__()
        self.title(f"Gabo AI Chat | WhatsApp Theme | {newversion} | Android Emulation")
        self.geometry("600x700") #frameselector
        self.resizable(False, False)

        # Chat frame
        self.chat_frame = ctk.CTkFrame(self, fg_color="#e5ddd5")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Canvas + scrollbar
        self.canvas = tk.Canvas(self.chat_frame, bg="#e5ddd5", highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.chat_frame, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Internal frame for bubbles
        self.bubbles_frame = ctk.CTkFrame(self.canvas, fg_color="#e5ddd5")
        self.bubbles_window = self.canvas.create_window((0, 0), window=self.bubbles_frame, anchor="nw")
        self.bubbles_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Entry + button
        self.controls_frame = ctk.CTkFrame(self, fg_color="#fff")
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Escribe un mensaje...", width=450)
        self.entry.pack(side=tk.LEFT, padx=(10, 5), pady=10, expand=True, fill=tk.X)
        self.entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(self.controls_frame, text="Enviar", command=self._send_message, fg_color="#075e54", text_color="#fff")
        self.send_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # Historial
        self.history = []

        # Mensaje de bienvenida
        self.after(500, lambda: self._add_bubble("👋 ¡Hola! Soy Gabo, tu asistente AI.<br>¿En qué puedo ayudarte hoy?", "gabo", markdown=True))

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1)

    def _on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self.bubbles_window, width=event.width)

    def _send_message(self):
        user_text = self.entry.get().strip()
        if user_text:
            self._add_bubble(user_text, "user")
            self.entry.delete(0, tk.END)
            self.send_btn.configure(state="disabled", text="Pensando...")
            threading.Thread(target=self._get_gabo_response, args=(user_text,), daemon=True).start()

    def _add_bubble(self, text, sender, markdown=False):
        # WhatsApp style colors
        bubble_color = "#dcf8c6" if sender == "user" else "#fff"
        text_color = "#222"
        align = tk.E if sender == "user" else tk.W
        border_radius = 22

        bubble = ctk.CTkFrame(self.bubbles_frame, fg_color=bubble_color, corner_radius=border_radius)
        bubble.pack(fill=tk.NONE, anchor=align, pady=3, padx=6)

        # Procesa markdown y reemplaza DeepSeek por Gabo
        show_text = text.replace("DeepSeek", "Gabo")
        if markdown:
            html = markdown2.markdown(show_text)
            clean_text = self._strip_html(html)
        else:
            clean_text = show_text

        # Detecta bloques de código
        if "```" in clean_text:
            parts = clean_text.split("```")
            if parts[0].strip():
                label = ctk.CTkLabel(bubble, text=parts[0].strip(), font=("Roboto", 13), text_color=text_color, wraplength=420, justify=tk.LEFT)
                label.pack(side=tk.TOP, padx=10, pady=(10,2), anchor="w")
            if len(parts) > 1 and parts[1].strip():
                codeblock = ctk.CTkTextbox(bubble, height=90, font=("Consolas", 11), fg_color="#222", text_color="#e4e4e4", wrap="none")
                codeblock.insert("1.0", parts[1].strip())
                codeblock.configure(state="disabled")
                codeblock.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(2,2))
                copy_btn = ctk.CTkButton(bubble, text="Copiar código", width=90, command=lambda t=parts[1].strip(): self._copy_to_clipboard(t))
                copy_btn.pack(side=tk.TOP, padx=10, pady=(0,7), anchor="e")
            if len(parts) > 2 and parts[2].strip():
                label2 = ctk.CTkLabel(bubble, text=parts[2].strip(), font=("Roboto", 13), text_color=text_color, wraplength=420, justify=tk.LEFT)
                label2.pack(side=tk.TOP, padx=10, pady=(2,10), anchor="w")
        else:
            label = ctk.CTkLabel(bubble, text=clean_text, font=("Roboto", 13), text_color=text_color, wraplength=420, justify=tk.LEFT)
            label.pack(side=tk.LEFT, padx=14, pady=10)

        # Footer WhatsApp style
        footer = ctk.CTkLabel(bubble, text=self._get_time(), font=("Roboto", 9), text_color="#555")
        footer.pack(side=tk.RIGHT, padx=10, pady=(0,4), anchor="se")

        self._on_frame_configure()

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Gabo AI", "¡Código copiado al portapapeles!")

    def _get_time(self):
        import datetime
        now = datetime.datetime.now()
        return now.strftime("%H:%M")

    def _strip_html(self, html_content):
        """Converts HTML to plain text for the bubble (removes tags, keeps code blocks)."""
        # markdown2 returns html, 
        # for simplicity, we remove tags except code blocks.
        import re
        # Replace <code>...</code> with ```...```
        html_content = re.sub(r"<code>(.+?)</code>", r"```\1```", html_content, flags=re.DOTALL)
        # Remove other tags
        html_content = re.sub(r"<[^>]+>", "", html_content)
        # Replace HTML entities
        html_content = html_content.replace("&nbsp;", " ").replace("&amp;", "&")
        return html_content

    def _get_gabo_response(self, user_text):
        try:
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": user_text}],
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            respuesta = data["choices"][0]["message"]["content"]
            # Reemplaza DeepSeek por Gabo automáticamente
            respuesta = respuesta.replace("DeepSeek", "Gabo")
            # Muestra la respuesta, procesando markdown y código
            self._add_bubble(respuesta, "gabo", markdown=True)
        except Exception as e:
            self._add_bubble("No se pudo entregar el mensaje.\n" + str(e), "gabo")
        finally:
            self.send_btn.configure(state="normal", text="Enviar")

if __name__ == "__main__":
    app = GaboAIApp()
    app.mainloop()
