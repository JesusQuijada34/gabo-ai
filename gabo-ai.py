import pygame
import sys
import math
import random
from typing import List, Dict, Tuple, Optional, Callable
import requests
import json
from datetime import datetime

# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gabo AI - Interfaz con Efectos HTML")

# Colores
BACKGROUND = (240, 240, 245)
SIDEBAR_BG = (30, 30, 40)
PRIMARY = (76, 175, 80)
PRIMARY_LIGHT = (105, 200, 110)
SECONDARY = (50, 130, 184)
TEXT = (30, 30, 30)
TEXT_LIGHT = (200, 200, 200)
WHITE = (255, 255, 255)
CARD_BG = (250, 250, 255)
SHADOW = (200, 200, 200, 100)
USER_MSG = (76, 175, 80)
AI_MSG = (240, 240, 245)

# Configuración de la API
API_KEY = "AIzaSyDD8X1GvPm6j3axGaWz-pmjKSQXdP8eci4"
MODELS = {
    "flash": {"name": "Gabo AI Flash", "model": "gemini-2.0-flash", "color": (76, 175, 80)},
    "pro": {"name": "Gabo AI Pro", "model": "gemini-1.5-pro-latest", "color": (50, 130, 184)},
    "classic": {"name": "Gabo AI Classic", "model": "gemini-1.0-pro", "color": (156, 39, 176)}
}
current_model = MODELS["flash"]

# Fuentes
font_small = pygame.font.SysFont("Arial", 14)
font_medium = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 24)
font_title = pygame.font.SysFont("Arial", 32, bold=True)

# Estados de la aplicación
class AppState:
    def __init__(self):
        self.messages = []
        self.input_text = ""
        self.typing_indicator = False
        self.typing_progress = 0
        self.animations = []
        self.particles = []
        self.sidebar_visible = True
        self.selected_tab = "chat"
        self.scroll_offset = 0
        self.max_scroll = 0

app_state = AppState()

# Clases para elementos de UI
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None, icon=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.icon = icon
        self.hovered = False
        self.alpha = 255

    def draw(self, surface):
        # Dibujar sombra
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (*SHADOW[:3], 100), shadow_rect, border_radius=8)

        # Dibujar botón
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        # Efecto de brillo en hover
        if self.hovered:
            highlight = pygame.Surface((self.rect.width, 4), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 100))
            surface.blit(highlight, (self.rect.x, self.rect.y))

        # Dibujar texto
        text_surf = font_medium.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        # Dibujar icono si existe
        if self.icon:
            icon_rect = pygame.Rect(self.rect.x + 10, self.rect.y + (self.rect.height - 20) // 2, 20, 20)
            # Aquí podrías dibujar un icono real

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            if self.action:
                self.action()
            return True
        return False

class InputBox:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def draw(self, surface):
        # Dibujar fondo
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)

        # Dibujar texto
        text_surf = font_medium.render(self.text, True, TEXT)
        surface.blit(text_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))

        # Dibujar cursor si está activo
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 10 + font_medium.size(self.text)[0]
            pygame.draw.line(surface, TEXT, (cursor_x, self.rect.y + 10),
                            (cursor_x, self.rect.y + self.rect.height - 10), 2)

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

        return None

class Message:
    def __init__(self, text, is_user=False):
        self.text = text
        self.is_user = is_user
        self.height = 0
        self.alpha = 0
        self.animation_progress = 0
        self.width = 400 if is_user else 500

    def draw(self, surface, x, y):
        # Calcular altura basada en el texto
        lines = self.wrap_text(self.text, self.width - 40)
        self.height = len(lines) * 25 + 30

        # Actualizar animación
        if self.animation_progress < 1:
            self.animation_progress += 0.05
            self.alpha = int(255 * self.animation_progress)

        # Crear superficie para el mensaje con alpha
        msg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Dibujar fondo del mensaje
        color = USER_MSG if self.is_user else AI_MSG
        pygame.draw.rect(msg_surface, (*color, self.alpha), (0, 0, self.width, self.height), border_radius=15)

        # Dibujar texto
        for i, line in enumerate(lines):
            text_surf = font_medium.render(line, True, (*TEXT, self.alpha))
            msg_surface.blit(text_surf, (20, 15 + i * 25))

        # Dibujar sombra
        shadow = pygame.Surface((self.width + 6, self.height + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 30))
        surface.blit(shadow, (x - 3, y - 3))

        # Dibujar mensaje
        surface.blit(msg_surface, (x, y))

        # Dibujar indicador de usuario/ai
        indicator = "Tú" if self.is_user else current_model["name"]
        indicator_surf = font_small.render(indicator, True, (*TEXT, self.alpha//2))
        surface.blit(indicator_surf, (x + 20, y + self.height + 5))

        return self.height

    def wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font_medium.size(test_line)[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed_x = random.uniform(-1, 1)
        self.speed_y = random.uniform(-2, 0)
        self.lifetime = random.randint(20, 40)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.size *= 0.95
        return self.lifetime > 0

    def draw(self, surface):
        alpha = min(255, self.lifetime * 6)
        pygame.draw.circle(surface, (*self.color, alpha), (int(self.x), int(self.y)), int(self.size))

# Funciones de utilidad
def draw_rounded_rect(surface, rect, color, radius=10):
    """Dibuja un rectángulo con bordes redondeados"""
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def create_particles(x, y, color, count=10):
    """Crea partículas en una posición específica"""
    for _ in range(count):
        app_state.particles.append(Particle(x, y, color))

def send_message_to_gemini(message):
    """Envía un mensaje a la API de Gemini"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model['model']}:generateContent"
        params = {"key": API_KEY}

        headers = {"Content-Type": "application/json"}

        data = {
            "contents": [{
                "parts": [{"text": message}]
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

    except Exception as e:
        return f"Error al conectar con Gabo AI: {str(e)}"

def add_message(text, is_user=False):
    """Añade un mensaje a la conversación"""
    app_state.messages.append(Message(text, is_user))
    # Crear partículas para el efecto
    if is_user:
        create_particles(WIDTH - 220, HEIGHT - 150, PRIMARY, 15)
    else:
        create_particles(220, HEIGHT - 150, SECONDARY, 15)

    # Calcular scroll máximo
    total_height = sum(msg.height + 20 for msg in app_state.messages)
    app_state.max_scroll = max(0, total_height - (HEIGHT - 200))

# Inicializar elementos de UI
input_box = InputBox(220, HEIGHT - 80, WIDTH - 440, 40)
send_button = Button(WIDTH - 200, HEIGHT - 80, 80, 40, "Enviar", PRIMARY, PRIMARY_LIGHT)

# Añadir mensaje de bienvenida
add_message("¡Hola! Soy Gabo AI, tu asistente de inteligencia artificial. ¿En qué puedo ayudarte hoy?")

# Bucle principal
clock = pygame.time.Clock()
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()

    # Manejar eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Manejar entrada de texto
        result = input_box.handle_event(event)
        if result:
            add_message(result, True)
            input_box.text = ""
            app_state.typing_indicator = True
            app_state.typing_progress = 0

        # Manejar botón de enviar
        if send_button.handle_event(event):
            if input_box.text:
                add_message(input_box.text, True)
                input_box.text = ""
                app_state.typing_indicator = True
                app_state.typing_progress = 0

        # Manejar scroll
        if event.type == pygame.MOUSEWHEEL:
            app_state.scroll_offset = max(0, min(app_state.max_scroll, app_state.scroll_offset - event.y * 30))

    # Actualizar elementos
    input_box.update()
    send_button.update(mouse_pos)

    # Actualizar partículas
    app_state.particles = [p for p in app_state.particles if p.update()]

    # Simular typing indicator
    if app_state.typing_indicator:
        app_state.typing_progress += 1
        if app_state.typing_progress > 60:  # Simular tiempo de respuesta
            app_state.typing_indicator = False
            response = send_message_to_gemini(app_state.messages[-1].text)
            add_message(response)

    # Dibujar interfaz
    screen.fill(BACKGROUND)

    # Dibujar sidebar
    sidebar_width = 200 if app_state.sidebar_visible else 0
    pygame.draw.rect(screen, SIDEBAR_BG, (0, 0, sidebar_width, HEIGHT))

    # Dibujar logo
    logo_text = font_title.render("Gabo AI", True, WHITE)
    screen.blit(logo_text, (sidebar_width//2 - logo_text.get_width()//2, 30))

    # Dibujar botones de modelo
    model_y = 100
    for model_id, model in MODELS.items():
        model_color = PRIMARY_LIGHT if model_id == current_model else SIDEBAR_BG
        model_rect = pygame.Rect(20, model_y, sidebar_width - 40, 50)
        pygame.draw.rect(screen, model_color, model_rect, border_radius=8)

        model_text = font_medium.render(model["name"], True, WHITE)
        screen.blit(model_text, (sidebar_width//2 - model_text.get_width()//2, model_y + 15))

        model_y += 70

    # Dibujar área de chat
    pygame.draw.rect(screen, WHITE, (sidebar_width, 0, WIDTH - sidebar_width, HEIGHT - 100))

    # Dibujar mensajes
    y_pos = 20 - app_state.scroll_offset
    for message in app_state.messages:
        x_pos = WIDTH - message.width - 40 if message.is_user else sidebar_width + 40
        height = message.draw(screen, x_pos, y_pos)
        y_pos += height + 20

    # Dibujar typing indicator
    if app_state.typing_indicator:
        indicator_x = sidebar_width + 60
        indicator_y = HEIGHT - 130
        for i in range(3):
            alpha = 100 + (155 * (abs((app_state.typing_progress // 5 + i) % 6 - 3) / 3))
            pygame.draw.circle(screen, (100, 100, 100, alpha),
                              (indicator_x + i * 20, indicator_y),
                              5)

    # Dibujar área de entrada
    pygame.draw.rect(screen, (230, 230, 235), (sidebar_width, HEIGHT - 100, WIDTH - sidebar_width, 100))
    input_box.rect.x = sidebar_width + 40
    input_box.draw(screen)

    # Dibujar botón de enviar
    send_button.rect.x = WIDTH - 200
    send_button.draw(screen)

    # Dibujar partículas
    for particle in app_state.particles:
        particle.draw(screen)

    # Actualizar pantalla
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
