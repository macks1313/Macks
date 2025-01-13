import os
import sys
import requests
import aiohttp
import socket
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

if not TELEGRAM_TOKEN:
    logger.error("Missing TELEGRAM_TOKEN in environment variables.")
    sys.exit(1)

if not API_KEY_LUNARCRUSH:
    logger.warning("API_KEY_LUNARCRUSH is not set. The bot cannot fetch cryptocurrency data.")

# Résolution DNS pour l'API LunarCrush
try:
    host_ip = socket.gethostbyname('api.lunarcrush.com')
    logger.info(f"LunarCrush resolved IP: {host_ip}")
except Exception as e:
    logger.error(f"Failed to resolve LunarCrush: {str(e)}")

# Initialisation du bot Telegram
application = Application.builder().token(TELEGRAM_TOKEN).build()

async def get_crypto_data(symbol: str) -> str:
    """Fetch cryptocurrency data from LunarCrush API."""
    if API_KEY_LUNARCRUSH:
        try:
            url = f"https://api.lunarcrush.com/v2?data=assets&key={API_KEY_LUNARCRUSH}&symbol={symbol}"
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"LunarCrush API request failed with status {response.status}, reason: {response.reason}")
                        return f"❌ LunarCrush API request failed with status {response.status}: {response.reason}"
                    
                    data = await response.json()
                    if not data.get("data"):
                        return "❌ No data found for this cryptocurrency on LunarCrush."

                    asset = data["data"][0]
                    return (
                        f"📈 {asset.get('name', 'N/A')} ({symbol})\n"
                        f"💰 Price: ${asset.get('price', 'N/A'):,.2f}\n"
                        f"📊 24h Change: {asset.get('percent_change_24h', 'N/A'):+.2f}%\n"
                        f"📈 7d Change: {asset.get('percent_change_7d', 'N/A'):+.2f}%\n"
                        f"💎 Market Cap: ${asset.get('market_cap', 'N/A'):,.0f}\n"
                        f"📊 Volume 24h: ${asset.get('volume_24h', 'N/A'):,.0f}"
                    )
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error with LunarCrush: {str(e)}")
            return "❌ Connection error occurred while fetching data from LunarCrush."
        except Exception as e:
            logger.error(f"Unexpected error with LunarCrush: {str(e)}")
            return "❌ An unexpected error occurred while fetching data from LunarCrush."
    else:
        return "❌ LunarCrush API key is not configured. Cannot fetch cryptocurrency data."

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
