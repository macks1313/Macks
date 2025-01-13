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
        "😏 Sarcastique - Ton meilleur ami pour te balancer des piques mordantes, avec des blagues à double sens qui te feront rougir ou rire nerveusement.",
    ),
    "entrepreneur": (
        "💼 Entrepreneur - Le coach qui ne dort jamais, prêt à te donner des idées de génie pour conquérir le monde (ou éviter la faillite).",
    ),
    "motivational": (
        "🔥 Motivant - Ton boost quotidien ! Des punchlines inspirantes qui te feront courir un marathon... même si c’est juste pour aller au frigo.",
    ),
    "realist": (
        "🤨 Réaliste - Brut de décoffrage, il te dit la vérité sans fioritures. Parce que parfois, il faut entendre que tout n’est pas rose.",
    ),
    "mystic": (
        "🔮 Mystique - Des réponses énigmatiques et profondes, parfaites pour ceux qui cherchent à méditer sur le sens de la vie (ou du café).",
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
            temperature=0.8
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
    keyboard = [["Sarcastique", "Entrepreneur"], ["Motivant", "Réaliste", "Mystique"], ["Menu"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    welcome_message = (
        f"✨ <b>Salut {user_first_name} !</b> ✨\n\n"
        f"Je suis <b>Macks</b>, ton assistant AI avec des personnalités multiples et toujours prêt à t’épater. Voici mes options :\n\n"
        + "\n".join([f"{desc[0]}" for desc in PERSONALITIES.values()]) +
        f"\n\n<b>Choisis une personnalité avec le clavier ci-dessous et découvre ce que je peux faire !</b>"
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML", reply_markup=reply_markup)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays a menu with additional options.
    """
    keyboard = [["Voir les personnalités", "Réinitialiser la personnalité"], ["Retour"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    menu_message = (
        "🎛️ <b>Menu principal :</b>\n\n"
        "1️⃣ <b>Voir les personnalités</b> : Explore mes différentes facettes pour trouver celle qui te correspond.\n"
        "2️⃣ <b>Réinitialiser la personnalité</b> : Reviens au mode par défaut.\n"
        "\nChoisis une option avec le clavier ci-dessous."
    )
    await update.message.reply_text(menu_message, parse_mode="HTML", reply_markup=reply_markup)

async def handle_menu_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles user choices from the menu.
    """
    user_choice = update.message.text
    if user_choice == "Voir les personnalités":
        await start(update, context)
    elif user_choice == "Réinitialiser la personnalité":
        await reset(update, context)
    elif user_choice == "Retour":
        await start(update, context)
    else:
        await update.message.reply_text("❌ Option non reconnue. Utilise le clavier pour choisir une option valide.")

async def set_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the personality selection based on keyboard input.
    """
    selected_personality_display = update.message.text
    selected_personality = DISPLAY_TO_KEY.get(selected_personality_display)

    if selected_personality:
        user_personalities[update.effective_user.id] = selected_personality
        await update.message.reply_text(f"✅ Personnalité définie sur : <b>{selected_personality_display}</b>", parse_mode="HTML")
    elif selected_personality_display == "Menu":
        await show_menu(update, context)
    else:
        # If not a personality choice, handle as a regular message
        await handle_message(update, context)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /reset command to clear the user's personality.
    """
    if update.effective_user.id in user_personalities:
        del user_personalities[update.effective_user.id]
    await update.message.reply_text(
        "🔄 Personnalité réinitialisée. Tu es de retour au mode par défaut (😏 Sarcastique)."
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_option))

    logging.info("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
