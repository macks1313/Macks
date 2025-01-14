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
        [InlineKeyboardButton("Market Cap Max", callback_data="config_market_cap_max")],
        [InlineKeyboardButton("Volume 24h Min", callback_data="config_volume_24h_min")],
        [InlineKeyboardButton("Variation 24h Min", callback_data="config_percent_change_24h_min")],
        [InlineKeyboardButton("Jours Max", callback_data="config_days_since_launch_max")],
        [InlineKeyboardButton("Supply Min", callback_data="config_circulating_supply_min")],
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        f"Voici les critères actuels :\n"
        f"🔹 Market Cap Max : {FILTER_CRITERIA['market_cap_max']} $\n"
        f"🔹 Volume 24h Min : {FILTER_CRITERIA['volume_24h_min']} $\n"
        f"🔹 Variation 24h Min : {FILTER_CRITERIA['percent_change_24h_min']}%\n"
        f"🔹 Jours Max : {FILTER_CRITERIA['days_since_launch_max']}\n"
        f"🔹 Supply Min : {FILTER_CRITERIA['circulating_supply_min']} tokens\n\n"
        "Cliquez sur un critère pour le modifier.",
        reply_markup=reply_markup
    )

# Fonction pour configurer un critère sélectionné
async def set_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Récupérer le critère sélectionné
    selected_criteria = query.data.replace("config_", "")
    context.user_data["current_criteria"] = selected_criteria

    # Boutons pour ajuster la valeur et revenir au menu principal
    buttons = [
        [
            InlineKeyboardButton("➖ -10%", callback_data=f"decrease_{selected_criteria}"),
            InlineKeyboardButton("➕ +10%", callback_data=f"increase_{selected_criteria}")
        ],
        [
            InlineKeyboardButton("½ Half", callback_data=f"half_{selected_criteria}"),
            InlineKeyboardButton("x2 Double", callback_data=f"double_{selected_criteria}")
        ],
        [InlineKeyboardButton("🔙 Retour", callback_data="back_to_criteria")]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    # Envoyer un message avec les options de modification
    await query.edit_message_text(
        text=f"⚙️ *Modification du critère* : {selected_criteria.replace('_', ' ').title()}\n\n"
             f"Valeur actuelle : {FILTER_CRITERIA[selected_criteria]}\n\n"
             "Utilisez les boutons ci-dessous pour ajuster la valeur ou revenez au menu principal.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
# Fonction pour ajuster un critère en fonction des boutons cliqués
async def adjust_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Extraire l'action (increase, decrease, half, double) et le critère
    action, criteria_key = query.data.split("_", 1)

    # Ajuster la valeur
    old_value = FILTER_CRITERIA[criteria_key]
    if action == "increase":
        FILTER_CRITERIA[criteria_key] *= 1.1  # Augmente de 10%
    elif action == "decrease":
        FILTER_CRITERIA[criteria_key] *= 0.9  # Réduit de 10%
    elif action == "half":
        FILTER_CRITERIA[criteria_key] /= 2  # Divise par 2
    elif action == "double":
        FILTER_CRITERIA[criteria_key] *= 2  # Multiplie par 2

    new_value = FILTER_CRITERIA[criteria_key]

    # Réafficher les options de modification pour le critère
    await set_criteria(update, context)

    # Envoyer un message de confirmation avec les détails du changement
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ *Modification réussie !*\n"
             f"🔹 *Critère* : {criteria_key.replace('_', ' ').title()}\n"
             f"🔸 *Ancienne valeur* : {old_value:.2f}\n"
             f"🔸 *Nouvelle valeur* : {new_value:.2f}",
        parse_mode="Markdown"
    )

    # Retour au menu de modification du critère
    await set_criteria(update, context)

# Fonction pour retourner à l'écran des critères
async def back_to_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Retour au menu principal des critères
    await display_criteria(update, context)

# Fonction pour enregistrer une nouvelle valeur pour le critère
async def save_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_value = float(update.message.text)
        current_criteria = context.user_data.get("current_criteria")

        if current_criteria and current_criteria in FILTER_CRITERIA:
            old_value = FILTER_CRITERIA[current_criteria]
            FILTER_CRITERIA[current_criteria] = new_value

            # Envoi d'une notification en temps réel
            await update.message.reply_text(
                f"✅ *Critère mis à jour* : {current_criteria.replace('_', ' ').title()}\n"
                f"🔹 Ancienne valeur : {old_value}\n"
                f"🔹 Nouvelle valeur : {new_value}"
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
        "🎉 *Bienvenue sur le bot Crypto !* 🎉\n\n"
        "Voici les commandes disponibles :\n"
        "🔹 `/cryptos` : Affiche les cryptos correspondant aux filtres actuels.\n"
        "🔹 `/set_criteria` : Configurez ou modifiez les critères de sélection.\n"
        "🔹 `/help` : Obtenez des explications détaillées sur le fonctionnement du bot.\n\n"
        "🔍 *Filtres actuellement appliqués* :\n"
        f"   - Market Cap Max : {FILTER_CRITERIA['market_cap_max']} $\n"
        f"   - Volume 24h Min : {FILTER_CRITERIA['volume_24h_min']} $\n"
        f"   - Variation 24h Min : {FILTER_CRITERIA['percent_change_24h_min']}%\n"
        f"   - Jours Max : {FILTER_CRITERIA['days_since_launch_max']}\n"
        f"   - Supply Min : {FILTER_CRITERIA['circulating_supply_min']} tokens\n\n"
        "👉 *Commencez dès maintenant* :\n"
        "   - Utilisez `/cryptos` pour explorer les cryptos filtrées.\n"
        "   - Utilisez `/set_criteria` pour ajuster les filtres selon vos besoins."
    )

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Guide d'utilisation du bot Crypto* 📖\n\n"
        "1️⃣ *Afficher les cryptos filtrées* :\n"
        "   - Utilisez `/cryptos` pour afficher les cryptos correspondant aux critères actuels.\n\n"
        "2️⃣ *Configurer ou modifier les critères* :\n"
        "   - Utilisez `/set_criteria` pour afficher les critères actuels.\n"
        "   - Cliquez sur un critère pour le modifier.\n"
        "   - Ajustez les valeurs avec les boutons +10% ou -10%.\n"
        "   - Revenez au menu principal avec le bouton \"Retour\".\n\n"
        "3️⃣ *Filtres disponibles* :\n"
        "   - 🔹 *Market Cap Max* : Limite supérieure de la capitalisation boursière (ex. : 1 milliard $).\n"
        "   - 🔹 *Volume 24h Min* : Volume minimum échangé en 24h (ex. : 100 000 $).\n"
        "   - 🔹 *Variation 24h Min* : Baisse minimale tolérée en pourcentage (ex. : -5%).\n"
        "   - 🔹 *Jours Max* : Nombre maximum de jours depuis le lancement (ex. : 730 jours).\n"
        "   - 🔹 *Supply Min* : Quantité minimale de tokens en circulation (ex. : 1).\n\n"
        "4️⃣ *Commandes disponibles* :\n"
        "   - `/start` : Affiche toutes les commandes et les critères actuels.\n"
        "   - `/cryptos` : Montre les cryptos correspondant aux critères sélectionnés.\n"
        "   - `/set_criteria` : Permet de modifier facilement les filtres.\n"
        "   - `/help` : Fournit ce menu d'aide détaillé.\n\n"
        "ℹ️ *Astuce* : Ajustez vos critères régulièrement pour découvrir de nouvelles opportunités de cryptos !"
    )

# Initialisation du bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commandes principales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cryptos", crypto_handler))
    application.add_handler(CommandHandler("set_criteria", display_criteria))

    # Handlers pour les interactions avec les boutons
    application.add_handler(CallbackQueryHandler(set_criteria, pattern="^config_"))
    application.add_handler(CallbackQueryHandler(adjust_criteria, pattern="^(increase|decrease|half|double)_"))
    application.add_handler(CallbackQueryHandler(back_to_criteria, pattern="^back_to_criteria"))

    # Lancer le bot en mode polling
    application.run_polling()

if __name__ == "__main__":
    main()
