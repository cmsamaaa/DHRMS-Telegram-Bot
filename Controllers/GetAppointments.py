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
state_dict: dict[int, int] = {}


# Callback data
class GetAppointmentsState:
    START = 0
    CHOOSING = 1
    LIST_APPOINTMENTS = 2
    APPOINTMENTS_DETAILS = 3
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
        case GetAppointmentsState.START:
            return [
                [InlineKeyboardButton("Nah, I'm good.", callback_data=str(GetAppointmentsState.END))]
            ]
        case GetAppointmentsState.APPOINTMENTS_DETAILS:
            return [
                [InlineKeyboardButton("⬅️Back", callback_data=str(GetAppointmentsState.START))]
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
    keyboard = await set_keyboard(GetAppointmentsState.START, prev_state)

    await store_state(update.effective_chat.id, GetAppointmentsState.START)
    await helpers.handle_message(update, "Enter your NRIC:", InlineKeyboardMarkup(keyboard))

    return GetAppointmentsState.CHOOSING


async def list_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: List All Upcoming Appointments")

    appt_list = []
    firstName = ""
    lastName = ""
    if update.message is not None:
        uri = f"https://happy-smile-dhrms.herokuapp.com/api/appointment/get/all/upcoming/nric/{update.message.text}"
        result = requests.get(uri)

        if result.status_code == 200:
            for appt in result.json():
                appt_list.append([f"#{appt.get('apptId')} | {appt.get('startDateTime')}"])
                firstName = appt.get('firstName')
                lastName = appt.get('lastName')


    appt_list.append(['⬅️Back'])
    keyboard = ReplyKeyboardMarkup(appt_list, one_time_keyboard=True)

    await store_state(update.effective_chat.id, GetAppointmentsState.LIST_APPOINTMENTS)

    if result.status_code == 200:
        await helpers.handle_message(update, f"Welcome back *{firstName} {lastName}*\! \n\nHere are your upcoming "
                                             f"appointments\! \n\n_Note: Appointments are displayed in the form of "
                                             f"DD/MM/YYYY HH:mm format\._ \n\nSelect an appointment to view more "
                                             f"details:",
                                     keyboard)
    else:
        await helpers.handle_message(update, f"You have no upcoming appointments\!", keyboard)

    return GetAppointmentsState.LIST_APPOINTMENTS


async def appointment_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: Appointment Details")

    prev_state = await get_state(update.effective_chat.id)
    keyboard = await set_keyboard(GetAppointmentsState.APPOINTMENTS_DETAILS, prev_state)

    appt_info_msg = "*APPOINTMENT DETAILS* 📝"
    if update.message is not None:
        uri = f"https://happy-smile-dhrms.herokuapp.com/api/appointment/get/{update.message.text.split('|')[0].strip()[1:]}"
        result = requests.get(uri)
        clinic_dict = result.json()
        appt_info_msg += f"\n\n*Date & Time:* {clinic_dict.get('startDateTime')} ⏰"
        appt_info_msg += f"\n*Status:* {clinic_dict.get('status')}"
        if clinic_dict.get('status') == 'Upcoming':
            appt_info_msg += f" 🟢"
        appt_info_msg += "\n\n🗺 *LOCATION* 📌"
        appt_info_msg += "\n*Clinic Name:* " + clinic_dict.get('clinicName').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)')
        appt_info_msg += "\n*Clinic Address:* " + clinic_dict.get('clinicAddress').replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)')
        appt_info_msg += "\n*Unit No\.:* \#" + clinic_dict.get('clinicUnit').replace('-', '\-')
        appt_info_msg += f"\n*Postal:* {clinic_dict.get('clinicPostal')}"
        appt_info_msg += "\n*Email:* " + clinic_dict.get('clinicEmail').replace('.', '\.').replace('_', '\_')
        if clinic_dict.get('clinicSubEmail') is not None:
            appt_info_msg += "\n*Secondary Email:* " + clinic_dict.get('clinicSubEmail').replace('.', '\.').replace(
                '_', '\_')
        appt_info_msg += f"\n*Phone:* \+65 {clinic_dict.get('clinicPhone')}"
        if clinic_dict.get('clinicSubEmail') is not None:
            appt_info_msg += f"\n*Secondary Phone:* \+65 {clinic_dict.get('clinicSubPhone')}"

    await store_state(update.effective_chat.id, GetAppointmentsState.APPOINTMENTS_DETAILS)
    await helpers.handle_message(update, appt_info_msg, InlineKeyboardMarkup(keyboard))

    return GetAppointmentsState.APPOINTMENTS_DETAILS


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
GET_APPOINTMENTS_CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start, pattern=f"^{STATES.GET_APPOINTMENTS}$")
    ],
    states={
        GetAppointmentsState.START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        GetAppointmentsState.CHOOSING: [
            MessageHandler(filters.Regex('^[STFG]\d{7}[A-Z]$') & ~filters.COMMAND, list_appointments)
        ],
        GetAppointmentsState.LIST_APPOINTMENTS: [
            MessageHandler(filters.Regex('^[#][0-9]+[ ][|][ ][\d]{2}[\/][\d]{2}[\/][\d]{4}[ ][\d]{2}[:][\d]{2}$') & ~filters.COMMAND, appointment_details),
            MessageHandler(filters.Regex('^⬅️Back$') & ~filters.COMMAND, start)
        ],
        GetAppointmentsState.APPOINTMENTS_DETAILS: [
            CallbackQueryHandler(start, pattern=f"^{GetAppointmentsState.START}$"),
        ],
        GetAppointmentsState.END: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)]
    },
    fallbacks=[
        CallbackQueryHandler(start, pattern=f"^{GetAppointmentsState.START}$"),
        CallbackQueryHandler(end, pattern=f"^{GetAppointmentsState.END}$"),
        CommandHandler("stop", end)
    ],
    map_to_parent={
        STATES.END: ConversationHandler.END
    }
)
