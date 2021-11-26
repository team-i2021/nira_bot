# coding: utf-8
import discord
from discord import message
from discord.ext import commands
from discord.ext.commands.bot import Bot
from os import getenv
import sys
import os
import re
import random
import a2s
import asyncio
import datetime
import bot_token
from discord.utils import get
import math
import shutil
import help_command
import srtr
import server_check
import subprocess
from subprocess import PIPE
import chardet
import urllib.request
import music
import web_api
import n_fc
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
from discord_buttons_plugin import *

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle


on_ali = ["1", "on", "On", "ON", "true", "True", "TRUE", "yes", "Yes", "YES"]
off_ali = ["0", "off", "Off", "OFF", "false", "False", "FALSE", "no", "No", "NO"]


# ユーザーが管理者権限を付与された「「「「「ロール」」」」」を所持しているか確認
def admin_check(guild, memb):
    role_list = []
    for role in memb.roles:
        role_list.append(role.id)
    for i in range(len(role_list)):
        role = get(guild.roles, id=role_list[i])
        if (role.permissions).administrator:
            return True
    return False

# エラーのembedを7文字で出せるようにする
def eh(err):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000)


##### BOTの設定 #####
intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix="n!", intents=intents)
buttons = ButtonsClient(bot)
bot.load_extension("jishaku")
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner


##### 通常反応 #####
@bot.listen()
async def on_message(message):
    # LINEでのメッセージ送信
    # 自分自身には反応しない
    if message.author.bot:
        return
    # しりとりブール
    if message.guild.id in n_fc.srtr_bool_list:
        if message.channel.id in n_fc.srtr_bool_list[message.guild.id]:
            await srtr.on_srtr(message, bot)
            return
    # 追加反応
    if message.guild.id in n_fc.ex_reaction_list:
        if n_fc.ex_reaction_list[message.guild.id]["value"] != 0:
            for i in range(n_fc.ex_reaction_list[message.guild.id]["value"]):
                if re.search(rf'{n_fc.ex_reaction_list[message.guild.id][f"{i+1}_tr"]}', message.content):
                    sended_mes = await message.reply(n_fc.ex_reaction_list[message.guild.id][f"{i+1}_re"])
                    return
    ###############################
    # 通常反応のブール値存在チェック #
    ###############################
    if message.guild.id not in n_fc.reaction_bool_list:
        n_fc.reaction_bool_list[message.guild.id] = {"all": 1, message.channel.id: 1}
        with open('reaction_bool_list.nira', 'wb') as f:
            pickle.dump(n_fc.reaction_bool_list, f)
    if message.channel.id not in n_fc.reaction_bool_list[message.guild.id]:
        n_fc.reaction_bool_list[message.guild.id][message.channel.id] = 1
        with open('reaction_bool_list.nira', 'wb') as f:
            pickle.dump(n_fc.reaction_bool_list, f)
    #########################################
    # 通常反応
    # 「n!nr [on/off]」で変更できます
    #########################################
    if n_fc.reaction_bool_list[message.guild.id]["all"] != 1:
        return
    if n_fc.reaction_bool_list[message.guild.id][message.channel.id] == 1:
        sended_mes = ""
        if re.search(r'(?:(。∀ ﾟ))', message.content):
            sended_mes = await message.reply("おっ、かわいいな")
        if re.search(r'(?:（´・ω・｀）)', message.content):
            sended_mes = await message.reply("かわいいですね...")
        if re.search(r'(?:草)', message.content):
            sended_mes = await message.reply("面白いなぁ（便乗）")
        if re.search(r'(?:https://www.nicovideo.jp)', message.content):
            sended_mes = await message.reply("にーっこにっこどうがっ？")
        if re.search(r'(?:https://www.youtube.com)', message.content):
            sended_mes = await message.reply("ようつべぇ？")
        if re.search(r'(?:https://twitter.com)', message.content):
            sended_mes = await message.reply("ついったあだあーわーい")
        if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
            if message.guild == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_zoku.mp4')
        if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
            sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/koikingu.jpg')
        if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
            if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
                if re.search(r'(?:水|みず|ミズ)', message.content):
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_water.jpg')
                else:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_sand.jpeg')
            elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_itou.png')
            elif re.search(r'(?:ごはん|飯|らいす|ライス|rice|Rice)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_rice.jpg')
            elif re.search(r'(?:枯|かれ|カレ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_kare.png')
            elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_fish.png')
            elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_dokusai.png')
            elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_seityou.jpeg')
            elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_nabe.jpg')
                sended_mes = await message.reply('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
            elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_sword.png')
            elif re.search(r'(?:あんど|and|アンド)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_and.png')
            elif re.search(r'(?:にらんど|ニランド|nirand|niland)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_land.png')
                sended_mes = await sended_mes.reply('https://sites.google.com/view/nirand/%E3%83%9B%E3%83%BC%E3%83%A0')
            elif re.search(r'(?:饅頭|まんじゅう|マンジュウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_manju.png')
            elif re.search(r'(?:レバ|れば)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/rebanira.jpg')
            elif re.search(r'(?:とり|トリ|bird|鳥)', message.content):
                rnd = random.randint(1, 2)
                if rnd == 1:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nirabird_a.png')
                elif rnd == 2:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nirabird_b.png')
            elif re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://twitter.com/DR36Hl04ZUwnEnJ')
            else:
                rnd = random.randint(1, 3)
                if rnd == 1:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_a.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_b.jpg')
                elif rnd == 3:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/nira_c.png')
        if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/tiramisu_a.png')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/tiramisu_b.png')
        if re.search(r'(?:ぴの|ピノ|pino)', message.content):
            rnd = random.randint(1, 3)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/pino_nm.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/pino_st.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/pino_cool.jpg')
        if re.search(r'(?:きつね|キツネ|狐)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 3)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/kitune_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/kitune_b.png')
            elif rnd == 3:
                sended_mes = await message.reply('https://twitter.com/rougitune')
        if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://www.youtube.com/IkumonTV')
        if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/apple.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://twitter.com/RINGOSANDAO')
        if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 4)
            else:
                rnd = random.randint(1, 2)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/sarmon_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/sarmon_b.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/sarmon_c.jpg')
            elif rnd == 4:
                sended_mes = await message.reply('https://twitter.com/Shake_Yuyu')
        if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
            await message.add_reaction("<:natsu:908565532268179477>")
        if re.search(r'(?:12pp|12PP)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/12pp.jpg')
        if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
                if rnd == 1:
                    sended_mes = await message.reply('https://twitter.com/namae_1216')
                elif rnd == 2:
                    sended_mes = await message.reply(':heart: by apple')
        if re.search(r'(?:みけ|ミケ|三毛)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/mike.mp4')
        if re.search(r'(?:あう)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/au.png')
        if re.search(r'(?:ろり|ロリ)', message.content):
            if re.search(r'(?:せろり|セロリ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/serori.jpg')
            else:
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/nira_bot/images/ri_par.png')
        if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 2
            if rnd == 1:
                sended_mes = await message.reply('毎晩10時が全盛期')
            elif rnd == 2:
                sended_mes = await message.reply('すごいひと')
        if re.search(r'(?:ｸｧ|きよわらい|きよ笑い|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)', message.content):
            sended_mes = await message.reply('ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww')
        if re.search(r'(?:ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B&oq=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B")
        if re.search(r'(?:かなしい|つらい|ぴえん|:pleading_face:|:cry:|:sob:|:weary:|:smiling_face_with_tear:|辛|悲しい|ピエン|泣く|泣きそう|いやだ|かわいそうに|可哀そうに)', message.content):
            sended_mes = await message.reply("https://nattyan-tv.github.io/nira_bot/images/kawaisou.png")
        if re.search(r'(?:あすか|アスカ|飛鳥)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/ribpggxcrmz74t6")
        if re.search(r'(?:しおりん)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/Aibell__game")
        if sended_mes != "":
            await sended_mes.add_reaction("<:trash:908565976407236608>")
            await asyncio.sleep(3)
            try:
                await sended_mes.remove_reaction("<:trash:908565976407236608>", bot.user)
                return
            except BaseException:
                return


##### 起動時のコード #####
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="起動中...", type=1), status=discord.Status.idle)
    try:
        with open('steam_server_list.nira', 'rb') as f:
            n_fc.steam_server_list = pickle.load(f)
        print("変数[steam_server_list]のファイル読み込みに成功しました。")
        print(n_fc.steam_server_list)
    except BaseException as err:
        print(f"変数[steam_server_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
    try:
        with open('reaction_bool_list.nira', 'rb') as f:
            n_fc.reaction_bool_list = pickle.load(f)
        print("変数[reaction_bool_list]のファイル読み込みに成功しました。")
        print(n_fc.reaction_bool_list)
    except BaseException as err:
        print(f"変数[reaction_bool_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
    try:
        with open('welcome_id_list.nira', 'rb') as f:
            n_fc.welcome_id_list = pickle.load(f)
        print("変数[welcome_id_list]のファイル読み込みに成功しました。")
        print(n_fc.welcome_id_list)
    except BaseException as err:
        print(f"変数[welcome_id_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
    try:
        with open('ex_reaction_list.nira', 'rb') as f:
            n_fc.ex_reaction_list = pickle.load(f)
        print("変数[ex_reaction_list]のファイル読み込みに成功しました。")
        print(n_fc.ex_reaction_list)
    except BaseException as err:
        print(f"変数[ex_reaction_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
    try:
        with open('srtr_bool_list.nira', 'rb') as f:
            n_fc.srtr_bool_list = pickle.load(f)
        print("変数[srtr_bool_list]のファイル読み込みに成功しました。")
        print(n_fc.srtr_bool_list)
    except BaseException as err:
        print(f"変数[srtr_bool_list]のファイル読み込みに失敗しましたが続行します。\n{err}")
    await bot.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1), status=discord.Status.online)
    print('初期セットアップ終了')
    print("Ready!")



##### コマンド類 #####
@bot.command()
async def create(ctx):
    if ctx.message.author.id in n_fc.py_admin:
        if ctx.message.content == "n!create":
            await ctx.message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
            return
        c_file_d = str((ctx.message.content).split(" ", 1)[1])
        try:
            with open(c_file_d, 'w'):
                pass
        except BaseException as err:
            await ctx.message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
            return
    else:
        await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))


@bot.command()
async def py_exec(ctx):
    if ctx.message.author.id in n_fc.py_admin:
        if ctx.message.content == "n!py_exec":
            await ctx.message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
            return
        e_file = str((ctx.message.content).split(" ", 1)[1])
        try:
            exec(open(e_file).read())
            return
        except BaseException as err:
            await ctx.message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
            return
    else:
        await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))


@bot.command()
async def read(ctx):
    if ctx.message.author.id not in n_fc.py_admin:
        await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
        return
    try:
        shutil.copyfile("nira.py", "nira_copy.txt")
        await ctx.message.reply('`nira.py（コピー）`', file=discord.File('nira_copy.txt'))
        os.remove('nira_copy.txt')
        return
    except BaseException as err:
        embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return


@bot.command()
async def restart(ctx):
    if ctx.message.author.id in n_fc.py_admin:
        await bot.change_presence(activity=discord.Game(name="再起動中...", type=1), status=discord.Status.dnd)
        restart_code = await ctx.message.reply("再起動準備中...")
        try:
            with open('steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            with open('reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
            with open('welcome_id_list.nira', 'wb') as f:
                pickle.dump(n_fc.welcome_id_list, f)
            with open('ex_reaction_list.nira', 'wb') as f:
                pickle.dump(n_fc.ex_reaction_list, f)
            with open('srtr_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.srtr_bool_list, f)
            await restart_code.edit(content="RESTART:`nira.py`\n再起動します")
            print("-----[n!restart]コマンドが実行されたため、再起動します。-----")
            os.execl(sys.executable, 'python3.7', "nira.py")
            return
        except BaseException as err:
            await ctx.message.reply(err)
            await bot.change_presence(activity=discord.Game(name="n!help", type=1), status=discord.Status.idle)
            return
    else:
        embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return


@bot.command()
async def exit(ctx):
    if ctx.message.author.id in n_fc.py_admin:
        await bot.change_presence(activity=discord.Game(name="終了中...", type=1), status=discord.Status.dnd)
        exit_code = await ctx.message.reply("終了準備中...")
        try:
            with open('steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            with open('reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
            with open('welcome_id_list.nira', 'wb') as f:
                pickle.dump(n_fc.welcome_id_list, f)
            with open('ex_reaction_list.nira', 'wb') as f:
                pickle.dump(n_fc.ex_reaction_list, f)
            with open('srtr_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.srtr_bool_list, f)
            await exit_code.edit(content="STOP:`nira.py`\n終了します")
            print("-----[n!exit]コマンドが実行されたため、終了します。-----")
            await bot.logout()
            exit()
            return
        except BaseException as err:
            await ctx.message.reply(err)
            await bot.change_presence(activity=discord.Game(name="n!help", type=1), status=discord.Status.idle)
            return
    else:
        embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return


@bot.command()
async def py(ctx):
    if ctx.message.author.id not in n_fc.py_admin:
        embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        await ctx.message.add_reaction("\U0000274C")
        return
    if ctx.message.content == "n!py":
        embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        await ctx.message.add_reaction("\U0000274C")
        return
    if ctx.message.content[:10] == "n!py await":
        if ctx.message.author.id not in n_fc.py_admin:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.repcly(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content == "n!py await":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
    mes = ctx.message.content[5:].splitlines()
    cmd_nm = len(mes)
    cmd_rt = []
    print(mes)
    for i in range(cmd_nm):
        if re.search(r'(?:await)', mes[i]):
            try:
                mes_py = mes[i].split(" ", 1)[1]
                cmd_rt.append(await eval(mes_py))
            except BaseException as err:
                await ctx.message.add_reaction("\U0000274C")
                embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                await ctx.message.reply(embed=embed)
                return
        else:
            try:
                exec(mes[i])
                cmd_rt.append("")
            except BaseException as err:
                await ctx.message.add_reaction("\U0000274C")
                embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                await ctx.message.reply(embed=embed)
                return
    await ctx.message.add_reaction("\U0001F197")
    return

@bot.command()
async def sh(ctx):
    if ctx.message.author.id not in n_fc.py_admin:
        embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        await ctx.message.add_reaction("\U0000274C")
        return
    else:
        if ctx.message.content == "n!sh":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        mes_sh = ctx.message.content[5:].splitlines()
        sh_nm = len(mes_sh)
        sh_rt = []
        print(mes_sh)
        for i in range(sh_nm):
            try:
                export = subprocess.run(f'{mes_sh[i]}', stdout=PIPE, stderr=PIPE, shell=True, text=True)
                sh_rt.append(export.stdout)
            except BaseException as err:
                await ctx.message.add_reaction("\U0000274C")
                embed = discord.Embed(title="Error", description=f"Shell error has occurred!\n・Pythonエラー```{err}```\n・スクリプトエラー```{export.stdout}```", color=0xff0000)
                await ctx.message.reply(embed=embed)
                return
        await ctx.message.add_reaction("\U0001F197")
        for i in range(len(sh_rt)):
            rt_sh = "\n".join(sh_rt)
        await ctx.message.reply(f"```{rt_sh}```")
        return


@bot.command()
async def save(ctx):
    if ctx.message.author.id in n_fc.py_admin:
        try:
            with open('steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            with open('reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
            with open('welcome_id_list.nira', 'wb') as f:
                pickle.dump(n_fc.welcome_id_list, f)
            with open('ex_reaction_list.nira', 'wb') as f:
                pickle.dump(n_fc.ex_reaction_list, f)
            with open('srtr_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.srtr_bool_list, f)
            await ctx.message.reply("Saved.")
        except BaseException as err:
            await ctx.message.reply(f"Error happend.\n{err}")
        return
    else:
        embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return

@bot.command()
async def ui(ctx):
    if admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
        if ctx.message.content[:8] == "n!ui set":
            try:
                set_id = int("".join(re.findall(r'[0-9]', ctx.message.content[9:])))
                n_fc.welcome_id_list[ctx.message.guild.id] = set_id
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(n_fc.welcome_id_list, f)
                channel = bot.get_channel(n_fc.welcome_id_list[ctx.message.guild.id])
                await channel.send("追加完了メッセージ\nこのメッセージが指定のチャンネルに送信されていれば完了です。")
                await ctx.message.reply("追加完了のメッセージを指定されたチャンネルに送信しました。\n送信されていない場合はにらBOTに適切な権限が与えられているかご確認ください。")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                return
        elif ctx.message.content == "n!ui del":
            try:
                if ctx.message.guild.id not in n_fc.reaction_bool_list:
                    seted_id = n_fc.welcome_id_list[ctx.message.guild.id]
                    del n_fc.welcome_id_list[ctx.message.guild.id]
                    with open('welcome_id_list.nira', 'wb') as f:
                        pickle.dump(n_fc.welcome_id_list, f)
                    await ctx.message.reply(f"削除しました。\n再度同じ設定をする場合は```n!ui set {seted_id}```と送信してください。")
                    return
                else:
                    await ctx.message.reply("設定されていません。")
                    return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                return
        elif ctx.message.content == "n!ui":
            try:
                if ctx.message.guild.id in n_fc.reaction_bool_list:
                    seted_id = int(n_fc.welcome_id_list[ctx.message.guild.id])
                    channel = bot.get_channel(n_fc.welcome_id_list[ctx.message.guild.id])
                    await ctx.message.reply(f"チャンネル：{channel.name}")
                    return
                else:
                    await ctx.message.reply("設定されていません。\n\n・追加```n!ui set [チャンネルID]```・削除```n!ui del```")
                    return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                return
    else:
        await ctx.message.reply(embed=discord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
        return

@bot.command()
async def srtr(ctx):
    if ctx.message.content == "n!srtr":
        embed = discord.Embed(title="しりとり", description=f"`n!srtr start`でそのチャンネルでしりとり（風対話）を実行し、`n!srtr stop`でしりとりを停止します。", color=0x00ff00)
        await ctx.message.reply(embed=embed)
        return
    if ctx.message.content == "n!srtr start":
        try:
            if ctx.message.guild.id in n_fc.srtr_bool_list:
                if ctx.message.channel.id in n_fc.srtr_bool_list:
                    embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは既にに実行されています。", color=0x00ff00)
                    await ctx.message.reply(embed=embed)
                    return
                else:
                    n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
            if ctx.message.guild.id not in n_fc.srtr_bool_list:
                n_fc.srtr_bool_list[ctx.message.guild.id] = {ctx.message.channel.id:1}
                with open('srtr_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.srtr_bool_list, f)
        except BaseException as err:
                await ctx.message.reply(embed=eh(err))
                return
        embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりを始めます。", color=0x00ff00)
        await ctx.message.reply(embed=embed)
        return
    if ctx.message.content == "n!srtr stop":
        try:
            if ctx.message.guild.id not in n_fc.srtr_bool_list:
                embed = discord.Embed(title="しりとり", description=f"{ctx.message.guild.name}でしりとりは実行されていません。", color=0x00ff00)
                await ctx.message.reply(embed=embed)
                return
            if ctx.message.channel.id not in n_fc.srtr_bool_list[ctx.message.guild.id]:
                embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でしりとりは実行されていません。", color=0x00ff00)
                await ctx.message.reply(embed=embed)
                return
            del n_fc.srtr_bool_list[ctx.message.guild.id][ctx.message.channel.id]
            with open('srtr_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.srtr_bool_list, f)
        except BaseException as err:
            await ctx.message.reply(embed=eh(err))
        embed = discord.Embed(title="しりとり", description=f"{ctx.message.channel.name}でのしりとりを終了します。", color=0x00ff00)
        await ctx.message.reply(embed=embed)
        return


@bot.command()
async def nr(ctx):
    try:
        if ctx.message.guild.id not in n_fc.reaction_bool_list: # 通常反応のブール値存在チェック
            n_fc.reaction_bool_list[ctx.message.guild.id] = {[ctx.message.channel.id]:1}
            n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 1
            with open('reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        if ctx.message.channel.id not in n_fc.reaction_bool_list[ctx.message.guild.id]:
            n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 1
            with open('reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        if ctx.message.content == "n!nr":
            if n_fc.reaction_bool_list[ctx.message.guild.id]["all"] == 0:
                setting = "サーバーで無効になっている為、チャンネルごとの設定は無効です。\n(`n!help nr`でご確認ください。)"
            elif n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] == 1:
                setting = "有効"
            elif n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] == 0:
                setting = "無効"
            else:
                setting = "読み込めませんでした。"
            await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`n!nr [on/off]`で変更できます。", color=0x00ff00))
            return
        if admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
            nr_setting = str((ctx.message.content).split(" ", 1)[1])
            if nr_setting in on_ali:
                n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を有効にしました。", color=0x00ff00))
            elif nr_setting in off_ali:
                n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 0
                await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を無効にしました。", color=0x00ff00))
            elif nr_setting[:3] == "all":
                if nr_setting in on_ali:
                    n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 1
                    await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を有効にしました。", color=0x00ff00))
                elif nr_setting in off_ali:
                    n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 0
                    await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を無効にしました。", color=0x00ff00))
                else:
                    await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
            else:
                await ctx.message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
            return
        else:
            await ctx.message.reply(embed=discord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return
    except BaseException as err:
        await ctx.message.reply(embed=eh(err))
        return

@bot.command()
async def admin(ctx):
    if admin_check(ctx.message.guild, ctx.message.author):
        await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
    elif ctx.message.author.id in n_fc.py_admin:
        await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。(開発者)\n**開発者として不用意な行動は慎んでください。**", color=0xffff00))
    else:
        await ctx.message.reply(embed=discord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
    return

@bot.command()
async def show_help(ctx):
    await help_command.n_help(ctx.message, bot)
    return

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="にらBOTについて", description="にらBOTは、かの有名なARK廃人の「にら」を元ネタとする、多機能DiscordBOTです！", color=0x00ff00)
    embed.add_field(name="ニラは繊細！", value="にらBOT(もといにら君)は、とっても繊細です！\nコマンドなどを沢山送ったりすると、落ちちゃうかもしれません！\n丁寧に扱ってください！", inline=False)
    embed.add_field(name="音声再生について", value="`n!join`及び`n!play [URL]`コマンドを使用した音楽再生は、大体サーバーのスペックの問題で再生出来ません。まぁ気にしないでね！", inline=False)
    embed.add_field(name="詳しくは...", value="[こちら](https://nattyan-tv.github.io/nira_web/index.html)からにらBOTの詳細をご確認いただけます！どうぞご覧ください！", inline=False)
    embed.add_field(name="困ったり暇だったら...", value="[ここ](https://discord.gg/awfFpCYTcP)から謎な雑談鯖に入れるよ！", inline=False)
    if ctx.message.author.id in n_fc.py_admin:
        embed.add_field(name="ってかお前って...", value="開発者だよなお前...\n\n[メインレポジトリ](https://github.com/nattyan-tv/nira_bot) / [ウェブページレポジトリ](https://github.com/nattyan-tv/)")
    await ctx.message.reply(embed=embed)
    return

@bot.command()
async def janken(ctx):
    if ctx.message.content == "n!janken":
        embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return
    mes = ctx.message.content
    try:
        mes_te = mes.split(" ", 1)[1]
    except BaseException as err:
        embed = discord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```n!janken [グー/チョキ/パー]```\n{err}", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return
    if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "ちょき" and mes_te != "パー" and mes_te != "ぱー":
        embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return
    embed = discord.Embed(title="にらにらじゃんけん", description="```n!janken [グー/チョキ/パー]```", color=0x00ff00)
    if mes_te == "グー" or mes_te == "ぐー":
        mes_te = "```グー```"
        embed.add_field(name="あなた", value=mes_te, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_gu.png")
    elif mes_te == "チョキ" or mes_te == "ちょき":
        mes_te = "```チョキ```"
        embed.add_field(name="あなた", value=mes_te, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_choki.png")
    elif mes_te == "パー" or mes_te == "ぱー":
        mes_te = "```パー```"
        embed.add_field(name="あなた", value=mes_te, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_pa.png")
    rnd_jyanken = random.randint(1, 3)
    if rnd_jyanken == 1:
        mes_te_e = "```グー```"
        embed.add_field(name="にら", value=mes_te_e, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_gu.png")
        if mes_te == "```グー```":
            res_jyan = ":thinking: あいこですね..."
        elif mes_te == "```チョキ```":
            res_jyan = ":laughing: 私の勝ちです！！"
        elif mes_te == "```パー```":
            res_jyan = ":pensive: あなたの勝ちですね..."
    elif rnd_jyanken == 2:
        mes_te_e = "```チョキ```"
        embed.add_field(name="にら", value=mes_te_e, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_choki.png")
        if mes_te == "```チョキ```":
            res_jyan = ":thinking: あいこですね..."
        elif mes_te == "```パー```":
            res_jyan = ":laughing: 私の勝ちです！！"
        elif mes_te == "```グー```":
            res_jyan = ":pensive: あなたの勝ちですね..."
    elif rnd_jyanken == 3:
        mes_te_e = "```パー```"
        embed.add_field(name="にら", value=mes_te_e, inline=False)
        embed.set_image(url="https://nattyan-tv.github.io/nira_bot/images/jyanken_pa.png")
        if mes_te == "```パー```":
            res_jyan = ":thinking: あいこですね..."
        elif mes_te == "```グー```":
            res_jyan = ":laughing: 私の勝ちです！！"
        elif mes_te == "```チョキ```":
            res_jyan = ":pensive: あなたの勝ちですね..."
    embed.add_field(name="\n```RESULT```\n", value=res_jyan, inline=False)
    await ctx.message.reply(embed=embed)
    return

@bot.command()
async def uranai(ctx):
    rnd_uranai = random.randint(1, 100)
    if rnd_uranai >= 1 and rnd_uranai <= 5:
        ur_w = 0
        stars = ""
        ur_m = "きっといいことあるよ...(`5%`)"
    elif rnd_uranai >= 6 and rnd_uranai <= 12:
        ur_w = 1
        stars = "**★**"
        ur_m = "まぁ星0よりはマシだし...？(`7%`)"
    elif rnd_uranai >= 13 and rnd_uranai <= 22:
        ur_w = 2
        stars = "**★★**"
        ur_m = "まぁ、大抵の人はそんなもんじゃね？(`10%`)"
    elif rnd_uranai >= 23 and rnd_uranai <= 35:
        ur_w = 3
        stars = "**★★★**"
        ur_m = "ほら、星みっつぅ～！w(`13%`)"
    elif rnd_uranai >= 36 and rnd_uranai <= 50:
        ur_w = 4
        stars = "**★★★★**"
        ur_m = "ガルパとかプロセカとかならいい方じゃん？(`15%`)"
    elif rnd_uranai >= 51 and rnd_uranai <= 69:
        ur_w = 5
        stars = "**★★★★★**"
        ur_m = "中途半端っすね。うん。(`19%`)"
    elif rnd_uranai >= 70 and rnd_uranai <= 82:
        ur_w = 6
        stars = "**★★★★★★**"
        ur_m = "おお、ええやん。(`13%`)"
    elif rnd_uranai >= 83 and rnd_uranai <= 89:
        ur_w = 7
        stars = "**★★★★★★★**"
        ur_m = "ラッキーセブンやん！すごいなぁ！(`7%`)"
    elif rnd_uranai >= 90 and rnd_uranai <= 95:
        ur_w = 8
        stars = "**★★★★★★★★**"
        ur_m = "星8でも十分すごいやん！！(`6%`)"
    elif rnd_uranai >= 96 and rnd_uranai <= 99:
        ur_w = 9
        stars = "**★★★★★★★★★**"
        ur_m = "いや、ここまで来たら星10出しなよwwwwwwwwwwwww(`4%`)"
    elif rnd_uranai == 100:
        ur_w = 10
        stars = "**★★★★★★★★★★**"
        ur_m = "星10は神の領域(当社調べ)だよ！！！！！凄い！！！(`1%`)"
    embed = discord.Embed(title="うらない", description=f"{stars}", color=0x00ff00)
    embed.add_field(name=f"あなたの運勢は**星10個中の{ur_w}個**です！", value=f"> {ur_m}")
    await ctx.message.reply(embed=embed)
    return

@bot.command()
async def embed(ctx):
    if ctx.message.content == "n!embed":
        embed = discord.Embed(title="Error", description="構文が間違っています。\n```n!embed [color(000000～ffffff)] [title]\n[description]```", color=0xff0000)
        await ctx.message.reply(embed=embed)
        return
    try:
        mes_ch = ctx.message.content.splitlines()
        emb_clr = int("".join(re.findall(r'[0-9]|[a-f]', str(mes_ch[0].split(" ", 2)[1]))), 16)
        emb_title = str(mes_ch[0].split(" ", 2)[2])
        emb_desc = "\n".join(mes_ch[1:])
        embed = discord.Embed(title=emb_title, description=emb_desc, color=emb_clr)
        await ctx.message.channel.send(embed=embed)
        return
    except BaseException as err:
        await ctx.message.reply(embed=eh(err))
        return


@buttons.click
async def del_ss_list_all(ctx):
    setting_del = ctx.message.content[13:].split("/",1)
    del_guild = bot.get_guild(int(setting_del[1][6:]))
    del_user = del_guild.get_member(int(setting_del[0][5:]))
    if admin_check(del_guild, del_user) == False:
        await ctx.reply("あなたは管理者ではないため削除できません！", flags = MessageFlags().EPHEMERAL)
        return
    del n_fc.steam_server_list[ctx.message.guild.id]
    with open('steam_server_list.nira', 'wb') as f:
        pickle.dump(n_fc.steam_server_list, f)
    await bot.http.delete_message(ctx.message.channel.id, ctx.message.id)
    await ctx.reply("リストを削除しました。", flags = MessageFlags().EPHEMERAL)
    return


@bot.command()
async def ss(ctx: commands.Context):
    if ctx.message.content[:8] == "n!ss add":
        if ctx.message.content == "n!ss add":
            await ctx.message.reply("構文が異なります。\n```n!ss add [表示名] [IPアドレス],[ポート番号]```")
            return
        try:
            if ctx.message.guild.id not in n_fc.steam_server_list:
                n_fc.steam_server_list[ctx.message.guild.id] = {"value": "0"}
            ad = ctx.message.content[9:].split(" ", 1)
            ad_name = str(ad[0])
            ad = ad[1].split(",", 1)
            ad_port = int(ad[1])
            ad_ip = str("".join(re.findall(r'[0-9]|\.', ad[0])))
            sset_point = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
            n_fc.steam_server_list[ctx.message.guild.id][f"{sset_point + 1}_ad"] = (ad_ip, ad_port)
            n_fc.steam_server_list[ctx.message.guild.id][f"{sset_point + 1}_nm"] = ad_name
            n_fc.steam_server_list[ctx.message.guild.id]["value"] = str(sset_point + 1)
            await ctx.message.reply(f"サーバー名：{ad_name}\nサーバーアドレス：({ad_ip},{ad_port})")
            with open('steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh(err))
    if ctx.message.content[:9] == "n!ss list":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        else:
            await ctx.message.reply(str(n_fc.steam_server_list[ctx.message.guild.id]).replace('value', '保存数').replace('ad', 'アドレス').replace('nm', '名前').replace('_', '\_').replace('{', '').replace('}', ''))
            return
    if ctx.message.content[:9] == "n!ss edit":
        if ctx.message.content == "n!ss edit":
            await ctx.message.reply("構文が異なります。\n```n!ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
            return
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        adre = ctx.message.content[10:].split(" ", 3)
        s_id = int("".join(re.findall(r'[0-9]', adre[0])))
        s_nm = str(adre[1])
        s_adre = str(adre[2]).split(",", 2)
        s_port = int(s_adre[1])
        s_ip = str("".join(re.findall(r'[0-9]|\.', s_adre[0])))
        b_value = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
        if b_value < s_id:
            await ctx.message.reply("そのサーバーナンバーのサーバーは登録されていません！\n`n!ss list`で確認してみてください。")
            return
        try:
            n_fc.steam_server_list[ctx.message.guild.id][f"{s_id}_ad"] = (s_ip, s_port)
            n_fc.steam_server_list[ctx.message.guild.id][f"{s_id}_nm"] = s_nm
            await ctx.message.reply(f"サーバーナンバー：{s_id}\nサーバー名：{s_nm}\nサーバーアドレス：{s_ip},{s_port}")
            with open('steam_server_list.nira', 'wb') as f:
                pickle.dump(n_fc.steam_server_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh(err))
            return
    if ctx.message.content[:8] == "n!ss del":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        if ctx.message.content != "n!ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except BaseException as err:
                await ctx.message.reply(embed=eh(err))
                return
            if admin_check(ctx.message.guild, ctx.message.author):
                if del_num > int(n_fc.steam_server_list[ctx.message.guild.id]["value"]):
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="そのサーバーは登録されていません！\n`n!ss list`で確認してみてください！", color=0xff0000))
                    return
                if del_num <= 0:
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="リストで0以下のナンバーは振り当てられていません。", color=0xff0000))
                    return
                try:
                    all_value = steam_server_list[ctx.message.guild.id]["value"]
                    print(all_value)
                    for i in range(all_value - del_num):
                        print(i)
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_nm"] = steam_server_list[ctx.message.guild.id][f"{del_num + i}_nm"]
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_ad"] = steam_server_list[ctx.message.guild.id][f"{del_num + i}_ad"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_nm"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_ad"]
                    n_fc.steam_server_list[ctx.message.guild.id]["value"] = all_value - 1
                    await ctx.message.reply(embed=discord.Embed(title="削除", description=f"ID:{del_num}のサーバーをリストから削除しました。", color=0xff0000))   
                except BaseException as err:
                    print(err)
                    await ctx.message.reply(embed=eh(err))
                    return
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return
        else:
            await buttons.send(
                content = f"追加反応リストの削除 - USER:{ctx.message.author.id}/GUILD:{ctx.message.guild.id}", 
                channel = ctx.channel.id,
                components = [ 
                    ActionRow([
                        Button(
                            label="削除する",
                            style=ButtonType().Danger,
                            custom_id="del_ss_list_all"
                        )
                    ])
                ]
            )
            return
    print(datetime.datetime.now())
    if ctx.message.content == "n!ss":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.message.guild.id]["value"])+1)):
                await server_check.server_check_async(bot.loop, embed, 0, ctx.message.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
        return
    mes = ctx.message.content
    try:
        mes_te = mes.split(" ", 1)[1]
    except BaseException as err:
        await ctx.message.reply(embed=eh(err))
        return
    if mes_te != "all":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            server_check.server_check(embed, 0, ctx.message.guild.id, mes_te)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
    elif mes_te == "all":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        async with ctx.message.channel.typing():
            embed = discord.Embed(title="Server Status Checker", description=f"{ctx.message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
            for i in map(str, range(1, int(n_fc.steam_server_list[ctx.message.guild.id]["value"])+1)):
                await server_check.server_check_async(bot.loop, embed, 1, ctx.message.guild.id, i)
            await asyncio.sleep(1)
            await ctx.message.reply(embed=embed)
    print("end")
    return

@bot.command()
async def er(ctx):
    if ctx.message.content[:8] == "n!er add":
        if ctx.message.content == "n!er add":
            await ctx.message.reply("構文が異なります。\n```n!er add [トリガー] [返信文]```")
            return
        try:
            if ctx.message.guild.id not in n_fc.ex_reaction_list:
                n_fc.ex_reaction_list[ctx.message.guild.id] = {"value":0}
            value = n_fc.ex_reaction_list[ctx.message.guild.id]["value"]
            ra = ctx.message.content[9:].split(" ", 1)
            react_triger = ra[0]
            react_return = ra[1]
            n_fc.ex_reaction_list[ctx.message.guild.id]["value"] = n_fc.ex_reaction_list[ctx.message.guild.id]["value"]+1
            n_fc.ex_reaction_list[ctx.message.guild.id][f'{value+1}_tr'] = str(react_triger)
            n_fc.ex_reaction_list[ctx.message.guild.id][f'{value+1}_re'] = str(react_return)
            await ctx.message.reply(f"トリガー：{ra[0]}\nリターン：{ra[1]}")
            with open('ex_reaction_list.nira', 'wb') as f:
                pickle.dump(n_fc.ex_reaction_list, f)
            return
        except BaseException as err:
            await ctx.message.reply(embed=eh(err))
    if ctx.message.content[:9] == "n!er list":
        if ctx.message.guild.id not in n_fc.ex_reaction_list or n_fc.ex_reaction_list[ctx.message.guild.id]["value"] == 0:
            await ctx.message.reply("追加返答は設定されていません。")
            return
        else:
            embed = discord.Embed(title="追加返答リスト", description="- にらBOT", color=0x00ff00)
            for i in range(int(n_fc.ex_reaction_list[ctx.message.guild.id]["value"])):
                embed.add_field(name=f"トリガー：{n_fc.ex_reaction_list[ctx.message.guild.id][f'{i+1}_tr']}", value=f"リターン：{n_fc.ex_reaction_list[ctx.message.guild.id][f'{i+1}_re']}", inline=False)
            await ctx.message.reply(embed=embed)
            return
    if ctx.message.content[:9] == "n!er edit":
        if ctx.message.content == "n!er edit":
            await ctx.message.reply("構文が異なります。\n```n!er edit [トリガー] [返信文]```")
            return
        if ctx.message.guild.id not in n_fc.ex_reaction_list:
            await ctx.message.reply("追加反応は登録されていません。")
            return
        if n_fc.ex_reaction_list[ctx.message.guild.id]["value"] == 0:
            await ctx.message.reply("追加反応は登録されていません。")
            return
        ssrt = ctx.message.content[10:].split(" ", 2)
        b_tr = ssrt[0]
        b_re = ssrt[1]
        try:
            rt_e = 0
            for i in range(math.floor((len(n_fc.ex_reaction_list[ctx.message.guild.id])-1)/2)):
                if n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_tr"] == b_tr:
                    await ctx.message.reply((n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_tr"], n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_re"]))
                    n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_re"] = b_re
                    await ctx.message.reply((n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_tr"], n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_re"]))
                    rt_e = 1
                    break
            if rt_e == 1:
                await ctx.message.reply(f"トリガー：{b_tr}\nリターン：{b_re}")
                with open('ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.ex_reaction_list, f)
                return
            elif rt_e == 0:
                await ctx.message.reply("そのトリガーは登録されていません！")
                return
        except BaseException as err:
            await ctx.message.reply(embed=eh(err))
            return
    if ctx.message.content == "n!er del":
        if ctx.message.guild.id not in n_fc.ex_reaction_list:
            await ctx.message.reply("追加返答は設定されていません。")
            return
        else:
            del_re = await ctx.message.reply("追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
            await del_re.add_reaction("\U00002B55")
            await del_re.add_reaction("\U0000274C")
            return
    return

@bot.command()
async def d(ctx):
    if ctx.message.content == "n!d":
        user = await bot.fetch_user(ctx.message.author.id)
        embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
        embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
        embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
        await ctx.message.reply(embed=embed)
        return
    else:
        user_id = int("".join(re.findall(r'[0-9]', ctx.message.content[4:])))
        try:
            user = await bot.fetch_user(user_id)
            embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
            await ctx.message.reply(embed=embed)
            return
        except BaseException:
            await ctx.message.reply(embed=discord.Embed(title="Error", description="ユーザーが存在しないか、データが取得できませんでした。", color=0xff0000))
            return

@bot.command()
async def ping(ctx):
    embed = discord.Embed(title="Ping", description=f"現在のPing値は`{round(bot.latency * 1000)}`msです。", color=0x00ff00)
    await ctx.message.reply(embed=embed)
    return

@bot.command()
async def join(ctx):
    await ctx.message.reply(embed=discord.Embed(title="お！？", description="まだVC系は整ってないよ！完成まではもうちょっと待ってね！", color=0xffff00))
    await music.join_channel(ctx.message, bot)
    return

@bot.command()
async def pause(ctx):
    await music.pause_music(ctx.message, bot)
    return

@bot.command()
async def play(ctx):
    await music.play_music(ctx.message, bot)
    return

@bot.command()
async def resume(ctx):
    await music.resume_music(ctx.message, bot)
    return

@bot.command()
async def stop(ctx):
    await music.stop_music(ctx.message, bot)
    return

@bot.command()
async def leave(ctx):
    await music.leave_channel(ctx.message, bot)
    return


# リアクション受信時
@bot.event
async def on_reaction_add(react, mem):
    # SteamServerListのリスト
    try:
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "サーバーリストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
            if n_fc.admin_check(react.message.guild, mem) or react.message.author.id in n_fc.py_admin:
                if str(react.emoji) == "\U00002B55":
                    del n_fc.steam_server_list[react.message.guild.id]
                    with open('steam_server_list.nira', 'wb') as f:
                        pickle.dump(n_fc.steam_server_list, f)
                    embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                    if mem.id == 669178357371371522:
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                    await react.message.channel.send(embed=embed)
                    await bot.http.delete_message(react.message.channel.id, react.message.id)
                    return
                elif str(react.emoji) == "\U0000274C":
                    await bot.http.delete_message(react.message.channel.id, react.message.id)
                    return
            else:
                user = await bot.fetch_user(mem.id)
                await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーのカスタムサーバーリスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                return
    except KeyError as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
        return
    except BaseException as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
        return
    # 追加返答のリスト
    try:
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
            if n_fc.admin_check(react.message.guild, mem) or react.message.author.id in n_fc.py_admin:
                if str(react.emoji) == "\U00002B55":
                    del n_fc.ex_reaction_list[react.message.guild.id]
                    with open('ex_reaction_list.nira', 'wb') as f:
                        pickle.dump(n_fc.ex_reaction_list, f)
                    embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                    if mem.id == 669178357371371522:
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                    await react.message.channel.send(embed=embed)
                    await bot.http.delete_message(react.message.channel.id, react.message.id)
                    return
                elif str(react.emoji) == "\U0000274C":
                    await bot.http.delete_message(react.message.channel.id, react.message.id)
                    return
            else:
                user = await bot.fetch_user(mem.id)
                await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーの追加返答リスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                return
    except KeyError as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
        return
    except BaseException as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
        return
    if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and str(react.emoji) == '<:trash:908565976407236608>':
        await bot.http.delete_message(react.message.channel.id, react.message.id)
        return

@bot.event
async def on_member_join(member):
    user_id = member.id
    try:
        user = await bot.fetch_user(user_id)
        if member.guild.id not in n_fc.welcome_id_list:
            return
        channel = bot.get_channel(n_fc.welcome_id_list[member.guild.id])
        embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
        embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
        embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
        await channel.send(embed=embed)
        return
    except BaseException as err:
        print(err)
        return


# Botの起動とDiscordサーバーへの接続
bot.run(bot_token.nira_dev)
