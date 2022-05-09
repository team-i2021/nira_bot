from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import nextcord
import re
import pickle

import sys,os

from cogs.debug import save
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh


#ユーザー情報表示系

home_dir = os.path.dirname(__file__)[:-4]

class user(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @nextcord.slash_command(
            name="d",
            description="ユーザー情報表示",
            guild_ids=n_fc.GUILD_IDS
        )
        async def d_slash(
                self,
                interaction: Interaction,
                user: nextcord.user = SlashOption(
                    name = "user",

                )):
    
    @commands.command(name="d", help="""\
    ユーザーの情報を表示します。
    引数を指定せずに`n!d`とだけ指定するとあなた自身の情報を表示します。
    `n!d [ユーザーID]`という風に指定すると、そのユーザーの情報を表示することが出来ます。
    ユーザーIDの指定方法は...多分調べれば出てきます。
    **メンションでも指定できますが、いざこざとかにつながるかもしれないのでしないほうが得策です。**""")
    async def d(self, ctx: commands.Context):
        if ctx.message.content == "n!d":
            user = await self.bot.fetch_user(ctx.message.author.id)
            embed = nextcord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
            embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
            await ctx.message.reply(embed=embed)
            return
        else:
            user_id = int("".join(re.findall(r'[0-9]', ctx.message.content[4:])))
            try:
                user = await self.bot.fetch_user(user_id)
                embed = nextcord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
                embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
                await ctx.message.reply(embed=embed)
                return
            except BaseException:
                await ctx.message.reply(embed=nextcord.Embed(title="Error", description="ユーザーが存在しないか、データが取得できませんでした。", color=0xff0000))
                return
    
    @commands.command(name="rk", help="""\
    ロールキーパー機能です。
    大前提、**ちゃんと機能するとは思わないでください。**
    `n!rk [on/off]`でロールキーパー機能の設定が可能です。ただ、ロールキーパー機能を有効にするには`n!ui`の、ユーザー情報表示を有効にしないと有効になりません。
    """)
    async def rk(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
            if ctx.message.content == "n!rk":
                embed = nextcord.Embed(title="ロールキーパー", description="`n!rk [on/off]`", color=0x00ff00)
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":0}
                    save()
                if n_fc.role_keeper[ctx.guild.id]["rk"] == 0:
                    role_bool = "無効"
                else:
                    role_bool = "有効"
                embed.add_field(name="ロールキーパーの状態", value=f"ロールキーパーは現在{role_bool}です")
                await ctx.reply(embed=embed)
                return
            if ctx.message.content[5:] in n_fc.on_ali:
                # ロールキーパーオンにしやがれ
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":1}
                else:
                    n_fc.role_keeper[ctx.guild.id]["rk"] = 1
            elif ctx.message.content[5:] in n_fc.off_ali:
                # ロールキーパーオフにしやがれ
                if ctx.guild.id not in n_fc.role_keeper:
                    n_fc.role_keeper[ctx.guild.id] = {"rk":0}
                else:
                    n_fc.role_keeper[ctx.guild.id]["rk"] = 0
            else:
                await ctx.reply("値が不正です。\n「on」とか「off」とか...")
                return
            save()
            await ctx.reply("ロールキーパーの設定を更新しました。")
            return
        else:
            await ctx.reply("権限がありません。")
    
    @commands.command(name="ui", help="""\
    誰かがDiscordサーバーに加入/離脱した際に、指定したチャンネルにそのユーザーの情報を表示します。
    それだけです。""")
    async def ui(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
            mes_arg = ctx.message.content.split(" ")
            if len(mes_arg) == 1:
                try:
                    if ctx.message.guild.id in n_fc.welcome_id_list:
                        seted_id = int(n_fc.welcome_id_list[ctx.message.guild.id])
                        channel = self.bot.get_channel(int(n_fc.welcome_id_list[ctx.message.guild.id]))
                        await ctx.message.reply(f"チャンネル：{channel.name}")
                        return
                    else:
                        await ctx.message.reply("設定されていません。\n\n・追加```n!ui set [チャンネルID]```・削除```n!ui del```")
                        return
                except BaseException as err:
                    await ctx.message.reply(embed=eh.eh(err))
                    return
            elif mes_arg[1] == "set":
                try:
                    set_id = int("".join(re.findall(r'[0-9]', mes_arg[2])))
                    n_fc.welcome_id_list[ctx.message.guild.id] = set_id
                    with open(f'{home_dir}/welcome_id_list.nira', 'wb') as f:
                        pickle.dump(n_fc.welcome_id_list, f)
                    channel = self.bot.get_channel(n_fc.welcome_id_list[ctx.message.guild.id])
                    await channel.send("追加完了メッセージ\nこのメッセージが指定のチャンネルに送信されていれば完了です。")
                    await ctx.message.reply("追加完了のメッセージを指定されたチャンネルに送信しました。\n送信されていない場合はにらBOTに適切な権限が与えられているかご確認ください。")
                    return
                except BaseException as err:
                    await ctx.message.reply(embed=eh.eh(err))
                    return
            elif  mes_arg[1] == "del":
                try:
                    if ctx.message.guild.id not in n_fc.welcome_id_list:
                        seted_id = n_fc.welcome_id_list[ctx.message.guild.id]
                        del n_fc.welcome_id_list[ctx.message.guild.id]
                        with open(f'{home_dir}/welcome_id_list.nira', 'wb') as f:
                            pickle.dump(n_fc.welcome_id_list, f)
                        await ctx.message.reply(f"削除しました。\n再度同じ設定をする場合は```n!ui set {seted_id}```と送信してください。")
                        return
                    else:
                        await ctx.message.reply("設定されていません。")
                        return
                except BaseException as err:
                    await ctx.message.reply(embed=eh.eh(err))
                    return
            else:
                try:
                    if ctx.message.guild.id in n_fc.welcome_id_list:
                        seted_id = int(n_fc.welcome_id_list[ctx.message.guild.id])
                        channel = self.bot.get_channel(int(n_fc.welcome_id_list[ctx.message.guild.id]))
                        await ctx.message.reply(f"チャンネル：{channel.name}")
                        return
                    else:
                        await ctx.message.reply("設定されていません。\n\n・追加```n!ui set [チャンネルID]```・削除```n!ui del```")
                        return
                except BaseException as err:
                    await ctx.message.reply(embed=eh.eh(err))
                    return

        else:
            await ctx.message.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return

def setup(bot):
    bot.add_cog(user(bot))
