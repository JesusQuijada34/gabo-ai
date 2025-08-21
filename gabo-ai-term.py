#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
import readline  # Para mejor experiencia de entrada
from time import sleep
from datetime import datetime
from typing import List, Dict, Optional

# Importaciones de Rich para interfaz colorida
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

# Configuración de la consola
console = Console()

# API Configuration
API_KEY = "AIzaSyDD8X1GvPm6j3axGaWz-pmjKSQXdP8eci4"
MODELS = {
    "1": {"name": "Gabo AI Flash", "model": "gemini-2.0-flash", "description": "Modelo rápido y eficiente"},
    "2": {"name": "Gabo AI Pro", "model": "gemini-1.5-pro-latest", "description": "Modelo avanzado con más capacidades"},
    "3": {"name": "Gabo AI Classic", "model": "gemini-1.0-pro", "description": "Versión clásica del asistente"}
}

# Historial de conversación
conversation_history: List[Dict] = []
current_model = MODELS["1"]  # Modelo por defecto

def clear_screen():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Muestra el banner de Gabo AI"""
    banner_text = Text()
    banner_text.append("🐍 ", style="bold green")
    banner_text.append("Gabo AI Terminal", style="bold cyan")
    banner_text.append(" 🐍", style="bold green")

    console.print(Panel(
        banner_text,
        style="bold blue",
        box=box.DOUBLE,
        padding=(1, 2)
    ))

    console.print("Tu asistente de IA en terminal. Escribe 'help' para ver comandos disponibles.\n", style="italic")

def display_help():
    """Muestra la ayuda de comandos"""
    help_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    help_table.add_column("Comando", style="cyan")
    help_table.add_column("Descripción", style="green")
    help_table.add_column("Ejemplo")

    help_table.add_row("help", "Muestra esta ayuda", "help")
    help_table.add_row("clear", "Limpia la pantalla", "clear")
    help_table.add_row("history", "Muestra el historial de conversación", "history")
    help_table.add_row("save", "Guarda la conversación en un archivo", "save chat.txt")
    help_table.add_row("model", "Cambia el modelo de IA", "model 2")
    help_table.add_row("exit", "Sale de la aplicación", "exit")
    help_table.add_row("-g", "Hace una pregunta directa", '-g "¿Cómo funciona Python?"')
    help_table.add_row("", "Pregunta normal", "¿Cómo estás?")

    console.print(Panel(
        help_table,
        title="[bold]Comandos de Gabo AI[/bold]",
        border_style="green",
        padding=(1, 2)
    ))

def display_models():
    """Muestra los modelos disponibles"""
    models_table = Table(show_header=True, header_style="bold yellow", box=box.ROUNDED)
    models_table.add_column("ID", style="cyan")
    models_table.add_column("Nombre", style="green")
    models_table.add_column("Modelo")
    models_table.add_column("Descripción")

    for id, model_info in MODELS.items():
        models_table.add_row(
            id,
            model_info["name"],
            model_info["model"],
            model_info["description"]
        )

    console.print(Panel(
        models_table,
        title="[bold]Modelos Disponibles[/bold]",
        border_style="blue",
        padding=(1, 2)
    ))

def change_model():
    """Permite cambiar el modelo de IA"""
    display_models()

    try:
        choice = IntPrompt.ask(
            "\nSelecciona el ID del modelo",
            choices=list(MODELS.keys()),
            default=1
        )

        global current_model
        current_model = MODELS[str(choice)]

        console.print(f"\n[bold green]✓[/bold green] Modelo cambiado a: [cyan]{current_model['name']}[/cyan]")
        sleep(1)

    except Exception as e:
        console.print(f"[bold red]Error al cambiar modelo:[/bold red] {e}")
        sleep(2)

def show_history():
    """Muestra el historial de conversación"""
    if not conversation_history:
        console.print("[italic yellow]No hay historial de conversación.[/italic yellow]")
        return

    history_table = Table(show_header=True, header_style="bold blue", box=box.ROUNDED)
    history_table.add_column("Fecha", style="cyan")
    history_table.add_column("Tipo", style="green")
    history_table.add_column("Mensaje")

    for msg in conversation_history:
        msg_type = "Usuario" if msg["is_user"] else "Gabo AI"
        style = "blue" if msg["is_user"] else "green"

        # Acortar mensajes largos para la tabla
        preview = msg["text"]
        if len(preview) > 50:
            preview = preview[:47] + "..."

        history_table.add_row(
            msg["time"],
            f"[{style}]{msg_type}[/{style}]",
            preview
        )

    console.print(Panel(
        history_table,
        title="[bold]Historial de Conversación[/bold]",
        border_style="yellow",
        padding=(1, 2)
    ))

    # Opción para ver detalles de un mensaje
    try:
        if Confirm.ask("\n¿Ver detalles de algún mensaje?"):
            msg_id = IntPrompt.ask(
                "Ingresa el número de mensaje (orden en la tabla)",
                min_value=1,
                max_value=len(conversation_history)
            )

            msg = conversation_history[msg_id - 1]
            console.print("\n" + "="*60)
            console.print(f"[bold]Fecha:[/bold] {msg['time']}")
            console.print(f"[bold]Tipo:[/bold] {'Usuario' if msg['is_user'] else 'Gabo AI'}")
            console.print(f"[bold]Mensaje:[/bold]")

            if msg["is_user"]:
                console.print(Panel(msg["text"], border_style="blue"))
            else:
                # Intentar formatear como markdown si es respuesta de AI
                try:
                    console.print(Markdown(msg["text"]))
                except:
                    console.print(Panel(msg["text"], border_style="green"))

            console.print("="*60)
    except:
        pass

def save_conversation(filename=None):
    """Guarda la conversación en un archivo"""
    if not filename:
        filename = Prompt.ask(
            "Nombre del archivo para guardar",
            default=f"gabo_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Conversación con Gabo AI\n")
            f.write("=" * 50 + "\n\n")

            for msg in conversation_history:
                sender = "Tú" if msg["is_user"] else "Gabo AI"
                f.write(f"{sender} ({msg['time']}):\n")
                f.write(msg["text"] + "\n")
                f.write("-" * 30 + "\n")

        console.print(f"[bold green]✓[/bold green] Conversación guardada en: [cyan]{filename}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]Error al guardar:[/bold red] {e}")

def send_to_gemini(prompt: str) -> str:
    """Envía un mensaje a la API de Gemini y devuelve la respuesta"""
    try:
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

        with console.status("[bold green]Gabo AI está pensando...[/bold green]", spinner="dots"):
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

def add_to_history(text: str, is_user: bool = True):
    """Añade un mensaje al historial"""
    conversation_history.append({
        "text": text,
        "is_user": is_user,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def display_response(response: str):
    """Muestra la respuesta de Gabo AI con formato"""
    console.print("\n")

    # Panel para el header de Gabo AI
    console.print(Panel.fit(
        f"[bold green]Gabo AI[/bold green] ([italic]{current_model['name']}[/italic])",
        border_style="green"
    ))

    # Intentar detectar y formatear código en la respuesta
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Es código
                # Intentar detectar lenguaje
                lines = part.split('\n')
                lang = lines[0].strip() if lines[0].strip() in ['python', 'javascript', 'java', 'html', 'css', 'bash'] else ''
                code = '\n'.join(lines[1:]) if lang else part

                console.print(Syntax(
                    code,
                    lang or "text",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True
                ))
            else:
                console.print(Markdown(part))
    else:
        console.print(Markdown(response))

    console.print("\n")

def process_command(command: str) -> bool:
    """Procesa comandos internos y devuelve False si debe salir"""
    global current_model

    if command.lower() in ['exit', 'quit', 'salir']:
        console.print("[bold green]¡Hasta pronto! 👋[/bold green]")
        return False

    elif command.lower() == 'help':
        display_help()

    elif command.lower() == 'clear':
        clear_screen()
        display_banner()

    elif command.lower() == 'history':
        show_history()

    elif command.lower().startswith('save'):
        parts = command.split(' ', 1)
        filename = parts[1] if len(parts) > 1 else None
        save_conversation(filename)

    elif command.lower() == 'model':
        change_model()

    elif command.lower().startswith('-g'):
        # Comando directo: -g "pregunta"
        parts = command.split(' ', 1)
        if len(parts) > 1:
            question = parts[1].strip('"\'')
            if question:
                add_to_history(question)
                response = send_to_gemini(question)
                add_to_history(response, False)
                display_response(response)
        else:
            console.print("[bold red]Uso:[/bold red] -g \"tu pregunta\"")

    elif command.strip():
        # Pregunta normal
        add_to_history(command)
        response = send_to_gemini(command)
        add_to_history(response, False)
        display_response(response)

    return True

def main():
    """Función principal de la aplicación"""
    clear_screen()
    display_banner()

    # Mostrar selección de modelos al inicio
    if not conversation_history:
        console.print("[bold]Selección inicial de modelo:[/bold]")
        display_models()

        try:
            choice = IntPrompt.ask(
                "Selecciona el ID del modelo a usar",
                choices=list(MODELS.keys()),
                default=1
            )

            global current_model
            current_model = MODELS[str(choice)]
            console.print(f"\n[bold green]✓[/bold green] Modelo seleccionado: [cyan]{current_model['name']}[/cyan]")

        except Exception as e:
            console.print(f"[bold red]Error seleccionando modelo:[/bold red] {e}")
            console.print("Usando modelo por defecto: Gabo AI Flash")

    console.print("\n[italic]Escribe tu mensaje o 'help' para ver comandos disponibles...[/italic]\n")

    # Bucle principal de la aplicación
    running = True
    while running:
        try:
            # Personalizar el prompt con el nombre del modelo actual
            prompt_text = Text()
            prompt_text.append(">>> ", style="bold green")
            prompt_text.append(f"[{current_model['name']}] ", style="italic cyan")

            user_input = console.input(prompt_text).strip()

            if user_input:
                running = process_command(user_input)

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]¿Quieres salir? Presiona Ctrl+C again o escribe 'exit'[/bold yellow]")
            try:
                sleep(2)  # Dar tiempo para la segunda interrupción
            except KeyboardInterrupt:
                console.print("\n[bold green]¡Hasta pronto! 👋[/bold green]")
                break
        except EOFError:
            console.print("\n[bold green]¡Hasta pronto! 👋[/bold green]")
            break
        except Exception as e:
            console.print(f"[bold red]Error inesperado:[/bold red] {e}")
            sleep(2)

if __name__ == "__main__":
    main()
