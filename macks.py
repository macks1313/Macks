# Partie A : Configuration initiale du bot et gestion des commandes de base (150 lignes)

from telegram import Update, Bot, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configuration initiale
DEFAULT_FILTERS = {
    "market_cap_max": 1000000000,  # 1 milliard
    "volume_24h_min": 100000,     # 100k
    "variation_24h_min": -5,      # -5%
    "jours_depuis_lancement_max": 730,
    "circulating_supply_min": 1,
}

current_filters = DEFAULT_FILTERS.copy()

# Fonction pour démarrer le bot et afficher les filtres actuels
def start(update: Update, context: CallbackContext):
    message = (
        "Bienvenue sur le bot Crypto !\n"
        "Utilisez les commandes suivantes pour interagir avec le bot :\n"
        "/cryptos - Afficher les cryptos filtrées\n"
        "/filters - Voir les filtres actuels\n"
        "/update_criteria <clé> <valeur> - Modifier un filtre spécifique\n"
        "/reset_filters - Réinitialiser les filtres par défaut\n"
    )
    update.message.reply_text(message)

# Fonction pour afficher les filtres actuels
def filters(update: Update, context: CallbackContext):
    message = "Filtres actuels :\n"
    for key, value in current_filters.items():
        message += f"- {key.replace('_', ' ').capitalize()} : {value}\n"
    update.message.reply_text(message)

# Fonction pour mettre à jour les filtres
def update_criteria(update: Update, context: CallbackContext):
    args = context.args

    if len(args) < 2:
        update.message.reply_text(
            "Erreur : Veuillez fournir une clé et une valeur. Exemple : /update_criteria market_cap_max 500000000"
        )
        return

    key, value = args[0], args[1]

    if key not in current_filters:
        update.message.reply_text(f"Erreur : La clé '{key}' n'est pas valide.")
        return

    try:
        # Convertir la valeur en entier ou float selon le besoin
        if isinstance(current_filters[key], int):
            value = int(value)
        elif isinstance(current_filters[key], float):
            value = float(value)
    except ValueError:
        update.message.reply_text("Erreur : La valeur doit être un nombre valide.")
        return

    # Mettre à jour le filtre
    current_filters[key] = value
    update.message.reply_text(f"Le filtre '{key}' a été mis à jour à : {value}")

# Fonction pour réinitialiser les filtres par défaut
def reset_filters(update: Update, context: CallbackContext):
    global current_filters
    current_filters = DEFAULT_FILTERS.copy()
    update.message.reply_text("Les filtres ont été réinitialisés aux valeurs par défaut.")

# Fonction simulée pour afficher les cryptos filtrées (sera implémentée en Partie B)
def cryptos(update: Update, context: CallbackContext):
    update.message.reply_text("Affichage des cryptos filtrées... (à implémenter en Partie B)")

# Configuration du bot et des commandes
def main():
    updater = Updater("YOUR_BOT_TOKEN_HERE", use_context=True)
    dp = updater.dispatcher

    # Ajout des handlers de commandes
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("filters", filters))
    dp.add_handler(CommandHandler("update_criteria", update_criteria))
    dp.add_handler(CommandHandler("reset_filters", reset_filters))
    dp.add_handler(CommandHandler("cryptos", cryptos))

    # Lancer le bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
