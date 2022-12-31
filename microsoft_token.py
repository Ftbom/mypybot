import json
import configparser
from msal import ConfidentialClientApplication

#获取token
def get_token():
    #若存在文件，从文件中读取
    try:
        with open(f'microsoft_token.json', 'r') as f:
            access_token = json.loads(f.read())['access_token']
    except:
        #获取配置
        config = configparser.ConfigParser()
        config.read('settings.ini')
        client_id = config['Onedrive']['client_id']
        client_secret = config['Onedrive']['client_secret']
        scopes = ['Files.ReadWrite.All']
        client = ConfidentialClientApplication(client_id  = client_id, client_credential = client_secret)
        authorization_url = client.get_authorization_request_url(scopes)
        print('将如下链接在浏览器打开，并输入返回的链接：')
        print(authorization_url)
        response_url = input()
        authorization_code = response_url[response_url.find('code=') + 5 : response_url.find('&session')]
        access_token = client.acquire_token_by_authorization_code(code = authorization_code, scopes = scopes)
        with open(f'microsoft_token.json', 'w') as f:
            f.write(json.dumps(access_token))
        access_token = access_token['access_token']
    return access_token

#刷新token
def refresh_token():
    with open(f'microsoft_token.json', 'r') as f:
        refresh_token = json.loads(f.read())['refresh_token']
    config = configparser.ConfigParser()
    config.read('settings.ini')
    client_id = config['Onedrive']['client_id']
    client_secret = config['Onedrive']['client_secret']
    scopes = ['Files.ReadWrite.All']
    client = ConfidentialClientApplication(client_id  = client_id, client_credential = client_secret)
    access_token = client.acquire_token_by_refresh_token(refresh_token, scopes)
    with open(f'microsoft_token.json', 'w') as f:
        f.write(json.dumps(access_token))
    access_token = access_token['access_token']
    return access_token