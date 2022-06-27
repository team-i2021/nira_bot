import logging
import traceback
import requests
import websockets
from util import admin_check, n_fc, eh, database
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import nextcord
import os
import pickle
import shutil
import subprocess
from subprocess import PIPE
import re
import asyncio
import json
from util import slash_tool

from cogs import normal_reaction as nr
import importlib

import HTTP_db

import sys

from nextcord.ext.commands.core import command

sys.path.append('../')


# loggingの設定
dir = sys.path[0]


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message


logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)


home_dir = os.path.dirname(__file__)[:-4]

# 管理者向けdebug

DBS = database.openSheet()
DATABASE_KEY = "B2"


def save():
    for i in range(len(n_fc.save_list)):
        with open(f'{home_dir}/{n_fc.save_list[i]}.nira', 'wb') as f:
            exec(f"pickle.dump(n_fc.{n_fc.save_list[i]}, f)")


def load():
    func_error_count = 0
    nira_f_num = len(os.listdir(home_dir))
    system_list = os.listdir(home_dir)
    logging.info((nira_f_num, system_list))
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
        logging.info("変数の読み込みに失敗しました。")


async def base_cog(bot, ctx, command, name):
    if ctx.message == None:
        type = 0
    else:
        type = 1
    if ctx.author.id in n_fc.py_admin:
        if type == 0 and command == None and name == None or type == 1 and ctx.message.content == "n!cog":
            embed = nextcord.Embed(
                title="cogs", description="`extension`", color=0x00ff00)
            embed.add_field(
                name="Cog Names", value="表示されている名前は、`cog.[Cog name]`のcog nameです。", inline=False)
            embed.add_field(
                name="amuse", value="娯楽系のコマンド。\n`janken`/`uranai`/`dice`")
            embed.add_field(
                name="bump", value="bump通知の設定コマンド及び、Bump取得とメッセージ送信。\n`bump`")
            embed.add_field(name="check", value="管理者チェックをするコマンド。\n`check`")
            embed.add_field(
                name="debug", value="管理者用コマンド。\n`create`/`py_exec`/`read`/`restart`/`exit`/`py`/`sh`/`save`/`cog`")
            embed.add_field(name="embed", value="Embed送信用コマンド。\n`embed`")
            embed.add_field(name="get_reaction", value="リアクションを受け取った際のイベント。")
            embed.add_field(name="info", value="にらBOTの情報系コマンド。\n`info`/`help`")
            embed.add_field(
                name="music", value="音楽再生(VC)に関するコマンド。\n`join`/`play`/`pause`/`resume`/`stop`/`leave`")
            embed.add_field(name="normal_reaction",
                            value="送信されたメッセージに反応するイベント。")
            embed.add_field(name="ping", value="pingコマンド。\n`ping`")
            embed.add_field(name="reaction", value="反応系コマンド。\n`nr`/`er`/`ar`")
            embed.add_field(name="siritori", value="しりとり系コマンド。\n`srtr`")
            embed.add_field(name="user_join", value="ユーザーがguildに入った際のイベント。")
            embed.add_field(name="user", value="ユーザー情報表示系コマンド。\n`d`/`ui`")
            embed.add_field(
                name="Cog function", value="cog系のコマンドです。`[Cog name]`には「`cog.`」を抜いたCogの名前だけを入力してください。", inline=False)
            embed.add_field(name="`/cog`/`n!cog`", value="cogの情報を表示します。")
            embed.add_field(
                name="`/cog reload [Cog name]`/`n!cog reload [Cog name]`", value="指定したCogをリロードします。")
            embed.add_field(
                name="`/cog load [Cog name]`/`n!cog load [Cog name]`", value="指定したCogをロードします。")
            embed.add_field(
                name="`/cog unload [Cog name]`/`n!cog unload [Cog name]`", value="指定したCogをアンロードします。")
            if type == 0:
                await ctx.respond(embed=embed)
            else:
                await ctx.reply(embed=embed)
            return
        elif type == 0 and command == "reload" and name != None or ctx.message.content[:12] == "n!cog reload":
            if type == 0:
                try:
                    bot.reload_extension(f"cogs.{name}")
                    await ctx.respond(f"リロードしました。")
                except BaseException as err:
                    await ctx.respond(f"リロードできませんでした。\n```{err}```")
            else:
                try:
                    bot.reload_extension(f"cogs.{ctx.message.content[13:]}")
                    await ctx.reply(f"リロードしました。")
                except BaseException as err:
                    await ctx.reply(f"リロードできませんでした。\n```{err}```")
        elif type == 0 and command == "load" and name != None or ctx.message.content[:10] == "n!cog load":
            if type == 0:
                try:
                    bot.reload_extension(f"cogs.{name}")
                    await ctx.respond(f"ロードしました。")
                except BaseException as err:
                    await ctx.respond(f"ロードできませんでした。\n```{err}```")
            else:
                try:
                    bot.load_extension(f"cogs.{ctx.message.content[11:]}")
                    await ctx.reply(f"ロードしました。")
                except BaseException as err:
                    await ctx.reply(f"ロードできませんでした。\n```{err}```")
        elif type == 0 and command == "unload" and name != None or ctx.message.content[:12] == "n!cog unload":
            if type == 0:
                try:
                    bot.unload_extension(f"cogs.{name}")
                    await ctx.respond(f"アンロードしました。")
                except BaseException as err:
                    await ctx.respond(f"アンロードできませんでした。\n```{err}```")
            else:
                try:
                    bot.unload_extension(f"cogs.{ctx.message.content[13:]}")
                    await ctx.reply(f"アンロードしました。")
                except BaseException as err:
                    await ctx.reply(f"アンロードできませんでした。\n```{err}```")
        elif type == 0 and command == "list" or ctx.message.content == "n!cog list":
            await ctx.reply(list(dict(bot.cogs).keys()))
        elif type == 0 and command == None or type == 0 and name == None:
            await ctx.respond("コマンドの引数が異常です。")
    else:
        if type == 0:
            await ctx.respond("管理者権限が必要です。")
        else:
            await ctx.reply("管理者権限が必要です。")
    return

class debug(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{dir}/setting.json', 'r'))["database_data"]
        self.client = HTTP_db.Client(
            url=datas["address"],
            port=datas["port"],
            password=open(f"{dir}/password").read()
        )

    async def ws(self, websocket, path):
        async for message in websocket:
            try:
                if message == "exit":
                    logging.info("Exit websocket...")
                    await websocket.close()
                    self.websocket_coro.cancel()
                    break
                    return
                elif message == "guilds":
                    await websocket.send(str(len(self.bot.guilds)))
                elif message == "users":
                    await websocket.send(str(len(self.bot.users)))
                elif message == "voice_clients":
                    await websocket.send(str(len(self.bot.voice_clients)))
                elif message == "GetLaunchData":
                    SETTING = json.load(
                        open(f'{sys.path[0]}/setting.json', 'r'))
                    TOKEN = SETTING["tokens"]["nira_bot"]
                    PREFIX = SETTING["prefix"]
                    await websocket.send(f"{PREFIX}@{TOKEN}")
                else:
                    rt = None
                    if re.search("await", message):
                        await exec(f"""{message}""")
                    else:
                        exec(f"""{message}""")
                    await websocket.send(str(rt))
            except BaseException as err:
                await websocket.send(f"An error has occured:{err}")

    async def ws_main(self, port):
        logging.info("Websocket....")
        async with websockets.serve(self.ws, "0.0.0.0", int(port)):
            await asyncio.Future()

    @commands.command()
    async def websocket(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            port = ctx.message.content.split(" ", 1)[1]
            try:
                await ctx.message.add_reaction("\U0001F310")
                self.websocket_coro = asyncio.create_task(self.ws_main(port))
                await self.websocket_coro
            except BaseException as err:
                logging.info(traceback.format_exc())
            await ctx.message.add_reaction("\U00002705")
        else:
            await ctx.message.reply(embed=nextcord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))

    @commands.command()
    async def restart(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            def check(m):
                return (m.content == 'y' or m.content == 'n') and m.author == ctx.author and m.channel == ctx.channel
            restart_code = await ctx.reply("```\nnira@nira-bot $ sudo restart nira-bot\nAre you sure want to restart nira-bot?[y/n]```")
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                await restart_code.edit(content="```\nnira@nira-bot $ sudo restart nira-bot\nAre you sure want to restart nira-bot?[y/n]\nTimed out.\nThe restart operation has been canceled.(timed out)```")
                return
            if msg.content == "n":
                await restart_code.edit(content="```\nnira@nira-bot $ sudo restart nira-bot\nAre you sure want to restart nira-bot?[y/n]\nn\nThe restart operation has been canceled.(user operation)```")
                return
            await self.bot.change_presence(activity=nextcord.Game(name="再起動中...", type=1), status=nextcord.Status.dnd)
            try:
                save()
                await restart_code.edit(content="```\nnira@nira-bot $ sudo restart nira-bot\nAre you sure want to restart nira-bot?[y/n]\ny\nRestarting nira-bot now...```")
                logging.info("-----[n!restart]コマンドが実行されたため、再起動します。-----")
                subprocess.run(
                    f'sudo systemctl restart nira',
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,
                    text=True
                )
                return
            except BaseException as err:
                await ctx.message.reply(f"An error has occurred during restart operation.\n```\n{err}```")
                await self.bot.change_presence(activity=nextcord.Game(name="n!help", type=1), status=nextcord.Status.idle)
                return
        else:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def exit(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            def check(m):
                return (m.content == 'y' or m.content == 'n') and m.author == ctx.author and m.channel == ctx.channel
            exit_code = await ctx.reply("```\nnira@nira-bot $ sudo shutdown nira-bot\nAre you sure want to shutdown nira-bot?[y/n]```")
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                await exit_code.edit(content="```\nnira@nira-bot $ sudo shutdown nira-bot\nAre you sure want to shutdown nira-bot?[y/n]\nTimed out.\nThe shutdown operation has been canceled.(timed out)```")
                return
            if msg.content == "n":
                await exit_code.edit(content="```\nnira@nira-bot $ sudo shutdown nira-bot\nAre you sure want to shutdown nira-bot?[y/n]\nn\nThe shutdown operation has been canceled.(user operation)```")
                return
            await self.bot.change_presence(activity=nextcord.Game(name="終了中...", type=1), status=nextcord.Status.dnd)
            await exit_code.edit(content="終了準備中...")
            try:
                save()
                await exit_code.edit(content="```\nnira@nira-bot $ sudo shutdown nira-bot\nAre you sure want to shutdown nira-bot?[y/n]\ny\nShutdowning nira-bot now...```")
                logging.info("-----[n!exit]コマンドが実行されたため、終了します。-----")
                await self.bot.close()
                subprocess.run(
                    f'sudo systemctl stop nira',
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,
                    text=True
                )
                return
            except BaseException as err:
                await ctx.message.reply(f"An error has occurred during shutdown operation.\n```\n{err}```")
                await self.bot.change_presence(activity=nextcord.Game(name="n!help", type=1), status=nextcord.Status.idle)
                return
        else:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def py(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content == "n!py":
            embed = nextcord.Embed(
                title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content[:10] == "n!py await":
            if ctx.message.author.id not in n_fc.py_admin:
                embed = nextcord.Embed(
                    title="Error", description="You don't have the required permission!", color=0xff0000)
                await ctx.message.repcly(embed=embed)
                await ctx.message.add_reaction("\U0000274C")
                return
            if ctx.message.content == "n!py await":
                embed = nextcord.Embed(
                    title="Error", description="The command has no enough arguments!", color=0xff0000)
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
                    embed = nextcord.Embed(
                        title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
            else:
                try:
                    exec(mes[i])
                    cmd_rt.append("")
                except BaseException as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = nextcord.Embed(
                        title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
        await ctx.message.add_reaction("\U0001F197")
        return

    @commands.command()
    async def sh(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        else:
            if ctx.message.content == "n!sh":
                embed = nextcord.Embed(
                    title="Error", description="The command has no enough arguments!", color=0xff0000)
                await ctx.message.reply(embed=embed)
                await ctx.message.add_reaction("\U0000274C")
                return
            mes_sh = ctx.message.content[5:].splitlines()
            sh_nm = len(mes_sh)
            sh_rt = []
            print(mes_sh)
            for i in range(sh_nm):
                try:
                    export = subprocess.run(
                        f'{mes_sh[i]}', stdout=PIPE, stderr=PIPE, shell=True, text=True)
                    sh_rt.append(export.stdout)
                except BaseException as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = nextcord.Embed(
                        title="Error", description=f"Shell error has occurred!\n・Pythonエラー```{err}```\n・スクリプトエラー```{export.stdout}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
            await ctx.message.add_reaction("\U0001F197")
            for i in range(len(sh_rt)):
                rt_sh = "\n".join(sh_rt)
            await ctx.message.reply(f"```{rt_sh}```")
            return

    @commands.command()
    async def save(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            try:
                save()
                await ctx.message.reply("Saved.")
                logging.info("変数をセーブしました。")
            except BaseException as err:
                await ctx.message.reply(f"Error happend.\n`{err}`")
            return
        else:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @nextcord.slash_command(name="extension", description="Manage cogs.", guild_ids=n_fc.GUILD_IDS)
    async def cog_slash(self, interaction):
        pass

    @cog_slash.subcommand(name="list", description="List cogs.")
    async def list_cog_slash(self, interaction):
        await interaction.response.send_message(f"```py\n{list(dict(self.bot.cogs).keys())}```", ephemeral=True)

    @cog_slash.subcommand(name="load", description="Load cog.")
    async def load_cogs_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        await interaction.response.defer()
        try:
            self.bot.load_extension(f"cogs.{cogname}")
            await interaction.followup.send(f"The cog `cogs.{cogname}` successfully loaded.", ephemeral=True)
        except BaseException as err:
            await interaction.followup.send(f"Failed to load cog `cogs.{cogname}`.\n```py\n{err}```", ephemeral=True)

    @cog_slash.subcommand(name="reload", description="Reload cog.")
    async def reload_cogs_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        await interaction.response.defer()
        try:
            self.bot.reload_extension(f"cogs.{cogname}")
            await interaction.followup.send(f"The cog `cogs.{cogname}` successfully reloaded.", ephemeral=True)
        except BaseException as err:
            await interaction.followup.send(f"Failed to reload cog `cogs.{cogname}`.\n```py\n{err}```", ephemeral=True)

    @cog_slash.subcommand(name="unload", description="Unload cog.")
    async def unload_cogs_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        await interaction.response.defer()
        try:
            self.bot.unload_extension(f"cogs.{cogname}")
            await interaction.followup.send(f"The cog `cogs.{cogname}` successfully unloaded.", ephemeral=True)
        except BaseException as err:
            await interaction.followup.send(f"Failed to unload cog `cogs.{cogname}`.\n```py\n{err}```", ephemeral=True)

    @commands.command(name="cog", help="Manage cogs.")
    async def cog(self, ctx: commands.Context):
        command = None
        name = None
        await base_cog(self.bot, ctx, command, name)
        return

    @commands.command()
    async def reaction(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return
        else:
            if ctx.message.content == "n!reaction":
                await ctx.reply("引数「ReplyID」が足りません。")
                return
            if ctx.message.content == "n!reaction reload":
                importlib.reload(nr)
                await ctx.reply("End")
            try:
                await nr.n_reaction(ctx.message, int(ctx.message.content.split(" ", 1)[1]))
            except BaseException as err:
                await ctx.reply(f"```{err}```")

    @commands.command()
    async def debug(self, ctx: commands.Context):
        if ctx.author.id in n_fc.py_admin:
            if ctx.message.content == "n!debug reload":
                message = await ctx.reply("変数の再ロードをしています...")
                try:
                    save()
                    importlib.reload(n_fc)
                    load()
                    SETTING = json.load(
                        open(f'{sys.path[0]}/setting.json', 'r'))
                    n_fc.py_admin = SETTING["py_admin"]
                    n_fc.GUILD_IDS = SETTING["guild_ids"]
                except BaseException as err:
                    await message.edit(content=f"エラーが発生しました。{err}")
                    return
                await message.edit(content=f"変数の読み込みが完了しました。\nAdmin:{n_fc.py_admin}")

    @commands.command()
    async def lb(self, ctx):
        return

    @nextcord.slash_command(name="db", description="database")
    async def db(self, interaction: Interaction):
        pass

    @db.subcommand(name="get", description="Method POST:/get")
    async def db_get(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            key = int(key)
        except ValueError:
            pass
        try:
            value = await self.client.get(key)
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/get", description=f"```\n{value}```", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/get", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="get_all", description="Method POST:/get_all")
    async def db_get_all(self, interaction: Interaction):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            value = await self.client.get_all()
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/get_all", description=f"```\n{value}```", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/get_all", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="post", description="Method POST:/post")
    async def db_post(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True), value: str = SlashOption(name="value", description="value", required=True)):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            key = int(key)
        except ValueError:
            pass
        try:
            value = int(value)
        except ValueError:
            pass
        try:
            await self.client.post(key, value)
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/post", description=f"```\n{value}```", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/post", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="exists", description="Method POST:/exists")
    async def db_exists(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            key = int(key)
        except ValueError:
            pass
        try:
            value = await self.client.exists(key)
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/exists", description=f"```\n{value}```", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/exists", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="delete", description="Method POST:/delete")
    async def db_delete(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            key = int(key)
        except ValueError:
            pass
        try:
            await self.client.delete(key)
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/delete", description=f"```\n{key}```", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/delete", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="delete_all", description="Method POST:/delete_all")
    async def db_delete_all(self, interaction: Interaction):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            await self.client.delete_all()
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/delete_all", description="", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="POST:/delete_all", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="info", description="Method GET:/info")
    async def db_info(self, interaction: Interaction):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            value = await self.client.info()
            await interaction.response.send_message(embed=nextcord.Embed(title="GET:/info", description=f"{value}", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="GET:/info", description=f"```\n{err}```", color=0xFF0000))

    @db.subcommand(name="ping", description="Method GET:/ping")
    async def db_ping(self, interaction: Interaction):
        if not self.bot.is_owner(interaction.user):
            raise Exception("Forbidden")
        try:
            value = await self.client.ping()
            await interaction.response.send_message(embed=nextcord.Embed(title="GET:/ping", description=f"{round(float(value.ping) * 1000, 2)}ms", color=0x00ff00))
        except HTTP_db.HTTP_db_Exception as err:
            await interaction.response.send_message(embed=nextcord.Embed(title="GET:/ping", description=f"```\n{err}```", color=0xFF0000))


def setup(bot):
    bot.add_cog(debug(bot))
    importlib.reload(slash_tool)
