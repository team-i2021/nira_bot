import a3rt_talkpy

import enum
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import n_fc
from util.nira import NIRA

from typing import Any

class TalkProvider(enum.Enum):
    A3RT = "a3rt"
    GEMINI = "gemini"

class Talk(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs: Any):
        self.bot = bot

        self.ai_provider = TalkProvider.A3RT

        a3rt_talk_token: str = self.bot.settings["talk_api"]
        self.a3rt_client = a3rt_talkpy.AsyncTalkClient(a3rt_talk_token)
        self.gcloud_token: str = self.bot.settings["gcloud_api"]
        self.GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={TOKEN}"
        if self.gcloud_token is not None:
            self.ai_provider = TalkProvider.GEMINI

    @property
    def footer_text(self) -> str:
        if self.ai_provider == TalkProvider.A3RT:
            return "Talk API Powered by A3RT"
        elif self.ai_provider == TalkProvider.GEMINI:
            return "Gemini AI Powered by Google Cloud API"
        else:
            return "Talk AI"

    @property
    def footer_icon(self) -> str | None:
        if self.ai_provider == TalkProvider.A3RT:
            return "https://a3rt.recruit.co.jp/common/images/logo_header.png"

    @property
    def get_embed_title(self) -> str:
        if self.ai_provider == TalkProvider.A3RT:
            return "Talk API"
        elif self.ai_provider == TalkProvider.GEMINI:
            return "Gemini AI"
        else:
            return "Talk AI"

    async def get_gemini_response(self, prompt: str) -> str | None:
        payload = {
            "contents": [
                {"role": "user", "parts": {"text": prompt}}
            ]
        }
        async with self.bot.session.post(self.GEMINI_URL.format(TOKEN=self.gcloud_token), json=payload) as resp:
            data = await resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def get_a3rt_response(self, prompt: str) -> str | None:
        resp = await self.a3rt_client.talk(query=prompt)
        if not resp.is_empty():
            return resp.reply
        return

    async def get_response(self, prompt: str) -> str | None:
        if self.ai_provider == TalkProvider.A3RT:
            return await self.get_a3rt_response(prompt)
        elif self.ai_provider == TalkProvider.GEMINI:
            return await self.get_gemini_response(prompt)

    @nextcord.slash_command(
        name="talk",
        description="Talk with AI",
        description_localizations={
            nextcord.Locale.ja: "AIと会話してみましょう。",
        },
    )
    async def talk_slash(
            self,
            interaction: Interaction,
            query: str = SlashOption(
                name="query",
                description="Conversation content",
                description_localizations={
                    nextcord.Locale.ja: "会話内容"
                },
                required=True,
            )
        ):
        await interaction.response.defer(ephemeral=False)
        try:
            resp = await self.get_response(query)
            if resp is None:
                await interaction.send(
                    embed=nextcord.Embed(
                        title=self.get_embed_title,
                        description="返答がありませんでした。",
                        color=0xffff00
                    )
                    .set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                )
            else:
                await interaction.send(
                    embed=nextcord.Embed(
                        title=self.get_embed_title,
                        description=resp,
                        color=0x00ff00
                    )
                    .set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                )
        except Exception as err:
            await interaction.send(
                    embed=nextcord.Embed(
                        title=self.get_embed_title,
                        description=f"エラーが発生しました。\n`{err}`",
                        color=0xff0000
                    )
                    .set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                )


def setup(bot: NIRA, **kwargs: Any):
    bot.add_cog(Talk(bot, **kwargs))
