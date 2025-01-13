import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

COINMARKETCAP_API = "COINMARKETCAP_API"
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"

def get_filtered_cryptos():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
    params = {"market_cap_max": 100000000, "market_cap_min": 1000000, "volume_24h_min": 500000}
    response = requests.get(url, headers=headers, params=params).json()
    filtered = []
    for crypto in response["data"]:
        # Add more filters here (e.g., variation, audits, etc.)
        filtered.append(crypto["name"])
    return filtered

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Bienvenue sur le bot Crypto ! Tapez /lowcap pour voir les cryptos à petite capitalisation.")

def lowcap(update: Update, context: CallbackContext) -> None:
    cryptos = get_filtered_cryptos()
    if cryptos:
        update.message.reply_text("Voici les cryptos filtrées :\n" + "\n".join(cryptos))
    else:
        update.message.reply_text("Aucune crypto ne correspond aux critères pour le moment.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("lowcap", lowcap))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
