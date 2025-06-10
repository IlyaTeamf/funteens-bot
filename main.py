import openai
import telebot
import os
from flask import Flask, request

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def load_runtime_prompt():
    try:
        with open("runtime_core_v2.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Ты — Funteens. Объясняй как бро, не как бот."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def receive_update():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def setup_webhook():
    webhook_url = f"{RENDER_EXTERNAL_URL}{TELEGRAM_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    prompt = load_runtime_prompt()

    try:
        thread = openai.beta.threads.create()

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            instructions=prompt
        )

        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if status.status == "completed":
                break
            elif status.status == "failed":
                bot.send_message(message.chat.id, "Упс! Что-то пошло не так.")
                return
            import time
            time.sleep(1.5)

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                text = msg.content[0].text.value
                bot.send_message(message.chat.id, text)
                return

        bot.send_message(message.chat.id, "Не удалось получить ответ.")

    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка: попробуй ещё раз позже.")
        print("Ошибка:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
