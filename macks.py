import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurer les logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Récupérer les tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Fonction de test pour /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Commande /start reçue de {update.effective_chat.id}")
    await update.message.reply_text("Salut ! Je suis actif !")

# Initialisation du bot
def main():
    logger.info("Démarrage du bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter une commande /start pour tester
    application.add_handler(CommandHandler("start", start))

    # Lancer le bot en mode polling
    application.run_polling()

if __name__ == "__main__":
    main()

