import sys

import HTTP_db
import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from cogs import embed, translate, tts
from util import n_fc
from util import nira


# メッセージコマンド

SYSDIR = sys.path[0]


class MessageCommandPulldown(nextcord.ui.Select):
    def __init__(self, bot: commands.Bot, client: HTTP_db.Client, interaction: Interaction, message: nextcord.Message):
        options = [
            nextcord.SelectOption(
                label="Embedコンテンツの取得", description="Embedの中身を取得します。", value="embed"
            ),
            nextcord.SelectOption(
                label="メッセージの翻訳", description="メッセージを翻訳します。", value="translate"
            ),
            nextcord.SelectOption(
                label="メッセージの読み上げ", description="メッセージをVCで読み上げます。", value="tts"
            )
        ]

        super().__init__(
            placeholder="選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )

        self.bot = bot
        self.kwargs = {"client": client}
        self.interaciton = interaction
        self.message = message
    
    async def callback(self, interaction: Interaction):
        value = self.values[0]
        if value == "embed":
            await embed.SendEmbed.embed_message_command(embed.SendEmbed(self.bot, self.kwargs), interaction, self.message)
        elif value == "translate":
            await translate.Translate.translation_message_command(translate.Translate(self.bot, self.kwargs), interaction, self.message)
        elif value == "tts":
            await tts.tts.speak_message(tts.tts(self.bot, self.kwargs), interaction, self.message)
        return




class MessageCommands(commands.Cog):
    def __init__(self, bot: nira.NIRA, **kwargs):
        self.bot = bot
            
    @nextcord.message_command(name="その他", guild_ids=n_fc.GUILD_IDS)
    async def other_message_command(self, interaction: Interaction, message: nextcord.Message):
        view = nextcord.ui.View()
        view.add_item(MessageCommandPulldown(self.bot, self.bot.client, interaction, message))
        await interaction.response.send_message("実行したいメッセージコマンドを選択してください。", view=view, ephemeral=True)
        return

def setup(bot, **kwargs):
    bot.add_cog(MessageCommands(bot, **kwargs))
