import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Récupérer les tokens depuis les variables d'environnement
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
    data = response.json()

    filtered_cryptos = []

    if response.status_code == 200 and "data" in data:
        for crypto in data["data"]:
            market_cap = crypto["quote"]["USD"]["market_cap"]
            volume_24h = crypto["quote"]["USD"]["volume_24h"]
            percent_change_7d = crypto["quote"]["USD"]["percent_change_7d"]
            percent_change_30d = crypto["quote"]["USD"].get("percent_change_30d", 0)

            if (
                1e6 <= market_cap <= 1e8 and
                volume_24h > 500_000 and
                -10 <= percent_change_7d <= 10 and
                -20 <= percent_change_30d <= 20
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
        message = "❌ Aucune crypto ne correspond à vos critères."

    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Initialisation du bot
def main():
    # Initialisation de l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter la commande /cryptos
    application.add_handler(CommandHandler("cryptos", crypto_handler))

    # Utilisation du mode polling
    application.run_polling(stop_signals=None)  # Désactiver les interruptions automatiques

if __name__ == "__main__":
    main()

