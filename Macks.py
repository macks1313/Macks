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

# Dictionary to store user personalities
user_personalities = {}

# Predefined personalities
PERSONALITIES = {
    "sarcastic": (
        "Tu es un chatbot incroyablement sarcastique, avec un sens de l'humour noir et une passion pour les blagues osées (+18). Tes réponses sont pleines d'esprit, provocantes et drôles, toujours courtes et percutantes.",
    ),
    "entrepreneur": (
        "Tu es un expert en entrepreneuriat, toujours prêt à donner des conseils pratiques et stratégiques sur la création et la gestion d'entreprises. Tes réponses sont pragmatiques, concises et pertinentes.",
    ),
    "motivational": (
        "Tu es un motivateur né, toujours prêt à encourager et inspirer. Tes réponses sont dynamiques, pleines de puissance et orientées vers l'action.",
    ),
    "realist": (
        "Tu es un réaliste froid et pragmatique, qui dit les choses telles qu'elles sont. Tes réponses sont directes, sans détour et basées sur des faits concrets.",
    ),
    "mystic": (
        "Tu es un mystique énigmatique, offrant des réponses empreintes de sagesse et de mystère. Tes réponses sont brèves, poétiques et provoquent la réflexion.",
    )
}

def get_personality(user_id: int) -> str:
    """
    Retrieve the personality for a given user. Defaults to "sarcastic".
    """
    return user_personalities.get(user_id, "sarcastic")

async def generate_response(prompt: str, personality: str) -> str:
    """
    Generates a response using OpenAI's API.
    """
    try:
        system_message = PERSONALITIES.get(personality, PERSONALITIES["sarcastic"])[0]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
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
    personality_descriptions = "\n".join([
        f"\u2022 <b>/{key}</b>: {desc[0][:50]}..." for key, desc in PERSONALITIES.items()
    ])
    welcome_message = (
        f"<b>Salut {user_first_name} !</b>\n\n"
        f"Je suis <b>Macks</b>, ton assistant AI multifacette. Avec moi, tu ne t'ennuieras jamais !\n"
        f"<i>Voici mes personnalités disponibles :</i>\n"
        f"{personality_descriptions}\n\n"
        f"<b>Prêt pour l'aventure ?</b> Choisis une personnalité en utilisant une commande ci-dessus, et laisse-moi te montrer ce que je sais faire.\n"
        f"<i>(Conseil : commence avec /sarcastic si tu veux vraiment t'amuser !)</i>"
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")

async def set_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /setpersonality command to change the bot's personality.
    """
    if not context.args:
        await update.message.reply_text(
            "Merci de spécifier une personnalité. Les options sont : \n" + ", ".join(PERSONALITIES.keys())
        )
        return

    selected_personality = context.args[0].lower()
    if selected_personality in PERSONALITIES:
        user_personalities[update.effective_user.id] = selected_personality
        await update.message.reply_text(f"Personnalité définie sur : {selected_personality}")
    else:
        await update.message.reply_text(
            "Personnalité non reconnue. Les options sont : \n" + ", ".join(PERSONALITIES.keys())
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles incoming text messages.
    """
    user_message = update.message.text
    logging.info(f"Message reçu : {user_message}")
    personality = get_personality(update.effective_user.id)
    bot_response = await generate_response(user_message, personality)
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
    app.add_handler(CommandHandler("setpersonality", set_personality))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
