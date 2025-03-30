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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Початкова команда."""
    user = update.effective_user
    
    # Зберігаємо дані користувача
    user_data[user.id] = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    
    user_info = f"ID: {user.id}, Ім'я: {user.first_name}, Прізвище: {user.last_name or 'Немає'}, Юзернейм: @{user.username or 'Немає'}"
    
    # Логуємо інформацію про користувача
    logger.info(f"СТАРТ: Користувач {user_info} запустив бота")
    print(f"СТАРТ: Користувач {user_info} запустив бота")
    
    # Відправляємо вітальне повідомлення користувачеві
    await update.message.reply_text(
        "Вітаю! Це бот для анонімних повідомлень👀.\n\n"
        "░🎉Просто надішліть текст, і я перешлю його анонімно🎉░.\n\n"
        "Тепер ви також можете відповідати на анонімні повідомлення, які отримуєте."
    )
    
    # Повідомляємо адміністратора про нового користувача
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Новий користувач почав використовувати бота:\n{user_info}"
        )
    except Exception as e:
        logger.error(f"Не вдалося надіслати повідомлення адміністратору: {e}")
        print(f"Помилка надсилання повідомлення адміністратору: {e}")

async def get_message_id():
    """Генерує унікальний ID для повідомлення."""
    return f"msg_{len(messages_data) + 1}"

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробка повідомлень від користувачів."""
    user = update.effective_user
    message_text = update.message.text
    
    # Оновлюємо дані користувача, якщо вони змінилися
    if user.id not in user_data:
        user_data[user.id] = {}
    
    user_data[user.id].update({
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'last_message': message_text
    })
    
    user_info = f"ID: {user.id}, Ім'я: {user.first_name}, Прізвище: {user.last_name or 'Немає'}, Юзернейм: @{user.username or 'Немає'}"
    
    # Логуємо повідомлення
    logger.info(f"ПОВІДОМЛЕННЯ: Від користувача {user_info}\nТекст: {message_text}")
    print(f"ПОВІДОМЛЕННЯ: Від користувача {user_info}\nТекст: {message_text}")
    
    # Генеруємо ID для цього повідомлення
    message_id = await get_message_id()
    
    # Зберігаємо інформацію про повідомлення
    messages_data[message_id] = {
        'sender_id': user.id,
        'text': message_text,
        'timestamp': update.message.date
    }
    
    # Повідомляємо користувача про отримання
    await update.message.reply_text(
        "✅ Ваше повідомлення отримано і буде анонімно переслано."
    )
    
    # Створюємо кнопки для відповіді на повідомлення
    keyboard = [
        [InlineKeyboardButton("Відповісти анонімно", callback_data=f"reply_{message_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Пересилаємо повідомлення адміністратору та для відповіді
    try:
        # Надсилаємо інформацію про відправника адміністратору (конфіденційно)
        if ADMIN_ID != user.id:  # Не надсилаємо адміну інформацію про себе
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📬 Нове анонімне повідомлення!\n\n"
                    f"Інформація про відправника (конфіденційно):\n{user_info}"
            )
            
            # Надсилаємо саме повідомлення з кнопкою для відповіді
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📝 Текст анонімного повідомлення:\n\n{message_text}",
                reply_markup=reply_markup
            )
        
        # Вибираємо отримувача повідомлення
        # Тут можна реалізувати логіку адресації повідомлень
        # Зараз всі повідомлення йдуть адміністратору
        recipient_id = ADMIN_ID
        
        # Якщо відправник - адміністратор, вибираємо останнього активного користувача
        if user.id == ADMIN_ID:
            # Знайдемо останнього активного користувача
            last_active_users = [uid for uid in user_data.keys() if uid != ADMIN_ID]
            if last_active_users:
                recipient_id = last_active_users[-1]  # Беремо останнього
        
        # Відправляємо повідомлення отримувачу (якщо це не той самий відправник)
        if recipient_id != user.id:
            await context.bot.send_message(
                chat_id=recipient_id,
                text=f"📝 Отримано анонімне повідомлення:\n\n{message_text}",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Не вдалося переслати повідомлення: {e}")
        print(f"Помилка пересилання повідомлення: {e}")
        
        # Повідомляємо користувача про помилку
        await update.message.reply_text(
            "⚠️ Виникла помилка при пересиланні повідомлення. Спробуйте пізніше."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка натискання кнопок."""
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на callback_query
    
    # Отримуємо дані кнопки
    data = query.data
    user = update.effective_user
    
    # Якщо це кнопка для відповіді
    if data.startswith("reply_"):
        message_id = data.split("_")[1]
        
        if message_id not in messages_data:
            await query.edit_message_text("⚠️ Це повідомлення більше недоступне.")
            return ConversationHandler.END
        
        # Запам'ятовуємо, на яке повідомлення відповідаємо
        context.user_data["reply_to_msg"] = message_id
        
        # Запитуємо текст відповіді
        await query.edit_message_text(
            text=f"💬 Введіть текст анонімної відповіді:\n\n"
                 f"На повідомлення: {messages_data[message_id]['text'][:50]}..."
        )
        
        return AWAITING_REPLY
    
    return ConversationHandler.END

async def process_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка відповіді користувача."""
    user = update.effective_user
    reply_text = update.message.text
    message_id = context.user_data.get("reply_to_msg")
    
    if not message_id or message_id not in messages_data:
        await update.message.reply_text("❌ Не вдалося визначити, на яке повідомлення відповідаєте.")
        return ConversationHandler.END
    
    # Знаходимо ID відправника оригінального повідомлення
    original_sender_id = messages_data[message_id]['sender_id']
    
    # Зберігаємо цю відповідь як нове повідомлення
    new_message_id = await get_message_id()
    messages_data[new_message_id] = {
        'sender_id': user.id,
        'text': reply_text,
        'in_reply_to': message_id,
        'timestamp': update.message.date
    }
    
    # Створюємо кнопку для відповіді на це повідомлення
    keyboard = [
        [InlineKeyboardButton("Відповісти анонімно", callback_data=f"reply_{new_message_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Надсилаємо відповідь відправнику оригінального повідомлення
    try:
        await context.bot.send_message(
            chat_id=original_sender_id,
            text=f"📨 Відповідь на ваше повідомлення:\n"
                 f"▶️ Ваше повідомлення: {messages_data[message_id]['text'][:50]}...\n\n"
                 f"📝 Відповідь: {reply_text}",
            reply_markup=reply_markup
        )
        
        # Підтверджуємо відправнику відповіді
        await update.message.reply_text(
            f"✅ Вашу анонімну відповідь успішно надіслано."
        )
        
        # Логуємо відповідь
        logger.info(f"ВІДПОВІДЬ: Користувач ID:{user.id} відповів на повідомлення ID:{message_id}")
        print(f"ВІДПОВІДЬ: Користувач ID:{user.id} відповів на повідомлення ID:{message_id}")
        
        # Також повідомляємо адміна про нову відповідь (якщо відправник не адмін)
        if user.id != ADMIN_ID and original_sender_id != ADMIN_ID:
            user_info = f"ID: {user.id}"
            if user.id in user_data:
                user_info = f"ID: {user.id}, Ім'я: {user_data[user.id].get('first_name', 'Немає')}, Юзернейм: @{user_data[user.id].get('username', 'Немає')}"
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📬 Нова анонімна відповідь!\n\n"
                     f"Інформація про відправника (конфіденційно):\n{user_info}\n\n"
                     f"На повідомлення: {messages_data[message_id]['text'][:50]}...\n\n"
                     f"Текст відповіді: {reply_text}",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Не вдалося надіслати відповідь: {e}")
        print(f"Помилка надсилання відповіді: {e}")
        await update.message.reply_text(f"❌ Помилка надсилання відповіді: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Скасування операції відповіді."""
    await update.message.reply_text("❌ Операцію скасовано.")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показати допомогу."""
    help_text = (
        "📌 Команди бота:\n\n"
        "/start - Запустити бота\n"
        "/help - Показати це повідомлення\n\n"
        "Просто надішліть текстове повідомлення, щоб відправити його анонімно.\n"
        "Ви можете відповідати на анонімні повідомлення, натиснувши кнопку 'Відповісти анонімно'."
    )
    
    # Додаємо інформацію для адміністратора
    if update.effective_user.id == ADMIN_ID:
        help_text += (
            "\n\n👑 Інформація для адміністратора:\n"
            "Ви бачите конфіденційну інформацію про всіх відправників."
        )
    
    await update.message.reply_text(help_text)

@flask_app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обробник вебхуків для Flask."""
    return 'OK'

@flask_app.route('/')
def index():
    """Проста сторінка для перевірки, що сервер працює."""
    return 'Бот працює!'

def main() -> None:
    """Головна функція бота."""
    print("Бот готовий до роботи в режимі webhook. Чекаємо вебхуки...")
    
    # Створення додатку
    application = Application.builder().token(TOKEN).build()
    
    # Створюємо ConversationHandler для відповідей
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback)],
        states={
            AWAITING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True,
    )
    
    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))
    
    # Налаштування webhook
    print(f"Налаштування webhook на {WEBHOOK_URL}/{TOKEN}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    # Запуск бота в режимі webhook через асинхронну петлю
    from threading import Thread
    
    def run_flask():
        flask_app.run(host='0.0.0.0', port=PORT)
    
    # Запускаємо Flask у окремому потоці
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаємо бота
    main()
