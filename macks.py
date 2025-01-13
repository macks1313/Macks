import os
import sys
import requests
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
import logging
from typing import Optional

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_env_variables():
    """Vérifie que toutes les variables d'environnement requises sont présentes"""
    required_vars = {
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
        'API_KEY_LUNARCRUSH': os.getenv('API_KEY_LUNARCRUSH'),
        'WEBHOOK_URL': os.getenv('WEBHOOK_URL')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return required_vars

# Vérification des variables d'environnement au démarrage
try:
    env_vars = check_env_variables()
    TELEGRAM_TOKEN = env_vars['TELEGRAM_TOKEN']
    API_KEY_LUNARCRUSH = env_vars['API_KEY_LUNARCRUSH']
    WEBHOOK_URL = env_vars['WEBHOOK_URL']
    PORT = int(os.getenv('PORT', '8443'))
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

# Initialisation Flask
app = Flask(__name__)

# Initialisation du bot Telegram
application = Application.builder().token(TELEGRAM_TOKEN).build()

async def get_crypto_data(symbol: str) -> str:
    """Fetch cryptocurrency data from LunarCrush API"""
    try:
        url = f"https://api.lunarcrush.com/v2?data=assets&key={API_KEY_LUNARCRUSH}&symbol={symbol}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"API request failed with status {response.status}")
                    return "❌ Failed to fetch data from LunarCrush."
                    
                data = await response.json()
                if not data.get("data"):
                    return "❌ No data found for this cryptocurrency."

                asset = data["data"][0]
                return (
                    f"📈 {asset.get('name', 'N/A')} ({symbol})\n"
                    f"💰 Price: ${asset.get('price', 'N/A'):,.2f}\n"
                    f"📊 24h Change: {asset.get('percent_change_24h', 'N/A'):+.2f}%\n"
                    f"📈 7d Change: {asset.get('percent_change_7d', 'N/A'):+.2f}%\n"
                    f"💎 Market Cap: ${asset.get('market_cap', 'N/A'):,.0f}\n"
                    f"📊 Volume 24h: ${asset.get('volume_24h', 'N/A'):,.0f}"
                )
                
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        return "❌ An error occurred while fetching cryptocurrency data."

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    welcome_message = (
        "🚀 Welcome to the Crypto Bot!\n\n"
        "Available commands:\n"
        "/crypto <symbol> - Get cryptocurrency data (e.g., /crypto BTC)\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(welcome_message)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await cmd_start(update, context)

async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /crypto command"""
    if not context.args:
        await update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /crypto BTC")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text("🔍 Fetching data...")
    message = await get_crypto_data(symbol)
    await update.message.reply_text(message)

# Register command handlers
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(CommandHandler("crypto", cmd_crypto))

# Flask routes
@app.route("/")
def index():
    return "Crypto Bot is running!"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    """Handle incoming webhook updates from Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        return str(e), 500

async def setup_webhook():
    """Setup webhook for Telegram bot"""
    try:
        webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
        logger.info(f"Setting webhook to: {webhook_url}")
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook setup complete")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        raise

if __name__ == "__main__":
    # Setup webhook
    import asyncio
    try:
        asyncio.run(setup_webhook())
        
        # Start Flask server
        logger.info(f"Starting Flask server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
