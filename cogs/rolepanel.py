import nextcord
from nextcord import Interaction, SlashOption, Role
from nextcord.ext import commands
from nextcord.utils import get
from os import getenv
import sys
from util.admin_check import admin_check
global task
import re
import pickle
import sys,os
sys.path.append('../')
from util import n_fc, mc_status
import datetime

PersistentViews = []

# rolepanel

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

class RolePanelView(nextcord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for i in args:
            self.add_item(RolePanelButton(i))

class RolePanelButton(nextcord.ui.Button):
    def __init__(self, arg):
        super().__init__(label=arg[0], style=nextcord.ButtonStyle.green, custom_id=f"RolePanel:{arg[1]}")
    
    async def callback(self, interaction: Interaction):
        try:
            role = interaction.guild.get_role(int(self.custom_id.split(':')[1]))
            for i in interaction.user.roles:
                if i == role:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"`{role.name}`を削除しました。", ephemeral=True)
                    return
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"`{role.name}`を付与しました。", ephemeral=True)
            return
        except BaseException as err:
            await interaction.response.send_message(f"ERR: {err}", ephemeral=True)


class rolepanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @nextcord.slash_command(name="rolepanel", description="ロールパネルを設置します")
    async def rolepanel_slash(
            self,
            interaction: Interaction,
            role1: Role = SlashOption(
                name="role1",
                description="1つ目のロール",
                required=True
            ),
            role2: Role = SlashOption(
                name="role2",
                description="2つ目のロール",
                required=False
            ),
        ):
        return



    @commands.command(name="rolepanel", aliases=["ロールパネル","rp","ろーるぱねる","ろーぱね"], help="""\
ロールパネル機能

ボタンを押すことでロールを付与/削除するメッセージを送信します。
```
n!rolepanel [メッセージ内容]
[ロールIDまたは名前1]
[ロールIDまたは名前2]...
```

ロールは最大で25個まで指定できます。
ただ、重複してのロール指定はできません。""")
    async def rolepanel(self, ctx: commands.Context):
        if ctx.message.content == "n!rolepanel debug":
            await ctx.message.add_reaction('🐛')
            if ctx.author.id in n_fc.py_admin:
                await ctx.send(f"{ctx.message.author.mention}", embed=nextcord.Embed(title="Views", description=PersistentViews, color=0x00ff00))
                return
            else:
                await ctx.send(f"{ctx.message.author.mention}", embed=nextcord.Embed(title="ERR", description="あなたは管理者ではありません。", color=0xff0000))
                return
            return
        if admin_check(ctx.guild, ctx.author) == False:
            await ctx.send("あなたは管理者ではありません。")
            return
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send("ロールパネル機能を使用するにはメッセージ内容とロールIDまたは名前を指定してください。")
            return
        elif len(ctx.message.content.splitlines()) > 26:
            await ctx.send("ロールパネル機能は最大で25個までロールを指定できます。")
            return
        args = ctx.message.content.splitlines()[0].split(" ", 1)
        if len(args) == 1:
            content = "にらBOT ロールパネル"
        else:
            content = args[1]
        ViewArgs = []
        embed_content = ""
        for i in range(len(ctx.message.content.splitlines())):
            if i == 0:
                continue
            role_id = None
            try:
                role_id = int(ctx.message.content.splitlines()[i])
            except ValueError:
                roles = ctx.guild.roles
                for j in range(len(roles)):
                    if roles[j].name == ctx.message.content.splitlines()[i]:
                        role_id = roles[j].id
                        break
                if role_id == None:
                    await ctx.reply(f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。")
                    return
            if role_id == None:
                await ctx.reply(f"エラー: 指定されたロール`{ctx.message.content.splitlines()[i]}`が存在しません。")
                return
            embed_content += f"{i}: <@&{role_id}>\n"
            ViewArgs.append([i, role_id])
        self.bot.add_view(RolePanelView(ViewArgs))
        PersistentViews.append(ViewArgs)
        with open(f'{sys.path[0]}/PersistentViews.nira', 'wb') as f:
            pickle.dump(PersistentViews, f)
        try:
            await ctx.send(embed=nextcord.Embed(title=f"{content}", description=embed_content, color=0x00ff00), view=RolePanelView(ViewArgs))
        except BaseException as err:
            await ctx.send(f"エラー: `{err}`")
            return


# args = [["ButtonLabel", "Role_Id"]]


def setup(bot):
    if os.path.exists(f'{sys.path[0]}/PersistentViews.nira'):
        with open(f'{sys.path[0]}/PersistentViews.nira', 'rb') as f:
            global PersistentViews
            PersistentViews = pickle.load(f)
    bot.add_cog(rolepanel(bot))
