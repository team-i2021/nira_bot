import asyncio

import nextcord
from nextcord.ext import application_checks, commands

from util.nira import NIRA

class ChannelSort(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot

    def which_channel(self, a: nextcord.abc.GuildChannel, b: nextcord.abc.GuildChannel) -> nextcord.abc.GuildChannel:
        """
        aとbのどちらのチャンネルが優位かを判定します

        優位条件1: チャンネル名が同じ場合、IDが小さい方が優位
        優位条件2: チャンネル名が異なる場合、Unicodeのコードポイント順で小さい方が優位
        優位条件3: それ以外の場合、チャンネルは同じと判断されるため、aが優位とされる

        Parameters
        ----------
        a : nextcord.abc.GuildChannel
            比較対象のチャンネル
        b : nextcord.abc.GuildChannel
            比較対象のチャンネル

        Returns
        -------
        nextcord.abc.GuildChannel
            優位なチャンネル

        """
        if a.name == b.name:
            if a.id < b.id:
                return a
            else:
                return b
        else:
            for i in range(min(len(a.name), len(b.name))):
                if a.name[i] != b.name[i]:
                    if ord(a.name[i]) < ord(b.name[i]):
                        return a
                    else:
                        return b
            return a

    def quick_sort(self, channels: list[nextcord.abc.GuildChannel]) -> list[nextcord.abc.GuildChannel]:
        """
        理解が間違ってなければクイックソートしてます
        """
        if len(channels) <= 1:
            return channels
        else:
            pivot = channels.pop(0)

            left = [c for c in channels if self.which_channel(c, pivot) == c]
            right = [c for c in channels if self.which_channel(c, pivot) == pivot]

            left = self.quick_sort(left)
            right = self.quick_sort(right)

            return left + [pivot] + right

    @application_checks.guild_only()
    @application_checks.has_guild_permissions(manage_channels=True)
    @application_checks.bot_has_guild_permissions(manage_channels=True)
    @nextcord.slash_command(
        name="sort",
        description="Sorts the channels in the server.",
        description_localizations={
            nextcord.Locale.ja: "サーバーのチャンネルを並べ替えます。",
        },
    )
    async def sort_slash(
        self,
        interaction: nextcord.Interaction,
        category: (nextcord.CategoryChannel | None) = nextcord.SlashOption(
            name="category",
            description="The category to sort.",
            description_localizations={
                nextcord.Locale.ja: "並べ替えるカテゴリー。",
            },
            required=False,
        ),
    ):
        await interaction.response.defer()
        if category is None:
            category = interaction.channel.category
        if category is None:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="カテゴリー外のチャンネルでこのコマンドを実行するには、カテゴリーを指定する必要があります。",
                    color=self.bot.color.ERROR,
                )
            )
            return

        channels = category.channels
        if len(channels) <= 1:
            await interaction.send(
                embed=nextcord.Embed(
                    title="終了",
                    description="指定したカテゴリーにはチャンネルが2つ以上ないため、操作が終了しました。",
                    color=self.bot.color.ATTENTION,
                )
            )
            return

        sorted_channels = self.quick_sort(channels)
        text_channels = [
            c for c in sorted_channels if isinstance(c, nextcord.TextChannel) or isinstance(c, nextcord.ForumChannel)
        ]
        voice_channels = [
            c for c in sorted_channels if isinstance(c, nextcord.VoiceChannel) or isinstance(c, nextcord.StageChannel)
        ]

        print(text_channels)
        print(voice_channels)

        for pos in range(len(text_channels)):
            if text_channels[pos].position == pos:
                continue
            await text_channels[pos].move(beginning=True, offset=pos, category=category)
            await asyncio.sleep(1)

        for pos in range(len(voice_channels)):
            if voice_channels[pos].position == pos:
                continue
            await voice_channels[pos].move(beginning=True, offset=pos, category=category)
            await asyncio.sleep(1)

        await interaction.send(
            embed=nextcord.Embed(title="完了", description="チャンネルの並べ替えが完了しました。", color=self.bot.color.NORMAL)
        )


def setup(bot: NIRA):
    bot.add_cog(ChannelSort(bot))
