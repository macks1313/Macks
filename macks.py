import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurer les logs
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Récupérer les tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COINMARKETCAP_API = os.getenv("COINMARKETCAP_API")

# URL de l'API CoinMarketCap
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

# Fonction pour filtrer les cryptos
def get_filtered_cryptos():
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
    params = {
        "start": "1",
        "limit": "500",
        "convert": "USD"
    }

    response = requests.get(CMC_URL, headers=headers, params=params)
    if response.status_code != 200:
        logger.error(f"Erreur API CoinMarketCap: {response.status_code}, {response.text}")
        return []

    data = response.json()

    filtered_cryptos = []

    if "data" in data:
        for crypto in data["data"]:
            market_cap = crypto["quote"]["USD"]["market_cap"]
            volume_24h = crypto["quote"]["USD"]["volume_24h"]
            percent_change_24h = crypto["quote"]["USD"]["percent_change_24h"]
            percent_change_7d = crypto["quote"]["USD"]["percent_change_7d"]
            volume_to_market_cap = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
            circulating_supply = crypto.get("circulating_supply", 0)
            date_added = crypto.get("date_added", "")

            # Calculer la durée depuis le lancement
            from datetime import datetime
            days_since_launch = (datetime.utcnow() - datetime.fromisoformat(date_added.replace("Z", ""))).days if date_added else None

            if (
                0 <= market_cap <= 1e8 and
                volume_24h > 500_000 and
                5 <= percent_change_24h <= 30 and
                10 <= percent_change_7d <= 100 and
                volume_to_market_cap > 10 and
                (days_since_launch is not None and days_since_launch < 300) and
                circulating_supply < 1e8
            ):
                filtered_cryptos.append({
                    "name": crypto["name"],
                    "symbol": crypto["symbol"],
                    "price": crypto["quote"]["USD"]["price"],
                    "market_cap": market_cap,
                    "volume_24h": volume_24h,
                    "percent_change_24h": percent_change_24h,
                    "percent_change_7d": percent_change_7d,
                    "volume_to_market_cap": volume_to_market_cap,
                    "circulating_supply": circulating_supply
                })

    return filtered_cryptos

# Commande /cryptos
async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    filtered_cryptos = get_filtered_cryptos()

    if filtered_cryptos:
        message = "\ud83d\udcca *Cryptos Filtrées :*\n\n"
        for crypto in filtered_cryptos[:10]:
            message += (
                f"\ud83d\udd38 *Nom* : {crypto['name']} ({crypto['symbol']})\n"
                f"\ud83d\udcb0 *Prix* : ${crypto['price']:.2f}\n"
                f"\ud83d\udcc8 *Market Cap* : ${crypto['market_cap']:.0f}\n"
                f"\ud83d\udcca *Volume (24h)* : ${crypto['volume_24h']:.0f}\n"
                f"\ud83d\udd3b *Variation 24h* : {crypto['percent_change_24h']:.2f}%\n"
                f"\ud83d\udd3b *Variation 7j* : {crypto['percent_change_7d']:.2f}%\n"
                f"\ud83d\udcc9 *Ratio Volume/Market Cap* : {crypto['volume_to_market_cap']:.2f}%\n"
                f"\ud83d\udd12 *Offre en circulation* : {crypto['circulating_supply']:.0f} tokens\n\n"
            )
    else:
        message = "\u274c Aucune crypto ne correspond à vos critères."

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue sur le bot Crypto !\n\n"
        "Utilisez /cryptos pour voir les cryptos filtrées.\n"
        "Filtres appliqués :\n"
        "- Market cap entre 0 et 100M$\n"
        "- Volume quotidien supérieur à 500k$\n"
        "- Variation 24h entre 5% et 30%\n"
        "- Variation 7j entre 10% et 100%\n"
        "- Ratio Volume/Market Cap > 10%\n"
        "- Lancement récent (< 300 jours)\n"
        "- Offre en circulation < 100M tokens"
    )

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Voici les commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/cryptos - Afficher les cryptos filtrées\n"
        "/help - Obtenir de l'aide"
    )

# Initialisation du bot
def main():
    logger.info("Démarrage du bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter les commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cryptos", crypto_handler))
    application.add_handler(CommandHandler("help", help_command))

    # Lancer le bot en mode polling
    application.run_polling()

if __name__ == "__main__":
    main()
