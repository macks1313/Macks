from telegram.ext import Application, CommandHandler

# Config variables
TELEGRAM_TOKEN = "votre_token_telegram"

# Commande /start
async def start(update, context):
    await update.message.reply_text("Bienvenue ! Utilisez /filter pour chercher des cryptos.")

# Commande /filter
async def filter_cryptos(update, context):
    await update.message.reply_text("Filtrage des cryptos... (à implémenter)")

# Configurer l'application Telegram
def main():
    # Nouvelle méthode pour initialiser l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajout des gestionnaires de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("filter", filter_cryptos))

    # Lancer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
