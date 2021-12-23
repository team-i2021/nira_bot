# coding: utf-8

#沢山のインポート
import discord
from discord import message
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.ext.commands.core import command
from discord.utils import get
from os import getenv
import sys

from util import n_fc
import json
import os
import requests
from cogs import ping as cogs_ping
from cogs import debug as cogs_debug

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
print("Imported")



print("Logged")
##### BOTの設定 #####
intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix="n!", intents=intents, help_command=None)
print("bot setted")
#じしゃく
bot.load_extension("jishaku")


#意味あるのかしらんけどjishakuのヘルプコマンド削除
bot.remove_command("help")

#設定読み込み
if os.path.isfile(f'{sys.path[0]}/setting.json') == False:
    exit()
setting = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
home_dir = sys.path[0]
token = setting["tokens"]["nira_bot"]
main_channel = setting["main_channel"]
n_fc.py_admin.append(int(setting["py_admin"]))

#loggingの設定
import logging
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{home_dir}/nira.log', level=logging.INFO)

#オーナー設定
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner

print("all setting loaded")

#cogのロード
try:
    cogs_dir = home_dir + "/cogs"
    cogs_num = len([name for name in os.listdir(cogs_dir) if os.path.isfile(os.path.join(cogs_dir, name))])+1
    cogs_list = os.listdir(cogs_dir)
    for i in range(cogs_num):
        if cogs_list[i] == "__pycache__":
            continue
        bot.load_extension(f"cogs.{cogs_list[i][:-3]}")
except BaseException as err:
    print(err)
    main_content = {
        "username": "エラーが発生しました",
        "content": f"BOTを起動時にエラーが発生しました。Cogの読み込みエラーです。\n```{err}```\nサービスは終了します。"
    }
    requests.post(main_channel, main_content)
    exit()
print("cog loading")



@bot.event
async def on_ready():
    bot.add_application_command(ping)
    bot.add_application_command(cog)
    bot.add_application_command(func)
    await bot.change_presence(activity=discord.Game(name="起動中...", type=1), status=discord.Status.idle)
    func_error_count = 0
    nira_f_num = len(os.listdir(home_dir))
    system_list = os.listdir(home_dir)
    logging.info((nira_f_num,system_list))
    for i in range(nira_f_num):
        logging.info(f"StartProcess:{system_list[i]}")
        if system_list[i][-5:] != ".nira":
            logging.info(f"Skip:{system_list[i]}")
            continue
        try:
            cog_name = system_list[i][:-5]
            with open(f'{home_dir}/{system_list[i]}', 'rb') as f:
                exec(f"n_fc.{cog_name} = pickle.load(f)")
            logging.info(f"変数[{system_list[i]}]のファイル読み込みに成功しました。")
            exec(f"logging.info(n_fc.{cog_name})")
        except BaseException as err:
            logging.info(f"変数[{system_list[i]}]のファイル読み込みに失敗しました。\n{err}")
            func_error_count = 1
    if func_error_count > 0:
        main_content = {
            "username": "エラーが発生しました",
            "content": f"BOTを起動時にエラーが発生しました。変数の読み込みエラーです。\nlogを確認してください。"
        }
        requests.post(main_channel, main_content)
    await bot.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1), status=discord.Status.online)
    logging.info('初期セットアップ終了')
    logging.info("Ready!")

print("func loaded")

@bot.slash_command(description="サーバーとのレスポンスを表示します。")
async def ping(ctx: commands.Context, address: str = None):
    await cogs_ping.base_ping(bot, ctx, address)
    return

@bot.slash_command()
async def cog(ctx: commands.Context, command: str = None, name: str = None):
    await cogs_debug.base_cog(bot, ctx, command, name)
    return

@bot.slash_command()
async def func(ctx: commands.Context, name: str = None):
    if ctx.author.id not in n_fc.py_admin:
        await ctx.respond("discordBotの管理者権限が必要です。")
    elif ctx.author.id in n_fc.py_admin:
        await ctx.respond(f"ファイル一覧\n```{os.listdir(home_dir)}```", ephemeral = True)

# BOT起動
print("run")
bot.run(token)
print("exit")
