"""Customized Radarr callbacks without movie tagging."""

from bot.callbacks.base import (
    check_path_selection,
    check_quality_selection,
    handle_cancel,
    handle_navigation,
)
from bot.utils.admin_notifications import report_addition
from bot.utils.conversation import delete_conversation, get_add_data, update_add_data
from bot.utils.log import set_up_logger
from bot.utils.text import translate
import settings


logger = set_up_logger("callbacks.radarr")
RADARR_CONFIG = {
    "add_monitored": settings.radarr_add_monitored,
    "search_on_add": settings.radarr_search_on_add,
    "min_availability": settings.radarr_min_availability,
}


async def handle_radarr_callback(update, context, bot, convo, cid, i, op, op_flags):
    """Route Radarr callback operations."""
    query = update.callback_query

    if op == "add":
        await handle_add_movie(update, context, bot, convo, cid, i, op_flags)
    elif op in ("prev", "next"):
        await handle_navigation(update, context, "movie", convo, cid, i, op)
    elif op in ("cancel", "done"):
        await handle_cancel(update, context, convo, cid, i, op)
    else:
        await query.answer()


async def handle_add_movie(update, context, bot, convo, cid, i, op_flags):
    """Collect path/quality choices and add a movie with no tags."""
    query = update.callback_query
    service = bot.radarr
    result = convo["results"][i]

    if op_flags:
        for key, value in op_flags.items():
            logger.debug(
                "Adding/Updating additional data for cid=[%s], key=[%s], value=[%s]...",
                cid,
                key,
                value,
            )
            update_add_data(cid, key, value)

    # Never present or process selectable, username, or forced movie tags.
    update_add_data(cid, "t", "")

    if not await check_path_selection(
        update, context, service, "movie", convo, cid, i
    ):
        return

    if not await check_quality_selection(
        update, context, service, "movie", convo, cid, i
    ):
        return

    logger.debug("All data is accounted for, proceeding to add movie without tags")
    try:
        added = service.add_movie(
            movie_info=result,
            monitored=RADARR_CONFIG["add_monitored"],
            search=RADARR_CONFIG["search_on_add"],
            min_avail=RADARR_CONFIG["min_availability"],
            additional_data=get_add_data(cid),
        )
    except Exception as error:
        logger.error("Error adding movie: %s", error)
        added = False

    if added:
        delete_conversation(cid)
        await query.message.reply_text(translate("added", title=result["title"]))
        await report_addition(context.bot, query.from_user, result["title"], "movie")
        await query.message.delete()
    else:
        await query.message.reply_text(translate("unknown_error_adding", kind="movie"))

    await query.answer()
