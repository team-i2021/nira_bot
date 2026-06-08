import asyncio
import distro
import importlib
import logging
import platform
import sys
import traceback
import psutil
import websockets

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import slash_tool
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
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.ws_task = None
        self.ws_port = None

    def cog_unload(self):
        if self.ws_task is not None:
            self.ws_task.cancel()

    async def ws_handler(self, websocket: websockets.ServerConnection):
        assert websocket.request
        logging.debug(websocket.request.path)
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

    @nextcord.slash_command(name="debug", description="Debug commands")
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


def setup(bot):
    bot.add_cog(Debug(bot))
    importlib.reload(slash_tool)
