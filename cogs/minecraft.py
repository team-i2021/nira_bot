from email.mime import base
from sqlalchemy import desc
from util.mc_status import minecraft as mc_status
from util import n_fc
from util.slash_tool import messages
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, ChannelType
import asyncio
import sys,os
import traceback



class minecraft_base:
    async def server_add(bot, ctx, name, host, port: int):
        addition_data = [name, f"{host}:{port}"]
        try:
            if ctx.guild.id not in n_fc.mc_server_list:
                n_fc.mc_server_list[ctx.guild.id] = {"value": 1, 1: addition_data}
            else:
                value = n_fc.mc_server_list[ctx.guild.id]["value"] + 1
                n_fc.mc_server_list[ctx.guild.id][value] = addition_data
                n_fc.mc_server_list[ctx.guild.id]["value"] = value
        except BaseException:
            await messages.mreply(ctx, f"サーバー追加時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000))
            return
        await messages.mreply(ctx, f"Task has completed.", embed=nextcord.Embed(title="サーバーを追加しました。", description=f"Server name:{name}\nServer host:{host}\nServer port:{port}", color=0x00ff00))
        return


    async def server_delete(bot, ctx, select_id):
        if ctx.guild.id not in n_fc.mc_server_list:
            await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
            return
        if select_id == "all":
            try:
                del n_fc.mc_server_list[ctx.guild.id]
            except BaseException:
                await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000))
                return
            await messages.mreply(ctx, f"おきのどくですが{ctx.guild.name}のMinecraftサーバーのデータは全て削除されました！")
            return
        
        if n_fc.mc_server_list[ctx.guild.id]["value"] < select_id:
            await messages.mreply(ctx, f"ID`{select_id}`にサーバーは登録されていません。")
            return
        
        if n_fc.mc_server_list[ctx.guild.id]["value"] == 1:
            try:
                del n_fc.mc_server_list[ctx.guild.id]
            except BaseException:
                await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000))
                return
            await messages.mreply(ctx, f"ID`{value}`のサーバーは削除されました。\n(全体のサーバー数が0になったため、データをすべて削除しました。)")
            return

        try:
            value = n_fc.mc_server_list[ctx.guild.id]["value"]
            for i in range(select_id, value):
                n_fc.mc_server_list[ctx.guild.id][i] = n_fc.mc_server_list[ctx.guild.id][i+1]
            del n_fc.mc_server_list[ctx.guild.id][value]
            n_fc.mc_server_list[ctx.guild.id]["value"] = value - 1
        except BaseException:
            await messages.mreply(ctx, f"サーバー削除時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000))
            return
        await messages.mreply(ctx, f"ID`{select_id}`のサーバーを削除しました。")
        return


    async def server_check(bot, ctx, id):
        # ID: None or String("all") or Int
        await ctx.reply(f"チェックコマンド（コマンド指定なし）\n{ctx.message.content}")


    async def server_list(bot, ctx):
        if ctx.guild.id not in n_fc.mc_server_list:
            await messages.mreply(ctx, f"{ctx.guild.name}にはMinecraftのサーバーは追加されていません。")
            return

        try:
            value = n_fc.mc_server_list[ctx.guild.id]["value"]
            user = bot.fetch_user(ctx.author.id)
            embed = nextcord.Embed(title="Minecraft サーバーリスト", description=f"{ctx.guild.name}のリスト", color=0x00ff00)
            for i in range(value-1):
                embed.add_field(name=f"ID:`{i+1}`", value=f"名前:`{n_fc.mc_server_list[ctx.guild.id][i+1][0]}`\nアドレス:`{n_fc.mc_server_list[ctx.guild.id][i+1][1]}`")
            await user.send(embed=embed)
            return
        except BaseException:
            await messages.mreply(ctx, f"サーバー列挙/送信時にエラーが発生しました。", embed=nextcord.Embed(title="An error has occurred...", description=f"```sh\n{traceback.format_exc()}```", color=0xff0000))
            return


class minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def mc(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            return
        base_arg = ctx.message.content.split(" ",1)
        if base_arg[1][:3] == "add":
            args = base_arg[1][4:].split(" ")
            if len(args) != 3:
                await ctx.reply("引数の数が**少ない**又は**多い**です。\n`n!mc add [名前] [アドレス] [ポート番号]`")
                return
            try:
                args[2] = int(args[2])
            except ValueError as err:
                await ctx.reply(f"ポートは数値でなければなりません。\n```sh\n{err}```")
                return
            await minecraft_base.server_add(self.bot, ctx, args[0], args[1], args[2])
            return
        elif base_arg[1][:3] == "del":
            if base_arg[1] == "del":
                await ctx.reply("このコマンドには引数指定が必要です。\n`n!mc del [サーバーID又は「del」]`")
                return
            arg = base_arg[1][4:]
            if arg != "all":
                try:
                    arg = int(arg)
                except ValueError as err:
                    await ctx.reply(f"サーバーIDの所には数値または「all」を入れなければなりません。\n```sh\n{err}```")
                    return
            await minecraft_base.server_delete(self.bot, ctx, arg)
            return
        elif base_arg[1][:4] == "n!mc list":
            await minecraft_base.server_list(self.bot, ctx)
            return
        else:
            if len(base_arg) == 1:
                arg = None
            elif base_arg[1] == "all":
                arg = "all"
            else:
                try:
                    arg = int(base_arg[1])
                except ValueError as err:
                    await ctx.reply(f"サーバーIDの所には数値または「all」を入れなければなりません。\n```sh\n{err}```")
                    return
            await minecraft_base.server_check(self.bot, ctx, arg)
            return
    
    @nextcord.slash_command(name="mc add", description="Minecraftのサーバーを追加します。")
    async def mc_add(
        self,
        interaction = Interaction,
        name: str = SlashOption(
            name="Server Name",
            description="サーバーの名前です。",
            required=True,
        ),
        host: str = SlashOption(
            name="Server Address",
            description="サーバーのアドレスです。",
            required=True,
        ),
        port: int = SlashOption(
            name="Server Port",
            description="サーバーのポートです。\nJava版 デフォルトポート:25565\nBE版 デフォルトポート:19132",
            required=True,
        ),):
        await minecraft_base.server_add(self.bot, interaction, name, host, port)
        return


def setup(bot):
    bot.add_cog(minecraft(bot))