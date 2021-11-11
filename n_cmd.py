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
from discord.utils import get
import math
import shutil
import help_command


from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
from discord.flags import MessageFlags

global steam_server_list
steam_server_list = {}
global ex_reaction_list
ex_reaction_list = {}
global reaction_bool_list
reaction_bool_list = {}
global welcome_id_list
welcome_id_list = {}

on_ali = ["1", "on", "On", "ON", "true", "True", "TRUE", "yes", "Yes", "YES"]
off_ali = ["0", "off", "Off", "OFF", "false", "False", "FALSE", "no", "No", "NO"]

# 開発者用コマンド(stop/restart/exec/create/read)を利用できるユーザーのID
py_admin = [669178357371371522]

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
    return discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000)

# ステータスチェック中にメッセージ返信ができないものを修正する(Created by tasuren)
async def server_check_async(loop, embed, type, g_id, n):
    return await loop.run_in_executor(
        None, server_check, embed, type, g_id, n
    )

# サーバーのステータスをチェックする
def server_check(embed, type, g_id, n):
    try:
        sv_ad = steam_server_list[g_id][f"{n}_ad"]
        sv_nm = steam_server_list[g_id][f"{n}_nm"]
    except BaseException:
        embed.add_field(name=f"サーバーは{n}にはセットされていません。", value="`n!ss list`でサーバーリストを確認してみましょう！", inline=False)
        return
    sv_dt = "None"
    try:
        print(f"{sv_nm}/{sv_ad} への接続")
        sv_dt = a2s.info(sv_ad)
        print(a2s.info(sv_ad))
        if type == 0:
            embed.add_field(name=f"> {sv_nm}", value=":white_check_mark:Success!", inline=False)
        elif type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{sv_dt}```", inline=False)
        user = ""
        sv_us = a2s.players(sv_ad)
        if type == 0:
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
        if type == 0:
            embed.add_field(name=f"> {sv_nm}", value=":x: Failure\n==========", inline=False)
        if type == 1:
            embed.add_field(name=f"> {sv_nm}", value=f"```{err}```", inline=False)
    return True

# メッセージチェック
async def nira_check(message, client):
    #############################
    # Pythonコードを含むコマンド
    #############################
    # ファイル生成(n!create [path])
    # 変数ファイルなどを削除した際に作成する場合はこれを使うと楽です。
    if message.content[:8] == "n!create":
        if message.author.id in py_admin:
            if message.content == "n!create":
                await message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
                return "exec"
            c_file_d = str((message.content).split(" ", 1)[1])
            try:
                with open(c_file_d, 'w'):
                    pass
            except BaseException as err:
                await message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
                return "exec"
        else:
            await message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
    # Pythonファイル実行
    # n!exec [filename]
    if message.content[:6] == "n!exec":
        if message.author.id in py_admin:
            if message.content == "n!exec":
                await message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
                return "exec"
            e_file = str((message.content).split(" ", 1)[1])
            try:
                exec(open(e_file).read())
                return "exec"
            except BaseException as err:
                await message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
                return "exec"
        else:
            await message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
    # ソースコード取得(n!read)
    # nira.pyのコードを取得したい場合に便利です。
    if message.content == "n!read":
        if message.author.id not in py_admin:
            await message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
            return "exec"
        try:
            shutil.copyfile("nira.py", "nira_copy.txt")
            await message.reply('`nira.py（コピー）`', file=discord.File('nira_copy.txt'))
            os.remove('nira_copy.txt')
            return "exec"
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
    # bot再起動(n!restart)
    # コードに変更を加えた際にこれを使うと便利です。
    if message.content == "n!restart":
        if message.author.id in py_admin:
            await client.change_presence(activity=discord.Game(name="再起動中...", type=1), status=discord.Status.dnd)
            restart_code = await message.reply("再起動準備中...")
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(welcome_id_list, f)
                await restart_code.edit(content="RESTART:`nira.py`\n再起動します")
                print("-----[n!restart]コマンドが実行されたため、再起動します。-----")
                os.execl(sys.executable, 'python3.7', "nira.py")
                return "exec"
            except BaseException as err:
                await message.reply(err)
                await client.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1), status=discord.Status.idle)
                return "exec"
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
    # bot停止(n!stop)
    # botを停止させたい場合にこれを使うと便利です。
    if message.content == "n!stop":
        if message.author.id in py_admin:
            stop_code = await message.reply("STOP:`nira.py`\n終了準備中...")
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(welcome_id_list, f)
                await stop_code.edit(content="STOP:`nira.py`\n終了します")
                await client.logout()
                exit()
                return "exec"
            except BaseException as err:
                await message.reply(err)
                return "exec"
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
    # !!!!!Pythonコード実行!!!!!
    # このコマンドは「大変危険」です！！！（まぁちゃんと権限設定してるけど）
    # Pythonコードを実行させたい場合はこれを利用してください。
    # (コードの返りは全て「cmd_rt」という配列に追加されます。cmd_rt[0]などと指定してください。)
    if message.content[:4] == "n!py":
        if message.author.id not in py_admin:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await message.reply(embed=embed)
            await message.add_reaction("\U0000274C")
            return "exec"
        if message.content == "n!py":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await message.reply(embed=embed)
            await message.add_reaction("\U0000274C")
            return "exec"
        if message.content[:10] == "n!py await":
            if message.author.id not in py_admin:
                embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
                await message.reply(embed=embed)
                await message.add_reaction("\U0000274C")
                return "exec"
            if message.content == "n!py await":
                embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
                await message.reply(embed=embed)
                await message.add_reaction("\U0000274C")
                return "exec"
        mes = message.content[5:].splitlines()
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
                    return "exec"
            else:
                try:
                    exec(mes[i])
                    cmd_rt.append("")
                except BaseException as err:
                    await message.add_reaction("\U0000274C")
                    embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
                    await message.reply(embed=embed)
                    return "exec"
        await message.add_reaction("\U0001F197")
        return "exec"
    # 変数のファイル化(保存)
    if message.content == "n!save":
        if message.author.id in py_admin:
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(welcome_id_list, f)
                await message.reply("Saved.")
            except BaseException as err:
                await message.reply(f"Error happend.\n{err}")
            return "exec"
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
    #################
    # 通常コマンド
    #################
    if message.content[:4] == "n!ui":
        if admin_check(message.guild, message.author) or message.author.id in py_admin:
            if message.content[:8] == "n!ui set":
                try:
                    set_id = int("".join(re.findall(r'[0-9]', message.content[9:])))
                    welcome_id_list[message.guild.id] = set_id
                    with open('welcome_id_list.nira', 'wb') as f:
                        pickle.dump(welcome_id_list, f)
                    channel = client.get_channel(welcome_id_list[message.guild.id])
                    await channel.send("追加完了メッセージ\nこのメッセージが指定のチャンネルに送信されていれば完了です。")
                    await message.reply("追加完了のメッセージを指定されたチャンネルに送信しました。\n送信されていない場合はにらBOTに適切な権限が与えられているかご確認ください。")
                    return "exec"
                except BaseException as err:
                    await message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                    return "exec"
            elif message.content == "n!ui del":
                try:
                    if message.guild.id not in reaction_bool_list:
                        seted_id = welcome_id_list[message.guild.id]
                        del welcome_id_list[message.guild.id]
                        with open('welcome_id_list.nira', 'wb') as f:
                            pickle.dump(welcome_id_list, f)
                        await message.reply(f"削除しました。\n再度同じ設定をする場合は```n!ui set {seted_id}```と送信してください。")
                        return "exec"
                    else:
                        await message.reply("設定されていません。")
                        return "exec"
                except BaseException as err:
                    await message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                    return "exec"
            elif message.content == "n!ui":
                try:
                    if message.guild.id in reaction_bool_list:
                        seted_id = int(welcome_id_list[message.guild.id])
                        channel = client.get_channel(welcome_id_list[message.guild.id])
                        await message.reply(f"チャンネル：{channel.name}")
                        return "exec"
                    else:
                        await message.reply("設定されていません。\n\n・追加```n!ui set [チャンネルID]```・削除```n!ui del```")
                        return "exec"
                except BaseException as err:
                    await message.reply(embed=discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
                    return "exec"
        else:
            await message.reply(embed=discord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return "exec"
    if message.content[:4] == "n!nr":
        try:
            if message.guild.id not in reaction_bool_list: # 通常反応のブール値存在チェック
                reaction_bool_list[message.guild.id] = 1
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(reaction_bool_list, f)
            if message.content == "n!nr":
                if reaction_bool_list[message.guild.id] == 1:
                    setting = "有効"
                elif reaction_bool_list[message.guild.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`n!nr [on/off]`で変更できます。", color=0x00ff00))
                return "exec"
            if admin_check(message.guild, message.author) or message.author.id in py_admin:
                nr_setting = str((message.content).split(" ", 1)[1])
                if nr_setting in on_ali:
                    reaction_bool_list[message.guild.id] = 1
                    await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="通常反応を有効にしました。", color=0x00ff00))
                elif nr_setting in off_ali:
                    reaction_bool_list[message.guild.id] = 0
                    await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="通常反応を無効にしました。", color=0x00ff00))
                else:
                    await message.reply(embed=discord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [on/off]`", color=0xff0000))
                return "exec"
            else:
                await message.reply(embed=discord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return "exec"
        except BaseException as err:
            await message.reply(embed=eh(err))
            return "exec"
    if message.content == "n!admin":
        if admin_check(message.guild, message.author):
            await message.reply(embed=discord.Embed(title="ADMIN", description=f"権限があるようです。", color=0x00ff00))
        elif message.author.id in py_admin:
            await message.reply(embed=discord.Embed(title="ADMIN", description=f"サーバー権限はありませんが、コマンドは実行できます。(開発者)\n**開発者として不用意な行動は慎んでください。**", color=0xffff00))
        else:
            await message.reply(embed=discord.Embed(title="ADMIN", description=f"権限がないようです。\n**（管理者権限を付与したロールがありませんでした。）**\n自分が管理者の場合は、自分に管理者権限を付与したロールを付けてください。", color=0xff0000))
        return "exec"
    # ヘルプコマンド
    if message.content[:6] == "n!help":
        await help_command.n_help(message, client)
        return "exec"
    if message.content[:9] == "n!janken":
        if message.content == "n!janken":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
        mes = message.content
        try:
            mes_te = mes.split(" ", 1)[1]
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```n!janken [グー/チョキ/パー]```\n{err}", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
        if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "ちょき" and mes_te != "パー" and mes_te != "ぱー":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
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
        await message.reply(embed=embed)
        return "exec"
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
        return "exec"
    if message.content[:7] == "n!embed":
        if message.content == "n!embed":
            embed = discord.Embed(title="Error", description="構文が間違っています。\n```n!embed [color(000000～ffffff)] [title]\n[description]```", color=0xff0000)
            await message.reply(embed=embed)
            return "exec"
        try:
            mes_ch = message.content.splitlines()
            emb_clr = int("".join(re.findall(r'[0-9]|[a-f]', str(mes_ch[0].split(" ", 2)[1]))), 16)
            emb_title = str(mes_ch[0].split(" ", 2)[2])
            emb_desc = "\n".join(mes_ch[1:])
            embed = discord.Embed(title=emb_title, description=emb_desc, color=emb_clr)
            await message.channel.send(embed=embed)
            return "exec"
        except BaseException as err:
            await message.reply(embed=eh(err))
            return "exec"
    # 超凄いサーバー監視システム
    if message.content[:4] == "n!ss":
        print(steam_server_list, type(steam_server_list))
        if message.content[:8] == "n!ss add":
            if message.content == "n!ss add":
                await message.reply("構文が異なります。\n```n!ss add [表示名] [IPアドレス],[ポート番号]```")
                return "exec"
            try:
                if message.guild.id not in steam_server_list:
                    steam_server_list[message.guild.id] = {"value": "0"}
                ad = message.content[9:].split(" ", 1)
                ad_name = str(ad[0])
                ad = ad[1].split(",", 1)
                ad_port = int(ad[1])
                ad_ip = str("".join(re.findall(r'[0-9]|\.', ad[0])))
                sset_point = int(steam_server_list[message.guild.id]["value"])
                steam_server_list[message.guild.id][f"{sset_point + 1}_ad"] = (ad_ip, ad_port)
                steam_server_list[message.guild.id][f"{sset_point + 1}_nm"] = ad_name
                steam_server_list[message.guild.id]["value"] = str(sset_point + 1)
                await message.reply(f"サーバー名：{ad_name}\nサーバーアドレス：({ad_ip},{ad_port})")
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                return "exec"
            except BaseException as err:
                await message.reply(embed=eh(err))
        if message.content[:9] == "n!ss list":
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            else:
                await message.reply(str(steam_server_list[message.guild.id]).replace('value', '保存数').replace('ad', 'アドレス').replace('nm', '名前').replace('_', '\_').replace('{', '').replace('}', ''))
                return "exec"
        if message.content[:9] == "n!ss edit":
            if message.content == "n!ss edit":
                await message.reply("構文が異なります。\n```n!ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
                return "exec"
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            adre = message.content[10:].split(" ", 3)
            s_id = int("".join(re.findall(r'[0-9]', adre[0])))
            s_nm = str(adre[1])
            s_adre = str(adre[2]).split(",", 2)
            s_port = int(s_adre[1])
            s_ip = str("".join(re.findall(r'[0-9]|\.', s_adre[0])))
            b_value = int(steam_server_list[message.guild.id]["value"])
            if b_value < s_id:
                await message.reply("そのサーバーナンバーのサーバーは登録されていません！\n`n!ss list`で確認してみてください。")
                return "exec"
            try:
                steam_server_list[message.guild.id][f"{s_id}_ad"] = (s_ip, s_port)
                steam_server_list[message.guild.id][f"{s_id}_nm"] = s_nm
                await message.reply(f"サーバーナンバー：{s_id}\nサーバー名：{s_nm}\nサーバーアドレス：{s_ip},{s_port}")
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(steam_server_list, f)
                return "exec"
            except BaseException as err:
                await message.reply(embed=eh(err))
                return "exec"
        if message.content == "n!ss del":
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            else:
                del_re = await message.reply("サーバーリストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
                await del_re.add_reaction("\U00002B55")
                await del_re.add_reaction("\U0000274C")
                return "exec"
        print(datetime.datetime.now())
        if message.content == "n!ss":
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server_list[message.guild.id]["value"])+1)):
                    print(i)
                    await server_check_async(client.loop, embed, 0, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
            print("end")
            return "exec"
        mes = message.content
        try:
            mes_te = mes.split(" ", 1)[1]
            print(mes_te)
        except BaseException as err:
            await message.reply(embed=eh(err))
            return "exec"
        if mes_te != "all":
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                server_check(embed, 0, message.guild.id, mes_te)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        elif mes_te == "all":
            if message.guild.id not in steam_server_list:
                await message.reply("サーバーは登録されていません。")
                return "exec"
            async with message.channel.typing():
                embed = discord.Embed(title="Server Status Checker", description=f"{message.author.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server_list[message.guild.id]["value"])+1)):
                    print(i)
                    await server_check_async(client.loop, embed, 1, message.guild.id, i)
                await asyncio.sleep(1)
                await message.reply(embed=embed)
        print("end")
        return "exec"
    if message.content[:5] == "n!ark":
        await message.reply(embed=discord.Embed(title="Notice", description="`n!ark`のサポートは終了しました。\n以降は`n!ss`をご利用ください。\n\n※詳しくは`n!help`でヘルプを表示してください。", color=0xffff00))
        return "exec"
    if message.content[:4] == "n!er":
        if message.content[:8] == "n!er add":
            if message.content == "n!er add":
                await message.reply("構文が異なります。\n```n!er add [トリガー] [返信文]```")
                return "exec"
            try:
                if message.guild.id not in ex_reaction_list:
                    ex_reaction_list[message.guild.id] = {"value":0}
                value = ex_reaction_list[message.guild.id]["value"]
                ra = message.content[9:].split(" ", 1)
                react_triger = ra[0]
                react_return = ra[1]
                ex_reaction_list[message.guild.id]["value"] = ex_reaction_list[message.guild.id]["value"]+1
                ex_reaction_list[message.guild.id][f'{value+1}_tr'] = str(react_triger)
                ex_reaction_list[message.guild.id][f'{value+1}_re'] = str(react_return)
                await message.reply(f"トリガー：{ra[0]}\nリターン：{ra[1]}")
                with open('ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(ex_reaction_list, f)
                return "exec"
            except BaseException as err:
                await message.reply(embed=eh(err))
        if message.content[:9] == "n!er list":
            if message.guild.id not in ex_reaction_list or ex_reaction_list[message.guild.id]["value"] == 0:
                await message.reply("追加返答は設定されていません。")
                return "exec"
            else:
                embed = discord.Embed(title="追加返答リスト", description="- にらBOT", color=0x00ff00)
                for i in range(int(ex_reaction_list[message.guild.id]["value"])):
                    embed.add_field(name=f"トリガー：{ex_reaction_list[message.guild.id][f'{i+1}_tr']}", value=f"リターン：{ex_reaction_list[message.guild.id][f'{i+1}_re']}", inline=False)
                await message.reply(embed=embed)
                return "exec"
        if message.content[:9] == "n!er edit":
            if message.content == "n!er edit":
                await message.reply("構文が異なります。\n```n!er edit [トリガー] [返信文]```")
                return "exec"
            if message.guild.id not in ex_reaction_list:
                await message.reply("追加反応は登録されていません。")
                return "exec"
            if ex_reaction_list[message.guild.id]["value"] == 0:
                await message.reply("追加反応は登録されていません。")
                return "exec"
            ssrt = message.content[10:].split(" ", 2)
            b_tr = ssrt[0]
            b_re = ssrt[1]
            try:
                rt_e = 0
                for i in range(math.floor((len(ex_reaction_list[message.guild.id])-1)/2)):
                    if ex_reaction_list[message.guild.id][f"{i+1}_tr"] == b_tr:
                        await message.reply((ex_reaction_list[message.guild.id][f"{i+1}_tr"], ex_reaction_list[message.guild.id][f"{i+1}_re"]))
                        ex_reaction_list[message.guild.id][f"{i+1}_re"] = b_re
                        await message.reply((ex_reaction_list[message.guild.id][f"{i+1}_tr"], ex_reaction_list[message.guild.id][f"{i+1}_re"]))
                        rt_e = 1
                        break
                if rt_e == 1:
                    await message.reply(f"トリガー：{b_tr}\nリターン：{b_re}")
                    with open('ex_reaction_list.nira', 'wb') as f:
                        pickle.dump(ex_reaction_list, f)
                    return "exec"
                elif rt_e == 0:
                    await message.reply("そのトリガーは登録されていません！")
                    return "exec"
            except BaseException as err:
                await message.reply(embed=eh(err))
                return "exec"
        if message.content == "n!er del":
            if message.guild.id not in ex_reaction_list:
                await message.reply("追加返答は設定されていません。")
                return "exec"
            else:
                del_re = await message.reply("追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
                await del_re.add_reaction("\U00002B55")
                await del_re.add_reaction("\U0000274C")
                return "exec"
        return "exec"
    if message.content[:3] == "n!d":
        if message.content == "n!d":
            user = await client.fetch_user(message.author.id)
            embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
            await message.reply(embed=embed)
            return "exec"
        else:
            user_id = int("".join(re.findall(r'[0-9]', message.content[4:])))
            try:
                user = await client.fetch_user(user_id)
                embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
                embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
                await message.reply(embed=embed)
                return "exec"
            except BaseException:
                await message.reply(embed=discord.Embed(title="Error", description="ユーザーが存在しないか、データが取得できませんでした。", color=0xff0000))
                return "exec"
