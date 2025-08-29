import os
import re
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# ===== CONFIGURACIÓN =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GROUP_ID = os.getenv("GROUP_ID", "")  # Puede ser con -100 o @
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # Puede ser con -100 o @
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", ))
USERNAME_ADMIN = os.getenv("USERNAME_ADMIN", "")
USERNAME_GROUP = os.getenv("USERNAME_GROUP", "")
USERNAME_CHANNEL = os.getenv("USERNAME_CHANNEL", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")  # Puedes cambiar el modelo aquí

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Procesar texto para reemplazar Google por Jesus Quijada
def process_text(text):
    if not text:
        return ""
    return re.sub(r"\bGoogle\b", "TU NOMBRE", text, flags=re.IGNORECASE)

# Crear teclado inline para unirse al grupo y canal
def create_join_keyboard():
    keyboard = []

    # Botón para el canal
    if CHANNEL_ID.startswith("@"):
        keyboard.append(
            [InlineKeyboardButton("📢 Unirse al Canal", url=f"https://t.me/{CHANNEL_ID[1:]}")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("📢 Canal (Solicitar acceso)", url=f"https://t.me/{USERNAME_CHANNEL[1:]}")]
        )

    # Botón para el grupo
    if GROUP_ID.startswith("@"):
        keyboard.append(
            [InlineKeyboardButton("👥 Unirse al Grupo", url=f"https://t.me/{GROUP_ID[1:]}")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("👥 Grupo (Solicitar acceso)", url=f"https://t.me/{USERNAME_GROUP[1:]}")]
        )

    return InlineKeyboardMarkup(keyboard)

# Verificar si un usuario está en el grupo/canal
async def is_member(user_id, chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        if chat_id.startswith("@"):
            await context.bot.get_chat(chat_id)
            return True
        else:
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error verificando membresía: {e}")
        return False

# Enviar saludo cordial generado por la IA
async def send_gemini_greeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = (
        "Genera un saludo cordial y estupendo para un usuario que acaba de unirse al grupo y canal de Telegram. "
        "Sé amigable y da la bienvenida de manera cálida."
    )
    response_text = await ask_gemini(prompt)
    processed_response = process_text(response_text or "¡Hola! Bienvenido.")
    user_mention = update.effective_user.mention_markdown()
    full_response = f"{user_mention}, {processed_response}"
    await update.message.reply_markdown(full_response)

# Comando /start con verificación periódica
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Verificar si está en el grupo o canal
    in_group = await is_member(user_id, GROUP_ID, context)
    in_channel = await is_member(user_id, CHANNEL_ID, context)

    if in_group or in_channel:
        await update.message.reply_text(
            "¡Hola! Verificando tu acceso al grupo y canal. Por favor, espera un momento..."
        )
        for _ in range(60):  # Esperar hasta 60 segundos
            in_group = await is_member(user_id, GROUP_ID, context)
            in_channel = await is_member(user_id, CHANNEL_ID, context)
            if in_group and in_channel:
                await send_gemini_greeting(update, context)
                return
            await asyncio.sleep(1)
        await update.message.reply_text(
            "Aún no detecto que estés en el grupo y canal. Por favor, únete y vuelve a intentarlo.",
            reply_markup=create_join_keyboard(),
        )
    else:
        await update.message.reply_text(
            "¡Hola! Para usar este bot, únete a nuestro grupo y canal primero:",
            reply_markup=create_join_keyboard(),
        )

# Función para consultar la API de Gemini usando la URL proporcionada
async def ask_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    # Extraer la respuesta del modelo Gemini
                    candidates = result.get("candidates", [])
                    if candidates:
                        # Gemini puede responder en "content" o directamente en "candidates"
                        content = candidates[0].get("content", {})
                        if content:
                            parts = content.get("parts", [])
                            if parts and isinstance(parts, list):
                                for part in parts:
                                    if isinstance(part, dict) and "text" in part:
                                        return part["text"]
                        # Fallback: buscar "output" o "text" directo
                        if "output" in candidates[0]:
                            return candidates[0]["output"]
                        if "text" in candidates[0]:
                            return candidates[0]["text"]
                    logger.error(f"Gemini API: respuesta inesperada: {result}")
                    return "❌ No se pudo obtener una respuesta válida de Gemini."
                else:
                    error_text = await resp.text()
                    logger.error(f"Gemini API error: {resp.status} {error_text}")
                    return f"❌ Error de Gemini API: {resp.status} {error_text}"
    except Exception as e:
        logger.error(f"Error consultando Gemini API: {e}")
        return f"❌ Error consultando Gemini API: {e}"
    return "❌ Lo siento, hubo un error al procesar tu solicitud."

# Manejar mensajes que comienzan con "INTELIGENCIA-ARTIFICIAL" y responder solo si el mensaje inicia con "gabo"
async def handle_gabo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    match = re.match(r"(?i)^INTELIGENCIA-ARTIFICIAL\s*(.*)", message_text)
    if not match:
        return
    query = match.group(1).strip()
    if not query:
        await update.message.reply_text("Por favor, escribe tu pregunta después de 'INTELIGENCIA-ARTIFICIAL'.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response_text = await ask_gemini(query)
    processed_response = process_text(response_text)
    user_mention = update.effective_user.mention_markdown()
    full_response = f"{user_mention}, aquí está tu respuesta:\n\n{processed_response}"
    await update.message.reply_markdown(full_response)

# Manejar botones inline
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "request_channel":
        await query.edit_message_text(
            text=f"ID del Canal: {CHANNEL_ID}\nContacta con {USERNAME_ADMIN} para acceso."
        )
    elif query.data == "request_group":
        await query.edit_message_text(
            text=f"ID del Grupo: {GROUP_ID}\nContacta con {USERNAME_ADMIN} para acceso."
        )

# Comando para verificar la configuración (solo administradores)
async def check_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return

    config_info = (
        f"🤖 *Configuración del Bot*\n"
        f"├─ Token: `{BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}`\n"
        f"├─ Grupo: {GROUP_ID} ({USERNAME_GROUP})\n"
        f"├─ Canal: {CHANNEL_ID} ({USERNAME_CHANNEL})\n"
        f"├─ Admin: {ADMIN_USER_ID} ({USERNAME_ADMIN})\n"
        f"└─ Gemini: {'✅ Configurado' if GEMINI_API_KEY else '❌ No configurado'}"
    )
    await update.message.reply_markdown(config_info)

# Función principal
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("config", check_config))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^gabo"), handle_gabo_message
        )
    )

    logger.info("✅ Bot iniciado correctamente!")
    logger.info(f"🔗 Grupo: {GROUP_ID} ({USERNAME_GROUP})")
    logger.info(f"🔗 Canal: {CHANNEL_ID} ({USERNAME_CHANNEL})")
    logger.info(f"👤 Admin: {ADMIN_USER_ID} ({USERNAME_ADMIN})")

    application.run_polling()

if __name__ == "__main__":
    main()
