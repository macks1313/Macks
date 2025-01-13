import os
from telegram import Update, ReplyKeyboardMarkup
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
        "😉 Sarcastique - Un chatbot incroyablement sarcastique, avec un sens de l'humour noir et une passion pour les blagues osées (+18).",
    ),
    "entrepreneur": (
        "💼 Entrepreneur - Un expert en entrepreneuriat, prêt à donner des conseils pratiques et stratégiques.",
    ),
    "motivational": (
        "🌟 Motivant - Toujours prêt à encourager et inspirer avec des réponses puissantes.",
    ),
    "realist": (
        "🤓 Réaliste - Froid, pragmatique et direct, avec une vision claire des faits.",
    ),
    "mystic": (
        "🌌 Mystique - Énigmatique et poétique, offrant des réponses empreintes de sagesse.",
    )
}

# Mapping between display names and internal keys
DISPLAY_TO_KEY = {
    "Sarcastique": "sarcastic",
    "Entrepreneur": "entrepreneur",
    "Motivant": "motivational",
    "Réaliste": "realist",
    "Mystique": "mystic"
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
    keyboard = [["Sarcastique", "Entrepreneur"], ["Motivant", "Réaliste", "Mystique"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    welcome_message = (
        f"<b>Salut {user_first_name} !</b>\n\n"
        f"Je suis <b>Macks</b>, ton assistant AI multifacette. Voici mes personnalités disponibles :\n\n"
        + "\n".join([f"{desc[0]}" for desc in PERSONALITIES.values()]) +
        f"\n\n<b>Choisis une personnalité avec le clavier ci-dessous et laisse-moi te surprendre !</b>"
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML", reply_markup=reply_markup)

async def set_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the personality selection based on keyboard input.
    """
    selected_personality_display = update.message.text
    selected_personality = DISPLAY_TO_KEY.get(selected_personality_display)

    if selected_personality:
        user_personalities[update.effective_user.id] = selected_personality
        await update.message.reply_text(f"Personnalité définie sur : {selected_personality_display} ✅")
    else:
        await update.message.reply_text(
            "Personnalité non reconnue. Choisis parmi le clavier ou utilise les commandes disponibles."
        )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /reset command to clear the user's personality.
    """
    if update.effective_user.id in user_personalities:
        del user_personalities[update.effective_user.id]
    await update.message.reply_text(
        "Personnalité réinitialisée. Reviens au mode par défaut (😉 Sarcastique)."
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
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_personality))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
