import a3rt_talkpy

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import n_fc
from util.nira import NIRA

from typing import Any

# A3RT Talk API
# 今流行りのAIチャットボットに便乗した形。

class Talk(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs: Any):
        # 型の理解がよわいから適当にAnyと書いてるがこれいかに（自分が理解するまではこれで放置）
        self.bot = bot
        token: str = self.bot.settings["talk_api"]
        self.client = a3rt_talkpy.AsyncTalkClient(token)

    @nextcord.slash_command(
        name="talk",
        description="Use of the system indicates that you agree to the Terms of Use.",
        description_localizations={
            nextcord.Locale.ja: "使用にはA3RT TalkAPIの利用規約に同意する必要があります。",
            nextcord.Locale.uk: "Використання A3RT TalkAPI вимагає згоди з Умовами використання."
        },
    )
    async def talk_slash(
            self,
            interaction: Interaction,
            query: str = SlashOption(
                name="query",
                description="Conversation content",
                description_localizations={
                    nextcord.Locale.ja: "会話内容",
                    nextcord.Locale.uk: "Зміст розмови"
                },
                required=True,
            )
        ):
        await interaction.response.defer(ephemeral=False)
        try:
            resp = await self.client.talk(query=query)
            if resp.is_empty():
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Talk API",
                        description="返答がありませんでした。",
                        color=0xffff00
                    )
                    .set_footer(
                        text="Talk API Powered by A3RT",
                        icon_url="https://a3rt.recruit.co.jp/common/images/logo_header.png"
                    )
                )
            else:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="Talk API",
                        description=resp.reply,
                        color=0x00ff00
                    )
                    .set_footer(
                        text="Talk API Powered by A3RT",
                        icon_url="https://a3rt.recruit.co.jp/common/images/logo_header.png"
                    )
                )
        except Exception as err:
            await interaction.send(
                    embed=nextcord.Embed(
                        title="Talk API",
                        description=f"エラーが発生しました。\n`{err}`",
                        color=0xff0000
                    )
                    .set_footer(
                        text="Talk API Powered by A3RT",
                        icon_url="https://a3rt.recruit.co.jp/common/images/logo_header.png"
                    )
                )


def setup(bot: NIRA, **kwargs: Any):
    bot.add_cog(Talk(bot, **kwargs))
