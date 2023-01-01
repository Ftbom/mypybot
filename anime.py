import requests
import urllib.parse

def trace_moe(url: str):
    results = requests.get("https://api.trace.moe/search?url={}"
        .format(urllib.parse.quote_plus(url))).json()
    if (results['error'] != ''):
        return {'error': results['error']}
    result = results["result"][0]
    anilist_id = result['anilist']
    #从anilist获取信息
    result['info'] = anilist_info(int(anilist_id))
    result['anilist'] = f'https://anilist.co/anime/{result["anilist"]}'
    #计算时间
    result['from'] = f'{int(result["from"] // 60)}m{int(result["from"] % 60)}s'
    result['to'] = f'{int(result["to"] // 60)}m{int(result["to"] % 60)}s'
    #{'info': {'cover':, 'native_name':, 'romaji_name':}, 'anilist':, 'filename':, 
    #'episode':, 'from':, 'to':, 'similarity':, 'video':, 'image': ''}
    return result

def anilist_info(id: int):
    base_url = 'https://graphql.anilist.co'
    query = '''
    query ($id: Int) { # Define which variables will be used in the query (id)
        Media (id: $id, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
            coverImage {large}
            title {
                romaji
                native
            }
        }
    }
    '''
    variables = {'id': id}
    result = requests.post(base_url, json={'query': query, 'variables': variables}).json()
    return {'cover': result['data']['Media']['coverImage']['large'], 'native_name': result['data']['Media']['title']['native'], 'romaji_name': result['data']['Media']['title']['romaji']}

def waifu_pics(type: str, category: str):
    types = ['sfw', 'nsfw']
    categories = {}
    categories['sfw'] = ['waifu', 'neko', 'shinobu', 'megumin', 'bully',
        'cuddle', 'cry', 'hug', 'awoo', 'kiss', 'lick', 'pat', 'smug',
        'bonk', 'yeet', 'blush', 'smile', 'wave', 'highfive', 'handhold',
        'nom', 'bite', 'glomp', 'slap', 'kill', 'kick', 'happy', 'wink',
        'poke', 'dance', 'cringe']
    categories['nsfw'] = ['waifu', 'neko', 'trap', 'blowjob']
    #判断类别和类型
    if not (type in types):
        return {'error': '类型错误'}
    if not (category in categories[type]):
        return {'error': '类别错误'}
    return requests.get(f'https://api.waifu.pics/{type}/{category}').json()