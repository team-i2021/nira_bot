import sys

import HTTP_db
import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from util import n_fc
from util import nira


# メッセージコマンド

SYSDIR = sys.path[0]


class MessageCommandPulldown(nextcord.ui.Select):
    def __init__(self, bot: nira.NIRA, interaction: Interaction, message: nextcord.Message):
        options = [
            nextcord.SelectOption(
                label="Embedコンテンツの取得", description="Embedの中身を取得します。", value="Embed"
            ),
            nextcord.SelectOption(
                label="メッセージの翻訳", description="メッセージを翻訳します。", value="Translate"
            ),
            nextcord.SelectOption(
                label="メッセージの読み上げ", description="メッセージをVCで読み上げます。", value="Text2Speech"
            )
        ]

        super().__init__(
            placeholder="選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )

        self.bot = bot
        self.interaciton = interaction
        self.message = message

    async def callback(self, interaction: Interaction):
        value = self.values[0]
        cog = self.bot.get_cog(value)
        if cog is None:
            await interaction.send(
                "エラーまたは、BOTの機能が制限されています。",
                embed=nextcord.Embed(
                    title="Q. どういう意味ですか？",
                    description="A. メッセージコマンドの機能を呼び出そうとしましたが、機能が見つかりませんでした。\n単純なエラーか、メンテナンスなどによりBOTの機能が制限されている場合があります。\nNEWSチャンネルを確認するか、詳しくはこのメッセージをスクショしてお問い合わせください。",
                    color=0xff0000
                ).set_footer(
                    text=f"debug::value:{value}"
                ),
                ephemeral=True
            )
        else:
            await cog.mscommand(interaction, self.message)


class MessageCommands(commands.Cog):
    def __init__(self, bot: nira.NIRA, **kwargs):
        self.bot = bot

    @nextcord.message_command(name="その他", guild_ids=n_fc.GUILD_IDS)
    async def other_message_command(self, interaction: Interaction, message: nextcord.Message):
        view = nextcord.ui.View()
        view.add_item(MessageCommandPulldown(self.bot, interaction, message))
        await interaction.response.send_message("実行したいメッセージコマンドを選択してください。", view=view, ephemeral=True)

def setup(bot: nira.NIRA, **kwargs):
    bot.add_cog(MessageCommands(bot, **kwargs))
