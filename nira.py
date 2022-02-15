# coding: utf-8

#沢山のインポート

import nextcord
from nextcord import message
from nextcord.ext import commands
from nextcord.ext.commands.bot import Bot
from nextcord.ext.commands.core import command
from nextcord.utils import get
from os import getenv
import sys
from nextcord import Interaction, SlashOption, ChannelType
from cogs.not_ready import not_ready
from concurrent.futures import ThreadPoolExecutor
from util import n_fc, admin_check, web_api, server_check
import json
import os
import requests
from cogs import ping as cogs_ping
from cogs import debug as cogs_debug
from cogs import server_status
from nextcord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
import traceback
import datetime
import asyncio
print("モジュールインポート完了")



##### BOTの設定 #####
intents = nextcord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.presences = True # Presence Intentだよ
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix="n!", intents=intents, help_command=None)
bot.remove_command("help") #意味あるのかしらんけどjishakuのヘルプコマンド削除
print("BOTの設定完了")
#じしゃく
# bot.add_cog("jishaku")





#設定読み込み
if os.path.isfile(f'{sys.path[0]}/setting.json') == False:
    exit()

setting = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
home_dir = os.path.dirname(__file__)
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

print("Loggingの設定完了")
#オーナー設定
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner

print("全設定完了")

bot.load_extension("cogs.not_ready")

print("Cog:not_ready読み込み完了")

@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Game(name="起動中... 1/3", type=1), status=nextcord.Status.idle)
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
            if system_list[i] == "notify_token.nira":
                logging.info("LINE NotifyのTOKENのため、表示はされません。")
            else:
                exec(f"logging.info(n_fc.{cog_name})")
        except BaseException as err:
            logging.info(f"変数[{system_list[i]}]のファイル読み込みに失敗しました。\n{err}")
            func_error_count = 1
    if func_error_count > 0:
        main_content = {
            "username": "エラーが発生しました",
            "content": f"BOTを起動時にエラーが発生しました。変数の読み込みエラーです。\nエラーコード:`{func_error_count}`\nlogを確認してください。"
        }
        requests.post(main_channel, main_content)
    print("変数の読み込み完了")
    await bot.change_presence(activity=nextcord.Game(name="起動中... 2/3", type=1), status=nextcord.Status.idle)
    # bot.add_application_command(ping)
    # bot.add_application_command(cog)
    # bot.add_application_command(func)
    # bot.add_application_command(reload)
    bot.add_application_command(line)
    bot.add_application_command(line_del)
    #cogのロード
    bot.unload_extension("cogs.not_ready")
    print("Cogの読み込み完了")
    await bot.change_presence(activity=nextcord.Game(name="起動中... 3/3", type=1), status=nextcord.Status.idle)
    for i in range(len(list(n_fc.force_ss_list.keys()))):
        print(list(n_fc.force_ss_list.keys())[i])
        try:
            print(f"復元対象チャンネルID:{n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][0]}")
            ch_obj = await bot.fetch_channel(n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][0])
            print(f"復元対象チャンネル名:{ch_obj.name}/復元対象メッセージID:{n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][1]}")
            messs = await ch_obj.fetch_message(n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][1])
            print(messs.author.id)
            await messs.edit(content=f"reloading now...\nPlease wait...\n```{datetime.datetime.now()}```", embed=None)
            print(f"復元対象メッセージコンテンツ:```{messs.content}```")
            n_fc.pid_ss[list(n_fc.force_ss_list.keys())[i]] = (asyncio.ensure_future(server_status.ss_force(bot, messs)),messs)
            print(f"復元完了")
        except BaseException as err:
            print(err, traceback.format_exc())
            main_content = {
                "username": "エラーが発生しました",
                "content": f"BOTを起動時にエラーが発生しました。タスクの復元中のエラーです。\n```{traceback.format_exc()}```\n無視して続行します。"
            }
            requests.post(main_channel, main_content)
            continue
    print("AutoSSのタスク復元完了")
    await bot.change_presence(activity=nextcord.Game(name="n!help | にらゲー", type=1), status=nextcord.Status.online)
    print("Welcome to nira-bot")

#機能しなかったときの保険↓
#loop = asyncio.get_event_loop()
#loop.run_in_executor(None, server_status.ss_force, bot, messs)

# @bot.slash_command(name="ping", description="サーバーとのレスポンスを表示します。")
# async def ping(interaction: Interaction, address: str = None):
#     await cogs_ping.base_ping(bot, interaction, address)
#     return

@bot.slash_command(description="AutoSSを更新します。")
async def reload(interaction: Interaction):
    if interaction.guild.id not in n_fc.pid_ss:
        await interaction.response.send_message(f"{interaction.guild.name}では、AutoSSは実行されていません。", ephemeral = True)
        return
    else:
        status_message = n_fc.pid_ss[interaction.guild.id][1]
        n_fc.pid_ss[interaction.guild.id] = (asyncio.ensure_future(server_status.ss_force(bot, status_message)),status_message)
        await interaction.response.send_message("リロードしました。", ephemeral = True)
        return

@bot.slash_command(description="LINE Notifyのトークンを設定します。")
async def line(interaction: Interaction, token: str):
    if token == "":
        await interaction.response.send_message("トークンは必須です。", ephemeral=True)
        return
    if admin_check.admin_check(interaction.guild, interaction.user) == False:
        await interaction.response.send_message("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
    else:
        token_result = web_api.line_token_check(token)
        if token_result[0] == False:
            await interaction.response.send_message(f"そのトークンは無効なようです。\n```{token_result[1]}```", ephemeral = True)
            return
        if interaction.guild.id not in n_fc.notify_token:
            n_fc.notify_token[interaction.guild.id] = {interaction.channel.id: token}
        else:
            n_fc.notify_token[interaction.guild.id][interaction.channel.id] = token
        with open('/home/nattyantv/nira_bot_rewrite/notify_token.nira', 'wb') as f:
            pickle.dump(n_fc.notify_token, f)
        await interaction.response.send_message(f"{interaction.guild.name}/{interaction.channel.name}で`{token}`を保存します。\nトークンが他のユーザーに見られないようにしてください。", ephemeral = True)

@bot.slash_command(description="LINE Notifyのトークンを削除します。")
async def line_del(interaction: Interaction):
    if admin_check.admin_check(interaction.guild, interaction.user) == False:
        await interaction.response.send_message("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
    else:
        if interaction.guild.id not in n_fc.notify_token:
            await interaction.response.send_message(f"{interaction.guild.name}では、LINEトークンが設定されていません。", ephemeral = True)
            return
        if interaction.channel.id not in n_fc.notify_token[interaction.guild.id]:
            await interaction.response.send_message(f"{interaction.channel.name}では、LINEトークンが設定されていません。", ephemeral = True)
            return
        del n_fc.notify_token[interaction.guild.id][interaction.channel.id]
        with open('/home/nattyantv/nira_bot_rewrite/notify_token.nira', 'wb') as f:
            pickle.dump(n_fc.notify_token, f)
        await interaction.response.send_message(f"{interaction.channel.name}でのLINEトークンを削除しました。", ephemeral = True)


def main():
    try:
        cogs_dir = home_dir + "/cogs"
        cogs_num = len(os.listdir(cogs_dir))
        cogs_list = os.listdir(cogs_dir)
        for i in range(cogs_num):
            if cogs_list[i][-3:] != ".py" or cogs_list[i] == "__pycache__" or cogs_list[i] == "not_ready.py":
                continue
            bot.load_extension(f"cogs.{cogs_list[i][:-3]}")
    except BaseException as err:
        print(err)
        main_content = {
            "username": "エラーが発生しました",
            "content": f"BOTを起動時にエラーが発生しました。Cogの読み込みエラーです。\n```{err}```\nサービスは終了します。"
        }
        requests.post(main_channel, main_content)
        sys.exit(1)
    
    # BOT起動
    print("BOT起動開始...")
    bot.run(token)
    print("BOT終了")

if __name__ == "__main__":
    main()