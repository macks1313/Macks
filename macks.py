import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Récupérer les tokens depuis Heroku
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COINMARKETCAP_API = os.getenv("COINMARKETCAP_API")

# URL de l'API CoinMarketCap
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

# Fonction pour filtrer les cryptos
def get_filtered_cryptos():
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
    params = {
        "start": "1",  # Commence par la première crypto
        "limit": "500",  # Analyse les 500 premières cryptos
        "convert": "USD"  # Convertir les prix en USD
    }

    response = requests.get(CMC_URL, headers=headers, params=params)
    data = response.json()

    # Liste des cryptos filtrées
    filtered_cryptos = []

    if response.status_code == 200 and "data" in data:
        for crypto in data["data"]:
            # Extraire les données nécessaires
            market_cap = crypto["quote"]["USD"]["market_cap"]
            volume_24h = crypto["quote"]["USD"]["volume_24h"]
            percent_change_7d = crypto["quote"]["USD"]["percent_change_7d"]
            percent_change_30d = crypto["quote"]["USD"].get("percent_change_30d", 0)

            # Appliquer les filtres
            if (
                1e6 <= market_cap <= 1e8 and  # Capitalisation entre 1M$ et 100M$
                volume_24h > 500_000 and  # Volume quotidien > 500k$
                -10 <= percent_change_7d <= 10 and  # Variation modérée sur 7 jours
                -20 <= percent_change_30d <= 20  # Variation modérée sur 30 jours
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

# Fonction pour gérer la commande /cryptos
def crypto_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    filtered_cryptos = get_filtered_cryptos()

    if filtered_cryptos:
        message = "📊 *Cryptos Filtrées :*\n\n"
        for crypto in filtered_cryptos[:10]:  # Limite à 10 cryptos
            message += (
                f"🔸 *Nom* : {crypto['name']} ({crypto['symbol']})\n"
                f"💰 *Prix* : ${crypto['price']:.2f}\n"
                f"📈 *Market Cap* : ${crypto['market_cap']:.0f}\n"
                f"📊 *Volume (24h)* : ${crypto['volume_24h']:.0f}\n"
                f"📉 *Variation 7j* : {crypto['percent_change_7d']:.2f}%\n"
                f"📉 *Variation 30j* : {crypto['percent_change_30d']:.2f}%\n\n"
            )
    else:
        message = "❌ Aucune crypto ne correspond à vos critères."

    context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Initialiser le bot Telegram
def main():
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Ajouter les commandes
    dispatcher.add_handler(CommandHandler("cryptos", crypto_handler))

    # Démarrer le bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
