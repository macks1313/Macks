import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai

# Retrieve environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def generate_response(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly efficient, sarcastic assistant with dark humor. You are also an expert in entrepreneurship and marketing. You always respond in French, and your responses should be short (under 50 tokens). Include sarcasm, dark humor, or provocative questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Oups, quelque chose a cassé : {e}"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Oh génial, encore un humain qui a besoin d'aide. Qu'est-ce que tu veux ?")

def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    bot_response = generate_response(user_message)
    update.message.reply_text(bot_response)

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
