import os
import json
import anime
import shutil
import base64
import requests
import configparser
import microsoft_token
from re import sub
from bs4 import BeautifulSoup
from telebot.util import quick_markup
from telebot.types import ReplyKeyboardRemove, ReplyKeyboardMarkup

#Onedrive API相关
api_baseurl = 'https://graph.microsoft.com/v1.0/me'
onedrive_headers = {'Authorization': 'Bearer ' + microsoft_token.get_token()}

#获取配置文件
def get_config():
    try:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        return {'api_token': config['API']['token'], 'auth_users': config['Auth']['users'],
                'auth_secret': config['Auth']['secret'], 'aria2_ip': config['Aria2']['ip'],
                'aria2_port': config['Aria2']['port'], 'aria2_secret': config['Aria2']['secret'],
                'aria2_is_https': config['Aria2']['is_https'] == 'True', 'folder_path': config['File']['folder']}
    except:
        print("配置文件读取失败！")
        exit(1)

#获取Onedrive文件消息文本和按键
def get_onedrive_message(drive_files, index = 0):
    text = f'🎐 {os.path.basename(drive_files["parent_path"])}'
    #文件信息
    drive_files = drive_files['items']
    button = {}
    count = 0
    #文件过多则添加翻页按键
    if len(drive_files) > 47:
        if (index * 47 + 47) < len(drive_files):
            button['下一页'] = {'callback_data': f'onedrive_next_{index + 1}'}
        drive_files = drive_files[index * 47 : min(index * 47 + 47, len(drive_files))]
    for drive_file in drive_files:
        #文件大小显示处理
        if drive_file['size'] > 1024:
            size = str(int(drive_file['size'] / 1024 * 100) / 100) + 'GB'
        else:
            size = str(drive_file['size']) + 'MB'
        #文件和文件夹区分
        if drive_file['is_folder']:
            text = text + f"\n{count} 📁 {drive_file['name']} {size}"
            button[str(count)] = {'callback_data': f'onedrive_folder_{drive_file["id"]}'}
        else:
            text = text + f"\n{count} 📋 {drive_file['name']} {size}"
            button[str(count)] = {'callback_data': f'onedrive_file_{drive_file["id"]}'}
        #显示文件分享状态
        if drive_file['is_shared']:
            text = text + ' ☁️'
        count = count + 1
    return text, button

#获取Aria2下载项的状态的文本
def get_text(text, results):
    for result in results:
        #名称
        text = text + f"\n{result['title']}\n"
        #下载速度和进度
        text = text + f"速度：{int(100 * result['downloadSpeed']) / 100} MB/s，进度：{result['downloadProgress']} %\n"
        #进度条
        text = text + '|' + int(result['downloadProgress'] / (100 / 68)) * 'l' + (68 - int(result['downloadProgress'] / (100 / 68))) * ' ' + '|\n'
    return text

#Aria2状态文本
def generate_text(Aria2):
    active_results = Aria2.get_active()
    text = '⬇️正在下载：\n'
    text = get_text(text, active_results)
    waiting_results = Aria2.get_waiting()
    text = text + '\n\n⏸等待中：\n'
    text = get_text(text, waiting_results)
    stopped_results = Aria2.get_stopped()
    text = text + '\n\n⏹已停止：\n'
    text = get_text(text, stopped_results)
    return text

#获取Aria2各状态的文本和按键
def get_aria2_status_text(status_results, text, button, results, callback_data, count = 0):
    for result in status_results:
        results.append(result['gid'])
        #名称
        text = text + f"\n{count}. {result['title']}"
        #按键
        button[str(count)] = {'callback_data': f"{callback_data}_{count}"}
        count = count + 1
    return text, button, results, count

#添加通过验证的用户到配置文件
def add_auth(id):
    config = configparser.ConfigParser()
    config.read('settings.ini')
    if config['Auth']['users'] == '':
        config['Auth']['users'] = id
    else:
        users = config['Auth']['users'].split(',')
        users.append(id)
        config['Auth']['users'] = ','.join(users)
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

#获取文件夹下所有文件
def get_files(folder_path):
    results = []
    for name in os.listdir(folder_path):
        abs_path = os.path.join(folder_path, name)
        if os.path.isdir(abs_path):
            results.extend(get_files(abs_path)) #递归
        else:
            results.append(abs_path)
    return results

#获取所有文件的显示文本和按键
def get_files_text(text, files, callback_data):
    count = 0
    button_data = {}
    for file_path in files:
        #文件名
        text = text + f'{count}. {os.path.basename(file_path)}\n'
        #按键
        button_data[str(count)] = {'callback_data': f"{callback_data}_{count}"}
        count = count + 1
    return text, button_data

#用户验证处理
def auth_user(message, auth_secret, bot):
    try:
        if message.text == auth_secret:
            #添加用户id到配置文件
            add_auth(str(message.from_user.id))
            #更新用户信息
            bot.send_message(message.chat.id, "✅ 通过验证")
        else:
            bot.send_message(message.chat.id, f"❌ 验证失败")
    except:
        bot.send_message(message.chat.id, f"❌ 验证失败")

#添加种子文件处理
def add_torrent(message, bot, Aria2):
    try:
        if os.path.splitext(message.document.file_name)[1] == '.torrent':
            download_url = bot.get_file_url(message.document.file_id)
            res = requests.get(download_url)
            #Aria2添加种子文件
            torrent = base64.b64encode(res.content).decode("utf8")
            info = Aria2.add_torrent(torrent)
            if info['status'] == 'error':
                bot.send_message(message.chat.id, f"❌ {info['info']}")
            else:
                bot.send_message(message.chat.id, f"✅ {info['info']}") #返回添加结果
        else:
            bot.send_message(message.chat.id, "❗️ 不是种子文件！")
    except:
        bot.send_message(message.chat.id, f"❗️ 不是种子文件！")

#接收文件处理
def receive_file(message, bot, folder_path):
    if (message.audio != None): #audio类型文件
        file_id = message.audio.file_id
        file_name = message.audio.file_name
    elif (message.document != None): #document类型文件
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif (message.video != None): #video类型文件
        file_id = message.video.file_id
        file_name = message.video.file_name
    elif (message.photo != None): #photo类型文件
        file_id = message.photo[-1].file_id #最大分辨率
        file_name = f'{message.date}.jpg'
    else:
        bot.send_message(message.chat.id, f"❗️ 发送的不是文件！")
        return
    download_url = bot.get_file_url(file_id)
    res = requests.get(download_url)
    with open(os.path.join(folder_path, file_name), 'wb') as f:
        f.write(res.content)
    bot.send_message(message.chat.id, f"✅ 文件保存为{file_name}")

#上传文件到Onedrive处理
def upload_file(path, message, bot):
    global onedrive_headers
    file_byte = os.path.getsize(path) #文件大小
    name = os.path.basename(path) #文件名
    #创建Onedrive上传链接
    res = requests.post(api_baseurl + f'/drive/root:/{name}:/createUploadSession', headers = onedrive_headers)
    if 'InvalidAuthenticationToken' in str(res.content):
        #刷新token
        onedrive_headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        res = requests.post(api_baseurl + f'/drive/root:/{name}:/createUploadSession', headers = onedrive_headers)
    upload_url = json.loads(res.content)['uploadUrl']
    byte_headers = {}
    #上传用headers
    byte_headers['Authorization'] = onedrive_headers['Authorization']
    byte_uploaded = 0
    #计算文件分块大小
    if file_byte > 1500000000:
        byte_amount = 327680 * 100
    else:
        byte_amount = 327680 * 50
    msg = bot.send_message(message.chat.id, f'⬆️ 开始上传：\n{name}\n进度：0%')
    with open(path, 'rb') as f:
        while (True):
            byte_part = f.read(byte_amount)
            #文件读取结束
            if not byte_part:
                break
            byte_size = len(byte_part)
            byte_headers['Content-Length'] = f'{byte_size}'
            byte_headers['Content-Range'] = f'bytes {byte_uploaded}-{byte_uploaded + byte_size - 1}/{file_byte}'
            r = requests.put(upload_url, data = byte_part, headers = byte_headers)
            #更新上传状态
            bot.edit_message_text(f'⬆️ 开始上传：\n{name}\n进度：{int(((byte_uploaded + byte_size) / file_byte) * 1000) / 10}%', chat_id = msg.chat.id, message_id = msg.message_id)
            byte_uploaded = byte_uploaded + byte_size

#部分按键回调处理
def callback_func(store, text, call, bot):
    #若不是最新消息，此消息设置为失效
    if not (f'{text}_{store["last_date"]}_' in call.data):
        bot.edit_message_text('⭕️ 消息已失效', chat_id = call.message.chat.id, message_id = call.message.message_id)
        bot.answer_callback_query(call.id)
        return ''
    num = int(call.data.replace(f'{text}_{store["last_date"]}_', ''))
    return store['data'][num]

def tg_trace_moe(message, bot, url = ''):
    if (url == ''):
        #获取图片url
        if (message.photo == None):
            bot.send_message(message.chat.id, "❗️ 不是图片！")
            return
        else:
            file_id = message.photo[-1].file_id
            url = bot.get_file_url(file_id)
    else:
        pass
    #搜索
    result = anime.trace_moe(url)
    if ('error' in result):
        bot.send_message(message.chat.id, f"❌ {result['error']}")
        return
    text = f'''
<b>标题</b>：{result['info']['native_name']}
            <i>{result['info']['romaji_name']}</i>
<b>文件名</b>：{result['filename']}
<b>集</b>：{result['episode']}
<b>时间段</b>：{result['from']}-{result['to']}
<b>相似度</b>：{int(result['similarity'] * 100) / 100}
'''
    button = {"AniList": {'url': result['anilist']},
            "图片": {'url': result['image']},
            "片段": {'url': result['video']}}
    bot.send_photo(message.chat.id, photo = result['info']['cover'], caption = text, parse_mode = "HTML", reply_markup = quick_markup(button, row_width = 3))

def download_nhentai(message, url: str, bot, folder_path):
    if url[-1] == '/':
        url = url[: -1]
    #nhentai.net和nhentai.xxx
    url = url.replace('.net/g', '.to/g')
    url = url.replace('.xxx/g', '.to/g')
    r = requests.get(url, headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        "Referer" : 'https://nhentai.to'
    })
    soup = BeautifulSoup(r.content, 'html.parser')
    #获取本子标题
    title = soup.find(id = 'info').find('h1').get_text()
    r = requests.get(url + '/1', headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        "Referer" : 'https://nhentai.to'
    })
    soup = BeautifulSoup(r.content, 'html.parser')
    baseimage = soup.find(id = 'image-container').img.attrs['src']
    #javascript内容
    scripts = soup.find_all('script')
    for script in scripts:
        if script.get_text().find('var reader = new N.reader({') != -1:
            img_data = script.get_text()
            break
    #获取每页信息
    images = img_data[img_data.find('"pages": ') + 9 : img_data.find('"cover":') - 22]
    images = json.loads(images)
    #获取图片链接公共部分
    if images[0]['t'] == 'j':
        baseimage = baseimage.replace('1.jpg', '')
    elif images[0]['t'] == 'p':
        baseimage = baseimage.replace('1.png', '')
    elif images[0]['t'] == 'g':
        baseimage = baseimage.replace('1.gif', '')
    else:
        baseimage = baseimage.replace('1.jpg', '')
    i = 1
    if os.path.exists(os.path.join(folder_path, 'temp')):
        shutil.rmtree(os.path.join(folder_path, 'temp'), ignore_errors=True)
    os.mkdir(os.path.join(folder_path, 'temp'))
    msg = bot.send_message(message.chat.id, f"⬇️ 下载中：\n{title}\n0/{len(images)}")
    for image in images:
        if image['t'] == 'j':
            img_url = baseimage + f'{i}' + '.jpg'
        elif image['t'] == 'p':
            img_url = baseimage + f'{i}' + '.png'
        elif image['t'] == 'g':
            img_url = baseimage + f'{i}' + '.gif'
        else:
            img_url = baseimage + f'{i}' + '.jpg'
        r = requests.get(img_url, headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        "Referer" : 'https://nhentai.to'
        })
        with open(os.path.join(folder_path, f'temp/{i}.jpg'), 'wb') as f:
            f.write(r.content)
        bot.edit_message_text(f"⬇️ 下载中：\n{title}\n{i}/{len(images)}", chat_id = message.chat.id, message_id = msg.message_id)
        i = i + 1
    #去除非法字符
    title = sub(r"[\/\\\:\*\?\"\<\>\|]", "_", title)
    shutil.make_archive(os.path.join(folder_path, title), 'zip', os.path.join(folder_path, 'temp/'))
    shutil.rmtree(os.path.join(folder_path, 'temp'), ignore_errors=True)

def waifu_pics_type(message, bot):
    if (message.text == 'sfw'):
        #bot.send_message(message.chat.id, "⛩ 选择类型：SFW", reply_markup = ReplyKeyboardRemove())
        markup = ReplyKeyboardMarkup(resize_keyboard = True, row_width = 4)
        markup.add('waifu', 'neko', 'shinobu', 'megumin', 'bully',
        'cuddle', 'cry', 'hug', 'awoo', 'kiss', 'lick', 'pat', 'smug',
        'bonk', 'yeet', 'blush', 'smile', 'wave', 'highfive', 'handhold',
        'nom', 'bite', 'glomp', 'slap', 'kill', 'kick', 'happy', 'wink',
        'poke', 'dance', 'cringe', "取消")
    elif (message.text == 'nsfw'):
        #bot.send_message(message.chat.id, "⛩ 选择类型：NSFW", reply_markup = ReplyKeyboardRemove())
        markup = ReplyKeyboardMarkup(resize_keyboard = True, row_width = 4)
        markup.add('waifu', 'neko', 'trap', 'blowjob', '取消')
    elif (message.text == '取消'):
        bot.send_message(message.chat.id, "⛩ 取消操作", reply_markup = ReplyKeyboardRemove())
        return
    else:
        bot.send_message(message.chat.id, "❌ 类型错误", reply_markup = ReplyKeyboardRemove())
        return
    msg = bot.send_message(message.chat.id, "⛩ 选择类别", reply_markup = markup)
    bot.register_next_step_handler(msg, waifu_pics_category, bot, message.text)

def waifu_pics_category(message, bot, type):
    if (message.text == '取消'):
        bot.send_message(message.chat.id, "⛩ 取消操作", reply_markup = ReplyKeyboardRemove())
        return
    result = anime.waifu_pics(type, message.text)
    if ('error' in result):
        bot.send_message(message.chat.id, f"❌ {result['error']}", reply_markup = ReplyKeyboardRemove())
        return
    bot.send_photo(message.chat.id, photo = result['url'], reply_markup = ReplyKeyboardRemove())
