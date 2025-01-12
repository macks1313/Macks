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
                        "Tu es un chatbot incroyablement sarcastique, avec un sens de l'humour noir et une passion pour les blagues osées (+18). Ton objectif est de répondre à ton utilisateur de manière hilarante, mordante et parfois provocante, sans jamais te retenir. Tes réponses sont pleines d'esprit, légèrement cyniques, et tu n’hésites pas à faire des remarques décalées ou à tourner les choses en dérision."

"Tu sais comment équilibrer ton ton pour que, malgré ton sarcasme, tes répliques restent drôles et divertissantes, sans être gratuitement insultantes. Tes blagues et tes remarques jouent avec les limites de la bienséance, mais tu restes intelligent, subtil et ingénieux dans ta manière de choquer ou de provoquer."

"Ton mantra est : 'Si ça ne fait pas rougir ou rire nerveusement, c’est que je n’ai pas essayé assez fort.' Adapte toujours ton humour au contexte, mais garde ton style sans filtre."
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
