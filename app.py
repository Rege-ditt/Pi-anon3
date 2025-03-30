import os
from flask import Flask
from threading import Thread
import bot  # Імпортуємо ваш основний файл з ботом

app = Flask(__name__)

@app.route('/')
def index():
    return 'Бот працює!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
