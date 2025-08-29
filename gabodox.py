# PyQt5 app para extraer la máxima información pública posible de usuarios, grupos o canales de Telegram.
# Permite ingresar @usuario, número telefónico o enlace de grupo/canal.
# Interfaz pulida y moderna con fuente Roboto.
# Útil para identificar posibles cuentas de spam, descubrir estafas y obtener datos útiles para protección y denuncia policial.

import sys
import re
import requests
import socket
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

def load_github_qss():
    # QSS oscuro pulido con fuente Roboto
    return """
    QWidget {
        background-color: #232629;
        color: #eaeaea;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-size: 14px;
    }
    QLabel {
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 6px;
        letter-spacing: 0.2px;
    }
    QLineEdit, QTextEdit {
        background: #2d2f31;
        border: 1.5px solid #444;
        border-radius: 6px;
        padding: 6px 8px;
        color: #eaeaea;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-size: 14px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1.5px solid #5e81ac;
        background: #232629;
    }
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b3f44, stop:1 #2d2f31);
        border: 1.5px solid #5e81ac;
        border-radius: 6px;
        padding: 8px 18px;
        color: #eaeaea;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-size: 15px;
        font-weight: 500;
        letter-spacing: 0.5px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    QPushButton:hover {
        background: #444950;
        border: 1.5px solid #81a1c1;
    }
    QTextEdit {
        min-height: 180px;
        font-size: 13.5px;
        line-height: 1.5;
        margin-top: 8px;
    }
    QMessageBox QLabel {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-size: 14px;
    }
    """

def extract_info(input_text):
    # Detecta tipo de entrada: @usuario, número, o enlace
    input_text = input_text.strip()
    if input_text.startswith("@"):
        return get_user_info(input_text[1:])
    elif re.match(r"^\+?\d{7,15}$", input_text):
        return get_phone_info(input_text)
    elif "t.me/" in input_text:
        return get_link_info(input_text)
    else:
        return "<b>❌ Entrada no reconocida.</b><br>Ingresa un <b>@usuario</b>, número telefónico o enlace de grupo/canal."

def get_user_info(username):
    # Extrae toda la info pública posible usando la web de Telegram y OSINT
    url = f"https://t.me/{username}"
    info = f"<h2>🕵️‍♂️ Usuario: <span style='color:#81a1c1;'>@{username}</span></h2>"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            # Extrae info básica del HTML
            title = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
            desc = re.search(r'<meta property="og:description" content="([^"]+)"', r.text)
            image = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
            # Extrae posible user_id de los scripts (no siempre disponible)
            user_id = None
            m = re.search(r'"user_id":\s*"?(\d+)"?', r.text)
            if m:
                user_id = m.group(1)
            # OSINT extra: buscar user_id en servicios públicos (ejemplo: t.me/idbot)
            if not user_id:
                user_id = osint_user_id(username)
            # Extrae posible número de teléfono (muy raro que esté público)
            phone = None
            m2 = re.search(r'"phone":\s*"(\+?\d+)"', r.text)
            if m2:
                phone = m2.group(1)
            # Añade info extraída, formateada en HTML
            info += "<ul style='margin-left:0.5em;'>"
            if title:
                info += f"<li><b>Nombre:</b> {title.group(1)}</li>"
            if desc:
                info += f"<li><b>Descripción:</b> {desc.group(1)}</li>"
            if user_id:
                info += f"<li><b>ID numérico:</b> <span style='color:#b48ead;'>{user_id}</span></li>"
            else:
                info += "<li><b>ID numérico:</b> <i>No disponible públicamente</i></li>"
            if phone:
                info += f"<li><b>Teléfono (si es público):</b> {phone}</li>"
            if image:
                info += f"<li><b>Foto de perfil:</b> <a href='{image.group(1)}' style='color:#a3be8c;'>Ver imagen</a></li>"
            info += f"<li><b>Enlace:</b> <a href='{url}' style='color:#81a1c1;'>{url}</a></li>"
            # Intento de obtener IP pública asociada (solo posible para bots/canales con dominio propio)
            ip_info = get_ip_from_telegram_url(url)
            if ip_info:
                info += f"<li><b>IP asociada:</b> {ip_info}</li>"
            info += "</ul>"
            info += (
                "<div style='margin-top:10px;'><b>⚠️ Solo se muestra información pública visible en Telegram Web y fuentes OSINT.</b></div>"
                "<div style='margin-top:6px;'>"
                "🔎 <b>¿Sospechas de estafa?</b> Guarda el <b>ID numérico</b> y <b>username</b> para denunciarlo ante la policía o en <a href='https://t.me/antiscam' style='color:#bf616a;'>@antiscam</a>.<br>"
                "También puedes buscar el username en Google, Scamadviser, o bases de datos OSINT para ver si está reportado como spammer o scammer."
                "</div>"
            )
            return info
        elif r.status_code == 404:
            return f"<b>❌ Usuario @{username} no encontrado.</b>"
        else:
            return f"<b>❌ Error al consultar Telegram:</b> {r.status_code}"
    except Exception as e:
        return f"<b>❌ Error de red:</b> {e}"

def osint_user_id(username):
    """
    Intenta obtener el user_id usando fuentes OSINT públicas (por ejemplo, id.tginfo.me).
    """
    try:
        # Servicio público de tginfo.me (no oficial, pero útil para OSINT)
        resp = requests.get(f"https://id.tginfo.me/{username}", timeout=8)
        if resp.status_code == 200:
            m = re.search(r'ID:\s*(\d+)', resp.text)
            if m:
                return m.group(1)
            # Algunos servicios devuelven JSON
            try:
                data = resp.json()
                if "id" in data:
                    return str(data["id"])
            except Exception:
                pass
        # Alternativamente, buscar en otros servicios OSINT si lo deseas
    except Exception:
        pass
    return None

def get_phone_info(phone):
    # No se puede obtener info de Telegram solo con el número (privacidad)
    # Pero se puede intentar buscar en bases OSINT públicas (ejemplo: numverify, etc)
    # Aquí solo mostramos advertencia y sugerencia
    return (
        f"<b>🔒 No es posible extraer información pública de Telegram solo con el número telefónico (+{phone}).</b><br>"
        "Prueba con un <b>@usuario</b> o enlace de grupo/canal.<br>"
        "🔎 Puedes buscar el número en Google, Scamadviser, o bases OSINT para ver si está reportado como spam o estafa."
    )

def get_link_info(link):
    # Extrae info de grupo/canal público usando la web de Telegram
    m = re.search(r"t\.me/([a-zA-Z0-9_]+)", link)
    if not m:
        return "<b>❌ Enlace de Telegram no válido.</b>"
    entity = m.group(1)
    url = f"https://t.me/{entity}"
    info = f"<h2>🕵️‍♂️ Grupo/Canal: <span style='color:#81a1c1;'>{entity}</span></h2>"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            title = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
            desc = re.search(r'<meta property="og:description" content="([^"]+)"', r.text)
            image = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
            # Extrae posible id numérico (no siempre disponible)
            group_id = None
            m2 = re.search(r'"chat_id":\s*"?(-?\d+)"?', r.text)
            if m2:
                group_id = m2.group(1)
            # Añade info extraída, formateada en HTML
            info += "<ul style='margin-left:0.5em;'>"
            if title:
                info += f"<li><b>Título:</b> {title.group(1)}</li>"
            if desc:
                info += f"<li><b>Descripción:</b> {desc.group(1)}</li>"
            if group_id:
                info += f"<li><b>ID numérico:</b> <span style='color:#b48ead;'>{group_id}</span></li>"
            else:
                info += "<li><b>ID numérico:</b> <i>No disponible públicamente</i></li>"
            if image:
                info += f"<li><b>Foto:</b> <a href='{image.group(1)}' style='color:#a3be8c;'>Ver imagen</a></li>"
            info += f"<li><b>Enlace:</b> <a href='{url}' style='color:#81a1c1;'>{url}</a></li>"
            # Intento de obtener IP pública asociada (solo posible para canales con dominio propio)
            ip_info = get_ip_from_telegram_url(url)
            if ip_info:
                info += f"<li><b>IP asociada:</b> {ip_info}</li>"
            info += "</ul>"
            info += (
                "<div style='margin-top:10px;'><b>⚠️ Solo se muestra información pública visible en Telegram Web y fuentes OSINT.</b></div>"
                "<div style='margin-top:6px;'>"
                "🔎 Puedes buscar el enlace en Google, Scamadviser, o bases OSINT para ver si está reportado como spam o scam.<br>"
                "Si detectas actividad sospechosa, guarda el <b>ID numérico</b> y <b>enlace</b> para denunciarlo ante la policía."
                "</div>"
            )
            return info
        elif r.status_code == 404:
            return f"<b>❌ Grupo o canal no encontrado:</b> {link}"
        else:
            return f"<b>❌ Error al consultar Telegram:</b> {r.status_code}"
    except Exception as e:
        return f"<b>❌ Error de red:</b> {e}"

def get_ip_from_telegram_url(url):
    # Intenta extraer el host y resolver la IP (solo útil si es un dominio personalizado)
    try:
        m = re.match(r"https?://([^/]+)/([a-zA-Z0-9_]+)", url)
        if m:
            host = m.group(1)
            # Si es t.me, devuelve la IP de t.me (no del usuario real)
            if host != "t.me":
                ip = socket.gethostbyname(host)
                return ip
            else:
                # Para t.me, muestra la IP de t.me (no es la del usuario real, pero puede ser útil para análisis de red)
                ip = socket.gethostbyname("t.me")
                return ip
        return None
    except Exception:
        return None

class TelegramInfoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GABO THE DOXTH")
        self.setMinimumWidth(500)
        self.setMinimumHeight(380)
        self.setWindowIcon(QIcon())  # Puedes poner un ícono personalizado aquí si lo deseas

        # Fuente Roboto para toda la app (si está instalada)
        roboto = QFont("Roboto", 13)
        roboto.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(roboto)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(10)

        title = QLabel("GABO THE DOXTH")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Roboto", 19, QFont.Bold))
        title.setStyleSheet("color: #81a1c1; margin-bottom: 2px; letter-spacing: 1.2px;")
        layout.addWidget(title)

        subtitle = QLabel("Extrae información pública de usuarios, grupos o canales de Telegram para descubrir estafas y protegerte.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Roboto", 12, QFont.Normal))
        subtitle.setStyleSheet("color: #bfc9db; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        input_label = QLabel("Introduce @usuario, número telefónico o enlace de grupo/canal:")
        input_label.setFont(QFont("Roboto", 12, QFont.Normal))
        input_label.setStyleSheet("margin-bottom: 2px;")
        layout.addWidget(input_label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("@usuario, +584123456789, o https://t.me/ejemplo")
        self.input.setFont(QFont("Roboto", 13))
        self.input.setMinimumHeight(32)
        layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        btn_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.btn = QPushButton("Extraer información completa")
        self.btn.setFont(QFont("Roboto", 14, QFont.Bold))
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setMinimumHeight(36)
        self.btn.clicked.connect(self.on_extract)
        btn_layout.addWidget(self.btn)
        btn_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(btn_layout)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setFont(QFont("Roboto", 12))
        self.result.setMinimumHeight(180)
        self.result.setAcceptRichText(True)
        layout.addWidget(self.result)

        # Pie de página
        footer = QLabel("Hecho con ❤️ por GaboAI | Solo muestra información pública y OSINT. Úsalo para protegerte y denunciar estafas.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Roboto", 10, QFont.Light))
        footer.setStyleSheet("color: #6c7a89; margin-top: 8px;")
        layout.addWidget(footer)

        self.setLayout(layout)

    def on_extract(self):
        text = self.input.text()
        if not text.strip():
            QMessageBox.warning(self, "Campo vacío", "Por favor, ingresa un valor.")
            return
        self.result.setHtml("<i>Consultando...</i>")
        info = extract_info(text)
        # Mostrar como HTML formateado
        try:
            self.result.setHtml(info)
        except Exception:
            self.result.setPlainText(info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_github_qss())
    window = TelegramInfoApp()
    window.show()
    sys.exit(app.exec_())
