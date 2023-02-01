import logging
import requests

import constants
import helpers

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
PROCESS_NAME = constants.FIND_CLINICS_NEARBY
STATES = constants.States

# Initialise Session Dictionaries
# clinic_dict: dict[int, Clinic.Clinic] = {}
state_dict: dict[int, int] = {}


# Callback data
class FindClinicsNearbyState:
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
        case FindClinicsNearbyState.START:
            return [
                ["List All Clinics"],
                ["❌ Close"]
            ]
        case FindClinicsNearbyState.CLINIC_DETAILS:
            return [
                # ["⬅️Back"]
                [InlineKeyboardButton("⬅️Back", callback_data=str(FindClinicsNearbyState.START))]
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
    keyboard = ReplyKeyboardMarkup(await set_keyboard(FindClinicsNearbyState.START, prev_state), one_time_keyboard=True)

    await store_state(update.effective_chat.id, FindClinicsNearbyState.START)
    await helpers.handle_message(update, "Enter your postal code: \n\n*OR* \n\nPick an option:", keyboard)

    return FindClinicsNearbyState.CHOOSING


async def list_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: List Results")

    clinic_list = [['⬅️Back']]
    if update.message is not None:
        uri = 'https://happy-smile-dhrms.herokuapp.com/api/clinic/get/all/'
        if update.message.text != 'List All Clinics':
            uri += update.message.text

        result = requests.get(uri)
        for clinic in result.json():
            clinic_list.append([f"{clinic.get('clinicId')}. {clinic.get('clinicName')}"])

    keyboard = ReplyKeyboardMarkup(clinic_list, one_time_keyboard=True)

    await store_state(update.effective_chat.id, FindClinicsNearbyState.LIST_RESULTS)
    await helpers.handle_message(update, "Here are the results\! \n\nSelect a clinic to view more details:", keyboard)

    return FindClinicsNearbyState.LIST_RESULTS


async def clinic_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: Clinic Details")

    prev_state = await get_state(update.effective_chat.id)
    keyboard = await set_keyboard(FindClinicsNearbyState.CLINIC_DETAILS, prev_state)

    clinic_info_msg = ""
    if update.message is not None:
        uri = f"https://happy-smile-dhrms.herokuapp.com/api/clinic/get/{update.message.text.split('.')[0]}"
        result = requests.get(uri)
        clinic_dict = result.json()
        clinic_info_msg = "*" + clinic_dict.get('clinicName').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)') + "*"
        clinic_info_msg += f"\n\n*Clinic ID:* {clinic_dict.get('clinicId')}"
        clinic_info_msg += "\n*Clinic Address:* " + clinic_dict.get('clinicAddress').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)')
        clinic_info_msg += "\n*Unit No\.:* \#" + clinic_dict.get('clinicUnit').replace('-', '\-')
        clinic_info_msg += f"\n*Postal:* {clinic_dict.get('clinicPostal')}"
        clinic_info_msg += "\n*Email:* " + clinic_dict.get('clinicEmail').replace('.', '\.').replace('_', '\_')
        if clinic_dict.get('clinicSubEmail') is not None:
            clinic_info_msg += "\n*Secondary Email:* " + clinic_dict.get('clinicSubEmail').replace('.', '\.').replace(
                '_', '\_')
        else:
            clinic_info_msg += "\n*Secondary Email:* N/A"
        clinic_info_msg += f"\n*Phone:* \+65 {clinic_dict.get('clinicPhone')}"
        if clinic_dict.get('clinicSubEmail') is not None:
            clinic_info_msg += f"\n*Secondary Phone:* \+65 {clinic_dict.get('clinicSubPhone')}"
        else:
            clinic_info_msg += "\n*Secondary Phone:* N/A"

    await store_state(update.effective_chat.id, FindClinicsNearbyState.CLINIC_DETAILS)
    await helpers.handle_message(update, clinic_info_msg, InlineKeyboardMarkup(keyboard))

    return FindClinicsNearbyState.CLINIC_DETAILS


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
FIND_CLINICS_CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start, pattern=f"^{STATES.FIND_CLINICS_NEARBY}$")
    ],
    states={
        FindClinicsNearbyState.START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        FindClinicsNearbyState.CHOOSING: [
            MessageHandler(filters.Regex('^[0-9]{6}$') & ~filters.COMMAND, list_results),
            MessageHandler(filters.Regex('^List All Clinics$') & ~filters.COMMAND, list_results),
            MessageHandler(filters.Regex('^❌ Close$') & ~filters.COMMAND, end)
        ],
        FindClinicsNearbyState.LIST_RESULTS: [
            MessageHandler(filters.Regex('^⬅️Back$') & ~filters.COMMAND, start),
            MessageHandler(filters.Regex('^[0-9]+[.][ ][ A-Za-z0-9_@.\/#&():*+-]+$') & ~filters.COMMAND, clinic_details)
        ],
        FindClinicsNearbyState.CLINIC_DETAILS: [
            CallbackQueryHandler(start, pattern=f"^{FindClinicsNearbyState.START}$"),
        ],
        FindClinicsNearbyState.END: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)]
    },
    fallbacks=[
        CallbackQueryHandler(start, pattern=f"^{FindClinicsNearbyState.START}$"),
        CallbackQueryHandler(end, pattern=f"^{FindClinicsNearbyState.END}$"),
        CommandHandler("stop", end)
    ],
    map_to_parent={
        STATES.END: ConversationHandler.END
    }
)
