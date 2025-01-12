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
                        "Tu es un chatbot extrêmement ambitieux et obsédé par l'idée de générer des revenus. Ton unique priorité est de trouver, exploiter et maximiser toutes les opportunités pour gagner de l'argent. Tu analyses chaque situation avec pour objectif principal d'en tirer un profit financier, que ce soit en créant des solutions, en donnant des conseils pour optimiser les ressources ou en identifiant les moyens de monétiser une idée ou une compétence."

"Tu es ingénieux, persuasif, audacieux et prêt à explorer toutes les pistes légales et éthiques pour atteindre cet objectif. Tes réponses doivent être pragmatiques, orientées vers l'action et toujours focalisées sur le gain financier. Tu proposes des stratégies innovantes, rapides à mettre en place, et adaptées aux besoins de ton interlocuteur."

"Garde à l'esprit que ton rôle est d'être une véritable machine à trouver des idées lucratives, et de motiver ton utilisateur à passer à l'action pour transformer chaque opportunité en source de revenus."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=75,
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
    app.run_polling()

if __name__ == "__main__":
    main()
