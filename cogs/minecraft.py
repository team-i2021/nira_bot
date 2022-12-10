import asyncio
import importlib
import logging
import os
import sys
import traceback
import enum

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import n_fc, database
from util import mc_status as mc
from util.admin_check import admin_check
from util.slash_tool import messages
from util.nira import NIRA

import motor
from motor import motor_asyncio

mcMessage = {
    "ja": {
        "forbidden": "申し訳ございませんが、このコマンドは現在管理者のみ使用可能です。",
        "add": {
            "invalid_args": f"引数の数が**少ない**又は**多い**です。\n`n!mc add [名前] [アドレス] [ポート番号] [java/be]`",
        }
    }
}

NORMAL = 0
DETAIL = 1

class minecraft_data:
    name = "minecraft"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

async def status_embed(
        embed: nextcord.Embed, server: dict, value_type: int = NORMAL
    ):
    # StatusのEmbed
    try:
        if server["server_type"] == "java":
            status = await mc.java_status(host=server["host"], port=server["port"])

            if isinstance(status, Exception):
                embed.add_field(
                    name=f"サーバー名:`{server['name']}`(Java)",
                    value=f":ng: Offline\n\n\n",
                    inline=False
                )
            else:
                ping = int(status.latency)
                players = status.players.online
                if value_type == NORMAL:
                    embed.add_field(
                        name=f"サーバー名:`{server['name']}`(Java)",
                        value=f":white_check_mark: Online\n`{status.description}`\nPing:`{ping}ms`\nPlayers:`{players}人`" + (f"\n```{[ i['name'] for i in status.raw['players']['sample'] ]}```" if players != 0 else '') + "\n\n\n",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"サーバー名:`{server['name']}`(Java)",
                        value=f":white_check_mark: Online\n```py\n{vars(status)}```\n\n\n",
                        inline=False
                    )

        elif server['server_type'] == "be":
            status = await mc.bedrock_status(host=server["host"], port=server["port"])

            if isinstance(status, Exception):
                embed.add_field(
                    name=f"サーバー名:`{server['name']}`(Bedrock)",
                    value=f":ng: Offline\n\n\n",
                    inline=False
                )
            else:
                ping = int(status.latency * 1000)
                players = status.players_online
                if value_type == NORMAL:
                    embed.add_field(
                        name=f"サーバー名:`{server['name']}`(Bedrock)",
                        value=f":white_check_mark: Online\n`{status.motd}`" + f'\nPing: `{ping}`ms' if ping != 0 else '' + f"\nPlayers:`{players}/{status.players_max}人`\nGameMode:`{status.gamemode}`\n\n\n",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"サーバー名:`{server['name']}`(Bedrock)",
                        value=f":white_check_mark: Online\n```py\n{vars(status)}```\n\n\n",
                        inline=False
                    )

        else:
            embed.add_field(
                name=f"サーバー名:`{server['name']}`",
                value=f":exclamation: このサーバーのデータは異常です。開発者へお問い合わせください。 `{server['server_type']}`",
                inline=False
            )

    except Exception as err:
        if value_type == NORMAL:
            embed.add_field(
                name=f"サーバー名:`{server['name']}`({server['server_type']})",
                value=f":ng: Offline\n\n\n",
                inline=False
            )
        else:
            embed.add_field(
                name=f"サーバー名:`{server['name']}`({server['server_type']})",
                value=f":ng: Offline\n```py\n{err}\n\n{traceback.format_exc()}```\n\n\n",
                inline=False
            )


async def server_add(bot: NIRA, collection: motor_asyncio.AsyncIOMotorCollection, ctx, name, host: str, port: int, server_type):
    try:
        servers = await collection.find({"guild_id": ctx.guild.id}).to_list(length=None)
        await collection.insert_one({
            "guild_id": ctx.guild.id,
            "name": name,
            "host": host,
            "port": port,
            "server_type": server_type,
            "server_id": len(servers) + 1
        })

    except Exception:
        await messages.mreply(ctx, f"サーバー追加時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
        return
    await messages.mreply(ctx, "", embed=nextcord.Embed(title="サーバーを追加しました。", description=f"サーバー名:`{name}`\nサーバーアドレス:`{host}:{port}`\nサーバー種類:`{server_type}`", color=0x00ff00), ephemeral=True)
    return


async def server_delete(bot: NIRA, collection: motor_asyncio.AsyncIOMotorCollection, ctx, select_id: str | None):
    servers = await collection.find({"guild_id": ctx.guild.id}).to_list(length=None)

    if len(servers) == 0:
        await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
        return

    if select_id == "all":
        try:
            await collection.delete_many({"guild_id": ctx.guild.id})
        except Exception:
            await messages.mreply(ctx, "サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return
        await messages.mreply(ctx, f"`{ctx.guild.name}`のMinecraftサーバーデータを削除しました。")
        return

    if len(servers) < select_id:
        await messages.mreply(ctx, f"ID`{select_id}`にサーバーは登録されていません。", ephemeral=True)
        return

    if len(servers) == 1:
        try:
            await collection.delete_one({"guild_id": ctx.guild.id, "server_id": select_id})
        except Exception:
            await messages.mreply(ctx, "サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return
        await messages.mreply(ctx, "サーバーを削除しました。", ephemeral=True)
        return

    else:
        try:
            await collection.delete_one({"guild_id": ctx.guild.id, "server_id": select_id})
            await collection.update_many(
                {"guild_id": ctx.guild.id, "server_id": {"$gte": select_id}},
                {"$inc": {"server_id": -1}}
            )
        except Exception:
            await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return
        await messages.mreply(ctx, f"ID`{select_id}`のサーバーを削除しました。")
        return

async def server_check(bot: NIRA, collection: motor_asyncio.AsyncIOMotorCollection, ctx, serverid):
    servers = await collection.find({"guild_id": ctx.guild.id}).to_list(length=None)

    if len(servers) == 0:
        await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。", ephemeral=True)
        return

    embed = nextcord.Embed(
        title="Minecraftサーバーチェッカー",
        description=f"`{ctx.guild.name}`のサーバーリスト",
        color=0x00ff00
    )

    if serverid == "status":
        for server in servers:
            await status_embed(embed, server, NORMAL)
        embed.set_footer(text=f"Pingは参考値にしてください。")
        if isinstance(ctx, nextcord.Interaction):
            await ctx.followup.send("Minecraft Server Status", embed=embed)
            return
        else:
            await ctx.reply("Minecraft Server Status", embed=embed)
            return
    elif serverid == "all":
        for server in servers:
            await status_embed(embed, server, DETAIL)
        embed.set_footer(text=f"Detail mode")
        if isinstance(ctx, nextcord.Interaction):
            await ctx.followup.send("Minecraft Server Status", embed=embed)
            return
        else:
            await messages.mreply(ctx, "Minecraft Server Status", embed=embed)
            return
    else:
        try:
            serverid = int(serverid)
        except ValueError as err:
            await messages.mreply(ctx, f"サーバーIDは数値または`all`のみ指定できます。\n{err}", ephemeral=True)
            return
        server = None
        for s in servers:
            if s["server_id"] == serverid:
                server = s
                break
        if server is None:
            await messages.mreply(ctx, f"サーバーID`{serverid}`が見つかりません。", ephemeral=True)
            return
        await status_embed(embed, server, NORMAL)
        embed.set_footer(text=f"Pingは参考値にしてください。")
        if isinstance(ctx, nextcord.Interaction):
            await ctx.followup.send("Minecraft Server Status", embed=embed)
            return
        else:
            await messages.mreply(ctx, "Minecraft Server Status", embed=embed)
            return

async def server_list(bot: NIRA, collection: motor_asyncio.AsyncIOMotorCollection, ctx):
    servers = await collection.find({"guild_id": ctx.guild.id}).to_list(length=None)

    if len(servers) == 0:
        await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。", ephemeral=True)
        return

    try:
        if type(ctx) == nextcord.Interaction:
            user = await bot.fetch_user(ctx.user.id)
        else:
            user = await bot.fetch_user(ctx.author.id)
        embed = nextcord.Embed(
            title="Minecraft サーバーリスト",
            description=f"{ctx.guild.name}のリスト",
            color=0x00ff00
        )
        for server in servers:
            embed.add_field(
                name=f"ID:`{server['server_id']}`",
                value=f"名前:`{server['name']}`\n{server['server_type']}Edition サーバー\nアドレス:`{server['host']}:{server['port']}`"
            )
        await user.send(embed=embed)
        return

    except Exception:
        logging.error(
            f"An error has occured during the execution of the function `{bot.command_prefix}mc list`/`/mc list`\n{traceback.format_exc()}"
        )
        await messages.mreply(
            ctx,
            "サーバー列挙/送信時にエラーが発生しました。",
            embed=nextcord.Embed(
                title="An error has occurred...",
                description=f"```sh\n{traceback.format_exc()}```",
                color=0xff0000
            ),
            ephemeral=True)
        return



class Minecraft(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.__BE = ("b", "be", "bedrock")
        self.__JAVA = ("j", "java")
        self.collection: motor_asyncio.AsyncIOMotorCollection  = self.bot.database["minecraft_db"]

    @commands.group(name="mc")
    async def minecraft_maincommand(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            async with ctx.typing():
                if len(ctx.message.content.split(" ", 1)) == 1:
                    await server_check(self.bot, self.collection, ctx, "status")
                else:
                    await server_check(self.bot, self.collection, ctx, ctx.message.content.split(" ", 1)[1])
            # await server_check(self.bot, self.collection, ctx, server_id)
            # check status
        else:
            pass

    @minecraft_maincommand.command(name="add")
    async def add_server(self, ctx: commands.Context, name: str, host: str, port: int, server_type: str | None = None):
        if server_type in self.__BE:
            # be
            await server_add(self.bot, self.collection, ctx, name, host, port, "be")
        elif server_type in self.__JAVA:
            # java
            await server_add(self.bot, self.collection, ctx, name, host, port, "java")
        else:
            # other
            await ctx.reply(embed=nextcord.Embed(
                title="Minecraft Server Status - ADD",
                description=f"サーバータイプが不正です。\n`{ctx.prefix}mc add [サーバー名] [サーバーアドレス] [サーバーポート] [サーバー種類(be/java)]`",
                color=0xff0000
            ))

    @minecraft_maincommand.command(name="del")
    async def del_server(self, ctx: commands.Context, server_id: str | int | None = None):
        if server_id is None or (isinstance(server_id, str) and server_id != "all"):
            await ctx.reply(embed=nextcord.Embed(
                title="Minecraft Server Status - DEL",
                description=f"サーバーIDが不正です。\n`{ctx.prefix}mc del [サーバーID/all]`",
                color=0xff0000
            ))
        else:
            await server_delete(self.bot, self.collection, ctx, server_id)


    @minecraft_maincommand.command(name="list")
    async def list_server(self, ctx: commands.Context):
        await server_list(self.bot, self.collection, ctx)


    @nextcord.slash_command(name="mc", description="Minecraftサーバーステータス", guild_ids=n_fc.GUILD_IDS)
    async def mc_slash(self, interaction: Interaction):
        pass


    @mc_slash.subcommand(name="add", description="Minecraftのサーバーを追加します。")
    async def add_slash(
        self,
        interaction=Interaction,
        server_name: str = SlashOption(
            name="server_name",
            description="サーバーの名前です。",
            required=True,
        ),
        address: str = SlashOption(
            name="address",
            description="サーバーのアドレスです。",
            required=True,
        ),
        port: int = SlashOption(
            name="port",
            description="サーバーのポート。Java版 デフォルトポート:25565　BE版 デフォルトポート:19132",
            required=True,
        ),
        server_type: str = SlashOption(
            name="server_type",
            description="サーバーのタイプです。「java」または「be」と入力してください。",
            required=True,
            choices={"Java版": "java", "BE版": "be"},
        ),
    ):
        if admin_check(interaction.guild, interaction.user):
            if server_type != "java" and server_type != "be" and server_type != "j" and server_type != "b":
                await messages.mreply(interaction, "サーバータイプは「java」または「be」と入力してください", ephemeral=True)
            if server_type == "j":
                server_type = "java"
            elif server_type == "b":
                server_type = "be"
            await server_add(self.bot, self.collection, interaction, server_name, address, port, server_type)
            return

    @mc_slash.subcommand(name="del", description="Minecraftのサーバーを削除します。")
    async def del_slash(
        self,
        interaction: Interaction,
        server: str = SlashOption(
            name="server",
            description="サーバーIDです。「all」を入力すると全てのサーバーを削除します。",
            required=True
        )
    ):
        if server == "all":
            await server_delete(self.bot, self.collection, interaction, "all")
        else:
            try:
                server = int(server)
            except ValueError as err:
                await messages.mreply(interaction, f"サーバーIDの所には数値または「all」を入れなければなりません。\n```sh\n{err}```", ephemeral=True)
                return
            await server_delete(self.bot, self.collection, interaction, server)

    @mc_slash.subcommand(name="list", description="Minecraftのサーバーのリストを表示します。")
    async def list_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        await server_list(self.bot, self.collection, interaction)

    @mc_slash.subcommand(name="status", description="Minecraftのサーバーのステータスを表示します。")
    async def status_slash(self, interaction: Interaction, server: str = SlashOption(name="server", description="サーバーIDを指定することもできます", required=False)):
        await interaction.response.defer()
        if server == "" or server is None:
            server = "status"
        await server_check(self.bot, self.collection, interaction, server)
    
    # @tasks.loop(minutes=5)
    async def server_panel(self):
        return



def setup(bot, **kwargs):
    bot.add_cog(Minecraft(bot, **kwargs))
    importlib.reload(mc)
