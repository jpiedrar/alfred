"""Persistent admin-chat configuration and addition notifications."""

import json
from pathlib import Path

from bot.utils.log import set_up_logger


logger = set_up_logger("admin_notifications")
ADMIN_CHAT_FILE = Path("data/admin_chat.json")


def save_admin_chat(chat_id):
    """Persist the Telegram chat that receives addition reports."""
    ADMIN_CHAT_FILE.write_text(
        json.dumps({"chat_id": int(chat_id)}),
        encoding="utf-8",
    )


def get_admin_chat():
    """Return the configured admin chat ID, or None when not configured."""
    try:
        data = json.loads(ADMIN_CHAT_FILE.read_text(encoding="utf-8"))
        return int(data["chat_id"])
    except FileNotFoundError:
        return None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        logger.error("Invalid admin-chat configuration: %s", error)
        return None


async def report_addition(telegram_bot, user, title, media_kind):
    """Report a completed movie or series addition to the configured chat."""
    chat_id = get_admin_chat()
    if chat_id is None:
        logger.warning("No admin chat configured; addition report was not sent")
        return

    display_name = user.full_name or user.username or str(user.id)
    try:
        await telegram_bot.send_message(
            chat_id=chat_id,
            text=f"{display_name} added {title} {media_kind}.",
        )
    except Exception as error:
        logger.error("Could not send addition report to chat [%s]: %s", chat_id, error)
