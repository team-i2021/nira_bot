import datetime
import logging
import os
import pickle
import re
import sys
from os import getenv
import traceback

import nextcord
from nextcord import Interaction, message
from nextcord.ext import commands
from nextcord.utils import get

from util import n_fc, mc_status
from util.admin_check import admin_check

global PollViews
PollViews = []

# pollpanel
# version2


class PollPanelSlashInput(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__(
            "投票パネル",
            timeout=None
        )

        self.bot = bot

        self.EmbedTitle = nextcord.ui.TextInput(
            label=f"投票パネルのタイトル",
            style=nextcord.TextInputStyle.short,
            placeholder=f"好きな猫に投票してね",
            required=False
        )
        self.add_item(self.EmbedTitle)

        self.PollType = nextcord.ui.TextInput(
            label=f"投票タイプ",
            style=nextcord.TextInputStyle.short,
            placeholder=f"「0」で一人一票、「1」で一人何票でも",
            required=True,
            min_length=1,
            max_length=1,
        )
        self.add_item(self.PollType)

        self.Polls = nextcord.ui.TextInput(
            label=f"投票内容（投票内容ごとに改行！）",
            style=nextcord.TextInputStyle.paragraph,
            placeholder=f"しろねこ\nくろねこ\nみけねこ",
            required=True
        )
        self.add_item(self.Polls)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        values = [i for i in self.Polls.value.splitlines() if i != ""]

        if "".join(re.findall(r'[0-1]', self.PollType.value)) == "":
            await interaction.followup.send("投票タイプは、「0」か「1」で入力してください")
            return

        if len(values) > 25:
            await interaction.followup.send("投票パネル機能は最大で24個まで選択肢を指定できます。")
            return

        embed_content = ""
        if int("".join(re.findall(r'[0-1]', self.PollType.value))) == 0:
            embed_content = "`一人一票`\n" + ":`0`票:なし\n".join(values) + ":`0`票:なし"
        else:
            embed_content = "`一人何票でも`\n" + \
                ":`0`票:なし\n".join(values) + ":`0`票:なし"

        self.bot.add_view(PollPanelView(values))
        PollViews.append(values)
        if self.EmbedTitle.value == "" or self.EmbedTitle.value is None:
            self.EmbedTitle.value = "にらBOT投票パネル"
        with open(f'{sys.path[0]}/PollViews.nira', 'wb') as f:
            pickle.dump(PollViews, f)
        try:
            await interaction.followup.send(f"作成者:{interaction.user.mention}", embed=nextcord.Embed(title=f"{self.EmbedTitle.value}", description=embed_content, color=0x00ff00), view=PollPanelView(values))
        except Exception:
            await interaction.followup.send(f"エラー: ```\n{traceback.format_exc()}```")
            return


class PollPanelView(nextcord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for i in args:
            self.add_item(PollPanelButton(i))
        self.add_item(PollPanelEnd())


class PollPanelButton(nextcord.ui.Button):
    def __init__(self, arg):
        super().__init__(
            label=arg,
            style=nextcord.ButtonStyle.green,
            custom_id=f"PolePanel:{arg}"
        )

    async def callback(self, interaction: Interaction):
        try:
            message = interaction.message
            content = message.embeds[0].description
            pollType = None
            if content.splitlines()[0] == "`一人一票`":
                pollType = True
            else:
                pollType = False
            who = interaction.user.id
            what = self.custom_id.split(':')[1]
            choice = {}
            Pollers = []
            for i in content.splitlines()[1:]:
                if i.split(":", 2)[2] != "なし":
                    choice[i.split(":", 2)[0]] = [
                        j for j in i.split(":", 2)[2].split("/")]
                else:
                    choice[i.split(":", 2)[0]] = []

            for i in choice.keys():
                Pollers.extend(choice[i])
            Pollers = list(set(Pollers))

            if not pollType and f"<@{who}>" not in Pollers:
                # 複数投票可&自分が投票していなかった
                choice[what].append(f"<@{who}>")

            elif not pollType and f"<@{who}>" in Pollers:
                # 複数投票可&自分が投票していた
                if f"<@{who}>" in choice[what]:
                    choice[what].remove(f"<@{who}>")
                else:
                    choice[what].append(f"<@{who}>")

            elif pollType and f"<@{who}>" not in Pollers:
                # 一人一票&自分が投票していなかった
                choice[what].append(f"<@{who}>")

            elif pollType and f"<@{who}>" in Pollers:
                # 一人一票&自分が投票していた
                if f"<@{who}>" not in choice[what]:
                    for i in choice.keys():
                        if f"<@{who}>" in choice[i]:
                            choice[i].remove(f"<@{who}>")
                    choice[what].append(f"<@{who}>")

                else:
                    choice[what].remove(f"<@{who}>")

            returnText = f"{content.splitlines()[0]}\n"
            for i in choice.keys():
                if choice[i] == []:
                    returnText += f"{i}:`0`票:なし\n"
                else:
                    returnText += f"{i}:`{len(choice[i])}`票:{'/'.join(choice[i])}\n"
            await interaction.message.edit(embed=nextcord.Embed(title=message.embeds[0].title, description=returnText, color=0x00ff00))

        except BaseException as err:
            await interaction.response.send_message(f"ERR: `{err}`", ephemeral=True)


class PollPanelEnd(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="締め切る", style=nextcord.ButtonStyle.red, custom_id="PolePanel:end")

    async def callback(self, interaction: Interaction):
        if interaction.message.content.split(":")[1] == interaction.user.mention:
            await interaction.message.edit(content="投票終了！", view=None)
            return
        else:
            await interaction.response.send_message("誰だおめぇ...？\n（投票製作者のみ締め切ることが出来ます！）", ephemeral=True)


class pollpanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="pollpanel", description="投票パネルを設置します", guild_ids=n_fc.GUILD_IDS)
    async def rolepanel_slash(
        self,
        interaction: Interaction
    ):
        modal = PollPanelSlashInput(self.bot)
        await interaction.response.send_modal(modal=modal)
        return

    @commands.command(name="pollpanel", aliases=["ポールパネル", "pp", "poll", ], help="""\
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
        if ctx.message.content == f"{self.bot.command_prefix}pollpanel debug":
            await ctx.message.add_reaction('🐛')
            if ctx.author.id in n_fc.py_admin:
                await ctx.send(f"{ctx.message.author.mention}", embed=nextcord.Embed(title="Views", description=PollViews, color=0x00ff00))
                return
            else:
                await ctx.send(f"{ctx.message.author.mention}", embed=nextcord.Embed(title="ERR", description="あなたは管理者ではありません。", color=0xff0000))
                return
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send(f"投票パネル機能を使用するにはメッセージ内容と選択肢を指定してください。\n```\n{self.bot.command_prefix}pollpanel [on/off] [メッセージ内容]\n[選択肢1]\n[選択肢2]...```")
            return
        elif len(ctx.message.content.splitlines()) > 25:
            await ctx.send("投票パネル機能は最大で24個まで選択肢を指定できます。")
            return
        args = ctx.message.content.splitlines()[0].split(" ", 2)

        if len(args) == 2:
            if args[1] not in ["on", "off"]:
                await ctx.send("引数が異常です。")
                return
            content = "にらBOT 投票パネル"
        elif len(args) == 3:
            if args[1] not in ["on", "off"]:
                await ctx.send("引数が異常です。")
                return
            content = args[2]
        else:
            await ctx.send("引数が足りません。")
            return
        ViewArgs = ctx.message.content.splitlines()[1:]
        embed_content = ""
        if args[1] == "on":
            embed_content = "`一人一票`\n" + \
                ":`0`票:なし\n".join(ViewArgs) + ":`0`票:なし"
            poll_type = True
        else:
            embed_content = "`一人何票でも`\n" + \
                ":`0`票:なし\n".join(ViewArgs) + ":`0`票:なし"
            poll_type = False

        self.bot.add_view(PollPanelView(ViewArgs))
        PollViews.append(ViewArgs)
        with open(f'{sys.path[0]}/PollViews.nira', 'wb') as f:
            pickle.dump(PollViews, f)
        try:
            await ctx.send(f"作成者:{ctx.author.mention}", embed=nextcord.Embed(title=f"{content}", description=embed_content, color=0x00ff00), view=PollPanelView(ViewArgs))
        except BaseException as err:
            await ctx.send(f"エラー: `{err}`")
            return


# args = [["ButtonLabel", "Role_Id"]]


def setup(bot):
    if os.path.exists(f'{sys.path[0]}/PollViews.nira'):
        with open(f'{sys.path[0]}/PollViews.nira', 'rb') as f:
            global PollViews
            PollViews = pickle.load(f)
    bot.add_cog(pollpanel(bot))
