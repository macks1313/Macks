import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

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

# États pour la commande de configuration
(SET_MARKET_CAP, SET_VOLUME, SET_VARIATION_7D, SET_VARIATION_30D) = range(4)

# Filtres par défaut
filters_config = {
    "market_cap_min": 1e6,
    "market_cap_max": 1e8,
    "volume_min": 500_000,
    "variation_7d_min": -10,
    "variation_7d_max": 10,
    "variation_30d_min": -20,
    "variation_30d_max": 20
}

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
            percent_change_7d = crypto["quote"]["USD"]["percent_change_7d"]
            percent_change_30d = crypto["quote"]["USD"].get("percent_change_30d", 0)

            if (
                filters_config["market_cap_min"] <= market_cap <= filters_config["market_cap_max"] and
                volume_24h > filters_config["volume_min"] and
                filters_config["variation_7d_min"] <= percent_change_7d <= filters_config["variation_7d_max"] and
                filters_config["variation_30d_min"] <= percent_change_30d <= filters_config["variation_30d_max"]
            ):
                filtered_cryptos.append({
                    "name": crypto["name"],
                    "symbol": crypto["symbol"],
                    "price": crypto["quote"]["USD"]["price"],
                    "market_cap": market_cap,
                    "volume_24h": volume_24h,
                    "percent_change_7d": percent_change_7d,
                    "percent_change_30d": percent_change_30d
                })

    return filtered_cryptos

# Commande /cryptos
async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    filtered_cryptos = get_filtered_cryptos()

    if filtered_cryptos:
        message = "📊 *Cryptos Filtrées :*\n\n"
        for crypto in filtered_cryptos[:10]:
            message += (
                f"🔸 *Nom* : {crypto['name']} ({crypto['symbol']})\n"
                f"💰 *Prix* : ${crypto['price']:.2f}\n"
                f"📈 *Market Cap* : ${crypto['market_cap']:.0f}\n"
                f"📊 *Volume (24h)* : ${crypto['volume_24h']:.0f}\n"
                f"📉 *Variation 7j* : {crypto['percent_change_7d']:.2f}%\n"
                f"📉 *Variation 30j* : {crypto['percent_change_30d']:.2f}%\n\n"
            )
    else:
        message = "❌ *Aucune crypto ne correspond à vos critères.*"

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Bienvenue sur le bot Crypto !*\n\n"
        "✨ *Fonctionnalités disponibles :*\n"
        "👉 Utilisez /cryptos pour voir les cryptos filtrées.\n"
        "👉 Utilisez /setfilters pour personnaliser vos filtres.\n\n"
        "⚙️ *Filtres actuels :*\n"
        f"- 📏 *Market cap* : Entre ${filters_config['market_cap_min']:,} et ${filters_config['market_cap_max']:,}\n"
        f"- 💹 *Volume quotidien* : Supérieur à ${filters_config['volume_min']:,}\n"
        f"- 📉 *Variation 7 jours* : Entre {filters_config['variation_7d_min']}% et {filters_config['variation_7d_max']}%\n"
        f"- 📉 *Variation 30 jours* : Entre {filters_config['variation_30d_min']}% et {filters_config['variation_30d_max']}%\n\n"
        "🛠️ *Commandes disponibles :*\n"
        "- /start : Démarrer le bot\n"
        "- /cryptos : Afficher les cryptos filtrées\n"
        "- /setfilters : Configurer vos filtres\n"
        "- /help : Obtenir de l'aide"
    )
# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Aide du bot Crypto :*\n\n"
        "📚 *Commandes disponibles :*\n"
        "- /start : Démarrer le bot\n"
        "- /cryptos : Afficher les cryptos filtrées\n"
        "- /setfilters : Configurer vos filtres\n"
        "- /help : Obtenir de l'aide\n\n"
        "🚀 Profitez de votre expérience crypto avec ce bot !"
    )

# Commande /setfilters
async def setfilters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ *Configuration des filtres* :\n"
        "Veuillez entrer la capitalisation minimale souhaitée (en $) :"
    )
    return SET_MARKET_CAP

async def set_market_cap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        filters_config["market_cap_min"] = float(update.message.text)
        await update.message.reply_text(
            "📏 Capitalisation minimale enregistrée.\n"
            "Veuillez entrer la capitalisation maximale souhaitée (en $) :"
        )
        return SET_VOLUME
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un nombre valide.")
        return SET_MARKET_CAP

async def set_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        filters_config["market_cap_max"] = float(update.message.text)
        await update.message.reply_text(
            "💹 Capitalisation maximale enregistrée.\n"
            "Veuillez entrer le volume quotidien minimum souhaité (en $) :"
        )
        return SET_VARIATION_7D
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un nombre valide.")
        return SET_VOLUME

async def set_variation_7d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        filters_config["volume_min"] = float(update.message.text)
        await update.message.reply_text(
            "📉 Volume quotidien minimum enregistré.\n"
            "Veuillez entrer la variation minimale sur 7 jours (en %) :"
        )
        return SET_VARIATION_30D
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un nombre valide.")
        return SET_VARIATION_7D

async def set_variation_30d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        filters_config["variation_7d_min"] = float(update.message.text)
        await update.message.reply_text(
            "📉 Variation sur 7 jours enregistrée.\n"
            "Veuillez entrer la variation minimale sur 30 jours (en %) :"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer un nombre valide.")
        return SET_VARIATION_30D

# Initialisation du bot
def main():
    logger.info("Démarrage du bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Configuration des commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cryptos", crypto_handler))
    application.add_handler(CommandHandler("help", help_command))

    # Gestion des filtres
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setfilters", setfilters)],
        states={
            SET_MARKET_CAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_market_cap)],
            SET_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_volume)],
            SET_VARIATION_7D: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_variation_7d)],
            SET_VARIATION_30D: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_variation_30d)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    # Lancer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
