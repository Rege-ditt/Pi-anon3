import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
import asyncio
from flask import Flask, request
import threading

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

# Базові команди бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробка команди /start"""
    user = update.effective_user
    await update.message.reply_text(f'Привіт, {user.first_name}! Я бот для анонімного спілкування з адміністратором.')
    
    # Зберігаємо інформацію про користувача
    user_data[user.id] = {
        'name': user.first_name,
        'username': user.username,
        'user_id': user.id
    }
    
    # Повідомляємо адміна про нового користувача
    if user.id != ADMIN_ID:
        admin_text = f"Новий користувач: {user.first_name} (@{user.username if user.username else 'без юзернейму'})"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробка команди /help"""
    help_text = """
    Доступні команди:
    /start - Початок роботи з ботом
    /help - Показати цю довідку
    
    Для відправки повідомлення адміністратору, просто надішліть текст.
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробка вхідних повідомлень"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Якщо це повідомлення від звичайного користувача
    if user_id != ADMIN_ID:
        # Відправляємо повідомлення адміну
        keyboard = [
            [InlineKeyboardButton("Відповісти", callback_data=f"reply_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        user_info = user_data.get(user_id, {'name': 'Невідомий користувач'})
        admin_text = f"Повідомлення від {user_info.get('name')} (ID: {user_id}):\n\n{message_text}"
        
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=reply_markup
        )
        
        # Зберігаємо ID повідомлення для відстеження
        messages_data[sent_message.message_id] = {
            'user_id': user_id,
            'message': message_text
        }
        
        # Підтверджуємо користувачу отримання
        await update.message.reply_text("Ваше повідомлення відправлено адміністратору.")
    
    # Якщо це повідомлення від адміна і він відповідає на чиєсь повідомлення
    else:
        # Перевіряємо, чи відповідає адмін на повідомлення користувача
        if update.message.reply_to_message and update.message.reply_to_message.message_id in messages_data:
            target_user_id = messages_data[update.message.reply_to_message.message_id]['user_id']
            
            # Відправляємо відповідь користувачу
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Відповідь від адміністратора:\n\n{message_text}"
            )
            
            await update.message.reply_text("Ваша відповідь відправлена користувачу.")
        else:
            await update.message.reply_text("Щоб відповісти користувачу, використовуйте функцію 'Відповісти' під його повідомленням або відповідайте на його повідомлення.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка натискань на кнопки"""
    query = update.callback_query
    await query.answer()
    
    # Перевіряємо, чи це кнопка відповіді
    if query.data.startswith("reply_"):
        user_id = int(query.data.split("_")[1])
        await query.edit_message_text(
            text=f"{query.message.text}\n\n(Очікування відповіді...)",
            reply_markup=None
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Введіть відповідь для користувача (ID: {user_id}):"
        )
        
        # Зберігаємо інформацію про поточне повідомлення для відповіді
        context.user_data['current_reply_to'] = user_id
        return AWAITING_REPLY
    
    return ConversationHandler.END

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Відправка відповіді користувачу"""
    reply_text = update.message.text
    user_id = context.user_data.get('current_reply_to')
    
    if user_id:
        # Відправляємо відповідь користувачу
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Відповідь від адміністратора:\n\n{reply_text}"
        )
        
        await update.message.reply_text("Ваша відповідь відправлена користувачу.")
        
        # Очищаємо дані про поточну відповідь
        context.user_data.pop('current_reply_to', None)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Відміна режиму відповіді"""
    await update.message.reply_text("Відповідь скасовано.")
    context.user_data.pop('current_reply_to', None)
    return ConversationHandler.END

@flask_app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обробник вебхуків для Flask."""
    return 'OK'

@flask_app.route('/')
def index():
    """Проста сторінка для перевірки, що сервер працює."""
    return 'Бот працює! Порт: ' + str(PORT)

def run_flask():
    """Функція для запуску Flask в окремому потоці"""
    flask_app.run(host='0.0.0.0', port=PORT)

def main() -> None:
    """Головна функція бота."""
    print(f"Бот готовий до роботи в режимі webhook на порту {PORT}. Чекаємо вебхуки...")
    
    # Створення додатку
    application = Application.builder().token(TOKEN).build()
    
    # Додавання обробників команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Створення ConversationHandler для обробки відповідей
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback)],
        states={
            AWAITING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_user)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Обробник звичайних повідомлень (має бути останнім)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Налаштування webhook
    print(f"Налаштування webhook на {WEBHOOK_URL}/{TOKEN}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        webhook_url_path=f"/{TOKEN}"
    )

if __name__ == "__main__":
    # Запускаємо Flask у окремому потоці
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаємо бота
    main()
