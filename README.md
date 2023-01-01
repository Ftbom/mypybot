# mypybot

使用Python编写的自用Telegram机器人，基于[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)

## 安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 功能

已实现：

* Aria2管理（添加、暂停、恢复、删除下载，显示进度）
* 指定文件夹内文件的接收、删除、上传Onedrive
* Onedrive文件的浏览、分享、取消分享
* 二次元相关
  >nhentai下载支持：所有nhentai.to，大部分nhentai.net，大部分nhentai.xxx
* 支持简单的用户验证

### 功能演示

![](screenshots/1.png)
![](screenshots/2.png)
![](screenshots/3.png)
![](screenshots/4.png)
![](screenshots/5.png)
![](screenshots/6.png)
![](screenshots/7.png)

## 配置文件

```config
[API]
token = 

[Aria2]
ip = 
port = 
secret = 
is_https = 

[Auth]
users = 
secret = 

[File]
folder = 

[Onedrive]
client_id = 
client_secret = 
```

### API

* `token`：Telegram机器人的token

### Aria2

* `ip`：Aria2服务的ip
* `port`：Aria2服务的端口
* `secret`：Aria2服务的密钥
* `is_https`：`True`或`False`

### Auth

* `users`：通过验证的用户的id。若留空，关闭用户验证，所有人均可使用机器人。机器人运行后通过验证的用户的id会自动被添加
* `secret`：用户验证的密码

### File

* `folder`：文件夹路径，此文件夹用于`/sendfile`、`/uploadfile`等命令

### Onedrive

* `client_id`：Onedrive应用id
* `client_secret`：Onedrive应用secret

仅支持Onedrive for Business

Onedrive应用需要`Files.ReadWrite.All`权限

第一次运行时，需按终端的输出提示进行Onedrive应用授权