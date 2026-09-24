"""Customized Sonarr callbacks with automatic Series/Anime destinations."""

from bot.callbacks.base import (
    check_quality_selection,
    handle_cancel,
    handle_navigation,
    update_media_message,
)
from bot.utils.conversation import (
    delete_conversation,
    get_add_data,
    update_add_data,
)
from bot.utils.admin_notifications import report_addition
from bot.utils.formatting import prepare_response
from bot.utils.log import set_up_logger
from bot.utils.text import translate
import settings


logger = set_up_logger("callbacks.sonarr")
SERIES_PATH = "/tv/Series"
ANIME_PATH = "/tv/Anime"

SONARR_CONFIG = {
    "add_monitored": settings.sonarr_add_monitored,
    "search_on_add": settings.sonarr_search_on_add,
    "season_monitor_prompt": settings.sonarr_season_monitor_prompt,
}


async def handle_sonarr_callback(update, context, bot, convo, cid, i, op, op_flags):
    """Route Sonarr callback operations."""
    query = update.callback_query

    if op == "add":
        await handle_add_series(update, context, bot, convo, cid, i, op_flags)
    elif op in ("prev", "next"):
        await handle_navigation(update, context, "series", convo, cid, i, op)
    elif op in ("cancel", "done"):
        await handle_cancel(update, context, convo, cid, i, op)
    else:
        await query.answer()


async def handle_add_series(update, context, bot, convo, cid, i, op_flags):
    """Collect non-path choices and add a series to its fixed destination."""
    query = update.callback_query
    service = bot.sonarr
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

    # The normal Add action is a standard series; the existing Add as Anime
    # action supplies st=a. Never derive or accept a root path from the user.
    additional_data = get_add_data(cid)
    destination = ANIME_PATH if additional_data.get("st") == "a" else SERIES_PATH
    configured_paths = {folder["path"] for folder in service._root_folders}
    if destination not in configured_paths:
        logger.error("Required Sonarr root folder is unavailable: [%s]", destination)
        delete_conversation(cid)
        await query.message.reply_text(
            f"The configured Sonarr folder {destination} is unavailable."
        )
        await query.message.delete()
        await query.answer()
        return

    update_add_data(cid, "p", destination)
    # Explicitly submit an empty tag list. No selectable, username, or forced
    # tags are processed for series.
    update_add_data(cid, "t", "")

    if not await check_quality_selection(
        update, context, service, "series", convo, cid, i
    ):
        return

    additional_data = get_add_data(cid)
    if (
        SONARR_CONFIG["season_monitor_prompt"]
        and additional_data.get("m", False) is False
    ):
        monitor_options = [
            translate("all_seasons"),
            translate("first_season"),
            translate("latest_season"),
        ]
        reply_message, reply_markup = prepare_response(
            "series",
            result,
            cid,
            i,
            len(convo["results"]),
            add=True,
            monitor_options=monitor_options,
        )
        await update_media_message(
            query.message,
            result["remotePoster"],
            caption=reply_message,
            reply_markup=reply_markup,
        )
        await query.answer()
        return

    logger.debug("All data is accounted for, proceeding to add to [%s]", destination)
    try:
        added = service.add_series(
            series_info=result,
            monitored=SONARR_CONFIG["add_monitored"],
            search=SONARR_CONFIG["search_on_add"],
            additional_data=get_add_data(cid),
        )
    except Exception as error:
        logger.error("Error adding series: %s", error)
        added = False

    if added:
        delete_conversation(cid)
        await query.message.reply_text(translate("added", title=result["title"]))
        await report_addition(context.bot, query.from_user, result["title"], "series")
        await query.message.delete()
    else:
        await query.message.reply_text(translate("unknown_error_adding", kind="series"))

    await query.answer()
