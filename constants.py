from typing import Union

import os
from dotenv import load_dotenv

import logging
import pytz
from telegram.ext import ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if load_dotenv() is False:
    logger.info(msg="Failed to load environment variables.")

# Bot Info
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
BOT_NAME: str = "HappySmile Assistant Bot"
WEBSITE: str = "https://happy-smile-dhrms.herokuapp.com/"
TIMEZONE: pytz = pytz.timezone('Asia/Singapore')

# Process Names
GET_APPOINTMENTS: str = "GET APPOINTMENTS"
FIND_CLINICS_NEARBY: str = "FIND CLINICS NEARBY"
GET_CLINIC_QUEUE: str = "GET CLINIC QUEUE"
VIEW_FAQ: str = "VIEW FAQ"

# Custom Datatypes
REPLY_MARKUP = Union[
    "InlineKeyboardMarkup", "ReplyKeyboardMarkup", "ReplyKeyboardRemove", "ForceReply"
]


class States:
    # State definitions for top level conversation
    SELECTING_ACTION, GET_APPOINTMENTS, FIND_CLINICS_NEARBY, GET_CLINIC_QUEUE, VIEW_FAQ, CREATE_PRODUCT = range(6)
    # State definitions for second level conversation
    # SELECTING_LEVEL, SELECTING_GENDER = range(3, 5)
    # State definitions for descriptions conversation
    # LINK_ACCOUNT, TYPING = range(5, 7)
    # Meta states
    BACK_TO_PARENT, SHOWING = range(7, 9)
    # Shortcut for ConversationHandler.END
    END = ConversationHandler.END
