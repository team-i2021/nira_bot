import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util.nira import NIRA


class Talk(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.GEMINI_URL = (
            "https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={TOKEN}"
        )

        self.gcloud_token = self.bot.settings.gcloud_api
        self.gemini_model = self.bot.settings.gemini_model

    @property
    def footer_text(self) -> str:
        return "Gemini AI Powered by Google Cloud API"

    @property
    def embed_title(self) -> str:
        return "Gemini AI"

    async def get_gemini_response(
        self, prompt: str, backprompt: str | None
    ) -> str | None:
        "Google CloudのGemini APIを使用して返答を取得します。"
        payload = {
            "contents": [
                {"role": "user", "parts": {"text": prompt}},
            ]
        }
        if backprompt:
            payload["contents"].insert(
                0, {"role": "model", "parts": {"text": backprompt}}
            )
        async with self.bot.session.post(
            self.GEMINI_URL.format(TOKEN=self.gcloud_token, MODEL=self.gemini_model),
            json=payload,
        ) as resp:
            data = await resp.json()
            if "error" in data:
                raise Exception(data["error"]["message"])
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def split_content(self, content: str) -> list[str]:
        if len(content) <= 2000:
            return [content]
        elif len(content) <= 10000:
            return [content[i : i + 2000] for i in range(0, len(content), 2000)]
        else:
            return [
                content[:2000],
                content[2000:4000],
                content[4000:6000],
                content[6000:8000],
                content[8000:9990] + "...",
            ]

    async def create_response(
        self, prompt: str, backprompt: str | None = None
    ) -> tuple[list[str], nextcord.Embed]:
        """AIからの返答を取得して返します。"""
        try:
            resp = await self.get_gemini_response(prompt, backprompt)
            if resp is None:
                contents = [""]
                result = nextcord.Embed(description="返答がありませんでした。", color=self.bot.color.ATTENTION)
            else:
                contents = self.split_content(resp)
                result = nextcord.Embed(description="AIから返答が返ってきました。", color=self.bot.color.NORMAL)
        except Exception as err:
            contents = [""]
            result = nextcord.Embed(description=f"エラーが発生しました。\n`{err}`", color=self.bot.color.ERROR)

        result.title = self.embed_title
        result.set_footer(text=self.footer_text)
        return contents, result

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
            description_localizations={nextcord.Locale.ja: "会話内容"},
            required=True,
        ),
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
お話内容

AIが返答した内容（のメッセージ）に対して、リプライを飛ばす形でこのコマンドを使用すると、疑似的に前の話から会話を続けることが出来ます。
それ以外のメッセージにリプライを飛ばす形でこのコマンドを使うことも出来ますが、AIに喋らせたという前提上AIが困惑するかもしれません。""",
    )
    async def talk_command(self, ctx: commands.Context, *, prompt: str):
        if (
            ctx.message.reference
            and ctx.message.reference.cached_message
            and ctx.message.reference.cached_message.content
        ):
            backprompt = ctx.message.reference.cached_message.content
        else:
            backprompt = None
        async with ctx.typing():
            contents, embed = await self.create_response(prompt, backprompt)
            for i in range(len(contents)):
                if i == len(contents) - 1:
                    await ctx.send(content=contents[i], embed=embed)
                else:
                    await ctx.send(content=contents[i])


def setup(bot: NIRA):
    bot.add_cog(Talk(bot))
