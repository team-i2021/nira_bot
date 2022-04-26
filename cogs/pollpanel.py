import nextcord
from nextcord import Interaction, message
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

from cogs.rolepanel import PersistentViews

# pollpanel

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

class PolePanelView(nextcord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for i in args:
            self.add_item(PolePanelButton(i))
        self.add_item(PolePanelEnd())


class PolePanelButton(nextcord.ui.Button):
    def __init__(self, arg):
        super().__init__(label=arg[0], style=nextcord.ButtonStyle.green, custom_id=f"PolePanel:{arg[1]}")
    
    async def callback(self, interaction: Interaction):
        message = Interaction.message
        content = message.embeds[0].description
        choice = {}
        for i in content.splitlines()[1:]:
            if i.split(":")[1] != "なし":
                choice[i.split(":")[0]] = [i for i in i.split(":")[1].split("/")]
            else:
                choice[i.split(":")[0]] = []
            
        try:
            return
        except BaseException as err:
            await interaction.response.send_message(f"ERR: {err}", ephemeral=True)


class PolePanelEnd(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="締め切る", style=nextcord.ButtonStyle.red)

    async def callback(self, interaction: Interaction):
        return


class pollpanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="pollpanel", aliases=["ポールパネル","pp","poll",], help="""\
投票パネル機能

ボタンを押すことで投票できるパネルを作成します。
```
n!pollpanel [on/off] [メッセージ内容]
[選択肢1]
[選択肢2]...
```

[on/off]は、onにすると1人1票しか入れられなくなります。

エイリアス：ポールパネル、pp、poll

選択肢は最大で24個まで指定できます。""")
    async def pollpanel(self, ctx: commands.Context):
        if admin_check(ctx.guild, ctx.author) == False:
            await ctx.send("あなたは管理者ではありません。")
            return
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send("ロールパネル機能を使用するにはメッセージ内容と選択肢を指定してください。\n```\nn!pollpanel [on/off] [メッセージ内容]\n[選択肢1]\n[選択肢2]...```")
            return
        elif len(ctx.message.content.splitlines()) > 25:
            await ctx.send("投票パネル機能は最大で24個まで選択肢を指定できます。")
            return
        args = ctx.message.content.splitlines()[0].split(" ", 2)
        if len(args) == 2:
            if args[1] not in ["on","off"]:
                await ctx.send("引数が異常です。")
                return
            content = "にらBOT 投票パネル"
        elif len(args) == 3:
            if args[1] not in ["on","off"]:
                await ctx.send("引数が異常です。")
                return
            content = args[2]
        else:
            await ctx.send("引数が足りません。")
            return
        if args[1] == "on":
            poll_type = True
        else:
            poll_type = False
        ViewArgs = ctx.message.content.splitlines()[1:]
        embed_content =  ":なし\n".join(ViewArgs) + ":なし"
        
        self.bot.add_view(PolePanelView(ViewArgs))
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
    bot.add_cog(pollpanel(bot))
