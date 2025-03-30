import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
import asyncio
from flask import Flask, request

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Токен та ID
TOKEN = "7903591351:AAH9zNPCwh4eTXMuMWQa1T0EwV5xgemwjds"
ADMIN_ID = 6085114476

# Для роботи на Render
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-app-name.onrender.com')

print(f"Порт для сервера: {PORT}")
print(f"Webhook URL: {WEBHOOK_URL}")

# Стани для ConversationHandler
AWAITING_MESSAGE = 0
AWAITING_REPLY = 1

# Зберігаємо інформацію про користувачів
user_data = {}
# Зберігаємо повідомлення для відстеження ланцюжків відповідей
messages_data = {}

# Повідомлення при запуску скрипта
print(f"Запуск бота з токеном: {TOKEN[:5]}...{TOKEN[-5:]}")
print(f"ID адміністратора: {ADMIN_ID}")

# Створюємо Flask застосунок для вебхуку
flask_app = Flask(__name__)

# Решта вашого коду залишається без змін
# ...

@flask_app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обробник вебхуків для Flask."""
    return 'OK'

@flask_app.route('/')
def index():
    """Проста сторінка для перевірки, що сервер працює."""
    return 'Бот працює! Порт: ' + str(PORT)

def main() -> None:
    """Головна функція бота."""
    print(f"Бот готовий до роботи в режимі webhook на порту {PORT}. Чекаємо вебхуки...")
    
    # Створення додатку
    application = Application.builder().token(TOKEN).build()
    
    # Додавання обробників...
    
    # Налаштування webhook
    print(f"Налаштування webhook на {WEBHOOK_URL}/{TOKEN}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    # Тут основна проблема! Flask повинен слухати той самий порт,
    # який очікує Render - а це порт 8080 з змінної PORT
    flask_app.run(host='0.0.0.0', port=PORT)
    
    # Решта вашого коду...
