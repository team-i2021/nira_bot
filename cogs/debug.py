import asyncio
import distro
import importlib
import logging
import platform
import re
import subprocess
import sys
import traceback
import psutil
import websockets
from subprocess import PIPE

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import n_fc, slash_tool
from util.nira import NIRA


SYSDIR = sys.path[0]

# 管理者向けdebug

def sysinfo() -> str:
    if platform.system() == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    elif platform.system() == "Windows":
        return f"Windows {platform.release()}"
    elif platform.system() == "Linux":
        return f"{distro.name()} {distro.version()}"
    else:
        return f"{platform.system()} {platform.release()}"



class Debug(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.ws_task = None
        self.ws_port = None

    def cog_unload(self):
        if self.ws_task is not None:
            self.ws_task.cancel()

    async def ws_handler(self, websocket, path):
        print(path)
        async for message in websocket:
            await websocket.send(f"にら「{message}」")

    async def ws_main(self):
        if self.ws_port is None:
            raise ValueError("Port not set.")
        logging.info(f"Start Websocket at {self.ws_port}....")
        try:
            async with websockets.serve(self.ws_handler, "0.0.0.0", self.ws_port):
                await asyncio.Future()
        except asyncio.CancelledError:
            logging.info("WebSocket server task cancelled.")

    @commands.command()
    async def websocket(self, ctx: commands.Context, arg: str | None = None, port: int | None = 32568):
        if arg is None:
            await ctx.reply(embed=nextcord.Embed(
                title="WebSocket Server Manager",
                description=f"Argument is missing.\n`{ctx.prefix}websocket [start/stop] [*port]`"
            ))
            return
        if (await self.bot.is_owner(ctx.author)):
            if arg == "start":
                if self.ws_task is None:
                    try:
                        self.ws_port = port
                        self.ws_task = asyncio.create_task(
                            self.ws_main()
                        )
                        await ctx.reply(embed=nextcord.Embed(
                            title="WebSocket Server Manager",
                            description=f"Started WebSocket Server on port {self.ws_port}"
                        ))
                    except Exception as err:
                        await ctx.reply(embed=nextcord.Embed(
                            title="WebSocket Server Manager",
                            description=f"Err: `{err}` has occurred during starting server.\n```sh\n{traceback.format_exc()}```"
                        ))
                else:
                    await ctx.reply(embed=nextcord.Embed(
                        title="WebSocket Server Manager",
                        description=f"WebSocket Server is currently running on port {self.ws_port}.\nIf you want to stop server, you can use following command: `{ctx.prefix}websocket stop`."
                    ))
            elif arg == "stop":
                if self.ws_task is None:
                    await ctx.reply(embed=nextcord.Embed(
                        title="WebSocket Server Manager",
                        description=f"WebSocket Server isn't running.\nIf you want to start server, you can use following command: `{ctx.prefix}websocket start [*port]`."
                    ))
                else:
                    try:
                        self.ws_task.cancel()
                        self.ws_task = None
                        self.ws_port = None
                        await ctx.reply(embed=nextcord.Embed(
                            title="WebSocket Server Manager",
                            description="WebSocket Server stopped."
                        ))
                    except Exception as err:
                        await ctx.reply(embed=nextcord.Embed(
                            title="WebSocket Server Manager",
                            description=f"Err: `{err}` has occurred during stopping server.\n```sh\n{traceback.format_exc()}```"
                        ))
        else:
            await ctx.reply(embed=nextcord.Embed(title="WebSocket Server Manager", description=f"Sorry. You don't have the required permission."))

    @commands.command()
    async def restart(self, ctx: commands.Context):
        if not self.bot.debug:
            await ctx.reply(f"本番環境においてリスタートコマンドを使用することはできません。")
            return
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
        if not self.bot.debug:
            await ctx.reply(f"本番環境においてリスタートコマンドを使用することはできません。")
            return
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
            try:
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

    @nextcord.slash_command(name="debug", description="Debug commands", guild_ids=n_fc.GUILD_IDS)
    async def debug_slash(self, interaction):
        pass

    @debug_slash.subcommand(name="reaction", description="Reaction Debug")
    async def reaction_debug_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if await self.bot.is_owner(interaction.user):
            cog = self.bot.get_cog("normal_reaction")
            if cog is None:
                await interaction.send(embed=nextcord.Embed(title="Error", description="`normal_reaction` cog not found.\nNot loaded?", color=0xff0000), ephemeral=True)
            else:
                await interaction.send(embed=nextcord.Embed(title="Success", description=f"`normal_reaction` cog found.\nLoaded.\nLast database update: `{cog.last_update}`", color=0x00ff00), ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()

    @debug_slash.subcommand(name="extension", description="Manage extensions")
    async def extension_slash(self, interaction):
        pass

    @extension_slash.subcommand(name="list", description="List extensions.")
    async def list_extension_slash(self, interaction):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(f"```py\n{list(dict(self.bot.cogs).keys())}```", ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()

    @extension_slash.subcommand(name="load", description="Load extension.")
    async def load_extension_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.defer()
            try:
                self.bot.load_extension(cogname)
                await interaction.followup.send(f"The cog `{cogname}` successfully loaded.", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"Failed to load cog `{cogname}`.\n```py\n{err}```", ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()

    @extension_slash.subcommand(name="reload", description="Reload extension.")
    async def reload_extension_slash(self, interaction: Interaction, cogname: str = SlashOption(name="cogname", description="Cog name.", required=True)):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.defer()
            try:
                self.bot.reload_extension(cogname)
                await interaction.followup.send(f"The cog `{cogname}` successfully reloaded.", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"Failed to reload cog `{cogname}`.\n```py\n{err}```", ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()

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
            raise NIRA.ForbiddenExpand()

    @debug_slash.subcommand(name="info", description="Show debug info.")
    async def info_slash(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise NIRA.ForbiddenExpand()
        await interaction.response.defer()

        embed = nextcord.Embed(
            title="Debug info",
            description=f"Hosting on {sysinfo()}",
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
        await interaction.followup.send(embed=embed)

    @debug_slash.subcommand(name="command", description="Manage commands")
    async def command_slash(self, interaction):
        pass

    @command_slash.subcommand(name="list", description="List commands")
    async def command_slash_list(self, interaction: Interaction):
        if not (await self.bot.is_owner(interaction.user)):
            raise NIRA.ForbiddenExpand()
        await interaction.response.send_message(embed=nextcord.Embed(title="COMMANDS", description=f"```py\n{self.bot.all_commands.keys()}```", color=0x00ff00))

    @command_slash.subcommand(name="sync", description="sync application command")
    async def command_slash_sync(
        self,
        interaction: Interaction,
        guild_id: str = SlashOption(name="guild_id", description="Guild id", required=False),
        associate_known: str = SlashOption(name="associate_known", description="associate_known", required=False),
        delete_unknown: bool = SlashOption(name="delete_unknown", description="delete_unknown", required=False),
        update_known: bool = SlashOption(name="update_known", description="update_known", required=False),
        register_new: bool = SlashOption(name="register_new", description="register_new", required=False),
    ):
        if not (await self.bot.is_owner(interaction.user)):
            raise NIRA.ForbiddenExpand()
        await interaction.response.defer()
        try:
            if not guild_id:
                guild_id = None
            else:
                guild_id = eval(guild_id)
            await self.bot.sync_application_commands(guild_id=guild_id, associate_known=associate_known, delete_unknown=delete_unknown, update_known=update_known, register_new=register_new)
            await interaction.followup.send(embed=nextcord.Embed(title="SYNC", description=f"```\n{guild_id}```", color=0x00ff00))
        except Exception:
            await interaction.followup.send(embed=nextcord.Embed(title="SYNC", description=f"```\n{traceback.format_exc()}```", color=0xFF0000))

    @commands.command()
    async def lb(self, ctx):
        return


def setup(bot, **kwargs):
    bot.add_cog(Debug(bot, **kwargs))
    importlib.reload(slash_tool)
