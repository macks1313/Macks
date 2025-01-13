import os
import requests
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
import asyncio
import logging
from typing import Optional

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CryptoBot:
    def __init__(self):
        # Configuration Heroku
        self.PORT = int(os.getenv('PORT', '8443'))
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL')
        if not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL environment variable is not set")

        # Configuration Telegram et LunarCrush
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN environment variable is not set")
            
        self.API_KEY_LUNARCRUSH = os.getenv("API_KEY_LUNARCRUSH")
        if not self.API_KEY_LUNARCRUSH:
            raise ValueError("API_KEY_LUNARCRUSH environment variable is not set")
            
        # Initialisation Flask
        self.app = Flask(__name__)
        self.application = None
        self.setup_routes()

    def setup_routes(self):
        """Configure Flask routes"""
        @self.app.route("/")
        def index():
            return "Crypto Bot is running!"

        @self.app.route("/webhook", methods=["POST"])
        async def webhook():
            if request.method == "POST":
                await self.process_update(request.get_json(force=True))
                return jsonify({"status": "ok"})
            return jsonify({"status": "error", "message": "Method not allowed"}), 405

    async def process_update(self, update_json):
        """Process incoming update from Telegram"""
        if self.application:
            async with self.application:
                update = Update.de_json(update_json, self.application.bot)
                await self.application.process_update(update)

    async def get_crypto_data(self, symbol: str) -> str:
        """
        Fetch cryptocurrency data from LunarCrush API
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            
        Returns:
            Formatted string with cryptocurrency information
        """
        try:
            url = f"https://api.lunarcrush.com/v2?data=assets&key={self.API_KEY_LUNARCRUSH}&symbol={symbol}"
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

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "🚀 Welcome to the Crypto Bot!\n\n"
            "Available commands:\n"
            "/crypto <symbol> - Get cryptocurrency data (e.g., /crypto BTC)\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(welcome_message)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        await self.cmd_start(update, context)

    async def cmd_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /crypto command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /crypto BTC")
            return

        symbol = context.args[0].upper()
        await update.message.reply_text("🔍 Fetching data...")
        message = await self.get_crypto_data(symbol)
        await update.message.reply_text(message)

    async def setup_webhook(self):
        """Set up webhook for Telegram bot"""
        webhook_url = f"{self.WEBHOOK_URL}/webhook"
        logger.info(f"Setting webhook to URL: {webhook_url}")
        await self.application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set successfully")

    async def init_bot(self):
        """Initialize the Telegram bot"""
        try:
            self.application = Application.builder().token(self.TELEGRAM_TOKEN).build()
            
            # Register command handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("crypto", self.cmd_crypto))
            
            # Set up webhook
            await self.setup_webhook()
            
            logger.info("Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise

    def run(self):
        """Main entry point to run the application"""
        logger.info("Starting application...")
        
        # Initialize bot in the background
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init_bot())
        
        # Start Flask server
        logger.info(f"Starting Flask server on port {self.PORT}")
        self.app.run(host="0.0.0.0", port=self.PORT)

if __name__ == "__main__":
    bot = CryptoBot()
    bot.run()
