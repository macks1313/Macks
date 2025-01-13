import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CommandHandler

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

# Définir des critères par défaut
FILTER_CRITERIA = {
    "market_cap_max": 1e9,
    "volume_24h_min": 100_000,
    "percent_change_24h_min": -5,
    "days_since_launch_max": 730,
    "circulating_supply_min": 1
}

# Fonction pour filtrer les cryptos
def get_filtered_cryptos(criteria):
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
                market_cap <= criteria.get("market_cap_max", 1e9) and
                volume_24h >= criteria.get("volume_24h_min", 100_000) and
                percent_change_24h >= criteria.get("percent_change_24h_min", -5) and
                (days_since_launch is not None and days_since_launch <= criteria.get("days_since_launch_max", 730)) and
                circulating_supply >= criteria.get("circulating_supply_min", 1)
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

# Commande pour mettre à jour les critères
async def update_criteria_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FILTER_CRITERIA
    try:
        args = context.args
        if len(args) % 2 != 0:
            await update.message.reply_text("Veuillez fournir des paires clé-valeur pour mettre à jour les critères.")
            return

        for i in range(0, len(args), 2):
            key = args[i]
            value = float(args[i + 1])
            if key in FILTER_CRITERIA:
                FILTER_CRITERIA[key] = value

        await update.message.reply_text(
            f"Critères mis à jour : {FILTER_CRITERIA}"
        )
    except Exception as e:
        await update.message.reply_text(f"Erreur lors de la mise à jour des critères : {e}")

# Commande /cryptos
async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    filtered_cryptos = get_filtered_cryptos(FILTER_CRITERIA)

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
        message = "\u274c Aucune crypto ne correspond à vos critères pour l'instant. Continuez à chercher des pépites !"

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue sur le bot Crypto !\n\n"
        "Utilisez /cryptos pour voir les cryptos filtrées.\n"
        "Utilisez /update_criteria suivi de paires clé-valeur pour modifier les critères de filtrage.\n"
        "Exemple : /update_criteria market_cap_max 500000000 volume_24h_min 200000\n\n"
        "Filtres par défaut :\n"
        "- Market cap max : 1B$\n"
        "- Volume quotidien min : 100k$\n"
        "- Variation 24h min : -5%\n"
        "- Jours depuis lancement max : 730\n"
        "- Circulating supply min : 1"
    )

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Voici les commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/cryptos - Afficher les cryptos filtrées\n"
        "/update_criteria - Mettre à jour les critères de filtrage\n"
        "/help - Obtenir de l'aide"
    )

# Initialisation du bot
def main():
    logger.info("Démarrage du bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter les commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cryptos", crypto_handler))
    application.add_handler(CommandHandler("update_criteria", update_criteria_handler))
    application.add_handler(CommandHandler("help", help_command))

    # Lancer le bot en mode polling
    application.run_polling()

if __name__ == "__main__":
    main()
