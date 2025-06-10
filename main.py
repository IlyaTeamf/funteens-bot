import openai
import telebot
import os
import time

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def load_runtime_prompt():
    try:
        with open("runtime_core_v2.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Ты — Funteens. Объясняй как бро, не как бот."

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

bot.infinity_polling()
