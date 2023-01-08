import logging

import constants
import helpers

import Controllers.Clinic as Clinic

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes, ConversationHandler, CallbackContext, MessageHandler, filters
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Essential Info
TELEGRAM_BOT_API_TOKEN = constants.TELEGRAM_BOT_API_TOKEN
BOT_NAME = constants.BOT_NAME
STATES = constants.States


# Sends a message with inline buttons attached.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    if query is not None:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("Find a clinic", callback_data=str(STATES.FIND_CLINICS_NEARBY))],
        [InlineKeyboardButton("Show Debugger", callback_data="data")]
    ]

    await helpers.handle_message(update, f"*Hello {update.effective_user.first_name}\!* \n\nWelcome to {BOT_NAME}\! \n\nWhat do you want to do?",
                                 InlineKeyboardMarkup(keyboard))

    return STATES.SELECTING_ACTION


# Return to /start menu
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    if query is not None:
        await query.answer()

    await start(update, context)

    return STATES.BACK_TO_PARENT


# Parses the CallbackQuery and updates the message text.
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()

    match query.data:
        case "data":
            await query.edit_message_text(text=str(query))
        case _:
            await query.edit_message_text(text=f"Selected option: {query.data}")

    return STATES.END


# Completely end conversation from within nested conversation.
async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Let us know how we can improve!")

    return STATES.END


# End Conversation
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()

    logger.info(f"User [{update.effective_user.first_name}] | Terminated the bot.")

    await context.bot.send_message(update.effective_chat.id, "Have a nice day!", None)

    return STATES.END


# Conversation Handler for [FIND CLINICS NEARBY]
# FIND_CLINICS_NEARBY_CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
#     entry_points=[CallbackQueryHandler(Account.start, pattern=f"^{STATES.FIND_CLINICS_NEARBY}$")],
#     states={
#         STATES.SELECTING_LEVEL: [
#             Clinic.LINK_ACCOUNT_CONV_HANDLER,
#             CallbackQueryHandler(back_to_start, pattern=f"^{STATES.BACK_TO_PARENT}$")
#         ]
#     },
#     fallbacks=[CommandHandler("stop", stop)],
#     map_to_parent={
#         STATES.BACK_TO_PARENT: STATES.SELECTING_ACTION,
#         STATES.END: ConversationHandler.END
#     }
# )

# Conversation Handler for [START]
CONV_HANDLER: ConversationHandler[CallbackContext] = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        STATES.SELECTING_ACTION: [
            Clinic.FIND_CLINICS_CONV_HANDLER,
            CallbackQueryHandler(button)
        ]
    },
    fallbacks=[CommandHandler("stop", stop)],
    map_to_parent={
        STATES.END: ConversationHandler.END
    }
)


def main() -> None:
    application = Application.builder().token(token=TELEGRAM_BOT_API_TOKEN).post_init(helpers.post_init).build()

    application.add_handler(CONV_HANDLER)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
