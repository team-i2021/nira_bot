import asyncio
import importlib
import json
import logging
import os
import pickle
import platform
import re
import shutil
import subprocess
import sys
import traceback
import psutil
import websockets
from subprocess import PIPE

import nextcord
import requests
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from cogs import normal_reaction as nr
from util import admin_check, n_fc, eh, database, slash_tool

import HTTP_db

SYSDIR = sys.path[0]

# 管理者向けdebug

def save():
    for i in range(len(n_fc.save_list)):
        with open(f'{SYSDIR}/{n_fc.save_list[i]}.nira', 'wb') as f:
            exec(f"pickle.dump(n_fc.{n_fc.save_list[i]}, f)")


def load():
    func_error_count = 0
    nira_f_num = len(os.listdir(SYSDIR))
    system_list = os.listdir(SYSDIR)
    logging.info((nira_f_num, system_list))
    for i in range(nira_f_num):
        logging.info(f"StartProcess:{system_list[i]}")
        if system_list[i][-5:] != ".nira":
            logging.info(f"Skip:{system_list[i]}")
            continue
        try:
            cog_name = system_list[i][:-5]
            with open(f'{SYSDIR}/{system_list[i]}', 'rb') as f:
                exec(f"n_fc.{cog_name} = pickle.load(f)")
            logging.info(f"変数[{system_list[i]}]のファイル読み込みに成功しました。")
            if system_list[i] == "notify_token.nira":
                logging.info("LINE NotifyのTOKENのため、表示はされません。")
            else:
                exec(f"logging.info(n_fc.{cog_name})")
        except Exception as err:
            logging.info(f"変数[{system_list[i]}]のファイル読み込みに失敗しました。\n{err}")
            func_error_count = 1
    if func_error_count > 0:
        logging.info("変数の読み込みに失敗しました。")

class debug(commands.Cog):
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot
        self.client = kwargs["client"]

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
            except Exception as err:
                await websocket.send(f"An error has occured:{err}")

    async def ws_main(self, port):
        logging.info("Websocket....")
        async with websockets.serve(self.ws, "0.0.0.0", int(port)):
            await asyncio.Future()

    @commands.command()
    async def websocket(self, ctx: commands.Context):
        if (await self.bot.is_owner(ctx.author)):
            port = ctx.message.content.split(" ", 1)[1]
            try:
                await ctx.message.add_reaction("\U0001F310")
                self.websocket_coro = asyncio.create_task(self.ws_main(port))
                await self.websocket_coro
            except Exception as err:
                logging.info(traceback.format_exc())
            await ctx.message.add_reaction("\U00002705")
        else:
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"You don't have the required permission.", color=0xff0000))

    @commands.command()
    async def restart(self, ctx: commands.Context):
        if (await self.bot.is_owner(ctx.author)):
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
                logging.info(
                    f"-----[{self.bot.command_prefix}restart]コマンドが実行されたため、再起動します。-----")
                subprocess.run(
                    f'sudo systemctl restart nira',
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,
                    text=True
                )
                return
            except Exception as err:
                await ctx.reply(f"An error has occurred during restart operation.\n```\n{err}```")
                await self.bot.change_presence(activity=nextcord.Game(name=f"{self.bot.command_prefix}help", type=1), status=nextcord.Status.idle)
                return
        else:
            embed = nextcord.Embed(
                title="Error", description=f"You don't have the required permission.", color=0xff0000)
            await ctx.reply(embed=embed)
            return

    @commands.command()
    async def exit(self, ctx: commands.Context):
        if (await self.bot.is_owner(ctx.author)):
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
                logging.info(
                    f"-----[{self.bot.command_prefix}exit]コマンドが実行されたため、終了します。-----")
                await self.bot.close()
                subprocess.run(
                    f'sudo systemctl stop nira',
                    stdout=PIPE,
                    stderr=PIPE,
                    shell=True,
                    text=True
                )
                return
            except Exception as err:
                await ctx.reply(f"An error has occurred during shutdown operation.\n```\n{err}```")
                await self.bot.change_presence(activity=nextcord.Game(name=f"{self.bot.command_prefix}help", type=1), status=nextcord.Status.idle)
                return
        else:
            embed = nextcord.Embed(
                title="Error", description=f"You don't have the required permission.", color=0xff0000)
            await ctx.reply(embed=embed)
            return

    @commands.command()
    async def py(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error", description=f"You don't have the required permission.", color=0xff0000)
            await ctx.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content == f"{self.bot.command_prefix}py":
            embed = nextcord.Embed(
                title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content.startswith(f"{self.bot.command_prefix}py await"):
            if ctx.author.id not in n_fc.py_admin:
                embed = nextcord.Embed(
                    title="Error", description=f"You don't have the required permission.", color=0xff0000)
                await ctx.message.repcly(embed=embed)
                await ctx.message.add_reaction("\U0000274C")
                return
            if ctx.message.content == f"{self.bot.command_prefix}py await":
                embed = nextcord.Embed(
                    title="Error", description="The command has no enough arguments!", color=0xff0000)
                await ctx.reply(embed=embed)
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
                except Exception as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = nextcord.Embed(
                        title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.reply(embed=embed)
                    return
            else:
                try:
                    exec(mes[i])
                    cmd_rt.append("")
                except Exception as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = nextcord.Embed(
                        title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.reply(embed=embed)
                    return
        await ctx.message.add_reaction("\U0001F197")
        return

    @commands.command()
    async def sh(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error", description=f"You don't have the required permission.", color=0xff0000)
            await ctx.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        else:
            if ctx.message.content == f"{self.bot.command_prefix}sh":
                embed = nextcord.Embed(
                    title="Error", description="The command has no enough arguments!", color=0xff0000)
                await ctx.reply(embed=embed)
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
                except Exception as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = nextcord.Embed(
                        title="Error", description=f"Shell error has occurred!\n・Pythonエラー```{err}```\n・スクリプトエラー```{export.stdout}```", color=0xff0000)
                    await ctx.reply(embed=embed)
                    return
            await ctx.message.add_reaction("\U0001F197")
            for i in range(len(sh_rt)):
                rt_sh = "\n".join(sh_rt)
            await ctx.reply(f"```{rt_sh}```")
            return

    @commands.command()
    async def save(self, ctx: commands.Context):
        if (await self.bot.is_owner(ctx.author)):
            try:
                save()
                await ctx.reply("Saved.")
                logging.info("変数をセーブしました。")
            except Exception as err:
                await ctx.reply(f"Error happend.\n`{err}`")
            return
        else:
            embed = nextcord.Embed(
                title="Error", description=f"You don't have the required permission.", color=0xff0000)
            await ctx.reply(embed=embed)
            return

    @nextcord.slash_command(name="debug", description="Debug commands", guild_ids=n_fc.GUILD_IDS)
    async def debug_slash(self, interaction):
        pass

    @debug_slash.subcommand(name="extension", description="Manage extensions")
    async def extension_slash(self, interaction):
        pass

    @extension_slash.subcommand(name="list", description="List extensions.")
    async def list_extension_slash(self, interaction):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(f"```py\n{list(dict(self.bot.cogs).keys())}```", ephemeral=True)
        else:
            raise Exception("Forbidden")

    @extension_slash.subcommand(name="load", description="Load extension.")
    async def load_extension_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.defer()
            try:
                self.bot.load_extension(cogname, extras={"client", self.client})
                await interaction.followup.send(f"The cog `{cogname}` successfully loaded.", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"Failed to load cog `{cogname}`.\n```py\n{err}```", ephemeral=True)
        else:
            raise Exception("Forbidden")

    @extension_slash.subcommand(name="reload", description="Reload extension.")
    async def reload_extension_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.defer()
            try:
                self.bot.unload_extension(cogname)
                self.bot.load_extension(f"{cogname}", extras={"client", self.client})
                await interaction.followup.send(f"The cog `{cogname}` successfully reloaded.", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"Failed to reload cog `{cogname}`.\n```py\n{err}```", ephemeral=True)
        else:
            raise Exception("Forbidden")

    @extension_slash.subcommand(name="unload", description="Unload extension.")
    async def unload_extension_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.defer()
            try:
                self.bot.unload_extension(cogname)
                await interaction.followup.send(f"The cog `{cogname}` successfully unloaded.", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"Failed to unload cog `{cogname}`.\n```py\n{err}```", ephemeral=True)
        else:
            raise Exception("Forbidden")

    @debug_slash.subcommand(name="info", description="Show debug info.")
    async def info_slash(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        os = platform.system()
        try:
            ping = f"{round((await self.client.ping()).ping * 1000, 2)}ms"
        except Exception:
            ping = "Connection Error"
        embed = nextcord.Embed(
            title="Debug info",
            description=f"Hosting on {os}",
            color=0x363636
        )
        embed.add_field(
            name="CPU",
            value=f"{psutil.cpu_percent(None)}%"
        )
        embed.add_field(
            name="RAM",
            value=f"{psutil.virtual_memory().percent}%"
        )
        embed.add_field(
            name="Ping(Discord)",
            value=f"{round(self.bot.latency * 1000, 2)}ms"
        )
        embed.add_field(
            name="Ping(HTTP_db)",
            value=ping
        )
        embed.add_field(
            name="Guilds",
            value=f"{len(self.bot.guilds)}"
        )
        embed.add_field(
            name="Users",
            value=f"{len(self.bot.users)}"
        )
        embed.add_field(
            name="VoiceClients",
            value=f"{len(self.bot.voice_clients)}"
        )
        embed.add_field(
            name="Extensions",
            value=f"```\n{list(dict(self.bot.cogs).keys())}```",
            inline=False
        )
        await interaction.followup.send(embed=embed, username="Debug info")

    @debug_slash.subcommand(name="db", description="database")
    async def db(self, interaction: Interaction):
        pass

    @db.subcommand(name="get", description="Method POST:/get")
    async def db_get(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            key = eval(key)
            value = await self.client.get(key)
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/get", description=f"```\n{value}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/get", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="get_all", description="Method POST:/get_all")
    async def db_get_all(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            value = await self.client.get_all()
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/get_all", description=f"```\n{value}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/get_all", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="post", description="Method POST:/post")
    async def db_post(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True), value: str = SlashOption(name="value", description="value", required=True)):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            key = eval(key)
            value = eval(value)
            await self.client.post(key, value)
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/post", description=f"```\n{value}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/post", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="exists", description="Method POST:/exists")
    async def db_exists(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            key = eval(key)
            value = await self.client.exists(key)
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/exists", description=f"```\n{value}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/exists", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="delete", description="Method POST:/delete")
    async def db_delete(self, interaction: Interaction, key: str = SlashOption(name="key", description="key", required=True)):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            key = eval(key)
            await self.client.delete(key)
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/delete", description=f"```\n{key}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="POST:/delete", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

#    @db.subcommand(name="delete_all", description="Method POST:/delete_all")
#    async def db_delete_all(self, interaction: Interaction):
#        if not (await self.bot.is_owner(interaction.user)):
#            raise Exception("Forbidden")
#        await interaction.response.defer()
#        try:
#            await self.client.delete_all()
#            await interaction.followup.send(embed=nextcord.Embed(title="POST:/delete_all", description="", color=0x00ff00))
#        except Exception:
#            await interaction.followup.send(embed=nextcord.Embed(title="POST:/delete_all", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="info", description="Method GET:/info")
    async def db_info(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            value = await self.client.info()
            await interaction.followup.send(embed=nextcord.Embed(title="GET:/info", description=f"{value}", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="GET:/info", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="ping", description="Method GET:/ping")
    async def db_ping(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            value = await self.client.ping()
            await interaction.followup.send(embed=nextcord.Embed(title="GET:/ping", description=f"{round(float(value.ping) * 1000, 2)}ms", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="GET:/ping", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @db.subcommand(name="reload", description="Reload databse module")
    async def db_reload(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            importlib.reload(HTTP_db)
            importlib.reload(database)
            await interaction.followup.send(embed=nextcord.Embed(title="RELOAD MODULES", description=f"Reloaded.\nHTTP_db:`{HTTP_db.__version__}`\nutil.database:`{database.__version__}`", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="RELOAD MODULES", description=f"```\n{traceback.format_exc()}```", color=0xff0000))

    @debug_slash.subcommand(name="command", description="Manage commands")
    async def command_slash(self, interaction):
        pass

    @command_slash.subcommand(name="list", description="List commands")
    async def command_slash_list(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.send_message(embed=nextcord.Embed(title="COMMANDS", description=f"```py\n{self.bot.all_commands.keys()}```", color=0x00ff00))
        return

    @command_slash.subcommand(name="sync", description="sync application command")
    async def command_slash_sync(
        self,
        interaction: Interaction,
        guild_id: str = SlashOption(name="guild_id", description="Guild id", required=False),
    ):
        if not (await self.bot.is_owner(interaction.user)):
            raise Exception("Forbidden")
        await interaction.response.defer()
        try:
            if not guild_id:
                guild_id = None
            else:
                guild_id = eval(guild_id)
            await self.bot.sync_application_commands(guild_id=guild_id)
            await interaction.followup.send(embed=nextcord.Embed(title="SYNC", description=f"```\n{guild_id}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="SYNC", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @commands.command()
    async def reaction(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            embed = nextcord.Embed(
                title="Error",
                description=f"You don't have the required permission.",
                color=0xff0000
            )
            await ctx.reply(embed=embed)
            return
        else:
            if ctx.message.content == f"{self.bot.command_prefix}reaction":
                await ctx.reply("引数「ReplyID」が足りません。")
                return
            if ctx.message.content == f"{self.bot.command_prefix}reaction reload":
                importlib.reload(nr)
                await ctx.reply("End")
            try:
                await nr.n_reaction(ctx.message, int(ctx.message.content.split(" ", 1)[1]))
            except Exception as err:
                await ctx.reply(f"```{err}```")

    @commands.command()
    async def debug(self, ctx: commands.Context, action: str):
        if await self.bot.is_owner(ctx.author):
            if action == "reload":
                message = await ctx.reply("変数の再ロードをしています...")
                try:
                    save()
                    importlib.reload(n_fc)
                    load()
                    SETTING = json.load(
                        open(f'{sys.path[0]}/setting.json', 'r'))
                    n_fc.py_admin = SETTING["py_admin"]
                    n_fc.GUILD_IDS = SETTING["guild_ids"]
                except Exception as err:
                    await message.edit(content=f"エラーが発生しました。{err}")
                    return
                await message.edit(content=f"変数の読み込みが完了しました。\nAdmin:{n_fc.py_admin}")

    @commands.command()
    async def lb(self, ctx):
        return


def setup(bot, **kwargs):
    bot.add_cog(debug(bot, **kwargs))
    importlib.reload(slash_tool)
