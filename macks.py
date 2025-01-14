import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

# Fonction pour afficher les critères actuels avec des boutons simplifiés
async def display_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Modifier Market Cap Max", callback_data="market_cap_max")],
        [InlineKeyboardButton("Modifier Volume 24h Min", callback_data="volume_24h_min")],
        [InlineKeyboardButton("Modifier Variation 24h Min", callback_data="percent_change_24h_min")],
        [InlineKeyboardButton("Modifier Jours Max", callback_data="days_since_launch_max")],
        [InlineKeyboardButton("Modifier Supply Min", callback_data="circulating_supply_min")],
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        f"Voici les filtres actuels :\n"
        f"🔹 Market Cap Max : {FILTER_CRITERIA['market_cap_max']} $\n"
        f"🔹 Volume 24h Min : {FILTER_CRITERIA['volume_24h_min']} $\n"
        f"🔹 Variation 24h Min : {FILTER_CRITERIA['percent_change_24h_min']}%\n"
        f"🔹 Jours Max : {FILTER_CRITERIA['days_since_launch_max']}\n"
        f"🔹 Supply Min : {FILTER_CRITERIA['circulating_supply_min']} tokens\n\n"
        "Cliquez sur un critère ci-dessous pour le modifier :",
        reply_markup=reply_markup
    )

# Fonction pour demander une nouvelle valeur pour le critère sélectionné
async def set_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_criteria = query.data  # Récupère le critère cliqué
    context.user_data["current_criteria"] = selected_criteria

    # Envoie un message pour demander la nouvelle valeur
    await query.edit_message_text(
        text=f"Vous avez sélectionné *{selected_criteria.replace('_', ' ').title()}*.\n\n"
             "Entrez une nouvelle valeur numérique :"
    )

# Fonction pour enregistrer une nouvelle valeur pour le critère
async def save_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_value = float(update.message.text)
        current_criteria = context.user_data.get("current_criteria")

        if current_criteria and current_criteria in FILTER_CRITERIA:
            FILTER_CRITERIA[current_criteria] = new_value
            await update.message.reply_text(
                f"✅ Le critère *{current_criteria.replace('_', ' ').title()}* a été mis à jour avec succès : {new_value}."
            )
        else:
            await update.message.reply_text("❌ Aucun critère valide en cours de modification.")
    except ValueError:
        await update.message.reply_text("❌ Veuillez entrer une valeur numérique valide.")

# Commande /cryptos
async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    filtered_cryptos = get_filtered_cryptos(FILTER_CRITERIA)

    if filtered_cryptos:
        message = "📊 *Cryptos Filtrées :*\n\n"
        for crypto in filtered_cryptos[:10]:
            message += (
                f"🔸 *Nom* : {crypto['name']} ({crypto['symbol']})\n"
                f"💰 *Prix* : ${crypto['price']:.2f}\n"
                f"📈 *Market Cap* : ${crypto['market_cap']:.0f}\n"
                f"📊 *Volume (24h)* : ${crypto['volume_24h']:.0f}\n"
                f"📉 *Variation 24h* : {crypto['percent_change_24h']:.2f}%\n"
                f"📉 *Variation 7j* : {crypto['percent_change_7d']:.2f}%\n"
                f"📊 *Ratio Volume/Market Cap* : {crypto['volume_to_market_cap']:.2f}%\n"
                f"🔒 *Offre en circulation* : {crypto['circulating_supply']:.0f} tokens\n\n"
            )
    else:
        message = "❌ Aucune crypto ne correspond à vos critères pour l'instant. Continuez à chercher des pépites !"

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue sur le bot Crypto !\n\n"
        "Voici les filtres par défaut appliqués :\n"
        f"🔹 Market Cap Max : {FILTER_CRITERIA['market_cap_max']} $\n"
        f"🔹 Volume 24h Min : {FILTER_CRITERIA['volume_24h_min']} $\n"
        f"🔹 Variation 24h Min : {FILTER_CRITERIA['percent_change_24h_min']}%\n"
        f"🔹 Jours Max : {FILTER_CRITERIA['days_since_launch_max']}\n"
        f"🔹 Supply Min : {FILTER_CRITERIA['circulating_supply_min']} tokens\n\n"
        "👉 Utilisez /cryptos pour afficher les cryptos correspondant à ces critères.\n"
        "👉 Utilisez /set_criteria pour modifier vos filtres facilement."
    )

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Guide d'utilisation du bot Crypto* 📖\n\n"
        "1️⃣ *Afficher les cryptos filtrées* :\n"
        "   - Utilisez la commande `/cryptos` pour afficher les cryptos correspondant aux critères actuels.\n\n"
        "2️⃣ *Voir ou modifier les critères de filtrage* :\n"
        "   - Utilisez `/set_criteria` pour voir les critères actuels et cliquer sur celui que vous voulez modifier.\n"
        "   - Entrez une nouvelle valeur numérique lorsque le bot vous le demande.\n\n"
        "3️⃣ *Filtres par défaut appliqués* :\n"
        "   - 🔹 Market Cap Max : Limite supérieure de la capitalisation boursière (ex. : 1 milliard $).\n"
        "   - 🔹 Volume 24h Min : Volume minimum échangé en 24h (ex. : 100 000 $).\n"
        "   - 🔹 Variation 24h Min : Baisse minimale tolérée en pourcentage (ex. : -5%).\n"
        "   - 🔹 Jours Max : Nombre maximum de jours depuis le lancement (ex. : 730 jours).\n"
        "   - 🔹 Supply Min : Quantité minimale de tokens en circulation (ex. : 1).\n\n"
        "📌 *Commandes disponibles* :\n"
        "   - `/start` : Voir le message d'accueil et les commandes.\n"
        "   - `/cryptos` : Afficher les cryptos filtrées.\n"
        "   - `/set_criteria` : Modifier les critères de filtrage.\n"
        "   - `/help` : Obtenir ce menu d'aide.\n\n"
        "ℹ️ Pour toute question, contactez l'administrateur."
    )

# Initialisation du bot
def main():
    logger.info("Démarrage du bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter les commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cryptos", crypto_handler))
    application.add_handler(CallbackQueryHandler(set_criteria))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_criteria", display_criteria))
    application.add_handler(CommandHandler("save_criteria", save_criteria))

    # Lancer le bot en mode polling
    application.run_polling()

if __name__ == "__main__":
    main()
