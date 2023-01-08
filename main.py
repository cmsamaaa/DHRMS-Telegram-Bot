import logging

import os
from dotenv import load_dotenv

import helpers

import bot

from telegram.ext import Application

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if load_dotenv() is False:
    logger.info(msg="Failed to load environment variables.")

# Essential Info
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')


def main() -> None:
    application = Application.builder().token(token=TELEGRAM_BOT_API_TOKEN).post_init(helpers.post_init).build()

    application.add_handler(bot.CONV_HANDLER)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
