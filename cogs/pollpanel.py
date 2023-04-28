import logging
import re
import traceback

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util import n_fc
from util.nira import NIRA

# pollpanel v2
pollpanel_title_compile = re.compile(r"作成者:<@[0-9]+>")
pollpanel_value_compile = re.compile(r".+:`[0-9]+`票:.+")

class PollPanelSlashInput(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "投票パネル",
            timeout=None
        )

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

        if self.EmbedTitle.value == "" or self.EmbedTitle.value is None:
            self.EmbedTitle.value = "にらBOT投票パネル"
        try:
            await interaction.followup.send(f"作成者:{interaction.user.mention}", embed=nextcord.Embed(title=f"{self.EmbedTitle.value}", description=embed_content, color=0x00ff00).set_footer(text="NIRA Bot - PollPanel v2"), view=PollPanelView(values))
        except Exception:
            await interaction.followup.send(f"エラー: ```\n{traceback.format_exc()}```")
            return



class PollPanelEditModal(nextcord.ui.Modal):
    def __init__(self, message: nextcord.Message, options: dict[str, str], polltype: int):
        super().__init__(
            "投票パネル 編集",
            timeout=None
        )

        self.message = message
        self.options = options
        self.poltype = polltype

        self.Polls = nextcord.ui.TextInput(
            label=f"投票選択肢",
            style=nextcord.TextInputStyle.paragraph,
            placeholder=f"くろねこ\nしろねこ\n刻晴",
            required=True,
            default_value="\n".join(list(options.keys()))
        )
        self.add_item(self.Polls)

        self.PollType = nextcord.ui.TextInput(
            label=f"投票タイプ",
            style=nextcord.TextInputStyle.short,
            placeholder=f"「0」で一人一票、「1」で一人何票でも",
            required=True,
            min_length=1,
            max_length=1,
            default_value=str(polltype)
        )
        self.add_item(self.PollType)

        self.add_item(
            nextcord.ui.TextInput(
                label="注意事項",
                style=nextcord.TextInputStyle.paragraph,
                default_value="現在ある選択肢を削除/編集すると、その選択肢へ投票された票も削除され、再度追加しても戻ってきません。",
                required=False
            )
        )

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        values = [i for i in self.Polls.value.splitlines() if i != ""]

        if len(values) > 25:
            await interaction.followup.send("投票パネル機能は最大で24個まで選択肢を指定できます。")
            return

        embed_content = ""
        options = {}
        Args = []
        if self.PollType.value == "0":
            embed_content = "`一人一票`\n"
        elif self.PollType.value == "1":
            embed_content = "`一人何票でも`\n"
        else:
            await interaction.followup.send("「投票タイプ」には0か1のみを指定できます")
            return


        for i in values:
            if i not in list(self.options.keys()):
                options[i] = "`0`票:なし"
            else:
                options[i] = self.options[i]
            Args.append(i)

        embed_content += "\n".join([f"{key}:{value}" for key, value in options.items()])

        EmbedTitle = self.message.embeds[0].title
        try:
            await self.message.edit(embed=nextcord.Embed(title=EmbedTitle, description=embed_content, color=0x00ff00).set_footer(text="NIRA Bot - PollPanel v2"), view=PollPanelView(Args))
        except Exception as err:
            await interaction.followup.send(f"エラー: `{err}`")
            return



class PollPanelView(nextcord.ui.View):
    def __init__(self, args: list[str]):
        super().__init__(timeout=None)

        for arg in args:
            self.add_item(PollPanelButton(arg))
        self.add_item(PollPanelEnd())
        self.stop()



class PollPanelButton(nextcord.ui.Button):
    def __init__(self, arg: str):
        super().__init__(
            label=arg,
            style=nextcord.ButtonStyle.green,
            custom_id=f"PollPanel:{arg}"
        )

    async def callback(self, interaction: Interaction):
        ...


class PollPanelEndConfirm(nextcord.ui.Button):
    def __init__(self, interaction: Interaction):
        super().__init__(label="本当に締め切る", style=nextcord.ButtonStyle.red)
        self.interaction = interaction

    async def callback(self, interaction: Interaction):
        await self.interaction.message.edit(content="投票終了！", view=None)
        await interaction.response.send_message("投票は締め切られました。", ephemeral=True)
        self.view.stop()

class PollPanelEnd(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="締め切る", style=nextcord.ButtonStyle.red, custom_id="PollPanel:end")

    async def callback(self, interaction: Interaction):
        ...

class Pollpanel(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @nextcord.message_command(name="Edit Pollpanel", name_localizations={nextcord.Locale.ja: "投票パネル編集"}, guild_ids=n_fc.GUILD_IDS)
    async def edit_pollpanel(self, interaction: Interaction, message: nextcord.Message):
        if message.author.id != self.bot.user.id:
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description=f"{self.bot.user.mention}が送信した投票パネルにのみこのコマンドを使用できます。", color=0xff0000), ephemeral=True)
            return
        if message.content == "投票終了！":
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description="投票は締め切られています。", color=0xff0000), ephemeral=True)
            return
        if (message.content == "" or message.content is None) or (message.embeds == [] or len(message.embeds) > 1) or re.fullmatch(pollpanel_title_compile, message.content) is None:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"""\
選択されたメッセージは投票パネルではないです。
(投票パネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: E1-{(message.content == "") * 1 + (message.content is None) * 2 + (message.embeds == []) * 4 + (len(message.embeds) > 1) * 8 + (re.fullmatch(pollpanel_title_compile, message.content) is None) * 16}`""",
                    color=0xff0000
                ),
                ephemeral=True
            )
            return
        if message.content.split(":")[1] != interaction.user.mention:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー",
                    description="この投票パネルは本当にあなたが作成したものですか？\nもしあなたが作成したのにこのメッセージが表示される場合はお問い合わせください。",
                    color=0xff0000
                ),
                ephemeral=True
            )
            return
        # await interaction.response.defer(ephemeral=True)
        options = {}
        for i in range(len(message.embeds[0].description.splitlines()[1:])):
            content = message.embeds[0].description.splitlines()[i+1]
            if re.fullmatch(pollpanel_value_compile, content) is None:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"""\
選択されたメッセージは投票パネルではないです。
(投票パネルであるにもかかわらずこのメッセージが表示される場合はお問い合わせください。)

・エラーコード
`Reject reason: E2-{i}`""",
                        color=0xff0000
                    ),
                    ephemeral=True
                )
                return
            values = content.split(":", 1)
            options[values[0]] = values[1]
        if message.embeds[0].description.splitlines()[0] == "`一人一票`":
            polltype = 0
        else:
            polltype = 1
        await interaction.response.send_modal(PollPanelEditModal(message, options, polltype))


    @nextcord.slash_command(name="pollpanel", description="Create pollpanel", description_localizations={nextcord.Locale.ja: "投票パネルを設置します"}, guild_ids=n_fc.GUILD_IDS)
    async def pollpanel_slash(
        self,
        interaction: Interaction
    ):
        modal = PollPanelSlashInput()
        await interaction.response.send_modal(modal=modal)


    @commands.command(name="pollpanel", aliases=["ポールパネル", "pp", "poll", "投票"], help="""\
投票パネル機能

ボタンを押すことで投票できるパネルを作成します。
```
n!pollpanel [on/off] [メッセージ内容]
[選択肢1]
[選択肢2]...
```

[on/off]は、onにすると1人1票しか入れられなくなります。

エイリアス: ポールパネル、pp、poll

選択肢は最大で24個まで指定できます。""")
    async def pollpanel(self, ctx: commands.Context):
        if len(ctx.message.content.splitlines()) < 2:
            await ctx.send(f"投票パネル機能を使用するにはメッセージ内容と選択肢を指定してください。\n```\n{ctx.prefix}pollpanel [on(一人一票)/off(一人何票でも)] [メッセージ内容]\n[選択肢1]\n[選択肢2]...```")
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
        else:
            embed_content = "`一人何票でも`\n" + \
                ":`0`票:なし\n".join(ViewArgs) + ":`0`票:なし"

        try:
            await ctx.send(
                f"作成者:{ctx.author.mention}",
                embed=nextcord.Embed(
                    title=f"{content}",
                    description=embed_content,
                    color=0x00ff00
                ).set_footer(
                    text="NIRA Bot - PollPanel v2"
                ),
                view=PollPanelView(ViewArgs)
            )
        except Exception as err:
            await ctx.send(f"エラー: `{err}`")
            return

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        # かりぱく
        # →投票に匿名性を持たせたりするような機能をつける場合はちょっと変える必要が...
        if interaction.type is not nextcord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id")
        if custom_id is None or not custom_id.startswith("PollPanel:"):
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if custom_id == "PollPanel:end":
            if interaction.message.content.split(":")[1] == interaction.user.mention:
                view = nextcord.ui.View()
                view.add_item(PollPanelEndConfirm(interaction))
                await interaction.send("本当に投票を締め切ってもよろしいですか！？\nもう投票できなくなります！", view=view, ephemeral=True)
            else:
                await interaction.send("誰だおめぇ...？\n（投票製作者のみ締め切ることが出来ます！）", ephemeral=True)
            return

        try:
            message = interaction.message
            content = message.embeds[0].description
            pollType = None
            if content.splitlines()[0] == "`一人一票`":
                pollType = True
            else:
                pollType = False
            who = interaction.user.id
            what = custom_id.split(':')[1]
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
            await interaction.message.edit(embed=nextcord.Embed(title=message.embeds[0].title, description=returnText, color=0x00ff00).set_footer(text="NIRA Bot - PollPanel v2"))

        except Exception as err:
            await interaction.response.send_message(f"ERR: `{err}`", ephemeral=True)
            logging.error(err, exc_info=True)


# args = [["ButtonLabel", "Role_Id"]]


def setup(bot, **kwargs):
    bot.add_cog(Pollpanel(bot, **kwargs))
