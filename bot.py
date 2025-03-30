import logging
import os
import threading
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
from flask import Flask
Налаштування логування
logging.basicConfig(
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.DEBUG
)
logger = logging.getLogger(name)
Токен та ID адміністратора
TOKEN = "7903591351:AAH9zNPCwh4eTXMuMWQa1T0EwV5xgemwjds"
ADMIN_ID = 6085114476
Стани для ConversationHandler
AWAITING_REPLY = 1
Зберігаємо інформацію про користувачів
user_data = {}
Flask додаток для обходу перевірки портів
app = Flask(name)
@app.route('/')
def health_check():
return "Bot is alive and waiting for Telegram messages"
def run_flask():
app.run(host='0.0.0.0', port=8000)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
user = update.effective_user
user_data[user.id] = {
'username': user.username,
'first_name': user.first_name,
'last_name': user.last_name
}
await update.message.reply_text(
"Вітаю! Надішліть повідомлення, і я перешлю його анонімно👀!\n"
"🎉 Просто надішліть текст, і я перешлю його АНОНІМНО 🎉"
)
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
user = update.effective_user
message_text = update.message.text
user_data[user.id] = {
'last_message': message_text
}
keyboard = [[InlineKeyboardButton("Відповісти анонімно", callback_data=f"reply_{user.id}")]]
reply_markup = InlineKeyboardMarkup(keyboard)

await context.bot.send_message(
    chat_id=ADMIN_ID,
    text=f"📬 Нове анонімне повідомлення:\n\n{message_text}",
    reply_markup=reply_markup
)
await update.message.reply_text("✅ Ваше повідомлення отримано і буде переслано анонімно✨!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
query = update.callback_query
await query.answer()
if query.data.startswith("reply_"):
user_id = int(query.data.split("_")[1])
context.user_data["reply_to"] = user_id
await query.edit_message_text(
text="Введіть відповідь для анонімного користувача."
)
return AWAITING_REPLY
return ConversationHandler.END
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
reply_text = update.message.text
reply_to_id = context.user_data.get("reply_to")
if not reply_to_id:
await update.message.reply_text("❌ Помилка: Не знайдено одержувача.")
return ConversationHandler.END
await context.bot.send_message(
    chat_id=reply_to_id,
    text=f"📨 Вам надійшла анонімна відповідь:\n\n{reply_text}"
)
await update.message.reply_text("✅ Відповідь успішно надіслана🍓!")
return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
await update.message.reply_text("❌ Операцію скасовано.")
return ConversationHandler.END
def main() -> None:
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
application = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_callback)],
    states={
        AWAITING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_user)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=True,
)

application.add_handler(CommandHandler("start", start))
application.add_handler(conv_handler)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

while True:
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Бот зупинився з помилкою: {e}. Перезапуск через 10 секунд...")
        time.sleep(10)

if name == "main":
main()
