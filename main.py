import os
import aria2
import system
from tools import *
import onedrive_files
from telebot import TeleBot
from telebot.util import quick_markup
from telebot.types import ReplyKeyboardMarkup

###############################
#############初始化#############
################################

#记录消息对应数据和最新消息的时间
files_info_store = {"last_date": 0}
files_receive_store = {"last_date": 0}
files_remove_store = {"last_date": 0}
aria2_pause_store = {"last_date": 0}
aria2_unpause_store = {"last_date": 0}
aria2_remove_store = {"last_date": 0}
aria2_rmstopped_store = {"last_date": 0}

#Onedrive路径信息
onedrive_parent_path = '/drive/root:'
onedrive_current_path = '/drive/root:'

#从配置文件获取设置
config = get_config()
auth_users = config['auth_users'].split(',')
auth_secret = config['auth_secret']
folder_path = config['folder_path']
API_TOKEN = config['api_token']
Aria2 = aria2.aria2(config['aria2_ip'], config['aria2_port'], config['aria2_secret'], config['aria2_is_https'])

bot = TeleBot(API_TOKEN) #初始化bot

#用户验证函数装饰器
def authentication(func):
    def wrapper(message):
        #配置文件未设置用户，则对所有用户开放
        if auth_users == ['']:
            pass
        else:
            #判断是否为允许的用户
            if not (str(message.from_user.id) in auth_users):
                bot.send_message(message.chat.id, f"⛔️ 未经允许的用户")
                return
        func(message)
        pass
    return wrapper

def auth_and_updata_users(message, auth_secret, bot):
    auth_user(message, auth_secret, bot)
    global auth_users
    #更新用户验证信息
    auth_users = get_config()['auth_users']

###############################
############功能命令############
################################
@bot.message_handler(commands = ['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, '''
*多功能机器人*
已实现功能：
● Aria2管理（添加、暂停、恢复、删除下载，显示进度）
● 指定文件夹内文件的接收、发送、删除、上传
● Onedrive文件的浏览、分享、取消分享
● 二次元相关
● 获取系统信息
● 获取用户id
输入 /help 获取帮助
'''
, parse_mode = 'Markdown')

@bot.message_handler(commands = ['auth'])
def get_auth(message):
    #未开启验证模式，或已通过验证
    if (auth_users == ['']) or (str(message.from_user.id) in auth_users):
        bot.send_message(message.chat.id, '⚠️ 无需验证')
    else:
        msg = bot.send_message(message.chat.id, '❓ 请输入密码')
        bot.register_next_step_handler(msg, auth_and_updata_users, auth_secret, bot)

@bot.message_handler(commands = ['help'])
def send_welcome(message):
    bot.send_message(message.chat.id, '''
*功能*
/auth - 用户验证
/help - 获取帮助
*Aria2相关*
/aria2add - 添加aria2下载
/aria2torrent - 通过种子文件添加aria2下载
/aria2status - 显示aria2下载状态
/aria2pause - 暂停aria2中的下载
/aria2unpause - 恢复aria2中已暂停的下载
/aria2remove - 删除aria2中的下载
/aria2rmstopped - 删除aria2中已停止的下载
*文件相关*
/sendfile - 发送文件到文件夹内
/receivefile - 接收文件夹内的文件
/uploadfile - 通过Onedrive上传指定文件
/rmfile - 删除文件夹内的文件
*Onedrive*
/onedrive - 管理Onedrive文件
*Anime*
/tracemoe - 动漫截图搜索
/waifupics - 随机二次元图片
/nhentai - 下载nhentai本子到文件夹内
*其他*
/getid - 获取用户id
/systemstatus - 获取系统信息
/custom - 自定义操作
'''
, parse_mode = 'Markdown')

###############################
##########Onedrive命令##########
################################
@bot.message_handler(commands = ['onedrive'])
@authentication
def onedrive(message):
    global onedrive_parent_path, onedrive_current_path
    #获取根目录下的文件信息
    drive_files = onedrive_files.get_children_of_root()
    #获取文本和按键信息
    text, button = get_onedrive_message(drive_files)
    #更新当前Onedrive的路径信息
    onedrive_current_path = drive_files['parent_path']
    onedrive_parent_path = os.path.dirname(drive_files['parent_path'])
    button['取消'] = {'callback_data': 'cancel'}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button, row_width = 4))

###############################
###########Anime命令###########
###############################
@bot.message_handler(commands = ['tracemoe'])
@authentication
def tracemoe(message):
    url = message.text.replace('/tracemoe ', '')
    #判断是否输入url
    if (url.replace(' ', '') == '') or (url == '/tracemoe'):
        msg = bot.send_message(message.chat.id, "⚠️ 请发送图片")
        bot.register_next_step_handler(msg, tg_trace_moe, bot)
    else:
        tg_trace_moe(message, bot, url)

@bot.message_handler(commands = ['waifupics'])
@authentication
def waifupics(message):
    markup = ReplyKeyboardMarkup(resize_keyboard = True)
    markup.add("sfw", "nsfw", "取消")
    msg = bot.send_message(message.chat.id, "⛩ 选择类型", reply_markup = markup)
    bot.register_next_step_handler(msg, waifu_pics_type, bot)

@bot.message_handler(commands = ['nhentai'])
@authentication
def nhentai(message):
    url = message.text.replace('/nhentai ', '')
    #判断是否输入url
    if (url.replace(' ', '') == '') or (url == '/nhentai'):
        bot.send_message(message.chat.id, "❗️请在/nhentai后输入链接")
        return
    else:
        download_nhentai(message, url, bot, folder_path)

###############################
############文件命令############
################################
@bot.message_handler(commands = ['sendfile'])
@authentication
def send_file(message):
    msg = bot.send_message(message.chat.id, "⚠️ 请发送文件")
    bot.register_next_step_handler(msg, receive_file, bot, folder_path)

@bot.message_handler(commands = ['receivefile'])
@authentication
def receive_file(message):
    global files_receive_store
    #获取文件夹内的所有文件
    files = get_files(folder_path)
    #更新消息信息
    files_receive_store = {"last_date": message.date, 'data': files}
    #获取文本和按键
    text = '📦 选择要接收的文件：\n'
    text, button_data = get_files_text(text, files, f'receive_{message.date}')
    button_data['取消'] = {'callback_data': 'cancel'}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

@bot.message_handler(commands = ['uploadfile'])
@authentication
def upload_to_onedrive(message):
    global files_info_store
    #获取文件夹内的所有文件
    files = get_files(folder_path)
    #更新消息信息
    files_info_store = {"last_date": message.date, 'data': files}
    #获取文本和按键
    text = '📦 选择要上传的文件：\n'
    text, button_data = get_files_text(text, files, f'file_{message.date}')
    button_data['取消'] = {'callback_data': 'cancel'}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

@bot.message_handler(commands = ['rmfile'])
@authentication
def remove_file(message):
    global files_remove_store
    files = get_files(folder_path)
    files_remove_store = {"last_date": message.date, 'data': files}
    text = '📦 选择要删除的文件：\n'
    text, button_data = get_files_text(text, files, f'remove_{message.date}')
    button_data['全部'] = {'callback_data': 'rmfile_all'} #删除所有
    button_data['取消'] = {'callback_data': 'cancel'}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

###############################
############其他命令############
################################
@bot.message_handler(commands = ['getid'])
@authentication
def get_id(message):
    bot.send_message(message.chat.id, message.from_user.id)

@bot.message_handler(commands = ['systemstatus'])
@authentication
def system_status(message):
    button = {'刷新': {'callback_data': 'system_refresh'}, '取消': {'callback_data': 'cancel'}}
    text = system.system_info() + '\n' + system.system_status()
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button, row_width = 4), parse_mode = "HTML")

@bot.message_handler(commands = ['custom'])
@authentication
def custom(message):
    try:
        import custom
        msgs = custom.run()
        for msg in msgs:
            bot.send_message(message.chat.id, msg, parse_mode = "HTML")
    except:
        bot.send_message(message.chat.id, "⚠️ custom.py文件导入失败")

###############################
###########Aria2命令############
################################
@bot.message_handler(commands = ['aria2add'])
@authentication
def aria2_add_url(message):
    url = message.text.replace('/aria2add ', '')
    if (url.replace(' ', '') == '') or (url == '/aria2add'):
        bot.send_message(message.chat.id, "❗️请在/aria2add后输入链接")
    else:
        info = Aria2.add_url(url)
        #结果反馈
        if info['status'] == 'error':
            bot.send_message(message.chat.id, f"❌ {info['info']}")
        else:
            bot.send_message(message.chat.id, f"✅ {info['info']}")

@bot.message_handler(commands = ['aria2torrent'])
@authentication
def aria2_add_torrent(message):
    msg = bot.send_message(message.chat.id, "⚠️ 请发送种子文件")
    bot.register_next_step_handler(msg, add_torrent, bot, Aria2)

@bot.message_handler(commands = ['aria2status'])
@authentication
def show_active(message):
    button = {'刷新': {'callback_data': 'refresh'}, '取消': {'callback_data': 'cancel'}}
    text = generate_text(Aria2)
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button, row_width = 4))

@bot.message_handler(commands = ['aria2pause'])
@authentication
def pause(message):
    global aria2_pause_store
    text = '请输入要暂停的项的序号：\n⬇️正在下载：'
    #获取正在下载的项
    active_results = Aria2.get_active()
    text, button_data, results, count = get_aria2_status_text(active_results, text, {}, [], f'pause_{message.date}')
    text = text + '\n⏸等待中：'
    #获取等待中的项
    waiting_results = Aria2.get_waiting_by_status(status = 'waiting')
    text, button_data, results, count = get_aria2_status_text(waiting_results, text, button_data, results, f'pause_{message.date}', count = count)
    button_data['全部'] = {'callback_data': 'pause_all'}
    button_data['取消'] = {'callback_data': 'cancel'}
    #更新信息
    aria2_pause_store = {"last_date": message.date, 'data': results}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

@bot.message_handler(commands = ['aria2unpause'])
@authentication
def unpause(message):
    global aria2_unpause_store
    text = '请输入要恢复的项的序号：\n▶️已暂停：'
    paused_results = Aria2.get_waiting_by_status(status = 'paused')
    text, button_data, results, count = get_aria2_status_text(paused_results, text, {}, [], f'unpause_{message.date}')
    button_data['全部'] = {'callback_data': 'unpause_all'}
    button_data['取消'] = {'callback_data': 'cancel'}
    aria2_unpause_store = {"last_date": message.date, 'data': results}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

@bot.message_handler(commands = ['aria2remove'])
@authentication
def remove(message):
    global aria2_remove_store
    text = '请输入要删除的项的序号：\n⬇️正在下载：'
    active_results = Aria2.get_active()
    text, button_data, results, count = get_aria2_status_text(active_results, text, {}, [], f'aremove_{message.date}')
    text = text + '\n⏸等待中：'
    waiting_results = Aria2.get_waiting()
    text, button_data, results, count = get_aria2_status_text(waiting_results, text, button_data, results, f'aremove_{message.date}', count = count)
    button_data['取消'] = {'callback_data': 'cancel'}
    aria2_remove_store = {"last_date": message.date, 'data': results}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

@bot.message_handler(commands = ['aria2rmstopped'])
@authentication
def remove(message):
    global aria2_rmstopped_store
    text = '请输入要删除的项的序号：\n⏹已停止：'
    stopped_results = Aria2.get_stopped()
    text, button_data, results, count = get_aria2_status_text(stopped_results, text, {}, [], f'rmstopped_{message.date}')
    button_data['全部'] = {'callback_data': 'rmstopped_all'}
    button_data['取消'] = {'callback_data': 'cancel'}
    aria2_rmstopped_store = {"last_date": message.date, 'data': results}
    bot.send_message(message.chat.id, text, reply_markup = quick_markup(button_data, row_width = 4))

###############################
############回调处理############
################################
@bot.callback_query_handler(func=lambda call: True)
def refresh(call):
    global onedrive_parent_path, onedrive_current_path
    if (call.data == 'refresh'):
        button = {'刷新': {'callback_data': 'refresh'}, '取消': {'callback_data': 'cancel'}}
        text = generate_text(Aria2)
        #若Aria2状态发生变化，更新消息
        if not (call.message.text.replace(' ', '').replace('\n', '') == text.replace(' ', '').replace('\n', '')):
            bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif (call.data == 'system_refresh'):
        button = {'刷新': {'callback_data': 'system_refresh'}, '取消': {'callback_data': 'cancel'}}
        text = system.system_info() + '\n' + system.system_status()
        if not (call.message.text.replace(' ', '').replace('\n', '') == text.replace(' ', '').replace('\n', '')):
            bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, parse_mode = "HTML", reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif ('cancel' == call.data):
        bot.edit_message_text('⭕️ 已取消操作', chat_id = call.message.chat.id, message_id = call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    elif ('rmfile_all' == call.data):
        os.system(f'rm -rf {folder_path}/*')
        bot.answer_callback_query(call.id)
        return
    elif ('pause_all' == call.data):
        Aria2.pause_all_download()
        bot.answer_callback_query(call.id)
        return
    elif ('unpause_all' == call.data):
        Aria2.unpause_all_download()
        bot.answer_callback_query(call.id)
        return
    elif ('rmstopped_all' == call.data):
        Aria2.remove_all_download_stopped()
        bot.answer_callback_query(call.id)
        return
    elif ('file_' == call.data[0 : 5]):
        file_path = callback_func(files_info_store, 'file', call, bot)
        if (file_path == ''):
            return
        bot.answer_callback_query(call.id)
        #上传文件
        upload_file(file_path, call.message, bot)
        return
    elif ('receive_' == call.data[0 : 8]):
        file_path = callback_func(files_receive_store, 'receive', call, bot)
        if (file_path == ''):
            return
        bot.answer_callback_query(call.id)
        #接收文件
        with open(file_path, 'rb') as f:
            bot.send_document(call.message.chat.id, f)
        return
    elif ('remove_' == call.data[0 : 7]):
        file_path = callback_func(files_remove_store, 'remove', call, bot)
        if (file_path == ''):
            return
        os.system(f'rm -f "{file_path}"')
        bot.answer_callback_query(call.id)
        return
    elif ('pause_' == call.data[0 : 6]):
        gid = callback_func(aria2_pause_store, 'pause', call, bot)
        if (gid == ''):
            return
        Aria2.pause_download(gid)
        bot.answer_callback_query(call.id)
        return
    elif ('unpause_' == call.data[0 : 8]):
        gid = callback_func(aria2_unpause_store, 'unpause', call, bot)
        if (gid == ''):
            return
        Aria2.unpause_download(gid)
        bot.answer_callback_query(call.id)
        return
    elif ('aremove_' == call.data[0 : 8]):
        gid = callback_func(aria2_remove_store, 'aremove', call, bot)
        if (gid == ''):
            return
        Aria2.remove_download(gid)
        bot.answer_callback_query(call.id)
        return
    elif ('rmstopped_' == call.data[0 : 10]):
        gid = callback_func(aria2_rmstopped_store, 'rmstopped', call, bot)
        if (gid == ''):
            return
        Aria2.remove_download_stopped(gid)
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_back' == call.data):
        #获取Onedrive文件夹下所有项
        if (onedrive_parent_path == '/drive/root:'):
            drive_files = onedrive_files.get_children_of_root()
        else:
            parent_id = onedrive_files.get_id_by_path(onedrive_parent_path)
            drive_files = onedrive_files.get_children_by_id(parent_id)
        #更新Onedrive路径信息
        onedrive_current_path = drive_files['parent_path']
        onedrive_parent_path = os.path.dirname(drive_files['parent_path'])
        text, button = get_onedrive_message(drive_files)
        if drive_files['parent_path'] != '/drive/root:':
            button['返回'] = {'callback_data': 'onedrive_back'}
        button['取消'] = {'callback_data': 'cancel'}
        bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_folder' == call.data[0 : 15]):
        drive_files = onedrive_files.get_children_by_id(call.data.replace('onedrive_folder_', ''))
        onedrive_current_path = drive_files['parent_path']
        onedrive_parent_path = os.path.dirname(drive_files['parent_path'])
        text, button = get_onedrive_message(drive_files)
        button['返回'] = {'callback_data': 'onedrive_back'}
        button['取消'] = {'callback_data': 'cancel'}
        bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_file' == call.data[0 : 13]):
        file_id = call.data.replace('onedrive_file_', '')
        item_data = onedrive_files.get_item_by_id(file_id)
        #文件大小显示处理
        if item_data['size'] > 1024:
            size = str(int(item_data['size'] / 1024 * 100) / 100) + 'GB'
        else:
            size = str(item_data['size']) + 'MB'
        if item_data['is_shared']:
            is_shared = '是'
        else:
            is_shared = '否'
        text = f'🎐 {item_data["name"]}\n大小：{size}, 已分享：{is_shared}'
        button = {}
        #是否已分享
        if item_data['is_shared']:
            button['获取链接'] = {'callback_data': f'onedrive_share_{item_data["id"]}'}
            button['取消分享'] = {'callback_data': f'onedrive_unshare_{item_data["id"]}'}
        else:
            button['分享'] = {'callback_data': f'onedrive_share_{item_data["id"]}'}
        button['返回'] = {'callback_data': 'od_file_back'}
        button['取消'] = {'callback_data': 'cancel'}
        bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_unshare' == call.data[0 : 16]):
        file_id = call.data.replace('onedrive_unshare_', '')
        onedrive_files.delete_shared_url(file_id)
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_share' == call.data[0 : 14]):
        file_id = call.data.replace('onedrive_share_', '')
        text = onedrive_files.get_shared_url(file_id)
        bot.send_message(call.message.chat.id, text)
        bot.answer_callback_query(call.id)
        return
    elif ('od_file_back' == call.data):
        if (onedrive_current_path == '/drive/root:'):
            drive_files = onedrive_files.get_children_of_root()
        else:
            current_id = onedrive_files.get_id_by_path(onedrive_current_path)
            drive_files = onedrive_files.get_children_by_id(current_id)
        text, button = get_onedrive_message(drive_files)
        if drive_files['parent_path'] != '/drive/root:':
            button['返回'] = {'callback_data': 'onedrive_back'}
        button['取消'] = {'callback_data': 'cancel'}
        bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    elif ('onedrive_next' == call.data[0 : 13]):
        #翻页
        index = int(call.data.replace('onedrive_next_', ''))
        current_id = onedrive_files.get_id_by_path(onedrive_current_path)
        drive_files = onedrive_files.get_children_by_id(current_id)
        text, button = get_onedrive_message(drive_files, index = index)
        button['返回'] = {'callback_data': 'onedrive_back'}
        button['取消'] = {'callback_data': 'cancel'}
        bot.edit_message_text(text, chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = quick_markup(button, row_width = 4))
        bot.answer_callback_query(call.id)
        return
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    bot.infinity_polling()
