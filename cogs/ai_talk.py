import a3rt_talkpy

import enum
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

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
        self.gcloud_token: str | None = self.bot.settings["gcloud_api"]
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
        """Google CloudのGemini APIを使用して返答を取得します。"""
        payload = {
            "contents": [
                {"role": "user", "parts": {"text": prompt}}
            ]
        }
        async with self.bot.session.post(self.GEMINI_URL.format(TOKEN=self.gcloud_token), json=payload) as resp:
            data = await resp.json()
            if "error" in data:
                raise Exception(data["error"]["message"])
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def get_a3rt_response(self, prompt: str) -> str | None:
        """A3RTのTalk APIを使用して返答を取得します。"""
        resp = await self.a3rt_client.talk(query=prompt)
        if not resp.is_empty():
            return resp.reply
        return

    async def get_response(self, prompt: str) -> str | None:
        """現在設定されているAIプロバイダから返答を取得します。"""
        if self.ai_provider == TalkProvider.A3RT:
            return await self.get_a3rt_response(prompt)
        elif self.ai_provider == TalkProvider.GEMINI:
            return await self.get_gemini_response(prompt)

    def split_content(self, content: str) -> list[str]:
        if len(content) <= 2000:
            return [content]
        elif len(content) <= 10000:
            return [content[i:i+2000] for i in range(0, len(content), 2000)]
        else:
            return [content[:2000], content[2000:4000], content[4000:6000], content[6000:8000], content[8000:9990] + "..."]

    async def create_response(self, prompt: str) -> tuple[list[str], nextcord.Embed]:
        """AIからの返答を取得して返します。"""
        try:
            resp = await self.get_response(prompt)
            if resp is None:
                return (
                    [""],
                    nextcord.Embed(
                        title=self.get_embed_title,
                        description="返答がありませんでした。",
                        color=0xffff00
                    ).set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                )
            else:
                return (
                    self.split_content(resp),
                    nextcord.Embed(
                        title=self.get_embed_title,
                        description="AIから返答が返ってきました。",
                        color=0x00ff00
                    ).set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                )
        except Exception as err:
            return (
                [""],
                nextcord.Embed(
                    title=self.get_embed_title,
                    description=f"エラーが発生しました。\n`{err}`",
                    color=0xff0000
                ).set_footer(
                    text=self.footer_text,
                    icon_url=self.footer_icon
                )
            )

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
            prompt: str = SlashOption(
                name="prompt",
                description="Conversation content",
                description_localizations={
                    nextcord.Locale.ja: "会話内容"
                },
                required=True,
            )
        ):
        assert not isinstance(interaction.channel, (nextcord.CategoryChannel, nextcord.ForumChannel))
        assert interaction.channel is not None
        await interaction.response.defer(ephemeral=False)
        contents, embed = await self.create_response(prompt)
        for i in range(len(contents)):
            await interaction.channel.send(content=contents[i])
        await interaction.followup.send(embed=embed)

    @commands.command(
        name="talk",
        help="""\
AIと会話してみましょう。
`n!talk [prompt]`

引数1: str
お話内容"""
    )
    async def talk_command(self, ctx: commands.Context, *, prompt: str):
        async with ctx.typing():
            contents, embed = await self.create_response(prompt)
            for i in range(len(contents)):
                if i == len(contents) - 1:
                    await ctx.send(content=contents[i], embed=embed)
                else:
                    await ctx.send(content=contents[i])


def setup(bot: NIRA, **kwargs: Any):
    bot.add_cog(Talk(bot, **kwargs))
