from threading import Thread
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup
from time import sleep
from re import split as re_split

from bot import DOWNLOAD_DIR, dispatcher
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage
from bot.helper.telegram_helper import button_build
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_url
from bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from .mirror import MirrorListener

listener_dict = {}

def _watch(bot, message, isZip=False, isLeech=False, multi=0):
    mssg = message.text
    user_id = message.from_user.id
    msg_id = message.message_id

    try:
        link = mssg.split(' ')[1].strip()
        if link.isdigit():
            multi = int(link)
            raise IndexError
        elif link.startswith(("|", "pswd:", "args:")):
            raise IndexError
    except:
        link = ''
    try:
        name_arg = mssg.split('|', maxsplit=1)
        if 'args: ' in name_arg[0]:
            raise IndexError
        else:
            name = name_arg[1]
        name = re_split(r' pswd: | args: ', name)[0]
        name = name.strip()
    except:
        name = ''
    try:
        pswd = mssg.split(' pswd: ')[1]
        pswd = pswd.split(' args: ')[0]
    except:
        pswd = None

    try:
        args = mssg.split(' args: ')[1]
    except:
        args = None

    if message.from_user.username:
        tag = f"@{message.from_user.username}"
    else:
        tag = message.from_user.mention_html(message.from_user.first_name)

    reply_to = message.reply_to_message
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text.strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)

    if not is_url(link):
        help_msg = "<b>Send link along with command line:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: mypassword [zip] args: x:y|x1:y1"
        help_msg += "\n\n<b>By replying to link:</b>"
        help_msg += "\n<code>/command</code> |newname pswd: mypassword [zip] args: x:y|x1:y1"
        help_msg += "\n\n<b>Args Example:</b> args: playliststart:^10|match_filter:season_number=18|matchtitle:S1"
        help_msg += "\n\n<b>NOTE:</b> Add `^` before integer, some values must be integer and some string."
        help_msg += " Like playlist_items:10 works with string so no need to add `^` before the number"
        help_msg += " but playlistend works only with integer so you must add `^` before the number like example above."
        help_msg += "\n\nCheck all arguments from this <a href='https://github.com/yt-dlp/yt-dlp/blob/a3125791c7a5cdf2c8c025b99788bf686edd1a8a/yt_dlp/YoutubeDL.py#L194'>FILE</a>."
        return sendMessage(help_msg, bot, message)

    listener = MirrorListener(bot, message, isZip, isLeech=isLeech, pswd=pswd, tag=tag)
    buttons = button_build.ButtonMaker()
    best_video = "bv*+ba/b"
    best_audio = "ba/b"
    ydl = YoutubeDLHelper(listener)
    try:
        result = ydl.extractMetaData(link, name, args, True)
        Thread(target=ydl.add_download, args=(link, f'{DOWNLOAD_DIR}{task_id}', name, best_video, False, args)).start()
    except Exception as e:
        msg = str(e).replace('<', ' ').replace('>', ' ')
        return sendMessage(tag + " " + msg, bot, message)
def _audio_subbuttons(task_id, msg, playlist=False):
    buttons = button_build.ButtonMaker()
    audio_qualities = [64, 128, 320]
    for q in audio_qualities:
        if playlist:
            i = 's'
            audio_format = f"ba/b-{q} t"
        else:
            i = ''
            audio_format = f"ba/b-{q}"
        buttons.sbutton(f"{q}K-mp3", f"qu {task_id} {audio_format}")
    buttons.sbutton("Back", f"qu {task_id} back")
    buttons.sbutton("Cancel", f"qu {task_id} cancel")
    SUBBUTTONS = InlineKeyboardMarkup(buttons.build_menu(2))
    editMessage(f"Choose Audio{i} Bitrate:", msg, SUBBUTTONS)
def _auto_cancel(msg, msg_id):
    sleep(120)
    try:
        del listener_dict[msg_id]
        editMessage('Timed out! Task has been cancelled.', msg)
    except:
        pass

def watch(update, context):
    _watch(context.bot, update.message)

def watchZip(update, context):
    _watch(context.bot, update.message, True)

def leechWatch(update, context):
    _watch(context.bot, update.message, isLeech=True)

def leechWatchZip(update, context):
    _watch(context.bot, update.message, True, True)

watch_handler = CommandHandler(BotCommands.WatchCommand, watch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
zip_watch_handler = CommandHandler(BotCommands.ZipWatchCommand, watchZip,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
leech_watch_handler = CommandHandler(BotCommands.LeechWatchCommand, leechWatch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
leech_zip_watch_handler = CommandHandler(BotCommands.LeechZipWatchCommand, leechWatchZip,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
quality_handler = CallbackQueryHandler(select_format, pattern="qu", run_async=True)

dispatcher.add_handler(watch_handler)
dispatcher.add_handler(zip_watch_handler)
dispatcher.add_handler(leech_watch_handler)
dispatcher.add_handler(leech_zip_watch_handler)
dispatcher.add_handler(quality_handler)
