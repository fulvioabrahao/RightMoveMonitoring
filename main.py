import logging
import os
from pymongo import MongoClient

from bson import ObjectId
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler
import random
import string


# Setup MongoDB
MONGO_HOST = os.getenv('MONGO_HOST')
client = MongoClient(MONGO_HOST)
db = client.rightmove

# global state machine
local_state_machine = {}

# enum for state machine


class StateMachine:
    START = 0
    LOCATION = 1
    MIN_PRICE = 2
    MAX_PRICE = 3
    MIN_BEDS = 4
    MAX_BEDS = 5
    CONFIRM = 6
    DONE = 7


def get_random_string(length=10):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


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

    # Todo, fetch the options from the database and put location_{location_id}_{sm_id} as the callback data

    sm_id = get_random_string()
    keyboard = [
        [InlineKeyboardButton(
            "Colindale", callback_data=f'location_1_{sm_id}')],
        [InlineKeyboardButton(
            "North Acton", callback_data=f'location_2_{sm_id}')],
        # Add as many locations as needed here
    ]

    # update state machine
    local_state_machine[sm_id] = StateMachine.LOCATION

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Please choose a location:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # Check if the callback data is one of the locations
    if query.data.startswith('location_'):

        (_, context.user_data['location'],
         sm_id) = query.data.split('_')

        # deny if wrong state
        if sm_id not in local_state_machine or local_state_machine[sm_id] != StateMachine.LOCATION:
            # send a message to user saying this question was already answered
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You already answered this question")
            return

        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'min_price_{i}_{sm_id}') for i in range(
                1800, 2601, 100)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # update state machine
        local_state_machine[sm_id] = StateMachine.MIN_PRICE

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a minimum price:", reply_markup=reply_markup)

    elif query.data.startswith('min_price_'):
        # context.user_data['min_price'] = int(query.data.split('_')[2])
        (_, _, min_price, sm_id) = query.data.split('_')
        context.user_data['min_price'] = int(min_price)

        # deny if wrong state
        if sm_id not in local_state_machine or local_state_machine[sm_id] != StateMachine.MIN_PRICE:
            # send a message to user saying this question was already answered
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You already answered this question")
            return

        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'max_price_{i}_{sm_id}') for i in range(
                context.user_data['min_price'], 2500, 100)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # update state machine
        local_state_machine[sm_id] = StateMachine.MAX_PRICE

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a maximum price:", reply_markup=reply_markup)

    elif query.data.startswith('max_price_'):
        (_, _, max_price, sm_id) = query.data.split('_')
        context.user_data['max_price'] = int(max_price)

        # deny if wrong state
        if sm_id not in local_state_machine or local_state_machine[sm_id] != StateMachine.MAX_PRICE:
            # send a message to user saying this question was already answered
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You already answered this question")
            return

        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(
                str(i), callback_data=f'min_beds_{i}_{sm_id}') for i in range(1, 5)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # update state machine
        local_state_machine[sm_id] = StateMachine.MIN_BEDS

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a minimum number of beds:", reply_markup=reply_markup)

    elif query.data.startswith('min_beds_'):

        (_, _, min_beds, sm_id) = query.data.split('_')
        context.user_data['min_beds'] = int(min_beds)

        # deny if wrong state
        if sm_id not in local_state_machine or local_state_machine[sm_id] != StateMachine.MIN_BEDS:
            # send a message to user saying this question was already answered
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You already answered this question")
            return

        # Now move on to the next question
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f'max_beds_{i}_{sm_id}') for i in range(
                context.user_data['min_beds'], 5)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # update state machine
        local_state_machine[sm_id] = StateMachine.MAX_BEDS

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a maximum number of beds:", reply_markup=reply_markup)

    elif query.data.startswith('max_beds_'):
        (_, _, max_beds, sm_id) = query.data.split('_')
        context.user_data['max_beds'] = int(max_beds)

        # deny if wrong state
        if sm_id not in local_state_machine or local_state_machine[sm_id] != StateMachine.MAX_BEDS:
            # send a message to user saying this question was already answered
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You already answered this question")
            return

        # update state machine
        local_state_machine[sm_id] = StateMachine.DONE

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
    elif query.data.startswith('remove_'):
        monitor_id = ObjectId(query.data.split('_')[1])
        db.monitors.delete_one({'_id': monitor_id})
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Monitor {monitor_id} removed.")


async def remove_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /removeMonitor command."""
    chat_id = update.effective_chat.id
    monitors = db.monitors.find({'chat_id': chat_id})
    keyboard = [[InlineKeyboardButton(
        f"Remove Monitor {monitor['_id']}", callback_data=f'remove_{str(monitor["_id"])}')] for monitor in monitors]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a monitor to remove:", reply_markup=reply_markup)


async def list_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /listMonitor command."""
    chat_id = update.effective_chat.id
    monitors = db.monitors.find({'chat_id': chat_id})

    for monitor in monitors:
        monitor_info = f"""Monitor ID: {monitor["_id"]}
        Location: {monitor['location']}
        Min price: {monitor['min_price']}
        Max price: {monitor['max_price']}
        Min beds: {monitor['min_beds']}
        Max beds: {monitor['max_beds']}"""
        await context.bot.send_message(chat_id=update.effective_chat.id, text=monitor_info)


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitor", monitor))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("removeMonitor", remove_monitor))
    application.add_handler(CommandHandler("listMonitor", list_monitor))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
