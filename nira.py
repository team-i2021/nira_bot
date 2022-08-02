# 沢山のインポート
import asyncio
import datetime
import json
import logging
import os
import pickle
import pip
import re
import sys
import traceback

import nextcord
import websockets
from nextcord.ext import commands
from nextcord import Interaction

from util import n_fc, database
# from util import database
from cogs import debug as cogs_debug, server_status, rolepanel, pollpanel

sys.setrecursionlimit(10000)  # エラー回避
print("モジュールインポート完了")

# 設定読み込み
if os.path.isfile(f'{sys.path[0]}/setting.json') == False:
    print("""BOTの設定ファイルが見つかりませんでした。
「nira.py」があるフォルダに「setting.json」をおいてください。
「setting_temp.json」というテンプレートがありますのでそちらを参考にしてください。

または、「setup.py」を実行して、画面の指示通りにしてください。""", file=sys.stderr)
    os._exit(0)

HOME = os.path.dirname(os.path.abspath(__file__))
SETTING = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
TOKEN = SETTING["tokens"]["nira_bot"]
PREFIX = SETTING["prefix"]
n_fc.GUILD_IDS = SETTING["guild_ids"]
n_fc.py_admin = SETTING["py_admin"]
UNLOAD_COGS = SETTING["unload_cogs"]
LOAD_COGS = SETTING["load_cogs"]
DEBUG = False
if len(sys.argv) > 1 and sys.argv[1] == "-d":
    DEBUG = True
    print(f"NIRA Bot Debug Mode\nThe following will be loaded... :{LOAD_COGS}")

##### BOTの設定 #####
intents = nextcord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.presences = False  # Presence Intentだよ
intents.members = True  # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
bot.remove_command("help")  # 意味あるのかしらんけどjishakuのヘルプコマンド削除
bot.load_extension("jishaku")

# データベースの設定
CLIENT = database.openClient()

# オーナー設定
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner
print("BOTの設定完了")


#DBS = database.openSheet()

# loggingの設定
FORMATTER = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=FORMATTER,
    filename=f'{sys.path[0]}/nira.log',
    level=logging.INFO,
)

print("外部設定完了")


# async def ws(websocket, path):
#    async for message in websocket:
#        try:
#            if message == "guilds":
#                await websocket.send(str(len(bot.guilds)))
#            elif message == "users":
#                await websocket.send(str(len(bot.users)))
#            elif message == "voice_clients":
#                await websocket.send(str(len(bot.voice_clients)))
#            elif message[:7] == "captcha":
#                user, guild = [int(i) for i in message[8:].split(" ",1)]
#                value = readValue(DBS, "B6")
#                role = value[guild]
#                Guild = await bot.fetch_guild(guild)
#                Member = await Guild.fetch_member(user)
#                await Member.add_roles(role)
#        except BaseException as err:
#            await websocket.send(f"An error has occured:{err}")
#
# async def ws_main(port):
#    logging.info("Websocket....")
#    async with websockets.serve(ws, "0.0.0.0", int(port)):
#        await asyncio.Future()


@bot.event
async def on_ready():
    print("起動後処理を開始...")
    await bot.change_presence(activity=nextcord.Game(name="起動中...(1/2)", type=1), status=nextcord.Status.idle)
    if os.path.exists(f'{sys.path[0]}/PersistentViews.nira'):
        with open(f'{sys.path[0]}/PersistentViews.nira', 'rb') as f:
            rolepanel.PersistentViews = pickle.load(f)
        for i in rolepanel.PersistentViews:
            bot.add_view(rolepanel.RolePanelView(i))

    if os.path.exists(f'{sys.path[0]}/PollViews.nira'):
        with open(f'{sys.path[0]}/PollViews.nira', 'rb') as f:
            pollpanel.PollViews = pickle.load(f)
        for i in pollpanel.PollViews:
            bot.add_view(pollpanel.PollPanelView(i))

    # asyncio.new_event_loop().run_in_executor(None, bottomup.MessagePin, bot)
    # asyncio.ensure_future(bottomup.MessagePin(bot))

    await bot.change_presence(activity=nextcord.Game(name="起動中...(2/2)", type=1), status=nextcord.Status.idle)
    print("ユーザー情報読み込み中")
    for i in bot.guilds:
        if i.id not in n_fc.role_keeper:
            n_fc.role_keeper[i.id] = {"rk": 0}
        for j in i.members:
            n_fc.role_keeper[i.id][j.id] = [
                k.id for k in j.roles if k.name != "@everyone"]
    if DEBUG:
        print(n_fc.role_keeper)
    cogs_debug.save()

    print("ユーザー情報読み込み完了")

    if not DEBUG:
        await bot.change_presence(activity=nextcord.Game(name=f"{PREFIX}help | にらゲー", type=1), status=nextcord.Status.online)
    else:
        await bot.change_presence(activity=nextcord.Game(name=f"{PREFIX} | にらゲー開発", type=1), status=nextcord.Status.dnd)

    print("Welcome to nira-bot!")
    print(f"""\
USER: {bot.user.name}#{bot.user.discriminator}
ID: {bot.user.id}
COGS: {[dict(bot.cogs)[i].qualified_name for i in dict(bot.cogs).keys()]}
COMMANDS: {[i.name for i in list(bot.commands)]}
""")

# 機能しなかったときの保険↓
#loop = asyncio.get_event_loop()
#loop.run_in_executor(None, server_status.ss_force, bot, messs)

# @bot.slash_command(name="ping", description="サーバーとのレスポンスを表示します。")
# async def ping(interaction: Interaction, address: str = None):
#     await cogs_ping.base_ping(bot, interaction, address)
#     return



# 変数読み込み
func_error_count = 0
for i in range(len(n_fc.save_list)):
    logging.info(f"Start:{n_fc.save_list[i]}")
    try:
        if os.path.isfile(f"{HOME}/{n_fc.save_list[i]}.nira"):
            with open(f'{HOME}/{n_fc.save_list[i]}.nira', 'rb') as f:
                exec(f"n_fc.{n_fc.save_list[i]} = pickle.load(f)")
            logging.info(f"変数[{n_fc.save_list[i]}]のファイル読み込みに成功しました。")
            if n_fc.save_list[i] == "notify_token.nira":
                logging.info("LINE NotifyのTOKENのため、表示はされません。")
            else:
                if DEBUG:
                    exec(f"logging.info(n_fc.{n_fc.save_list[i]})")
        else:
            logging.info("ファイルが存在しません。")
            with open(f"{HOME}/{n_fc.save_list[i]}.nira", "wb") as f:
                pickle.dump({}, f)
    except Exception as err:
        logging.info(
            f"変数[{n_fc.save_list[i]}]のファイル読み込みに失敗しました。\n{err}\n{traceback.format_exc()}")
        print("変数の読み込み時にエラーが発生しました。ログを確認して、再度やり直してください。", file=sys.stderr)
        os._exit(0)
print("変数の読み込み完了")

# load extensions
cogs_dir = HOME + "/cogs"
cogs_num = len(os.listdir(cogs_dir))
cogs_list = os.listdir(cogs_dir)
if DEBUG:
    cogs_num = len(LOAD_COGS)
    cogs_list = LOAD_COGS
for i in range(cogs_num):
    try:
        if cogs_list[i][-3:] != ".py" or cogs_list[i] == "__pycache__" or cogs_list[i] == "not_ready.py" or cogs_list[i] in UNLOAD_COGS:
            continue
        bot.load_extension(f"cogs.{cogs_list[i][:-3]}", extras={"client": CLIENT})
    except Exception as err:
        print("Cog読み込み失敗:", cogs_list[i], file=sys.stderr)
        traceback.print_exc()
        logging.error(f"Cog読み込み失敗: {cogs_list[i]}", exc_info=True)
        continue
print("Cogの読み込み終了")


def main():
    # BOT起動
    print("BOT起動開始...")
    bot.run(TOKEN)
    print("BOT終了")


if __name__ == "__main__":
    main()
