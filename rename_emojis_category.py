import os
import requests
import time
from dotenv import load_dotenv
import requests
import sys

load_dotenv()

# MisskeyのインスタンスURLとアクセストークンを設定
instance_url = os.environ.get('MISSKEY_INSTANCE_URL')
access_token = os.environ.get('MISSKEY_ACCESS_TOKEN')

def get_emoji_list(since_id=None, until_id=None):
    url = f'{instance_url}/api/admin/emoji/list'
    payload = {
        'i': access_token,
        'limit': 100
    }
    if since_id:
        payload['sinceId'] = since_id
    if until_id:
        payload['untilId'] = until_id

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f'エラー発生: {e}')
        return None

def fetch_all_emojis():
    emojis = []
    until_id = None
    while True:
        emoji_list = get_emoji_list(until_id=until_id)
        if not emoji_list:
            break  # 絵文字がない場合はループ終了

        emojis.extend(emoji_list)  # 絵文字をリストに追加

        until_id = emoji_list[-1]['id']  # 次のリクエストのために最後の絵文字のIDを設定
        time.sleep(1)  # レート制限を考慮して待ち時間を設定
    return emojis


# カテゴリごとに絵文字を整理する関数
def organize_emojis_by_category(emojis):
    organized_emojis = {}
    for emoji in emojis:
        category = emoji['category']
        if category not in organized_emojis:
            organized_emojis[category] = []
        organized_emojis[category].append(emoji)
    return organized_emojis


# 特定のカテゴリの絵文字を新しいカテゴリ名に更新する関数
def update_emoji_category(emojis, old_category, new_category, dryrun):
    for emoji in emojis:
        if emoji['category'] == old_category:
            if dryrun:
                print(f"DRYRUN: 絵文字 {emoji['name']} はカテゴリ '{old_category}' から '{new_category}' に更新されます。")
            else:
                emoji['category'] = new_category
                update_emoji(emoji)


# 絵文字を更新するためのリクエストを送る関数
def update_emoji(emoji):
    url = f'{instance_url}/api/admin/emoji/update'
    payload = {
        'i': access_token
    } | emoji 

    payload['category'] = new_category
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"絵文字 {emoji['name']} を更新しました。")
    except requests.RequestException as e:
      print('絵文字 ' + emoji['name'] + ' の更新中にエラー発生: ' + str(e))

# コマンドラインからパラメータを受け取る
if len(sys.argv) < 3 or len(sys.argv) > 4:
    print("使い方: python rename_emojis_category.py [旧カテゴリ名] [新カテゴリ名] [--dryrun]")
    sys.exit(1)

old_category = sys.argv[1]
new_category = sys.argv[2]
dryrun = len(sys.argv) == 4 and sys.argv[3] == '--dryrun'

# すべての絵文字を取得する
emoji_list = fetch_all_emojis()

# 特定のカテゴリの絵文字を新しいカテゴリ名に更新
update_emoji_category(emoji_list, old_category, new_category, dryrun)