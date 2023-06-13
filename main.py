from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
import os
from pymongo import MongoClient

# Setup MongoDB
MONGO_HOST = os.getenv('MONGO_HOST')
client = MongoClient(MONGO_HOST)
db = client.rightmove


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Get the bot token from an environment variable
TOKEN = os.getenv('TELEGRAM_TOKEN')


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! I am your Telegram bot.')


def monitor(update: Update, context: CallbackContext) -> None:
    """Handles the /monitor command."""
    chat_id = update.effective_chat.id
    try:
        location, min_beds, max_beds, min_price, max_price = context.args
        min_beds, max_beds, min_price, max_price = map(
            int, [min_beds, max_beds, min_price, max_price])

        monitor = {
            'chat_id': chat_id,
            'location': location,
            'min_beds': min_beds,
            'max_beds': max_beds,
            'min_price': min_price,
            'max_price': max_price
        }

        db.monitors.insert_one(monitor)

        update.message.reply_text(
            f'Monitor created successfully. ID: {monitor["_id"]}')
    except (IndexError, ValueError):
        logger.error('Error creating monitor: {}'.format(context.args))
        update.message.reply_text(
            'Usage: /monitor <location> <min beds> <max beds> <min price> <max price>')


def fetch(update: Update, context: CallbackContext) -> None:
    """Handles the /fetch command."""
    pass


def remove_monitor(update: Update, context: CallbackContext) -> None:
    """Handles the /removeMonitor command."""
    pass


def list_monitor(update: Update, context: CallbackContext) -> None:
    """Handles the /listMonitor command."""
    pass


def main():
    """Start the bot."""
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("monitor", monitor))
    dp.add_handler(CommandHandler("fetch", fetch))
    dp.add_handler(CommandHandler("removeMonitor", remove_monitor))
    dp.add_handler(CommandHandler("listMonitor", list_monitor))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
