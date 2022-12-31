import json
import requests
import microsoft_token

api_baseurl = 'https://graph.microsoft.com/v1.0/me'
headers = {'Authorization': 'Bearer ' + microsoft_token.get_token()}

#获取根目录的所有项
def get_children_of_root():
    global headers
    drive_data = requests.get(f'{api_baseurl}/drive/root/children', headers = headers).content
    #判断是否需要刷新
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.get(f'{api_baseurl}/drive/root/children', headers = headers).content
    drive_data = json.loads(drive_data)
    items = []
    for item in drive_data['value']:
        items.append({'name': item['name'], 'size': int(item['size'] / 10000) / 100, 'id': item['id'], 'is_folder': ('folder' in item), 'is_shared': ('shared' in item)})
    return {'items': items, 'parent_path': item['parentReference']['path']}

#通过id获取子项
def get_children_by_id(item_id: str):
    global headers
    drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}/children', headers = headers).content
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}/children', headers = headers).content
    drive_data = json.loads(drive_data)
    items = []
    for item in drive_data['value']:
        items.append({'name': item['name'], 'size': int(item['size'] / 10000) / 100, 'id': item['id'], 'is_folder': ('folder' in item), 'is_shared': ('shared' in item)})
    return {'items': items, 'parent_path': item['parentReference']['path']}

#取消共享
def delete_shared_url(item_id: str):
    global headers
    drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}/permissions', headers = headers).content
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}/permissions', headers = headers).content
    drive_data = json.loads(drive_data)
    for value in drive_data['value']:
        if value['roles'] == ['read']:
            requests.delete(f'{api_baseurl}/drive/items/{item_id}/permissions/{value["id"]}', headers = headers)

#设为共享并获取共享链接
def get_shared_url(item_id: str):
    global headers
    share_type = {"type": "view", "scope": "anonymous"}
    drive_data = requests.post(f'{api_baseurl}/drive/items/{item_id}/createLink', json = share_type, headers = headers).content
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.post(f'{api_baseurl}/drive/items/{item_id}/createLink', json = share_type, headers = headers).content
    drive_data = json.loads(drive_data)
    return drive_data['link']['webUrl']

#通过路径获取id
def get_id_by_path(path: str):
    global headers
    drive_data = requests.get(f'{api_baseurl}{path}', headers = headers).content
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.get(f'{api_baseurl}{path}', headers = headers).content
    drive_data = json.loads(drive_data)
    return drive_data['id']

#通过id获取信息
def get_item_by_id(item_id: str):
    global headers
    drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}', headers = headers).content
    if 'InvalidAuthenticationToken' in str(drive_data):
        headers = {'Authorization': 'Bearer ' + microsoft_token.refresh_token()}
        drive_data = requests.get(f'{api_baseurl}/drive/items/{item_id}', headers = headers).content
    drive_data = json.loads(drive_data)
    return {'name': drive_data['name'], 'size': int(drive_data['size'] / 10000) / 100, 'id': drive_data['id'], 'is_shared': ('shared' in drive_data)}