import asyncio
import os
import threading

from flask import Flask

import userbot
from userbot import BOTLOG_CHATID, PM_LOGGER_GROUP_ID

from .Config import Config
from .core.logger import logging
from .core.session import catub
from .utils import (
    add_bot_to_logger_group,
    install_externalrepo,
    load_plugins,
    setup_bot,
    startupmessage,
    verifyLoggerGroup,
)

LOGS = logging.getLogger("CatUserbot")

LOGS.info(userbot.__copyright__)
LOGS.info(f"Licensed under the terms of the {userbot.__license__}")

cmdhr = Config.COMMAND_HAND_LER

# Flask app
app = Flask(__name__)


async def startup_process():
    await verifyLoggerGroup()
    await load_plugins("plugins")
    await load_plugins("assistant")
    LOGS.info("============================================================================")
    LOGS.info("||               Yay your userbot is officially working.!!!")
    LOGS.info(f"||   Congratulation, now type {cmdhr}alive to see message if catub is live")
    LOGS.info("||   If you need assistance, head to https://t.me/catuserbot_support")
    LOGS.info("============================================================================")
    await verifyLoggerGroup()
    await add_bot_to_logger_group(BOTLOG_CHATID)
    if PM_LOGGER_GROUP_ID != -100:
        await add_bot_to_logger_group(PM_LOGGER_GROUP_ID)
    await startupmessage()


async def externalrepo():
    string = "<b>Your external repo plugins have imported.<b>\n\n"
    if Config.EXTERNAL_REPO:
        data = await install_externalrepo(Config.EXTERNAL_REPO, Config.EXTERNAL_REPOBRANCH, "xtraplugins")
        string += f"<b>➜ Repo:  </b><a href='{data[0]}'><b>{data[1]}</b></a>\n<b>     • Imported Plugins:</b>  <code>{data[2]}</code>\n<b>     • Failed to Import:</b>  <code>{', '.join(data[3])}</code>\n\n"
    if Config.BADCAT:
        data = await install_externalrepo(Config.BADCAT_REPO, Config.BADCAT_REPOBRANCH, "badcatext")
        string += f"<b>➜ Repo:  </b><a href='{data[0]}'><b>{data[1]}</b></a>\n<b>     • Imported Plugins:</b>  <code>{data[2]}</code>\n<b>     • Failed to Import:</b>  <code>{', '.join(data[3])}</code>\n\n"
    if Config.VCMODE:
        data = await install_externalrepo(Config.VC_REPO, Config.VC_REPOBRANCH, "catvc")
        string += f"<b>➜ Repo:  </b><a href='{data[0]}'><b>{data[1]}</b></a>\n<b>     • Imported Plugins:</b>  <code>{data[2]}</code>\n<b>     • Failed to Import:</b>  <code>{', '.join(data[3])}</code>\n\n"
    if "Imported Plugins" in string:
        await catub.tgbot.send_message(BOTLOG_CHATID, string, parse_mode="html")


async def init_all():
    await setup_bot()
    await startup_process()
    await externalrepo()


def run_flask():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)


async def main():
    LOGS.info("Starting Userbot")
    await init_all()
    LOGS.info("TG Bot Startup Completed")

    # Start Flask server in background
    threading.Thread(target=run_flask, daemon=True).start()

    # Keep bot running
    await catub.run_until_disconnected()


# Python
if __name__ == "__main__":
    import sys

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        LOGS.info("Bot stopped.")
        sys.exit()
