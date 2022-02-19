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
    async def server_add(bot, ctx, name, host, port):
        await messages.mreply(ctx, f"MCサーバーを追加するコマンドテスト", embed=nextcord.Embed(title="Args", description=f"Server name:{name}\nServer host:{host}\nServer port:{port}", color=0x00ff00))
    
    async def server_delete(bot, ctx):
        await ctx.reply(f"削除コマンド\n{ctx.message.content}")
    
    async def server_check(bot, ctx):
        await ctx.reply(f"チェックコマンド（コマンド指定なし）\n{ctx.message.content}")
    
    async def server_list(bot, ctx):
        await ctx.reply(f"サーバーリストコマンド\n{ctx.message.content}")


class minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def mc(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            return
        if ctx.message.content[:8] == "n!mc add":
            args = ctx.message.content[9:].split(" ")
            if len(args) != 3:
                await ctx.reply("引数の数が**少ない**又は**多い**です。\n`n!mc add [名前] [アドレス] [ポート番号]`")
                return
            try:
                await minecraft_base.server_add(self.bot, ctx, args[0], args[1], args[2])
            except BaseException as err:
                exc_type, exc_obj, exc_tb = sys.exc_info() 
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                await ctx.reply(f"err:{err}\nfile:{fname}\nline:{exc_tb.tb_lineno}\ntraceback:```sh\n{traceback.format_exc()}```")
            return
        elif ctx.message.content[:8] == "n!mc del":
            await minecraft_base.server_delete(self.bot, ctx, 1)
        elif ctx.message.content[:9] == "n!mc list":
            await minecraft_base.server_list(self.bot, ctx, 1)
        else:
            await minecraft_base.server_check(self.bot, ctx, 1)
    
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