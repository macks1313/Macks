import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Récupérer les variables d'environnement (Heroku)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY_LUNARCRUSH = os.getenv("API_KEY_LUNARCRUSH")

# Fonction pour interagir avec LunarCrush API
def get_crypto_data(symbol):
    url = f"https://api.lunarcrush.com/v2?data=assets&key={API_KEY_LUNARCRUSH}&symbol={symbol}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            asset = data["data"][0]
            name = asset.get("name", "N/A")
            price = asset.get("price", "N/A")
            change_24h = asset.get("percent_change_24h", "N/A")
            return f"📈 {name} ({symbol})\n💰 Price: ${price}\n📊 Change (24h): {change_24h}%"
        else:
            return "❌ No data found for this cryptocurrency."
    else:
        return "❌ Failed to fetch data from LunarCrush."

# Commande /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Use /crypto <symbol> to get cryptocurrency data.")

# Commande /crypto
def crypto(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /crypto BTC")
        return

    symbol = context.args[0].upper()
    message = get_crypto_data(symbol)
    update.message.reply_text(message)

# Configurer le bot
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Ajouter des commandes
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("crypto", crypto))

    # Démarrer le bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
