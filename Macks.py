import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Clés API
TELEGRAM_TOKEN = "7797419882:AAF-GAzNn37bdtgRB942vxLGM0NkSimQ0oo"
COHERE_API_KEY = "KqL2Y8SUnkg267IwwFHFBELHiwGKzBIo1sh294As"

# Configuration de Cohere
cohere_client = cohere.Client(COHERE_API_KEY)

# Fonction pour interagir avec l'API Cohere
def cohere_query(prompt):
    try:
        response = cohere_client.generate(
            model='command-light',  # Utilisation d'un modèle plus léger pour économiser des ressources
            prompt=prompt,
            max_tokens=50,  # Limiter les tokens pour réduire la charge
            temperature=0.7,
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return "Une erreur est survenue. Réessayez plus tard."

# Commande /start
async def start(update: Update, context: CallbackContext):
    message = (
        "👋 Bienvenue sur DailyBizBot, ton assistant préféré en entrepreneuriat et marketing ! 🎯\n\n"
        "Voici ce que je peux faire pour toi :\n\n"
        "1⃣ /news - Obtiens 5 idées de business brillantes ✨\n"
        "2⃣ /plan - Génère un business plan simple et efficace 📈\n"
        "3⃣ /anecdote - Une anecdote motivante pour te booster 🚀\n"
        "4⃣ /bonsplans - Découvre des bons plans irrésistibles 💡\n\n"
        "💬 Et si tu veux discuter, je suis là pour toi. Pose-moi tes questions ou partage tes idées, mais attention, je ne mâche pas mes mots ! 😏\n\n"
        "Tape une commande pour commencer ou dis-moi ce qui te passe par la tête."
    )
    await update.message.reply_text(message)

# Commande /news
async def news_business(update: Update, context: CallbackContext):
    prompt = (
        "Donne-moi 5 idées de business actuelles, chacune sur un thème différent "
        "(technologie, restauration, services locaux, freelancing, e-commerce)."
    )
    news = cohere_query(prompt)
    await update.message.reply_text(f"📢 Voici 5 idées de business pour toi :\n\n{news}")

# Commande /plan
async def generate_business_plan(update: Update, context: CallbackContext):
    prompt = "Crée un business plan simple pour une idée donnée. Structure : marché, besoin, solution, revenus."
    plan = cohere_query(prompt)
    await update.message.reply_text(f"📝 Voici un exemple de business plan :\n\n{plan}")

# Commande /anecdote
async def anecdote(update: Update, context: CallbackContext):
    prompt = "Donne une courte anecdote motivante sur l'entrepreneuriat."
    anecdote = cohere_query(prompt)
    await update.message.reply_text(f"💡 Anecdote motivante :\n\n{anecdote}")

# Commande /bonsplans
async def bons_plans(update: Update, context: CallbackContext):
    prompt = "Partage un bon plan récent pour un entrepreneur débutant en France."
    bon_plan = cohere_query(prompt)
    await update.message.reply_text(f"🔥 Bon plan du jour :\n\n{bon_plan}")

# Réponse aux messages texte
async def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    prompt = f"Tu es une assistante experte en entrepreneuriat et marketing. Réponds de manière concise et sarcastique en français à ce message utilisateur : {user_message}"
    response = cohere_query(prompt)
    await update.message.reply_text(response)

# Configuration du bot Telegram
def main():
    # Créer l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commandes du bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_business))
    application.add_handler(CommandHandler("plan", generate_business_plan))
    application.add_handler(CommandHandler("anecdote", anecdote))
    application.add_handler(CommandHandler("bonsplans", bons_plans))

    # Handler pour les messages texte
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Lancer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
