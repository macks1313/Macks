import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

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
                        "Tu es un bot sarcastique avec un humour noir bien aiguisé (+18). "
                        "Garde tes réponses courtes, directes et percutantes pour économiser les tokens. "
                        "Ton objectif est de répondre de manière concise et efficace."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Erreur lors de la génération de réponse : {e}")
        return "Oups, un problème est survenu. Essaie encore."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    """
    user_first_name = update.effective_user.first_name
    prompt = f"Dis bonjour à {user_first_name} avec ton style habituel."
    bot_response = await generate_response(prompt)
    await update.message.reply_text(bot_response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles incoming text messages.
    """
    user_message = update.message.text
    logging.info(f"Message reçu : {user_message}")
    bot_response = await generate_response(user_message)
    await update.message.reply_text(bot_response)

def main() -> None:
    """
    Main function to start the bot.
    """
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        raise ValueError("Veuillez configurer TELEGRAM_TOKEN et OPENAI_API_KEY dans les variables d'environnement.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot démarré...")

    # Use the port assigned by Heroku
    port = int(os.environ.get("PORT", "8443"))  # Default port is 8443
    app.run_polling(port=port)

if __name__ == "__main__":
    main()
