# coding: utf-8

#沢山のインポート
import discord
from discord import message
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.utils import get
from os import getenv
import sys, re, asyncio, datetime, bot_token, util.server_check as server_check
from subprocess import PIPE
from util import n_fc, admin_check, eh
from discord_buttons_plugin import *
import json
import os
import requests

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle

#loggingの設定
import logging
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename='/home/nattyantv/nira.log', level=logging.INFO)

##### BOTの設定 #####
intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix="n!", intents=intents, help_command=None)
buttons = ButtonsClient(bot)

#じしゃく
bot.load_extension("jishaku")

#オーナー設定
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner

#意味あるのかしらんけどjishakuのヘルプコマンド削除
bot.remove_command("help")

#設定読み込み
setting = json.load(open('/home/nattyantv/nira_bot_rewrite/setting.json', 'r'))
home_dir = setting["home_dir"]
token = setting["tokens"]["nira_bot"]


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
    main_content = {
        "username": "エラーが発生しました",
        "content": f"BOTを起動時にエラーが発生しました。Cogの読み込みエラーです。\n```{err}```\nサービスは終了します。"
    }
    requests.post("https://discord.com/api/webhooks/918125489405714452/-NQMQMuuafLyoRAYNw-tBWKT1hsJRKcWjilYrZX1gPdce8en1FqgR1TK0p-Kn02b1Aom", main_content)
    exit()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="起動中...", type=1), status=discord.Status.idle)
    func_error_count = 0
    try:
        with open(f'{home_dir}/steam_server_list.nira', 'rb') as f:
            n_fc.steam_server_list = pickle.load(f)
        logging.info("変数[steam_server_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.steam_server_list)
    except BaseException as err:
        logging.info(f"変数[steam_server_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 1
    try:
        with open(f'{home_dir}/reaction_bool_list.nira', 'rb') as f:
            n_fc.reaction_bool_list = pickle.load(f)
        logging.info("変数[reaction_bool_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.reaction_bool_list)
    except BaseException as err:
        logging.info(f"変数[reaction_bool_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 2
    try:
        with open(f'{home_dir}/welcome_id_list.nira', 'rb') as f:
            n_fc.welcome_id_list = pickle.load(f)
        logging.info("変数[welcome_id_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.welcome_id_list)
    except BaseException as err:
        logging.info(f"変数[welcome_id_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 4
    try:
        with open(f'{home_dir}/ex_reaction_list.nira', 'rb') as f:
            n_fc.ex_reaction_list = pickle.load(f)
        logging.info("変数[ex_reaction_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.ex_reaction_list)
    except BaseException as err:
        logging.info(f"変数[ex_reaction_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 8
    try:
        with open(f'{home_dir}/srtr_bool_list.nira', 'rb') as f:
            n_fc.srtr_bool_list = pickle.load(f)
        logging.info("変数[srtr_bool_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.srtr_bool_list)
    except BaseException as err:
        logging.info(f"変数[srtr_bool_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 16
    try:
        with open(f'{home_dir}/all_reaction_list.nira', 'rb') as f:
            n_fc.all_reaction_list = pickle.load(f)
        logging.info("変数[all_reaction_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.all_reaction_list)
    except BaseException as err:
        logging.info(f"変数[all_reaction_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 32
    try:
        with open(f'{home_dir}/bump_list.nira', 'rb') as f:
            n_fc.bump_list = pickle.load(f)
        logging.info("変数[bump_list]のファイル読み込みに成功しました。")
        logging.info(n_fc.bump_list)
    except BaseException as err:
        logging.info(f"変数[bump_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
        func_error_count = func_error_count + 64
    if func_error_count > 0:
        main_content = {
            "username": "エラーが発生しました",
            "content": f"BOTを起動時にエラーが発生しました。変数の読み込みエラーです。\n`エラーコード:{func_error_count}`\nなおそのまま実行することは推奨されません。"
        }
        requests.post("https://discord.com/api/webhooks/918125489405714452/-NQMQMuuafLyoRAYNw-tBWKT1hsJRKcWjilYrZX1gPdce8en1FqgR1TK0p-Kn02b1Aom", main_content)
    await bot.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1), status=discord.Status.online)
    logging.info('初期セットアップ終了')
    logging.info("Ready!")

# BOT起動

bot.run(token)