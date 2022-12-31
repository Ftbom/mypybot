# 多功能Telegram机器人

## 配置文件

```config
[API]
;Telegram机器人token
token = 

[Aria2]
;Aria2服务的ip
ip = 
;Aria2服务的端口
port = 
;Aria2服务的密钥
secret = 
;是否使用http连接
is_https = 

[Auth]
;留空则机器人无需验证即可使用
;至少填入一个则机器人开启验证
;填入用户的id，使用,隔开
;开启验证后，用户输入/auth并通过验证，会自动将用户id填入
users = 
;验证密码
secret = 

[File]
;文件夹的路径
;文件相关的命令对应的文件夹
folder = 

[Onedrive]
;Onedrive bussiness API
client_id = 
client_secret = 
```