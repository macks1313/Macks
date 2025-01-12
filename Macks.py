import os
import openai
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Memory store for user conversations
user_conversations = {}

def start(update, context):
    """Send a welcome message and basic instructions."""
    user_first_name = update.message.chat.first_name
    welcome_message = (
        f"Bonjour {user_first_name}! Pose-moi tes questions ou partage tes pensées, je suis là pour répondre."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

def help_command(update, context):
    """Provide a list of commands and their descriptions."""
    help_text = (
        "Voici quelques commandes que tu peux utiliser:\n"
        "/start - Lancer le bot\n"
        "/help - Obtenir de l'aide\n"
        "/clear - Effacer notre conversation\n"
        "Pose-moi une question ou dis-moi quelque chose, et je répondrai."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

def clear_conversation(update, context):
    """Clear the conversation memory for the user."""
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
        context.bot.send_message(chat_id=update.effective_chat.id, text="Notre conversation a été effacée.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Aucune conversation à effacer.")

def generate_response(user_id, user_message):
    """Generate a response using OpenAI's GPT model."""
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # Retrieve the conversation history for the user
        conversation_history = user_conversations.get(user_id, [])
        conversation_history.append({"role": "user", "content": user_message})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant plein de sarcasme, d'humour noir, et de blagues parfois osées. "
                        "Tu ne dépasses jamais 50 tokens par réponse et tu t'efforces de poser des questions pour engager la conversation. "
                        "Même dans ton ton sarcastique, tu cherches à motiver et inspirer subtilement."
                    )
                }
            ] + conversation_history,
            max_tokens=50  # Limiter les tokens pour des réponses courtes
        )

        # Update the conversation history with the assistant's response
        assistant_message = response.choices[0].message['content'].strip()
        conversation_history.append({"role": "assistant", "content": assistant_message})
        user_conversations[user_id] = conversation_history

        return assistant_message
    except Exception as e:
        return f"Oups, une erreur est survenue : {e}"

def handle_message(update, context):
    """Handle user messages and respond using GPT-3.5."""
    user_id = update.effective_user.id
    user_message = update.message.text
    bot_response = generate_response(user_id, user_message)
    context.bot.send_message(chat_id=update.effective_chat.id, text=bot_response)

def main():
    """Start the bot."""
    # Récupérer les tokens depuis les variables d'environnement
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    if not TOKEN:
        print("Erreur : TELEGRAM_TOKEN non défini.")
        return

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Ajouter des gestionnaires de commandes
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("clear", clear_conversation))

    # Ajouter un gestionnaire de messages pour répondre aux messages texte
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Démarrer le bot
    updater.start_polling()
    print("Bot en cours d'exécution...")
    updater.idle()

if __name__ == "__main__":
    main()
