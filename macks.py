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
COINMARKETCAP_API = os.getenv('COINMARKETCAP_API')

if not TELEGRAM_TOKEN:
    logger.error("Missing TELEGRAM_TOKEN in environment variables.")
    sys.exit(1)

if not COINMARKETCAP_API:
    logger.warning("COINMARKETCAP_API is not set. The bot cannot fetch cryptocurrency data.")

# Initialisation du bot Telegram
application = Application.builder().token(TELEGRAM_TOKEN).build()

async def get_filtered_cryptos(user_filters: dict) -> str:
    """Fetch cryptocurrencies based on user-provided filtering criteria."""
    if COINMARKETCAP_API:
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
            params = {"limit": 5000, "sort": "market_cap", "sort_dir": "asc"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"CoinMarketCap API request failed with status {response.status}, reason: {response.reason}")
                        return f"❌ CoinMarketCap API request failed with status {response.status}: {response.reason}"

                    data = await response.json()
                    results = []

                    for crypto in data.get("data", []):
                        market_cap = crypto['quote']['USD'].get('market_cap', 0)
                        volume_24h = crypto['quote']['USD'].get('volume_24h', 0)
                        percent_change_7d = crypto['quote']['USD'].get('percent_change_7d', 0)
                        percent_change_30d = crypto['quote']['USD'].get('percent_change_30d', 0)

                        # Apply user filters
                        if (
                            user_filters['min_market_cap'] <= market_cap <= user_filters['max_market_cap'] and
                            volume_24h > user_filters['min_volume'] and
                            user_filters['min_change_7d'] <= percent_change_7d <= user_filters['max_change_7d'] and
                            user_filters['min_change_30d'] <= percent_change_30d <= user_filters['max_change_30d']
                        ):
                            results.append(
                                f"📈 **Name**: {crypto['name']} \({crypto['symbol']}\)\n"
                                f"💰 **Price**: \${crypto['quote']['USD']['price']:,.2f}\n"
                                f"💎 **Market Cap**: \${market_cap:,.2f}\n"
                                f"🔄 **24h Volume**: \${volume_24h:,.2f}\n"
                                f"📉 **7d Change**: {percent_change_7d:+.2f}\%\n"
                                f"📈 **30d Change**: {percent_change_30d:+.2f}\%\n"
                                f"⏰ **Last Updated**: {crypto['last_updated']}\n"
                            )

                    if not results:
                        return "❌ No cryptocurrencies found matching the criteria."

                    explanation = (
                        "**Filtering Criteria Explanation:**\n"
                        f"1️⃣ **Market Cap**: Between \${user_filters['min_market_cap']:,} and \${user_filters['max_market_cap']:,}.\n"
                        f"2️⃣ **24h Volume**: Greater than \${user_filters['min_volume']:,}.\n"
                        f"3️⃣ **7d Change**: Between {user_filters['min_change_7d']}\% and {user_filters['max_change_7d']}\%.\n"
                        f"4️⃣ **30d Change**: Between {user_filters['min_change_30d']}\% and {user_filters['max_change_30d']}\%.\n"
                    )

                    return explanation + "\n\n**Results:**\n" + "\n---\n".join(results)
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error with CoinMarketCap: {str(e)}")
            return "❌ Connection error occurred while fetching data from CoinMarketCap."
        except Exception as e:
            logger.error(f"Unexpected error with CoinMarketCap: {str(e)}")
            return "❌ An unexpected error occurred while fetching data from CoinMarketCap."
    else:
        return "❌ CoinMarketCap API key is not configured. Cannot fetch cryptocurrency data."

async def cmd_filtered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /filtered command to fetch cryptocurrencies based on criteria."""
    logger.info("Received /filtered command")

    # Default filter values
    filters = {
        'min_market_cap': 1_000_000,
        'max_market_cap': 100_000_000,
        'min_volume': 500_000,
        'min_change_7d': -15,
        'max_change_7d': 15,
        'min_change_30d': -20,
        'max_change_30d': 20
    }

    # Parse user-provided filters
    if context.args:
        try:
            for arg in context.args:
                key, value = arg.split('=')
                if key in filters:
                    filters[key] = float(value) if 'change' in key or 'volume' in key else int(value)
        except ValueError:
            await update.message.reply_text("❌ Invalid filter format. Use key=value pairs, e.g., min_market_cap=5000000.")
            return

    await update.message.reply_text("🔍 Fetching filtered cryptocurrencies with your criteria...")
    message = await get_filtered_cryptos(filters)
    await update.message.reply_text(message, parse_mode="MarkdownV2")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    logger.info("Received /start command")
    welcome_message = (
        "🚀 Welcome to the Crypto Bot\!\n\n"
        "🌟 Available commands:\n"
        "/crypto \<symbol\> \- Get cryptocurrency data \(e\.g\., /crypto BTC\)\n"
        "/filtered \[key\=value\] \- Filter cryptocurrencies \(e\.g\., /filtered min_market_cap\=5000000 min_volume\=1000000\)\n"
        "/help \- Show this help message"
    )
    await update.message.reply_text(welcome_message, parse_mode="MarkdownV2")

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
    await update.message.reply_text(message, parse_mode="Markdown")

# Register command handlers
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(CommandHandler("crypto", cmd_crypto))
application.add_handler(CommandHandler("filtered", cmd_filtered))

if __name__ == "__main__":
    try:
        logger.info("Starting bot in polling mode...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start polling: {e}")
        sys.exit(1)
