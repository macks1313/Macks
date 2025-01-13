import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from flask import Flask, request
import asyncio

# Récupérer les variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY_LUNARCRUSH = os.getenv("API_KEY_LUNARCRUSH")

# Initialiser Flask pour le serveur
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

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
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome! Use /crypto <symbol> to get cryptocurrency data.")

# Commande /crypto
async def crypto(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /crypto BTC")
        return

    symbol = context.args[0].upper()
    message = get_crypto_data(symbol)
    await update.message.reply_text(message)

# Fonction principale pour démarrer le bot
async def run_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter des commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("crypto", crypto))

    # Démarrer le bot
    await application.run_polling()

# Point d'entrée principal
if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Démarrer le bot dans un thread asyncio
    loop.create_task(run_bot())

    # Démarrer Flask
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
