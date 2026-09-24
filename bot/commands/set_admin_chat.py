"""Admin-only command for configuring the addition-report chat."""

from bot.utils.admin_notifications import save_admin_chat
from bot.utils.auth import authenticated
from bot.utils.log import set_up_logger


logger = set_up_logger("commands.set_admin_chat")


async def set_admin_chat_command(update, context, bot):
    """Set the current chat, or a supplied chat ID, as the report destination."""
    user = update.effective_user
    message = update.effective_message

    if user is None or authenticated(user.id) != 2:
        await message.reply_text("Only a Searcharr administrator can set the admin chat.")
        return

    if context.args:
        try:
            chat_id = int(context.args[0])
        except ValueError:
            await message.reply_text("Usage: /setadminchat or /setadminchat <chat_id>")
            return
    else:
        chat_id = update.effective_chat.id

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Admin reports are now enabled in this chat. Alfred is watching the library.",
        )
    except Exception as error:
        logger.error("Could not verify admin chat [%s]: %s", chat_id, error)
        await message.reply_text(
            "I could not message that chat. Add Alfred to it first, then try again."
        )
        return

    save_admin_chat(chat_id)
    if chat_id != update.effective_chat.id:
        await message.reply_text(f"Admin reports will now be sent to chat {chat_id}.")
