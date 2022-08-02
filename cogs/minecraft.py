import asyncio
import importlib
import logging
import os
import sys
import traceback

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

import util.mc_status as mc_status
from util import n_fc, database
from util.admin_check import admin_check
from util.slash_tool import messages

mcMessage = {
    "ja": {
        "forbidden": "申し訳ございませんが、このコマンドは現在管理者のみ使用可能です。",
        "add": {
            "invalid_args": f"引数の数が**少ない**又は**多い**です。\n`n!mc add [名前] [アドレス] [ポート番号] [java/be]`",
        }
    }
}

class minecraft_data:
    name = "minecraft"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


class minecraft_base:
    async def server_add(self, ctx, name, host, port: int, server_type):
        addition_data = [name, f"{host}:{port}", server_type]
        try:
            if ctx.guild.id not in minecraft_data.value:
                minecraft_data.value[ctx.guild.id] = {
                    "value": 1, 1: addition_data}
            else:
                value = minecraft_data.value[ctx.guild.id]["value"] + 1
                minecraft_data.value[ctx.guild.id][value] = addition_data
                minecraft_data.value[ctx.guild.id]["value"] = value
            await database.default_push(self.client, minecraft_data)
        except Exception:
            await messages.mreply(ctx, f"サーバー追加時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return
        await messages.mreply(ctx, "", embed=nextcord.Embed(title="サーバーを追加しました。", description=f"Server name:`{name}`\nServer host:`{host}:{port}`\nServer type:`{server_type}`", color=0x00ff00), ephemeral=True)
        return

    async def server_delete(self, ctx, select_id):
        if ctx.guild.id not in minecraft_data.value:
            await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
            return

        if select_id == "all":
            try:
                del minecraft_data.value[ctx.guild.id]
                await database.default_push(self.client, minecraft_data)
            except Exception:
                await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
                return
            await messages.mreply(ctx, f"```\nおきのどくですが{ctx.guild.name}のMinecraftサーバーのデータは全て削除されました！```")
            return

        if minecraft_data.value[ctx.guild.id]["value"] < select_id:
            await messages.mreply(ctx, f"ID`{select_id}`にサーバーは登録されていません。", ephemeral=True)
            return

        if minecraft_data.value[ctx.guild.id]["value"] == 1:
            try:
                del minecraft_data.value[ctx.guild.id]
                await database.default_push(self.client, minecraft_data)
            except Exception:
                await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
                return
            await messages.mreply(ctx, f"サーバーを削除しました。", ephemeral=True)
            return

        try:
            value = minecraft_data.value[ctx.guild.id]["value"]
            for i in range(select_id, value):
                minecraft_data.value[ctx.guild.id][i] = minecraft_data.value[ctx.guild.id][i+1]
            del minecraft_data.value[ctx.guild.id][value]
            minecraft_data.value[ctx.guild.id]["value"] = value - 1
            await database.default_push(self.client, minecraft_data)
        except Exception:
            await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return
        await messages.mreply(ctx, f"ID`{select_id}`のサーバーを削除しました。")
        return

    async def server_check(self, ctx, serverid):
        # ID: None or String("all") or Int
        if ctx.guild.id not in minecraft_data.value:
            if type(ctx) == nextcord.Interaction:
                await ctx.followup.send(f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
                return
            else:
                await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
                return
        embed = nextcord.Embed(
            title="Minecraftサーバーチェッカー",
            description=f"`{ctx.guild.name}`のサーバーリスト",
            color=0x00ff00
        )
        if serverid == "status":
            for i in range(minecraft_data.value[ctx.guild.id]["value"]):
                try:
                    if minecraft_data.value[ctx.guild.id][i+1][2] == "java":
                        status = await asyncio.wait_for(mc_status.minecraft_status.java_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][i+1][1]), timeout=3)
                        ping = int(status.latency)
                        players = status.players.online
                        if players != 0:
                            embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                            value=f":white_check_mark: Online\n`{status.description}`\nPing:`{ping}ms`\nPlayers:`{players}人`\n```{[i['name'] for i in status.raw['players']['sample']]}```\n\n\n", inline=False)
                        else:
                            embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                            value=f":white_check_mark: Online\n`{status.description}`\nPing:`{ping}ms`\nPlayers:`{players}人`\n\n\n", inline=False)
                    elif minecraft_data.value[ctx.guild.id][i+1][2] == "be":
                        status = await asyncio.wait_for(mc_status.minecraft_status.bedrock_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][i+1][1]), timeout=3)
                        if mc_status.minecraft_status.error_check(status):
                            embed.add_field(
                                name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})", value=f":ng: Offline\n\n\n", inline=False)
                        else:
                            ping = int(status.latency*1000)
                            players = status.players_online
                            if ping == 0:
                                embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                                value=f":white_check_mark: Online\n`{status.motd}`\nPlayers:`{players}/{status.players_max}人`\nGameMode:`{status.gamemode}`\n\n\n", inline=False)
                            else:
                                embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                                value=f":white_check_mark: Online\n`{status.motd}`\nPing:`{ping}ms`\nPlayers:`{players}/{status.players_max}人`\nGameMode:`{status.gamemode}`\n\n\n", inline=False)
                except BaseException:
                    embed.add_field(
                        name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})", value=f":ng: Offline\n\n\n", inline=False)
                embed.set_footer(text=f"Pingは参考値にしてください。")
            if type(ctx) == nextcord.Interaction:
                await ctx.followup.send("Minecraft Server Status", embed=embed)
                return
            else:
                await messages.mreply(ctx, "Minecraft Server Status", embed=embed)
                return
        elif serverid == "all":
            for i in range(minecraft_data.value[ctx.guild.id]["value"]):
                try:
                    if minecraft_data.value[ctx.guild.id][i+1][2] == "java":
                        status = await asyncio.wait_for(mc_status.minecraft_status.java_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][i+1][1]), timeout=3)
                        embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                        value=f":white_check_mark: Online\n```py\n{vars(status)}```\n\n\n", inline=False)
                    elif minecraft_data.value[ctx.guild.id][i+1][2] == "be":
                        status = await asyncio.wait_for(mc_status.minecraft_status.bedrock_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][i+1][1]), timeout=3)
                        if mc_status.minecraft_status.error_check(status):
                            embed.add_field(
                                name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})", value=f":ng: Offline\n```py\n{status}```\n\n\n", inline=False)
                        else:
                            embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                            value=f":white_check_mark: Online\n```py\n{vars(status)}```\n\n\n", inline=False)
                except BaseException as err:
                    embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][i+1][0]}`({minecraft_data.value[ctx.guild.id][i+1][2]})",
                                    value=f":ng: Offline\n```py\n{err}\n\n{traceback.format_exc()}```\n\n\n", inline=False)
                embed.set_footer(text=f"Detail mode")
            if type(ctx) == nextcord.Interaction:
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
            result = None
            for i in minecraft_data.value[ctx.guild.id].keys():
                if i == serverid:
                    result = True
                    break
                continue
            if result == None:
                await messages.mreply(ctx, f"サーバーID`{serverid}`が見つかりません。", ephemeral=True)
                return
            try:
                if minecraft_data.value[ctx.guild.id][serverid][2] == "java":
                    status = await asyncio.wait_for(mc_status.minecraft_status.java_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][serverid][1]), timeout=3)
                    ping = int(status.latency)
                    players = status.players.online
                    if players != 0:
                        embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})",
                                        value=f":white_check_mark: Online\n`{status.description}`\nPing:`{ping}ms`\nPlayers:`{players}人`\n```{[i['name'] for i in status.raw['players']['sample']]}```\n\n\n", inline=False)
                    else:
                        embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})",
                                        value=f":white_check_mark: Online\n`{status.description}`\nPing:`{ping}ms`\nPlayers:`{players}人`\n\n\n", inline=False)
                elif minecraft_data.value[ctx.guild.id][serverid][2] == "be":
                    status = await asyncio.wait_for(mc_status.minecraft_status.bedrock_unsync(self.bot.loop, minecraft_data.value[ctx.guild.id][serverid][1]), timeout=3)
                    if mc_status.minecraft_status.error_check(status):
                        embed.add_field(
                            name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})", value=f":ng: Offline\n\n\n", inline=False)
                    else:
                        ping = int(status.latency*1000)
                        players = status.players_online
                        if ping == 0:
                            embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})",
                                            value=f":white_check_mark: Online\n`{status.motd}`\nPlayers:`{players}/{status.players_max}人`\nGameMode:`{status.gamemode}`\n\n\n", inline=False)
                        else:
                            embed.add_field(name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})",
                                            value=f":white_check_mark: Online\n`{status.motd}`\nPing:`{ping}ms`\nPlayers:`{players}/{status.players_max}人`\nGameMode:`{status.gamemode}`\n\n\n", inline=False)
            except BaseException:
                embed.add_field(
                    name=f"サーバー名:`{minecraft_data.value[ctx.guild.id][serverid][0]}`({minecraft_data.value[ctx.guild.id][serverid][2]})", value=f":ng: Offline\n\n\n", inline=False)
            embed.set_footer(text=f"Pingは参考値にしてください。")
            if type(ctx) == nextcord.Interaction:
                await ctx.followup.send("Minecraft Server Status", embed=embed)
                return
            else:
                await messages.mreply(ctx, "Minecraft Server Status", embed=embed)
                return

    async def server_list(self, ctx):
        if ctx.guild.id not in minecraft_data.value:
            await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。", ephemeral=True)
            return

        try:
            value = minecraft_data.value[ctx.guild.id]["value"]
            if type(ctx) == nextcord.Interaction:
                user = await self.bot.fetch_user(ctx.user.id)
            else:
                user = await self.bot.fetch_user(ctx.author.id)
            embed = nextcord.Embed(
                title="Minecraft サーバーリスト", description=f"{ctx.guild.name}のリスト", color=0x00ff00)
            for i in range(value):
                embed.add_field(
                    name=f"ID:`{i+1}`", value=f"名前:`{minecraft_data.value[ctx.guild.id][i+1][0]}`\n{minecraft_data.value[ctx.guild.id][i+1][2]}Edition サーバー\nアドレス:`{minecraft_data.value[ctx.guild.id][i+1][1]}`")
            await user.send(embed=embed)
            return

        except BaseException:
            logging.error(
                f"An error has occured during the execution of the function `{self.bot.command_prefix}mc list`/`/mc list`\n{traceback.format_exc()}")
            await messages.mreply(ctx, f"サーバー列挙/送信時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return


class minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = database.openClient()
        asyncio.ensure_future(database.default_pull(self.client, minecraft_data))

    @commands.command(name="mc", help="""\
MinecraftのJava/BEサーバーのステータスを表示します
このコマンドは、**user毎**で**10秒**のクールダウンがあります。
このコマンドのヘルプは別ページにあります。
[ヘルプはこちら](https://sites.google.com/view/nira-bot/%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89/minecraft)""")
    @commands.cooldown(1, 10, type=commands.BucketType.user)
    async def mc(self, ctx: commands.Context):
        base_arg = ctx.message.content.split(" ", 1)

        if len(base_arg) == 1:
            base_arg.append("status")

        if base_arg[1][:3] == "add":
            if not admin_check(ctx.guild, ctx.author):
                await ctx.reply("管理者権限がないため、コマンドを実行できません。")
                return
            args = base_arg[1][4:].split(" ")
            if len(args) != 4:
                await ctx.reply(mcMessage["ja"]["add"]["invalid_args"])
                return
            try:
                args[2] = int(args[2])
            except ValueError as err:
                await ctx.reply(f"ポートは数値でなければなりません。\n```sh\n{err}```")
                return
            if args[3] != "java" and args[3] != "be" and args[3] != "j" and args[3] != "b":
                await messages.mreply(ctx, f"サーバータイプは「java」または「be」と入力してください。\n`{self.bot.command_prefix}mc add [名前] [アドレス] [ポート番号] [java/be]")
            if args[3] == "j":
                args[3] = "java"
            elif args[3] == "b":
                args[3] = "be"
            await minecraft_base.server_add(self, ctx, args[0], args[1], args[2], args[3])
            return
        elif base_arg[1][:3] == "del":
            if not admin_check(ctx.guild, ctx.author):
                await ctx.reply("管理者権限がないため、コマンドを実行できません。")
                return
            if base_arg[1] == "del":
                await ctx.reply(f"このコマンドには引数指定が必要です。\n`{self.bot.command_prefix}mc del [サーバーID又は「del」]`")
                return
            arg = base_arg[1][4:]
            if arg != "all":
                try:
                    arg = int(arg)
                except ValueError as err:
                    await ctx.reply(f"サーバーIDの所には数値または「all」を入れなければなりません。\n```sh\n{err}```")
                    return
            await minecraft_base.server_delete(self, ctx, arg)
            return
        elif base_arg[1][:4] == "list":
            if not admin_check(ctx.guild, ctx.author):
                await ctx.reply("管理者権限がないため、コマンドを実行できません。")
                return
            await minecraft_base.server_list(self, ctx)
            return
        else:
            async with ctx.channel.typing():
                await minecraft_base.server_check(self, ctx, base_arg[1])
                return

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
            await minecraft_base.server_add(self, interaction, server_name, address, port, server_type)
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
            await minecraft_base.server_delete(self, interaction, "all")
        else:
            try:
                server = int(server)
            except ValueError as err:
                await messages.mreply(interaction, f"サーバーIDの所には数値または「all」を入れなければなりません。\n```sh\n{err}```", ephemeral=True)
                return
            await minecraft_base.server_delete(self, interaction, server)

    @mc_slash.subcommand(name="list", description="Minecraftのサーバーのリストを表示します。")
    async def list_slash(self, interaction: Interaction):
        await minecraft_base.server_list(self, interaction)

    @mc_slash.subcommand(name="status", description="Minecraftのサーバーのステータスを表示します。")
    async def status_slash(self, interaction: Interaction, server: str = SlashOption(name="server", description="サーバーIDを指定することもできます", required=False)):
        await interaction.response.defer()
        if server == "" or server is None:
            server = "status"
        await minecraft_base.server_check(self, interaction, server)


def setup(bot):
    bot.add_cog(minecraft(bot))
    importlib.reload(mc_status)
