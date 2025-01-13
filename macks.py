import os
import sys
import requests
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Vérification des variables d'environnement
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY_LUNARCRUSH = os.getenv('API_KEY_LUNARCRUSH')

if not TELEGRAM_TOKEN or not API_KEY_LUNARCRUSH:
    logger.error("Missing TELEGRAM_TOKEN or API_KEY_LUNARCRUSH in environment variables.")
    sys.exit(1)

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
    logger.info("Received /start command")
    welcome_message = (
        "🚀 Welcome to the Crypto Bot!\n\n"
        "Available commands:\n"
        "/crypto <symbol> - Get cryptocurrency data (e.g., /crypto BTC)\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(welcome_message)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    logger.info("Received /help command")
    await cmd_start(update, context)

async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /crypto command"""
    logger.info(f"Received /crypto command with args: {context.args}")
    if not context.args:
        await update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /crypto BTC")
        return

    symbol = context.args[0].upper()
    logger.info(f"Fetching data for symbol: {symbol}")
    await update.message.reply_text("🔍 Fetching data...")
    message = await get_crypto_data(symbol)
    await update.message.reply_text(message)

# Register command handlers
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(CommandHandler("crypto", cmd_crypto))

if __name__ == "__main__":
    try:
        logger.info("Starting bot in polling mode...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start polling: {e}")
        sys.exit(1)
