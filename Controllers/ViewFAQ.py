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
PROCESS_NAME = constants.VIEW_FAQ
STATES = constants.States

# Initialise Session Dictionaries
state_dict: dict[int, int] = {}
faq_dict: dict[str, str] = {
    "What is HappySmile?": "We are a platform that links up dental clinics and patients. Clinics can join our "
                           "platform to be exposed to customers on our platform. Patients on the other hand, "
                           "can use our platform to find a suitable clinic within their vicinity.",
    "Can I Get An MC (Medical Certificate) From You?": "Yes, most of the clinics should be able to issue MC. However, "
                                                       "MCs are only provided to cover specific procedures. Please "
                                                       "check with the clinic that you're visiting to confirm if they "
                                                       "can do so.",
    "Do You Accept CHAS Or Pioneer Generation Cards?": "Please check with the respective clinic that you will be "
                                                       "visiting. Always remember to bring the original card along "
                                                       "with you. You are entitled to a subsidy (fee reduction) "
                                                       "according to the limits set by your card type. Do note that "
                                                       "CHAS and Pioneer cards do not entitle you for free treatment.",
    "Do You Accept Walk-In Patients?": "You can check the current queue status and make an appointment on the spot "
                                       "with a few clicks. You are however, required to be a registered user on our "
                                       "platform.",
    "What Should I Bring On My First Appointment?": "Please bring your identification documents (NRIC, EP, Work Pass, "
                                                    "passport), insurance policyholder cards/policy numbers, "
                                                    "CHAS/Pioneer Generation cards (if applicable), insurance forms ("
                                                    "if required), list of medication you are currently taking and "
                                                    "the most recent copy of any previous dental x-rays. It is a good "
                                                    "idea to email your x-rays to the clinic prior to your visit.",
    "Can I Use My Medisave To Pay For My Dental Treatment?": "Yes, you may. However, Medisave only covers certain "
                                                             "surgical treatments. "
}


# Callback data
class ViewFAQState:
    START = 0
    CHOOSING = 1
    DISPLAY_ANSWER = 2
    END = 3


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
        case ViewFAQState.START:
            list_question = []
            for key in faq_dict.keys():
                list_question.append([key])
            list_question.append(["❌ Close"])
            return list_question
        case ViewFAQState.DISPLAY_ANSWER:
            return [
                [InlineKeyboardButton("⬅️Back", callback_data=str(ViewFAQState.START))]
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
    keyboard = ReplyKeyboardMarkup(await set_keyboard(ViewFAQState.START, prev_state), one_time_keyboard=True)

    await store_state(update.effective_chat.id, ViewFAQState.START)
    await helpers.handle_message(update, "Pick an option:", keyboard)

    return ViewFAQState.CHOOSING


async def display_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | [{PROCESS_NAME}] State: FAQ Answer")

    prev_state = await get_state(update.effective_chat.id)
    keyboard = await set_keyboard(ViewFAQState.DISPLAY_ANSWER, prev_state)

    answer = faq_dict.get(update.message.text)

    if answer is None:
        answer = "Sorry, I'm not sure about this. Perhaps you can try emailing the clinic?"

    answer = answer.replace('.', '\.').replace('-', '\-').replace('(', '\(').replace(')', '\)')
    await store_state(update.effective_chat.id, ViewFAQState.DISPLAY_ANSWER)
    await helpers.handle_message(update, answer, InlineKeyboardMarkup(keyboard))

    return ViewFAQState.DISPLAY_ANSWER


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"{update.effective_user.first_name} [{update.effective_user.id}] | Aborted [{PROCESS_NAME}] process.")

    await helpers.handle_message(update,
                                 "Alright, I'll see you again soon\! " +
                                 "\n\nFor more information, please visit our website at " +
                                 WEBSITE.replace('.', '\.').replace('-', '\-') + "\." +
                                 "\n\nPress start on the menu or type \/start to start the bot again\.",
                                 ReplyKeyboardRemove())

    await clear_state(update.effective_chat.id)
    return STATES.END


# Initialise a conversation handler for [VIEW FAQ]
VIEW_FAQ_CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start, pattern=f"^{STATES.VIEW_FAQ}$")
    ],
    states={
        ViewFAQState.START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        ViewFAQState.CHOOSING: [
            MessageHandler(filters.Regex('^❌ Close$') & ~filters.COMMAND, end),
            MessageHandler(filters.TEXT & ~filters.COMMAND, display_answer)
        ],
        ViewFAQState.DISPLAY_ANSWER: [
            CallbackQueryHandler(start, pattern=f"^{ViewFAQState.START}$"),
        ],
        ViewFAQState.END: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)]
    },
    fallbacks=[
        CallbackQueryHandler(start, pattern=f"^{ViewFAQState.START}$"),
        CallbackQueryHandler(end, pattern=f"^{ViewFAQState.END}$"),
        CommandHandler("stop", end)
    ],
    map_to_parent={
        STATES.END: ConversationHandler.END
    }
)
