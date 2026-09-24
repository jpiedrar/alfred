"""Authenticated-user command that asks Docker to restart this container."""

import asyncio
import json
import os
import random
import signal
from pathlib import Path

from bot.utils.auth import authenticated
from bot.utils.log import set_up_logger


logger = set_up_logger("commands.reset")
RESET_NOTIFICATION_FILE = Path("data/reset_notification.json")
RESET_START_MESSAGES = (
    "Very good. Restarting Searcharr. Do try not to summon the Batcomputer while I’m away.",
    "Right away. Even the finest machinery benefits from a moment to collect itself.",
    "Of course. Searcharr is taking a brief tactical withdrawal—Master Wayne’s phrase, not mine.",
    "Restarting now. The cave will be unattended for approximately one dramatic pause.",
)
RESET_COMPLETE_MESSAGES = (
    "Searcharr is back, sir. The cave remains intact.",
    "At your service. Searcharr has returned—refreshed, discreet, and properly caffeinated.",
    "All systems restored. I took the liberty of not rebooting the Batmobile.",
    "Searcharr is operational again. Master Wayne would call that a successful contingency.",
)


async def notify_reset_complete(application):
    """Send a pending confirmation after the new bot process has started."""
    if not RESET_NOTIFICATION_FILE.exists():
        return

    try:
        pending = json.loads(RESET_NOTIFICATION_FILE.read_text(encoding="utf-8"))
        chat_id = int(pending["chat_id"])
        await application.bot.send_message(
            chat_id=chat_id,
            text=random.choice(RESET_COMPLETE_MESSAGES),
        )
        RESET_NOTIFICATION_FILE.unlink()
        logger.info("Sent reset completion message to chat [%s]", chat_id)
    except Exception as error:
        # Keep the marker so a later container start can retry the notification.
        logger.error("Could not send reset completion message: %s", error)


async def reset_command(update, context, bot):
    """Acknowledge an authenticated user, then terminate the main process."""
    user = update.effective_user

    if user is None or not authenticated(user.id):
        logger.warning(
            "Rejected reset request from Telegram user id [%s]",
            getattr(user, "id", "unknown"),
        )
        if update.effective_message is not None:
            await update.effective_message.reply_text(
                "You must be authenticated with Searcharr to use this command."
            )
        return

    logger.warning(
        "Container restart requested by Telegram user [%s] (id [%s])",
        user.username,
        user.id,
    )
    await update.effective_message.reply_text(random.choice(RESET_START_MESSAGES))

    # The data directory survives the container restart. The new process reads
    # this marker during initialization and confirms completion to this chat.
    RESET_NOTIFICATION_FILE.write_text(
        json.dumps({"chat_id": update.effective_chat.id}),
        encoding="utf-8",
    )

    # Give Telegram's HTTP request time to flush before stopping PID 1. Docker
    # will start it again when the container uses an unless-stopped/always policy.
    await asyncio.sleep(1)
    os.kill(os.getpid(), signal.SIGTERM)
