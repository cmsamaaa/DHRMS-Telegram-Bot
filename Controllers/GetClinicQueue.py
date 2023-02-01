import logging
import requests

import constants
import helpers

from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CommandHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Essential Info
TELEGRAM_BOT_API_TOKEN = constants.TELEGRAM_BOT_API_TOKEN
BOT_NAME = constants.BOT_NAME
WEBSITE = constants.WEBSITE
PROCESS_NAME = constants.GET_CLINIC_QUEUE
STATES = constants.States

# Initialise Session Dictionaries
# clinic_dict: dict[int, Clinic.Clinic] = {}
state_dict: dict[int, int] = {}


# Callback data
class GetClinicQueueState:
    START = 0
    CHOOSING = 1
    LIST_RESULTS = 2
    CLINIC_DETAILS = 3
    END = 4


""" START OF SUPPORT METHODS

The following methods are sections of the code extracted for re-usability, thus avoiding code redundancy.
These methods may be transferred to another file/class in the future.
"""


# Store current state
async def store_state(chat_id: int, state: int = -1) -> None:
    state_dict[chat_id] = state


# Get state from dictionary
async def get_state(chat_id: int) -> int:
    if chat_id in state_dict:
        return state_dict[chat_id]


# Clear chat state
async def clear_state(chat_id: int) -> bool:
    if chat_id in state_dict:
        del state_dict[chat_id]
        return True
    else:
        return False


# Set keyboard
async def set_keyboard(curr_state: int, prev_state: int) -> list[list[InlineKeyboardButton]] | list[list[str]]:
    match curr_state:
        case GetClinicQueueState.START:
            return [
                ["List All Clinics"],
                ["❌ Close"]
            ]
        case GetClinicQueueState.CLINIC_DETAILS:
            return [
                # ["⬅️Back"]
                [InlineKeyboardButton("⬅️Back", callback_data=str(GetClinicQueueState.START))]
            ]


""" END OF SUPPORT METHODS """

""" START OF BOT METHODS

The following methods are sections of the code extracted for re-usability, thus avoiding code redundancy.
These methods may be transferred to another file/class in the future.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | Started [{PROCESS_NAME}] process.")
    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: Start")

    prev_state = await get_state(update.effective_chat.id)
    keyboard = ReplyKeyboardMarkup(await set_keyboard(GetClinicQueueState.START, prev_state), one_time_keyboard=True)

    await store_state(update.effective_chat.id, GetClinicQueueState.START)
    await helpers.handle_message(update, "Pick an option:", keyboard)

    return GetClinicQueueState.CHOOSING


async def list_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | Started [{PROCESS_NAME}] process.")
    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: Start")

    clinic_list = [['⬅️Back']]
    if update.message is not None:
        uri = 'https://happy-smile-dhrms.herokuapp.com/api/clinic/get/all/'
        if update.message.text != 'List All Clinics':
            uri += update.message.text

        result = requests.get(uri)
        for clinic in result.json():
            clinic_list.append([f"{clinic.get('clinicId')}. {clinic.get('clinicName')}"])

    keyboard = ReplyKeyboardMarkup(clinic_list, one_time_keyboard=True)

    await store_state(update.effective_chat.id, GetClinicQueueState.LIST_RESULTS)
    await helpers.handle_message(update, "Select a clinic to view its current queue status:", keyboard)

    return GetClinicQueueState.LIST_RESULTS


async def clinic_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: View Clinic Queue Status")

    prev_state = await get_state(update.effective_chat.id)
    keyboard = await set_keyboard(GetClinicQueueState.CLINIC_DETAILS, prev_state)

    queue_info_msg = ""
    if update.message is not None:
        uri = f"https://happy-smile-dhrms.herokuapp.com/api/queue/get/count/{update.message.text.split('.')[0]}"
        result = requests.get(uri)

        if result.status_code == 200:
            queue_dict = result.json()
            queue_info_msg = "*" + queue_dict.get('clinicName').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)') + "*"

            if queue_dict.get('count') < 5:
                queue_info_msg += f"\n\n🟢 *SHORT WAITING TIME* 🟢"
            elif queue_dict.get('count') < 10:
                queue_info_msg += f"\n\n🟡 *MODERATE WAITING TIME* 🟡"
            else:
                queue_info_msg += f"\n\n🔴 *LONG WAITING TIME* 🔴"

            queue_info_msg += f"\n\nCurrently in Queue: *{queue_dict.get('count')}*"
        else:
            uri = f"https://happy-smile-dhrms.herokuapp.com/api/clinic/get/{update.message.text.split('.')[0]}"
            result = requests.get(uri)
            clinic_dict = result.json()
            queue_info_msg = "*" + clinic_dict.get('clinicName').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)') + "*"
            queue_info_msg += f"\n\n🟢 *SHORT WAITING TIME* 🟢"
            queue_info_msg += f"\n\nCurrently in Queue: *None*"

    queue_info_msg += f"\n\n_Note: This message is generated at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\. Please go back and select the clinic again to get the latest queue status\._"

    await store_state(update.effective_chat.id, GetClinicQueueState.CLINIC_DETAILS)
    await helpers.handle_message(update, queue_info_msg, InlineKeyboardMarkup(keyboard))

    return GetClinicQueueState.CLINIC_DETAILS


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | Cancelled [{PROCESS_NAME}] process.")

    await helpers.handle_message(update,
                                 "Alright, I'll see you again soon\! " +
                                 "\n\nFor more information, please visit our website at " +
                                 WEBSITE.replace('.', '\.').replace('-', '\-') + "\." +
                                 "\n\nPress start on the menu or type \/start to start the bot again\.",
                                 ReplyKeyboardRemove())

    await clear_state(update.effective_chat.id)
    return STATES.END


# Initialise a conversation handler for [PRODUCT CREATION]
GET_CLINIC_QUEUE_CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start, pattern=f"^{STATES.GET_CLINIC_QUEUE}$")
    ],
    states={
        GetClinicQueueState.START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        GetClinicQueueState.CHOOSING: [
            MessageHandler(filters.Regex('^List All Clinics$') & ~filters.COMMAND, list_results),
            MessageHandler(filters.Regex('^❌ Close$') & ~filters.COMMAND, end)
        ],
        GetClinicQueueState.LIST_RESULTS: [
            MessageHandler(filters.Regex('^⬅️Back$') & ~filters.COMMAND, start),
            MessageHandler(filters.Regex('^[0-9]+[.][ ][ A-Za-z0-9_@.\/#&():*+-]+$') & ~filters.COMMAND, clinic_details)
        ],
        GetClinicQueueState.CLINIC_DETAILS: [
            CallbackQueryHandler(start, pattern=f"^{GetClinicQueueState.START}$"),
        ],
        GetClinicQueueState.END: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)]
    },
    fallbacks=[
        CallbackQueryHandler(start, pattern=f"^{GetClinicQueueState.START}$"),
        CallbackQueryHandler(end, pattern=f"^{GetClinicQueueState.END}$"),
        CommandHandler("stop", end)
    ],
    map_to_parent={
        STATES.END: ConversationHandler.END
    }
)
