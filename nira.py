# 沢山のインポート
import asyncio
import json
import logging
import os
import sys
import traceback
import time

import nextcord

from motor import motor_asyncio

from util import n_fc, database
from util.nira import NIRA

sys.setrecursionlimit(10000)  # エラー回避
print("モジュールインポート完了")

import onami

# 設定読み込み
if os.path.isfile(f'{sys.path[0]}/setting.json') == False:
    print("""BOTの設定ファイルが見つかりませんでした。
「nira.py」があるフォルダに「setting.json」をおいてください。
「setting_temp.json」というテンプレートがありますのでそちらを参考にしてください。

または、「setup.py」を実行して、画面の指示通りにしてください。""", file=sys.stderr)
    os._exit(0)

HOME = os.path.dirname(os.path.abspath(__file__))
SETTING = json.load(open(f'{sys.path[0]}/setting.json', 'r'))


n_fc.GUILD_IDS = SETTING["guild_ids"]
n_fc.py_admin = SETTING["py_admin"]
UNLOAD_COGS = SETTING["unload_cogs"]
LOAD_COGS = SETTING["load_cogs"]
DEBUG = False

if len(sys.argv) > 1 and sys.argv[1] == "-d":
    DEBUG = True
    print(f"NIRA Bot Debug Mode\nThe following will be loaded... :{LOAD_COGS}")


##### データベースの設定 #####
CLIENT = database.openClient()
_MONGO_CLIENT = motor_asyncio.AsyncIOMotorClient(SETTING["database_url"])


# for i in range(1, 4):
#     print(f"データベース接続チェック {i}/3...")
#     result = requests.post(f"{CLIENT.url}/auth", json={"password": CLIENT.password})
#     if result.status_code != 200:
#         if i <= 2: print(f"データベースに接続できませんでした。\nステータスコード: {result.status_code}");
#         else: print("データベースに接続できませんでした。\nプログラムを終了します。"); os._exit(0)
#     else:
#         if result.json()["status"] == "success": print("データベースに接続できました。"); break
#         else: print("データベースのパスワードが違います。\nプログラムを終了します。"); os._exit(0)
#     time.sleep(1)


##### BOTの設定 #####
intents = nextcord.Intents.all() # 全部のインテントが有効になる
intents.typing = False # 重くなる可能性があるのでTypingを無効化
intents.presences = False # 未認証なのでPresence Intentは無効化
intents.members = True # Members Intentを有効化
intents.message_content = True # Message Content Intentを有効化

bot = NIRA(
    command_prefix=SETTING["prefix"],
    intents=intents,
    help_command=None,
    activity=nextcord.Game(name="Connecting...", type=1),
    status=nextcord.Status.dnd,
    debug=DEBUG,
    token=SETTING["tokens"]["nira_bot"],
    client=CLIENT, # http_db
    mongo=_MONGO_CLIENT, # mongo_db
    database_name=SETTING["database_name"],
    shard_id=SETTING["shard_id"],
    shard_count=SETTING["shard_count"],
    settings=SETTING,
)

bot.load_extension("onami")

print("BOTの設定完了")


##### loggingの設定 #####

FORMATTER = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=FORMATTER,
    filename=f'{sys.path[0]}/nira.log',
    level=logging.INFO,
)

print("Logging設定完了")



@bot.event
async def on_ready():
    if not bot.debug:
        await bot.change_presence(activity=nextcord.Game(name=f"{bot.command_prefix}help | にらゲー", type=1), status=nextcord.Status.online)
    else:
        await bot.change_presence(activity=nextcord.Game(name=f"{bot.command_prefix} | にらゲー開発", type=1), status=nextcord.Status.dnd)

    print("Welcome to nira-bot!")
    print(f"""\
USER: {bot.user.name}#{bot.user.discriminator}
ID: {bot.user.id}
COGS: {[dict(bot.cogs)[i].qualified_name for i in dict(bot.cogs).keys()]}
COMMANDS: {[i.name for i in list(bot.commands)]}
""")


# 暫定: 元のエラーハンドラが反応して標準エラーにスタックトレースを出力してしまうので
#       bot.event で上書きして強制的に消えてもらう (nextcord が対応したら削除する)
async def on_application_command_error(interaction, exception):
    pass


# 非デバッグモードでのみイベント登録する
if not bot.debug:
    bot.event(on_application_command_error)

# load extensions
cogs_dir = HOME + "/cogs"
cogs_num = len(os.listdir(cogs_dir))
cogs_list = os.listdir(cogs_dir)
if bot.debug:
    cogs_num = len(LOAD_COGS)
    cogs_list = LOAD_COGS
for i in range(cogs_num):
    try:
        if cogs_list[i][-3:] != ".py" or cogs_list[i] == "__pycache__" or cogs_list[i] == "not_ready.py" or cogs_list[i] in UNLOAD_COGS:
            continue
        bot.load_extension(f"cogs.{cogs_list[i][:-3]}")
    except Exception as err:
        print("Cog読み込み失敗:", cogs_list[i], file=sys.stderr)
        traceback.print_exc()
        logging.error(f"Cog読み込み失敗: {cogs_list[i]}", exc_info=True)
        continue
print("Cogの読み込み終了")


def main():
    # BOT起動
    print("BOT起動開始...")
    bot.run()
    print("BOT終了")


if __name__ == "__main__":
    main()
