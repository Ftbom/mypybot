import os
import time
import yt_dlp
from tools import get_config
from telebot.types import ReplyKeyboardRemove, ReplyKeyboardMarkup

temp_bot = None
temp_msg = None
format_num = -1

def get_format_num(message, num):
    global temp_bot
    global temp_msg
    global format_num
    if (message.text == '取消'):
        temp_bot.send_message(message.chat.id, "取消下载", reply_markup = ReplyKeyboardRemove())
        format_num = -2
        return
    else:
        try:
            number = int(message.text)
            if ((number < 0) or (number >= num)):
                temp_bot.send_message(message.chat.id, "未选择正确的格式", reply_markup = ReplyKeyboardRemove())
                format_num = 1000
                return
        except:
            format_num = -1
            return
        temp_bot.send_message(message.chat.id, "开始下载", reply_markup = ReplyKeyboardRemove())
        temp_msg = temp_bot.send_message(message.chat.id, "获取下载进度...")
        format_num = number

def my_hook(d):
    global last_progress_text
    if (format_num == -1):
        return
    if d['status'] == 'error':
        temp_bot.edit_message_text("下载出错", chat_id = temp_msg.chat.id, message_id = temp_msg.message_id)
    elif d['status'] == 'finished':
        temp_bot.edit_message_text(f"{os.path.basename(d['filename'])}\n下载已完成", chat_id = temp_msg.chat.id, message_id = temp_msg.message_id)
    elif d['status'] == 'downloading':
        file_name = os.path.basename(d['filename'])
        try:
            progress = f"{round(d['downloaded_bytes']/d['total_bytes'] * 100, 2)}%"
        except:
            progress = 'Unknown'
        try:
            downloaded = f"{round(d['downloaded_bytes'] / 1024**2, 2)}MB"
        except:
            downloaded = 'Unknown'
        try:
            total = f"{round(d['total_bytes'] / 1024**2, 2)}MB"
        except:
            total = 'Unknown'
        try:
            speed = f"{round(d['speed'] / 1024**2, 2)}MB/s"
        except:
            speed = 'Unknown'
        text = f"{file_name}\n进度：{progress} {downloaded}/{total}\n速度：{speed}"
        try:
            temp_bot.edit_message_text(text, chat_id = temp_msg.chat.id, message_id = temp_msg.message_id)
        except:
            pass

def format_selector(ctx):
    global temp_bot
    global temp_msg
    global format_num
    # formats are already sorted worst to best
    formats = ctx.get('formats')[::-1]
    markup = ReplyKeyboardMarkup(resize_keyboard = True)
    text = "选择视频格式：\n"
    num = 0
    if 'format_note' in formats[0]:
        for format in formats:
            if (format['vcodec'] == 'none'):
                continue
            if ('filesize' in format) and (format['filesize'] != None):
                text = text + f"{num}  {format['format_id']}  {format['format_note']}  {round(format['filesize'] / 1023**2, 2)}MB\n"
            else:
                text = text + f"{num}  {format['format_id']}  {format['format_note']}\n"
            markup.add(str(num))
            num = num + 1
    else:
        for format in formats:
            if (format['vcodec'] == 'none'):
                continue
            if ('filesize' in format) and (format['filesize'] != None):
                text = text + f"{num}  {format['format_id']}  {round(format['filesize'] / 1023**2, 2)}MB\n"
            else:
                text = text + f"{num}  {format['format_id']}\n"
            markup.add(str(num))
            num = num + 1
    markup.add('取消')
    msg = temp_bot.send_message(temp_msg.chat.id, text, reply_markup = markup)
    temp_bot.register_next_step_handler(msg, get_format_num, num)
    num = 0
    while (True):
        num = num + 1
        time.sleep(1)
        if (num > 60):
            temp_bot.send_message(temp_msg.chat.id, "超时未操作，输入任意内容取消任务", reply_markup = ReplyKeyboardRemove())
            return
        if (format_num == -1):
            continue
        if (format_num == -2):
            return
        else:
            try:
                best_video = formats[format_num]
                break
            except:
                return
    try:
        # find compatible audio extension
        audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
        # vcodec='none' means there is no video
        best_audio = next(f for f in formats if (
            f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))
        # These are the minimum required fields for a merged format
        yield {
            'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
            'ext': best_video['ext'],
            'requested_formats': [best_video, best_audio],
            # Must be + separated list of protocols
            'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
        }
    except:
        yield {
            'format_id': best_video["format_id"],
            'ext': best_video['ext'],
            'requested_formats': [best_video],
            'protocol': best_video["protocol"]
        }

folder = get_config()['folder_path']
ydl_opts = {
    'format': format_selector,
    'progress_hooks': [my_hook],
    'paths': {'home': folder, 'temp': folder}
}

def video_download(url, bot, message):
    global temp_bot
    global temp_msg
    global format_num
    format_num = -1
    temp_msg = message
    temp_bot = bot
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        if not ('Requested format is not available' in str(e)):
            bot.send_message(message.chat.id, str(e))