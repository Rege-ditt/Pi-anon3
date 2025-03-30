import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler

# Налаштування логування - збільшуємо рівень деталізації
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Змінено з INFO на DEBUG для більш детальних логів
)
logger = logging.getLogger(__name__)

# Токен та ID
TOKEN = "7903591351:AAH9zNPCwh4eTXMuMWQa1T0EwV5xgemwjds"
ADMIN_ID = 6085114476

# Стани для ConversationHandler
AWAITING_MESSAGE = 0
AWAITING_REPLY = 1

# Зберігаємо інформацію про користувачів
user_data = {}

# Повідомлення при запуску скрипта
print(f"Запуск бота з токеном: {TOKEN[:5]}...{TOKEN[-5:]}")
print(f"ID адміністратора: {ADMIN_ID}")

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
        "░🎉Просто надішліть текст, і я перешлю його АНОНІМНО🎉░."
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
    
    # Повідомляємо користувача про отримання
    await update.message.reply_text(
        "✅ Ваше повідомлення отримано і буде анонімно переслано✨                                                         ⚠️ На жаль, функція відповіді на надіслане Вам анонімне повідомлення зараз недоступна😭 ."
    )
    
    # Створюємо кнопки для відповіді на повідомлення
    keyboard = [
        [InlineKeyboardButton("Відповісти анонімно", callback_data=f"reply_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Пересилаємо повідомлення адміністратору
    try:
        # Надсилаємо інформацію про відправника (тільки адміністратору)
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
    except Exception as e:
        logger.error(f"Не вдалося переслати повідомлення адміністратору: {e}")
        print(f"Помилка пересилання повідомлення адміністратору: {e}")
        
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
    
    # Якщо це кнопка для відповіді
    if data.startswith("reply_"):
        user_id = int(data.split("_")[1])
        
        # Запам'ятовуємо, кому відповідаємо
        context.user_data["reply_to"] = user_id
        
        # Запитуємо текст відповіді
        await query.edit_message_text(
            text=f"Введіть текст відповіді для користувача ID: {user_id}\n\n"
                 f"Останнє повідомлення: {user_data.get(user_id, {}).get('last_message', 'Немає')}"
        )
        
        return AWAITING_REPLY
    
    return ConversationHandler.END

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробка відповіді адміністратора."""
    # Перевіряємо, чи це адміністратор
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ця функція доступна тільки адміністратору.")
        return ConversationHandler.END
    
    reply_text = update.message.text
    reply_to_id = context.user_data.get("reply_to")
    
    if not reply_to_id:
        await update.message.reply_text("❌ Не вдалося визначити, кому відповідати.")
        return ConversationHandler.END
    
    # Надсилаємо відповідь користувачу
    try:
        await context.bot.send_message(
            chat_id=reply_to_id,
            text=f"📨 Відповідь від адміністратора:\n\n{reply_text}"
        )
        
        # Підтверджуємо адміністратору
        user_info = f"ID: {reply_to_id}"
        if reply_to_id in user_data:
            user = user_data[reply_to_id]
            user_info = f"ID: {reply_to_id}, Ім'я: {user.get('first_name', 'Немає')}, Юзернейм: @{user.get('username', 'Немає')}"
        
        await update.message.reply_text(
            f"✅ Вашу відповідь успішно надіслано користувачу:\n{user_info}"
        )
        
        logger.info(f"ВІДПОВІДЬ: Адміністратор відповів користувачу {reply_to_id}: {reply_text}")
        print(f"ВІДПОВІДЬ: Адміністратор відповів користувачу {reply_to_id}: {reply_text}")
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
        "Просто надішліть текстове повідомлення, і воно буде анонімно переслано адміністратору."
    )
    
    # Додаємо інформацію для адміністратора
    if update.effective_user.id == ADMIN_ID:
        help_text += (
            "\n\n👑 Команди адміністратора:\n"
            "Ви можете відповідати на анонімні повідомлення, натиснувши кнопку 'Відповісти анонімно'"
        )
    
    await update.message.reply_text(help_text)

def main() -> None:
    """Головна функція бота."""
    print("Бот готовий до роботи. Натисніть Ctrl+C для завершення.")
    
    # Створення додатку
    application = Application.builder().token(TOKEN).build()
    
    # Створюємо ConversationHandler для відповідей адміністратора
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback)],
        states={
            AWAITING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True,
    )
    
    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
