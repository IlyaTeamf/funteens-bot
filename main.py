import os
import telebot
import time
import traceback
from flask import Flask, request
from openai import OpenAI

# Переменные окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def index():
    return "Funteens bot is running!", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    print("📨 Пришёл запрос:", user_input)

    try:
        thread = client.beta.threads.create()
        print("🧵 Thread создан:", thread.id)

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        print("📨 Сообщение отправлено в OpenAI.")

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        print("🚀 Run запущен:", run.id)

        # Ожидаем выполнения
        for _ in range(10):
            status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            print("🔄 Статус выполнения:", status.status)

            if status.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                response_text = messages.data[0].content[0].text.value
                print("✅ Ответ от ассистента:", response_text)
                bot.send_message(message.chat.id, response_text)
                return
            elif status.status == "failed":
                print("❌ Запуск провалился.")
                bot.send_message(message.chat.id, "Упс! Что-то пошло не так.")
                return

            time.sleep(1)

        bot.send_message(message.chat.id, "Ответ не готов. Попробуй ещё раз.")
    except Exception as e:
        print("💥 Ошибка в handle_message:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, "Ошибка: попробуй ещё раз позже.")

# Запуск
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{os.getenv('RENDER_EXTERNAL_URL')}{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
