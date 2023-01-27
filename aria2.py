import os
import json
import time
import requests

#添加下载项的函数装饰器
def add_download(func):
    def wrapper(self, url):
        #添加下载
        res = requests.post(self.aira2_url, func(self, url))
        result = json.loads(res.content.decode("utf-8"))
        #获取错误信息
        try:
            return {'status': 'error', 'info': result['error']['message']}
        except:
            pass
        gid = result['result']
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    	        'method':'aria2.tellStatus',
                    'params':[f"token:{self.token}", gid]})
        #等待3s后查询结果
        time.sleep(3)
        res = requests.post(self.aira2_url, jsonreq)
        result = json.loads(res.content.decode("utf-8"))['result']
        if result['status'] == 'error':
            return {'status': 'error', 'info': result['errorMessage']}
        else:
            #若下载文件夹，返回文件夹名
            title = result['files'][0]['path']
            des_name = result['dir'].replace("\\", '/') #处理Windows系统路径
            title = title.replace(des_name, '')
            if (os.path.dirname(title) == '/') or (os.path.dirname(title) == ''):
                title = os.path.basename(title)
            else:
                title = os.path.dirname(title)[1 :]
            return {'status': 'success', 'info': title}
    return wrapper

#获取下载状态的函数装饰器
def get_status(func):
    def wrapper(self):
        res = requests.post(self.aira2_url, func(self))
        temp_results = json.loads(res.content.decode("utf-8"))['result']
        results = []
        for result in temp_results:
            #获取下载项的名称
            title = result['files'][0]['path']
            des_name = result['dir'].replace("\\", '/')
            title = title.replace(des_name, '')
            if (os.path.dirname(title) == '/') or (os.path.dirname(title) == ''):
                title = os.path.basename(title)
            else:
                title = os.path.dirname(title)[1 :]
            results.append({"gid": result["gid"], "title": title, "downloadSpeed": 10**(-6) * int(result["downloadSpeed"]),
                            "downloadProgress": (10000 * int(result["completedLength"]) // max(int(result["totalLength"]), 1)) / 100})
        return results
    return wrapper

class aria2():
    def __init__(self, ip: str, port: str, token: str, is_https: bool):
        if (is_https):
            self.aria2_url = f'https://{ip}:{port}/jsonrpc'
        else:
            self.aira2_url = f'http://{ip}:{port}/jsonrpc'
        self.token = token
    
    def is_connected(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.getVersion',
              	    'params':[f"token:{self.token}"]})
        try:
            info = requests.post(self.aira2_url, jsonreq).json()
            if 'error' in info:
                return False
            return True
        except:
            return False

    @add_download
    def add_url(self, url):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.addUri',
                    'params':[f"token:{self.token}", [url]]})
        return jsonreq

    @add_download
    def add_torrent(self, torrent):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.addTorrent',
              	    'params':[f"token:{self.token}", torrent]})
        return jsonreq

    @get_status 
    def get_active(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.tellActive',
              	    'params':[f"token:{self.token}"]})
        return jsonreq

    @get_status
    def get_waiting(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.tellWaiting',
              	    'params':[f"token:{self.token}", 0, 5]})
        return jsonreq

    @get_status
    def get_stopped(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.tellStopped',
              	    'params':[f"token:{self.token}", 0, 5]})
        return jsonreq
    
    #获取等待中的项，通过status筛选，默认为暂停的项
    def get_waiting_by_status(self, status = 'paused'):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    				    'method':'aria2.tellWaiting',
                      	    'params':[f"token:{self.token}", 0, 5]})
        res = requests.post(self.aira2_url, jsonreq)
        temp_results = json.loads(res.content.decode("utf-8"))['result']
        results = []
        for result in temp_results:
            if not (result['status'] == status):
                continue
            title = result['files'][0]['path']
            des_name = result['dir'].replace("\\", '/')
            title = title.replace(des_name, '')
            if (os.path.dirname(title) == '/') or (os.path.dirname(title) == ''):
                title = os.path.basename(title)
            else:
                title = os.path.dirname(title)[1 :]
            results.append({"gid": result["gid"], "title": title, "downloadSpeed": 10**(-6) * int(result["downloadSpeed"]),
                            "downloadProgress": (10000 * int(result["completedLength"]) // max(int(result["totalLength"]), 1)) / 100})
        return results

    def remove_download_stopped(self, gid):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.removeDownloadResult',
              	    'params':[f"token:{self.token}", gid]})
        requests.post(self.aira2_url, jsonreq)
    
    def remove_download(self, gid):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.forceRemove',
              	    'params':[f"token:{self.token}", gid]})
        requests.post(self.aira2_url, jsonreq)

    def pause_download(self, gid):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.forcePause',
              	    'params':[f"token:{self.token}", gid]})
        requests.post(self.aira2_url, jsonreq)

    def pause_all_download(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.forcePauseAll',
              	    'params':[f"token:{self.token}"]})
        requests.post(self.aira2_url, jsonreq)
    
    def unpause_download(self, gid):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.unpause',
              	    'params':[f"token:{self.token}", gid]})
        requests.post(self.aira2_url, jsonreq)

    def unpause_all_download(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.unpauseAll',
              	    'params':[f"token:{self.token}"]})
        requests.post(self.aira2_url, jsonreq)
    
    def remove_all_download_stopped(self):
        jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
	    			'method':'aria2.purgeDownloadResult',
              	    'params':[f"token:{self.token}"]})
        requests.post(self.aira2_url, jsonreq)