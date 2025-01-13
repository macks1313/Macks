import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

COINMARKETCAP_API = "YOUR_COINMARKETCAP_API_KEY"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"

def get_filtered_cryptos():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
    params = {"market_cap_max": 100000000, "market_cap_min": 1000000, "volume_24h_min": 500000}
    response = requests.get(url, headers=headers, params=params).json()
    filtered = []
    for crypto in response["data"]:
        # Ajoute des filtres supplémentaires si nécessaire
        filtered.append(crypto["name"])
    return filtered

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Bienvenue sur le bot Crypto ! Tapez /lowcap pour voir les cryptos à petite capitalisation.")

async def lowcap(update: Update, context: CallbackContext) -> None:
    cryptos = get_filtered_cryptos()
    if cryptos:
        await update.message.reply_text("Voici les cryptos filtrées :\n" + "\n".join(cryptos))
    else:
        await update.message.reply_text("Aucune crypto ne correspond aux critères pour le moment.")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lowcap", lowcap))

    application.run_polling()

if __name__ == "__main__":
    main()
