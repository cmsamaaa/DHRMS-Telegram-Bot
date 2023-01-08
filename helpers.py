import telegram
from telegram import (
    BotCommand,
    Message,
    Update
)
from telegram.ext import Application

import constants

REPLY_MARKUP = constants.REPLY_MARKUP


# Custom startup logic that requires to await coroutines
async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand(command="start", description="Start talking to the bot."),
        BotCommand(command="stop", description="Terminates interactions with the bot."),
        # BotCommand(command="hello", description="Bot will greet you."),
        # BotCommand(command="help", description="Did you say you need help?")
    ]
    await application.bot.set_my_commands(bot_commands)


# To handle messages between CallbackQueryHandler and MessageHandler methods
async def handle_message(update: Update = None, text: str = None, reply_markup: REPLY_MARKUP | None = None) -> Message:
    query = update.callback_query

    if query is not None:
        await query.answer()
        await query.delete_message()
        return await update.effective_chat.send_message(text, telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=reply_markup)
    else:
        return await update.message.reply_text(text, telegram.constants.ParseMode.MARKDOWN_V2, reply_markup=reply_markup)
