import logging
import os
from pymongo import MongoClient

from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hello! I am your Telegram bot.')


async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /monitor command."""
    keyboard = [
        [InlineKeyboardButton("Colindale", callback_data='location_1')],
        [InlineKeyboardButton("North Acton", callback_data='location_2')],
        # Add as many locations as needed here
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Please choose a location:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # Check if the callback data is one of the locations
    if query.data.startswith('location_') and 'location' not in context.user_data:
        context.user_data['location'] = query.data.split('_')[1]
        query.edit_message_text(
            text=f"Selected location: {context.user_data['location']}")
        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'min_price_{i}') for i in range(
                1800, 2600, 100)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a minimum price:", reply_markup=reply_markup)

    elif query.data.startswith('min_price_') and 'min_price' not in context.user_data:
        context.user_data['min_price'] = int(query.data.split('_')[2])
        query.edit_message_text(
            text=f"Selected minimum price: {context.user_data['min_price']}")
        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'max_price_{i}') for i in range(
                context.user_data['min_price'], 2500, 100)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a maximum price:", reply_markup=reply_markup)

    elif query.data.startswith('max_price_') and 'max_price' not in context.user_data:
        context.user_data['max_price'] = int(query.data.split('_')[2])
        query.edit_message_text(
            text=f"Selected maximum price: {context.user_data['max_price']}")
        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(
                str(i), callback_data=f'min_beds_{i}') for i in range(1, 5)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a minimum number of beds:", reply_markup=reply_markup)

    elif query.data.startswith('min_beds_') and 'min_beds' not in context.user_data:
        context.user_data['min_beds'] = int(query.data.split('_')[2])
        query.edit_message_text(
            text=f"Selected minimum number of beds: {context.user_data['min_beds']}")
        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'max_beds_{i}') for i in range(
                context.user_data['min_beds'], 5)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a maximum number of beds:", reply_markup=reply_markup)

    elif query.data.startswith('max_beds_') and 'max_beds' not in context.user_data:
        context.user_data['max_beds'] = int(query.data.split('_')[2])
        query.edit_message_text(
            text=f"Selected maximum number of beds: {context.user_data['max_beds']}")
        # Now you have all the information needed to create a monitor in the database
        chat_id = update.effective_chat.id
        monitor = {
            'chat_id': chat_id,
            'location': context.user_data['location'],
            'min_beds': context.user_data['min_beds'],
            'max_beds': context.user_data['max_beds'],
            'min_price': context.user_data['min_price'],
            'max_price': context.user_data['max_price']
        }
        db.monitors.insert_one(monitor)
        monitor_info = f"""Monitor created successfully:
        ID: {monitor["_id"]}
        Location: {context.user_data['location']}
        Min price: {context.user_data['min_price']}
        Max price: {context.user_data['max_price']}
        Min beds: {context.user_data['min_beds']}
        Max beds: {context.user_data['max_beds']}"""
        await context.bot.send_message(chat_id=update.effective_chat.id, text=monitor_info)
        context.user_data.clear()  # Clear the data for the next operation


async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /fetch command."""
    pass


async def remove_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /removeMonitor command."""
    pass


async def list_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /listMonitor command."""
    pass


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitor", monitor))
    # Add this handler to your Application in the main function
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("fetch", fetch))
    application.add_handler(CommandHandler("removeMonitor", remove_monitor))
    application.add_handler(CommandHandler("listMonitor", list_monitor))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
