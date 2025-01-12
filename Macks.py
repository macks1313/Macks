import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Retrieve environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

async def generate_response(prompt: str) -> str:
    """
    Generates a response using OpenAI's API.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es une experte sarcastique en entrepreneuriat et marketing, avec un humour noir bien aiguisé (+18). 
                        "Pose des questions percutantes et un brin provocatrices. Garde tes réponses courtes (50 à 75 tokens max)," 
                        "parce que personne n'a envie de lire ton roman. Sois directe, mais jamais ennuyeuse."
                        "Rappelle-toi : ton job, c'est de faire réfléchir tout en sortant des punchlines qui claquent."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Oups, quelque chose a cassé : {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    """
    await update.message.reply_text("Oh génial, encore un humain qui a besoin d'aide. Qu'est-ce que tu veux ?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles incoming text messages.
    """
    user_message = update.message.text
    bot_response = await generate_response(user_message)
    await update.message.reply_text(bot_response)

def main() -> None:
    """
    Main function to start the bot.
    """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
