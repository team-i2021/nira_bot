# coding: utf-8
import discord
from os import getenv
import sys
import os
import re
import random
import a2s
import asyncio
import datetime
import bot_token

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
from discord.flags import MessageFlags

# | N     N  IIIII  RRRR     A     BBBB   OOOOO  TTTTT
# | NN    N    I    R  R    A A    B   B  O   O    T
# | N N   N    I    R  R   A   A   B   B  O   O    T
# | N  N  N    I    RRRR   AAAAA   BBBB   O   O    T
# | N   N N    I    RR     A   A   B   B  O   O    T
# | N    NN    I    R R    A   A   B   B  O   O    T
# | N     N  IIIII  R  R   A   A   BBBB   OOOOO    T  v.永遠にβバージョン

ark_1 = ("60.114.86.249", 27015)  # アイランド
ark_1_nm = "The Island :free:"
ark_2 = ("60.114.86.249", 27016)  # アベレーション
ark_2_nm = "Aberration :dollar:"
ark_3 = ("60.114.86.249", 27017)  # エクスティンクション
ark_3_nm = "Extinction :dollar:"
ark_4 = ("60.114.86.249", 27018)  # ジェネシス1
ark_4_nm = "Genesis: Part 1 :dollar:"
ark_5 = ("60.114.86.249", 27019)  # ジェネシス2
ark_5_nm = "Genesis: Part 2 :dollar:"
ark_6 = ("60.114.86.249", 27020)  # ラグナロク
ark_6_nm = "Ragnarok :free:"
steam_server_list = {}
admin_role_list = {}
reaction_bool_list = {}
on_ali = ["1", "on", "On", "ON", "true", "True", "TRUE", "yes", "Yes", "YES"]
off_ali = ["0", "off", "Off", "OFF", "false", "False", "FALSE", "no", "No", "NO"]

py_admin = [669178357371371522]

client = discord.Client()


async def server_check_async(loop, embed, type, g_id, n):
    return await loop.run_in_executor(
        None, server_check, embed, type, g_id, n
    )

def server_check(embed, type, g_id, n):
    if n == "1":
        sv_ad = ark_1
        sv_nm = ark_1_nm
    elif n == "2":
        sv_ad = ark_2
        sv_nm = ark_2_nm
    elif n == "3":
        sv_ad = ark_3
        sv_nm = ark_3_nm
    elif n == "4":
        sv_ad = ark_4
        sv_nm = ark_4_nm
    elif n == "5":
        sv_ad = ark_5
        sv_nm = ark_5_nm
    elif n == "6":
        sv_ad = ark_6
        sv_nm = ark_6_nm
    elif n == "7":
        sv_ad = steam_server_list[str(g_id)]["1_ad"]
        sv_nm = steam_server_list[str(g_id)]["1_nm"]
    elif n == "8":
        sv_ad = steam_server_list[str(g_id)]["2_ad"]
        sv_nm = steam_server_list[str(g_id)]["2_nm"]
    if type == 3:
        try:
            sv_ad = steam_server_list[str(g_id)][f"{n}_ad"]
            sv_nm = steam_server_list[str(g_id)][f"{n}_nm"]
        except BaseException:
            embed.add_field(name=f"サーバーは{n}にはセットされていません。", value="`n!ss list`でサーバーリストを確認してみましょう！", inline=False)
            return
    sv_dt = "None"
    try:
        print(f"{sv_nm}/{sv_ad} への接続")
        sv_dt = a2s.info(sv_ad)
        print(a2s.info(sv_ad))
        if type == 0 or type == 3:
            embed.add_field(name=f"> {sv_nm}", value=":white_check_mark:Success!", inline=False)
        elif type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        if type == 0 or type == 3:
            if a2s.players(sv_ad) != []:
                sv_users_str = str(a2s.players(sv_ad)).replace("[", "").replace("]", "")
                sv_users_str = sv_users_str[7:]
                sv_users_str = sv_users_str + ", Player("
                sv_users_list = sv_users_str.split("), Player(")
                for i in range(len(a2s.players(sv_ad))):
                    sp_info = sv_users_list[-2]
                    splited = sp_info.split(", ", 4)[1]
                    user_add = splited.replace("name='", "").replace("'", "")
                    if user_add != "":
                        user = user + "\n" + f"```{user_add}```"
                    sv_users_list.pop()
                if user == "":
                    user = "（ユーザーデータが取得出来ませんでした。）"
                embed.add_field(name="> Online User", value=f"ユーザー数:{len(a2s.players(sv_ad))}人{user}\n==========", inline=False)
            else:
                embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
        elif type == 1:
            embed.add_field(name="> Online User", value=f"```{sv_us}```", inline=False)
    except BaseException as err:
        print(err)
        if type == 0 or type == 3:
            embed.add_field(name=f"> {sv_nm}", value=":x: Failure\n==========", inline=False)
        if type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    return True

# 起動時処理
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="読み込み中...", type=1), status=discord.Status.dnd)
    try:
        with open('steam_server_list.nira', 'rb') as f:
            global steam_server_list
            steam_server_list = pickle.load(f)
        print(steam_server_list, type(steam_server_list))
    except BaseException:
        print("変数[steam_server_list]のファイル読み込みに失敗しました。続行します。")
    try:
        with open('reaction_bool_list.nira', 'rb') as f:
            global reaction_bool_list
            reaction_bool_list = pickle.load(f)
        print(reaction_bool_list, type(reaction_bool_list))
    except BaseException:
        print("変数[reaction_bool_list]のファイル読み込みに失敗しました。続行します。")
    await client.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1), status=discord.Status.online)
    print('Launched! NIRABOT v.永遠にβバージョン')

# メッセージ受信時処理
@client.event
async def on_message(message):
    # 自分自身には反応しない
    if message.author.id == 892759276152573953:
        return
    #############################
    # Pythonコードを含むコマンド
    #############################
    # ファイル生成(n!create [path])
    # 変数ファイルなどを削除した際に作成する場合はこれを使うと楽です。
    if message.content[:8] == "n!create":
        if message.author.id in py_admin:
            if message.content == "n!create":
                await message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
                return
            c_file_d = str((message.content).split(" ", 1)[1])
            try:
                with open(c_file_d, 'w'):
                    pass
            except BaseException as err:
                await message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
                return
        else:
            await message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
    # ソースコード取得(n!read)
    # nira.pyのコードを取得したい場合に便利です。
    if message.content == "n!read":
        if message.author.id not in py_admin:
            await message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
            return
        try:
            await message.reply('`nira.py`', file=discord.File('nira.py'))
            return
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return
    # bot再起動(n!restart)
    # コードに変更を加えた際にこれを使うと便利です。
    if message.content == "n!restart":
        if message.author.id in py_admin:
            await client.change_presence(activity=discord.Game(name="再起動中...", type=1), status=discord.Status.idle)
            await message.reply("`nira.py` > `nira.py`\n再起動します...")
            print("プログラムを再起動します。")
            os.execl(sys.executable, 'python3.7', "nira.py")
            return
        else:
            embed = discord.Embed(title="Error", description="権限がありません。", color=0xff0000)
            await message.reply(embed=embed)
            return
    # bot停止(n!stop)
    # botを停止させたい場合にこれを使うと便利です。
    if message.content == "n!stop":
        if message.author.id in py_admin:
            await message.reply("STOP:`nira.py`\n終了します...")
            await client.logout()
            exit()
            return
        else:
            embed = discord.Embed(title="Error", description="権限がありません。", color=0xff0000)
            await message.reply(embed=embed)
            return
    # !!!!!Pythonコード実行!!!!!
    # このコマンドは「大変危険」です！！！（まぁちゃんと権限設定してるけど）
    # Pythonコードを実行させたい場合はこれを利用してください。
    # (コードの返りは全て「cmd_rt」という配列に追加されます。cmd_rt[0]などと指定してください。)
    if message.content[:6] == "n!exec":
        if message.author.id not in py_admin:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await message.reply(embed=embed)
            await message.add_reaction("\U0000274C")
            return
        if message.content == "n!exec":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await message.reply(embed=embed)
            await message.add_reaction("\U0000274C")
            return
        if re.search(r'(?:n!exec await)', message.content):
            if message.author.id not in py_admin:
                embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
                await message.reply(embed=embed)
                await message.add_reaction("\U0000274C")
                return
            if message.content == "n!exec await":
                embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
                await message.reply(embed=embed)
                await message.add_reaction("\U0000274C")
                return
        mes = message.content[7:].splitlines()
        cmd_nm = len(mes)
        cmd_rt = []
        print(mes)
        for i in range(cmd_nm):
            if re.search(r'(?:await)', mes[i]):
                try:
                    mes_py = mes[i].split(" ", 1)[1]
                    cmd_rt.append(await eval(mes_py))
                except BaseException as err:
                    await message.add_reaction("\U0000274C")
                    embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
                    await message.reply(embed=embed)
                    return
            else:
                try:
                    exec(mes[i])
                    cmd_rt.append("")
                except BaseException as err:
                    await message.add_reaction("\U0000274C")
                    embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
                    await message.reply(embed=embed)
                    return
        await message.add_reaction("\U0001F197")
        return
    #################
    # 通常コマンド
    #################
    if message.content[:4] == "n!nr":
        try:
            if str(message.guild.id) not in reaction_bool_list: # 通常反応のブール値存在チェック
                reaction_bool_list[str(message.guild.id)] = 1
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
            if message.content == "n!nr":
                if reaction_bool_list[str(message.guild.id)] == 1:
                    setting = "有効"
                elif reaction_bool_list[str(message.guild.id)] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`n!nr [on/off]`で変更できます。", color=0x00ff00))
                return
            nr_setting = str((message.content).split(" ", 1)[1])
            if nr_setting in on_ali:
                reaction_bool_list[str(message.guild.id)] = 1
                await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="通常反応を有効にしました。", color=0x00ff00))
            elif nr_setting in off_ali:
                reaction_bool_list[str(message.guild.id)] = 0
                await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="通常反応を無効にしました。", color=0x00ff00))
            else:
                await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [on/off]`", color=0xff0000))
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
            return
    # ヘルプコマンド
    if message.content == "n!help":
        embed = discord.Embed(title="ニラbot HELP", description="ニラちゃんの扱い方", color=0x00ff00)
        embed.set_author(name="製作者：なつ", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.add_field(name="```にら系の単語+α```", value="(きっと)なんかしらの反応を示します。\n(通常反応設定が無効になってる場合は反応しません。)", inline=False)
        embed.add_field(name="```n!help```", value="このヘルプを表示します。", inline=False)
        embed.add_field(name="```n!ss [value]```", value="指定されたValueのカスタムSteamServerのステータス表示を行います。(※valueを指定しないと、リストの全てのサーバーを表示します。)", inline=False)
        embed.add_field(name="```n!ss add [ServerName] [ServerIP],[ServerPort]```", value="カスタムSteamServerのリストに追加します。", inline=False)
        embed.add_field(name="```n!ss list```", value="カスタムSteamServerのリストを表示します。", inline=False)
        embed.add_field(name="```n!ss del```", value="カスタムSteamServerのリストを初期化します。", inline=False)
        if message.guild.id == 870642671415337001:
            embed.add_field(name="```n!ark [server]```", value="dinosaur鯖(ここでのメインARK鯖)に接続できるか表示します。", inline=False)
            embed.add_field(name="> Server list", value="`1`:The Island\n`2`:Aberration\n`3`:Exctinction\n`4`:Genesis: Part 1\n`5`:Genesis: Part 2\n`6`:Ragnarok", inline=False)
            embed.add_field(name="> [server]を指定しないと", value="全てのサーバーの状態が表示されます。", inline=False)
        embed.add_field(name="```n!embed [title] [descripition]```", value="Embedを生成して送信します。", inline=False)
        embed.add_field(name="```n!janken [グー/チョキ/パー]]```", value="じゃんけんで遊びます。確率操作はしてません。", inline=False)
        embed.add_field(name="```n!uranai```", value="あなたの運勢が占われます。同上。\n==========", inline=False)
        embed.add_field(name="```n!nr [on/off]```", value="通常反応の設定を変更します。", inline=False)
        embed.add_field(name="・リアクションについて", value="このbotの発したメッセージの一部には、<:trash:896021635470082048>のリアクションが自動的に付きます。\nこのリアクションを押すとそのメッセージが削除されます。", inline=False)
        await message.reply(embed=embed)
        if message.author.id in py_admin:
            embed = discord.Embed(title="Error?", description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\n(今はGitHubにあんまプッシュしてないから、`home/pi/nira.py`を見てね)", color=0xff0000)
            await message.reply(embed=embed)
            return
        return
    if re.search(r'(?:n!janken)', message.content):
        if message.content == "n!janken":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 1)[1]
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```n!janken [グー/チョキ/パー]```\n{err}", color=0xff0000)
            await message.reply(embed=embed)
            return
        if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "ちょき" and mes_te != "パー" and mes_te != "ぱー":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        embed = discord.Embed(title="にらにらじゃんけん", description="```n!janken [グー/チョキ/パー]```", color=0x00ff00)
        if mes_te == "グー" or mes_te == "ぐー":
            mes_te = "```グー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
        elif mes_te == "チョキ" or mes_te == "ちょき":
            mes_te = "```チョキ```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
        elif mes_te == "パー" or mes_te == "ぱー":
            mes_te = "```パー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
        rnd_jyanken = random.randint(1, 3)
        if rnd_jyanken == 1:
            mes_te_e = "```グー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
            if mes_te == "```グー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```チョキ```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```パー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 2:
            mes_te_e = "```チョキ```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
            if mes_te == "```チョキ```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```パー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```グー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 3:
            mes_te_e = "```パー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
            if mes_te == "```パー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```グー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```チョキ```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        embed.add_field(name="\n```RESULT```\n", value=res_jyan, inline=False)
        await message.reply(embed=embed)
        return
    if message.content == "n!uranai":
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
        await message.reply(embed=embed)
        return
    if re.search(r'(?:n!embed)', message.content):
        if message.content == "n!embed":
            embed = discord.Embed(title="Error", description="構文が間違っています。\n```n!embed [title] [description(スペースなど利用可能)]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        try:
            mes_ch = message.content
            emb_title = mes_ch.split(" ", 2)[1]
            emb_desc = mes_ch.split(" ", 2)[2]
            embed = discord.Embed(title=emb_title, description=emb_desc, color=0x000000)
            await message.channel.send(embed=embed)
            return
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return
    # 超凄いサーバー監視システム
    if message.content[:4] == "n!ss":
        print(steam_server_list, type(steam_server_list))
        if message.content[:8] == "n!ss add":
            try:
                if str(message.guild.id) not in steam_server_list:
                    steam_server_list[str(message.guild.id)] = {"value": "0"}
                ad = message.content[9:].split(" ", 1)
                ad_name = str(ad[0])
                ad = ad[1].split(",", 1)
                ad_port = int(ad[1])
                ad_ip = str("".join(re.findall(r'[0-9]|\.', ad[0])))
                sset_point = int(steam_server_list[str(message.guild.id)]["value"])
                steam_server_list[str(message.guild.id)][f"{sset_point + 1}_ad"] = (ad_ip, ad_port)
                steam_server_list[str(message.guild.id)][f"{sset_point + 1}_nm"] = ad_name
                steam_server_list[str(message.guild.id)]["value"] = str(sset_point + 1)
                await message.reply(f"サーバー名：{ad_name}\nサーバーアドレス：({ad_ip},{ad_port})")
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                return
            except BaseException as err:
                await message.reply(err)
        if message.content[:9] == "n!ss list":
            if str(message.guild.id) not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return
            else:
                await message.reply(str(steam_server_list[str(message.guild.id)]).replace('value', '保存数').replace('ad', 'アドレス').replace('nm', '名前').replace('_', '\_').replace('{', '').replace('}', ''))
                return
        if message.content == "n!ss del":
            del_re = await message.reply("リストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
            await del_re.add_reaction("\U00002B55")
            await del_re.add_reaction("\U0000274C")
            return
        print(datetime.datetime.now())
        if message.content == "n!ss":
            if str(message.guild.id) not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server_list[str(message.guild.id)]["value"])+1)):
                    await server_check_async(client.loop, embed, 3, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
            print("end")
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 1)[1]
            print(mes_te)
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return
        if mes_te != "all":
            if str(message.guild.id) not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                server_check(embed, 3, message.guild.id, mes_te)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        elif mes_te == "all":
            if str(message.guild.id) not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server_list[str(message.guild.id)]["value"])+1)):
                    await server_check_async(client.loop, embed, 3, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        print("end")
        return
    if message.content[:5] == "n!ark":
        if message.guild.id != 870642671415337001:
            return
        print(datetime.datetime.now())
        if message.content == "n!ark":
            async with message.channel.typing():
                embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, 7)):
                    await server_check_async(client.loop, embed, 0, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
            print("end")
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 1)[1]
            print(mes_te)
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"エラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
        if mes_te != "1" and mes_te != "2" and mes_te != "3" and mes_te != "4" and mes_te != "5" and mes_te != "6" and mes_te != "7" and mes_te != "8" and mes_te != "all":
            embed = discord.Embed(title="Error", description="```n!ark [server]```\nServer引数を`1～6`で指定してください。\n\n> Server list\n`1`:The Island\n`2`:Aberration\n`3`:Exctinction\n`4`:Genesis: Part 1\n`5`:Genesis: Part 2\n`6`:Ragnarok", color=0xff0000)
            await message.reply(embed=embed)
            return
        if mes_te != "all":
            async with message.channel.typing():
                embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                server_check(embed, 0, message.guild.id, mes_te)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        elif mes_te == "all":
            async with message.channel.typing():
                embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, 7)):
                    await server_check_async(client.loop, embed, 1, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        print("end")
        return
    if message.content[:3] == "n!d":
        if message.content == "n!d":
            user = await client.fetch_user(message.author.id)
            await message.reply(user.created_at)
            return
        else:
            user_id = message.content[4:]
            try:
                user = await client.fetch_user(user_id)
                await message.reply(user.created_at)
                return
            except BaseException:
                await message.reply(embed=discord.Embed(title="Error", description="ユーザーが存在しないか、データが取得できませんでした。", color=0xff0000))
                return
    ###############################
    # 通常反応のブール値存在チェック #
    ###############################
    if str(message.guild.id) not in reaction_bool_list:
                reaction_bool_list[str(message.guild.id)] = 1
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
    #########################################
    # 通常反応
    # 「n!nr [on/off]」で変更できます
    #########################################
    if reaction_bool_list[str(message.guild.id)] == 1:
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
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_zoku.mp4')
        if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/koikingu.jpg')
        if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
            if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
                if re.search(r'(?:水|みず|ミズ)', message.content):
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_water.jpg')
                else:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sand.jpeg')
            elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_itou.png')
            elif re.search(r'(?:ごはん|飯|らいす|ライス|rice|Rice)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_rice.jpg')
            elif re.search(r'(?:枯|かれ|カレ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_kare.png')
            elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_fish.png')
            elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_dokusai.png')
            elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_seityou.jpeg')
            elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_nabe.jpg')
                sended_mes = await message.reply('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
            elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sword.png')
            elif re.search(r'(?:あんど|and|アンド)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_and.png')
            elif re.search(r'(?:んど|ンド|nd)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_land.png')
                sended_mes = await sended_mes.reply('https://sites.google.com/view/nirand/%E3%83%9B%E3%83%BC%E3%83%A0')
            elif re.search(r'(?:饅頭|まんじゅう|マンジュウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_manju.png')
            elif re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://twitter.com/DR36Hl04ZUwnEnJ')
            else:
                rnd = random.randint(1, 3)
                if rnd == 1:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_b.jpg')
                elif rnd == 3:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_c.png')
        if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_a.png')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_b.png')
        if re.search(r'(?:ぴの|ピノ|pino)', message.content):
            rnd = random.randint(1, 3)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_nm.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_st.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_cool.jpg')
        if re.search(r'(?:きつね|キツネ|狐)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 3)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
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
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://twitter.com/RINGOSANDAO')
        if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 4)
            else:
                rnd = random.randint(1, 3)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
            elif rnd == 4:
                sended_mes = await message.reply('https://twitter.com/Shake_Yuyu')
        if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
            await message.add_reaction("<:shiro:892787951673692161>")
        if re.search(r'(?:12pp|12PP)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
        if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
                if rnd == 1:
                    sended_mes = await message.reply('https://twitter.com/namae_1216')
                elif rnd == 2:
                    sended_mes = await message.reply(':heart: by apple')
        if re.search(r'(?:みけ|ミケ|三毛)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
        if re.search(r'(?:あう)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/au.png')
        if re.search(r'(?:ろり|ロリ)', message.content):
            if re.search(r'(?:せろり|セロリ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
            else:
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
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
            sended_mes = await message.reply("https://nattyan-tv.github.io/tensei_disko/images/kawaisou.png")
        if re.search(r'(?:あすか|アスカ|飛鳥)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/ribpggxcrmz74t6")
        if re.search(r'(?:しおりん)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/Aibell__game")
        if sended_mes != "":
            await sended_mes.add_reaction("<:trash:896021635470082048>")
            await asyncio.sleep(3)
            try:
                await sended_mes.remove_reaction("<:trash:896021635470082048>", client.user)
                return
            except BaseException:
                return

                
# リアクション受信時
@client.event
async def on_reaction_add(react, mem):
    print(mem.id, react.message.author.id, react.message.content, mem.roles)
    try:
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "リストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
            role_list = []
            for role in mem.roles:
                role_list.append(role.id)
            if 876433165105897482 in role_list or 894365538724237353 in role_list or mem.id == 669178357371371522:
                if str(react.emoji) == "\U00002B55":
                    del steam_server_list[str(react.message.guild.id)]
                    if  os.path.isfile("steam_server_list.nira"):
                        os.remove('steam_server_list.nira')
                    with open('steam_server_list.nira', 'wb') as f:
                        pickle.dump(steam_server_list, f)
                    embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                    if mem.id == 669178357371371522:
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nlistはホームディレクトリに「`steam_server_list.nira`」という形式で保存されています。\n全てのguildのリストを削除するには、Pythonコード`os.remove([filename])`を使用して削除することが可能です。", color=0xffffff)
                    await react.message.channel.send(embed=embed)
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
                elif str(react.emoji) == "\U0000274C":
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
            else:
                user = await client.fetch_user(mem.id)
                await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーのリスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                return
    except KeyError as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
        return
    except BaseException as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
        return
    if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and str(react.emoji) == '<:trash:896021635470082048>':
        await client.http.delete_message(react.message.channel.id, react.message.id)
        return

# Botの起動とDiscordサーバーへの接続
client.run(bot_token.nira_token)
