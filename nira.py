# coding: utf-8
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

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle

##### BOTの設定 #####
intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix="n!", intents=intents, help_command=None)
buttons = ButtonsClient(bot)

bot.load_extension("jishaku")

async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner

bot.remove_command("help")

#cogのロード(そのうちちゃんとまとめます)
bot.load_extension("cogs.amuse")
bot.load_extension("cogs.check")
bot.load_extension("cogs.debug")
bot.load_extension("cogs.embed")
bot.load_extension("cogs.get_reaction")
bot.load_extension("cogs.info")
bot.load_extension("cogs.music")
bot.load_extension("cogs.normal_reaction")
bot.load_extension("cogs.ping")
bot.load_extension("cogs.reaction")
bot.load_extension("cogs.siritori")
bot.load_extension("cogs.user_join")
bot.load_extension("cogs.user")

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


##### ボタンのせいでまだ唯一移植できてない「n!ss」コマンド #####
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
            await ctx.message.reply(embed=eh.eh(err))
    if ctx.message.content[:9] == "n!ss list":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        else:
            if admin_check(ctx.message.guild, ctx.message.author):
                user = await bot.fetch_user(ctx.message.author.id)
                embed = discord.Embed(title="Steam Server List", description=f"「{ctx.message.guild.name}」のサーバーリスト\n```保存数：{str(n_fc.steam_server_list[ctx.message.guild.id]['value'])}```", color=0x00ff00)
                for i in range(int(n_fc.steam_server_list[ctx.message.guild.id]['value'])):
                    embed.add_field(name=f"保存名：`{str(n_fc.steam_server_list[ctx.message.guild.id][f'{i+1}_nm'])}`", value=f"アドレス：`{str(n_fc.steam_server_list[ctx.message.guild.id][f'{i+1}_ad'])}`")
                await user.send(embed=embed)
                await ctx.message.add_reaction("\U00002705")
                return
            else:
                await ctx.message.reply(embed=discord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
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
            await ctx.message.reply(embed=eh.eh(err))
            return
    if ctx.message.content[:8] == "n!ss del":
        if ctx.message.guild.id not in n_fc.steam_server_list:
            await ctx.message.reply("サーバーは登録されていません。")
            return
        if ctx.message.content != "n!ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except BaseException as err:
                await ctx.message.reply(embed=eh.eh(err))
                return
            if admin_check(ctx.message.guild, ctx.message.author):
                if del_num > int(n_fc.steam_server_list[ctx.message.guild.id]["value"]):
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="そのサーバーは登録されていません！\n`n!ss list`で確認してみてください！", color=0xff0000))
                    return
                if del_num <= 0:
                    await ctx.message.reply(embed=discord.Embed(title="エラー", description="リストで0以下のナンバーは振り当てられていません。", color=0xff0000))
                    return
                try:
                    all_value = int(n_fc.steam_server_list[ctx.message.guild.id]["value"])
                    print(all_value)
                    for i in range(all_value - del_num):
                        print(i)
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_nm"] = n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i}_nm"]
                        n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i - 1}_ad"] = n_fc.steam_server_list[ctx.message.guild.id][f"{del_num + i}_ad"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_nm"]
                    del n_fc.steam_server_list[ctx.message.guild.id][f"{all_value}_ad"]
                    n_fc.steam_server_list[ctx.message.guild.id]["value"] = all_value - 1
                    await ctx.message.reply(embed=discord.Embed(title="削除", description=f"ID:{del_num}のサーバーをリストから削除しました。", color=0xff0000))   
                except BaseException as err:
                    print(err)
                    await ctx.message.reply(embed=eh.eh(err))
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
        await ctx.message.reply(embed=eh.eh(err))
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


# Botの起動とDiscordサーバーへの接続
bot.run(bot_token.nira_token)