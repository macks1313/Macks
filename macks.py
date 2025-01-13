import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Config variables
COINMARKETCAP_API = "votre_clé_coinmarketcap"
TELEGRAM_TOKEN = "votre_token_telegram"

# Commande /start pour Telegram
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Bienvenue ! Utilisez /filter pour chercher des cryptos.")

# Commande /filter pour Telegram
def filter_cryptos(update: Update, context: CallbackContext) -> None:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
    params = {
        "start": 1,
        "limit": 200,
        "market_cap_min": 1000000,
        "market_cap_max": 100000000,
        "volume_24h_min": 500000,
        "sort": "market_cap",
        "sort_dir": "asc",
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    results = []

    # Filtrage supplémentaire
    for crypto in data["data"]:
        if abs(crypto["quote"]["USD"]["percent_change_7d"]) < 10:  # Variation modérée
            results.append(
                f"{crypto['name']} ({crypto['symbol']}): ${crypto['quote']['USD']['price']:.2f}"
            )

    if results:
        update.message.reply_text("\n".join(results[:10]))
    else:
        update.message.reply_text("Aucune crypto trouvée correspondant à vos critères.")

# Configurer le bot Telegram
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("filter", filter_cryptos))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
