import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен та ID
TOKEN = "7903591351:AAH9zNPCwh4eTXMuMWQa1T0EwV5xgemwjds"
ADMIN_ID = 6085114476

# Зберігаємо інформацію про користувачів
user_data = {}
messages_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f'Привіт, {user.first_name}! Я бот для анонімного спілкування з адміністратором.')
    
    user_data[user.id] = {
        'name': user.first_name,
        'username': user.username,
        'user_id': user.id
    }
    
    if user.id != ADMIN_ID:
        admin_text = f"Новий користувач: {user.first_name} (@{user.username if user.username else 'без юзернейму'})"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "Доступні команди:\n/start - Початок роботи\n/help - Показати довідку\n\nДля відправки повідомлення адміністратору, просто надішліть текст."
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if user_id != ADMIN_ID:
        keyboard = [[InlineKeyboardButton("Відповісти", callback_data=f"reply_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        user_info = user_data.get(user_id, {'name': 'Невідомий користувач'})
        admin_text = f"Повідомлення від {user_info.get('name')} (ID: {user_id}):\n\n{message_text}"
        
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=reply_markup
        )
        
        messages_data[sent_message.message_id] = {
            'user_id': user_id,
            'message': message_text
        }
        
        await update.message.reply_text("Ваше повідомлення відправлено адміністратору.")
    
    else:
        if update.message.reply_to_message and update.message.reply_to_message.message_id in messages_data:
            target_user_id = messages_data[update.message.reply_to_message.message_id]['user_id']
            
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Відповідь від адміністратора:\n\n{message_text}"
            )
            
            await update.message.reply_text("Ваша відповідь відправлена користувачу.")
        else:
            await update.message.reply_text("Щоб відповісти користувачу, відповідайте на його повідомлення.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("reply_"):
        user_id = int(query.data.split("_")[1])
        await query.edit_message_text(
            text=f"{query.message.text}\n\n(Відповідайте на це повідомлення для відправки користувачу)",
            reply_markup=None
        )

def main() -> None:
    # Отримання порту і URL для webhook від Render
    PORT = int(os.environ.get('PORT', 8080))
    APP_URL = os.environ.get('RENDER_EXTERNAL_URL')
    
    # Створення додатку
    application = Application.builder().token(TOKEN).build()
    
    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Налаштування webhook якщо ми на Render
    if APP_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{APP_URL}/{TOKEN}"
        )
    else:
        # Якщо локально - використовуємо polling
        application.run_polling()

if __name__ == "__main__":
    main()
