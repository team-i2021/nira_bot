import asyncio
from typing import TypeVar

import nextcord
from nextcord.ext import application_checks, commands

from util.nira import NIRA

from motor import motor_asyncio

GuildChannelT_co = TypeVar("GuildChannelT_co", bound=nextcord.abc.GuildChannel, covariant=True)

class ChannelUtil(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.vclimit_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["vclimit_role"]
        self.vclimit_channel_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["vclimit_channel"]

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

    def quick_sort(self, channels: list[GuildChannelT_co]) -> list[GuildChannelT_co]:
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
        assert interaction.channel is not None
        assert not isinstance(interaction.channel, nextcord.PartialMessageable)

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

    @application_checks.guild_only()
    @nextcord.slash_command(
        name="vclimit",
        description="Sets the user limit of the voice channel.",
        description_localizations={
            nextcord.Locale.ja: "ボイスチャンネルのユーザー上限を設定します。",
        },
    )
    async def vclimit_slash(self, interaction: nextcord.Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_guild_permissions(manage_channels=True)
    @vclimit_slash.subcommand(
        name="grant",
        description="Sets whether to allow anyone to execute the user limit command on this VC",
        description_localizations={
            nextcord.Locale.ja: "ユーザー上限コマンドをこのVCで誰にでも許可するかを設定します。",
        },
    )
    async def vclimit_grant_slash(
        self,
        interaction: nextcord.Interaction,
        grant: bool = nextcord.SlashOption(
            name="grant",
            description="Whether to allow anyone to execute the user limit command on this VC.",
            description_localizations={
                nextcord.Locale.ja: "このVCでユーザー上限コマンドを誰にでも許可するか。",
            },
            required=True,
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        assert isinstance(interaction.guild, nextcord.Guild)
        assert isinstance(interaction.user, nextcord.Member)
        # コマンド実行者が入っているボイスチャンネルを取得
        if interaction.user.voice is None:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="このコマンドを実行するには、ボイスチャンネルに入室している必要があります。",
                    color=self.bot.color.ERROR,
                ),
                ephemeral=True,
            )
            return
        channel = interaction.user.voice.channel
        assert isinstance(channel, nextcord.VoiceChannel)
        if grant:
            await self.vclimit_channel_collection.update_one({"guild_id": interaction.guild.id}, {"$set": {str(channel.id): True}}, upsert=True)
        else:
            await self.vclimit_channel_collection.update_one({"guild_id": interaction.guild.id}, {"$unset": {str(channel.id): True}}, upsert=True)
        await interaction.send(
            embed=nextcord.Embed(
                title="完了",
                description=f"<#{channel.id}>で、ロールが付与されていないユーザーによる、ユーザー上限コマンドの実行{'が出来るように' if grant else 'が出来なく'}なりました。",
                color=self.bot.color.NORMAL,
            ),
            ephemeral=True,
        )


    @application_checks.guild_only()
    @application_checks.has_guild_permissions(manage_channels=True)
    @vclimit_slash.subcommand(
        name="manage",
        description="Sets the role that can execute the user limit command.",
        description_localizations={
            nextcord.Locale.ja: "ユーザー上限コマンドを実行できるロールを設定します。",
        },
    )
    async def vclimit_manage_slash(
        self,
        interaction: nextcord.Interaction,
        managerole: nextcord.Role = nextcord.SlashOption(
            name="managerole",
            description="The role that can execute the user limit command.",
            description_localizations={
                nextcord.Locale.ja: "ユーザー上限コマンドを実行できるロール",
            },
            required=True,
        ),
    ):
        await interaction.response.defer(ephemeral=True)
        assert isinstance(interaction.guild, nextcord.Guild)
        await self.vclimit_collection.update_one(
            {"_id": interaction.guild.id}, {"$set": {"managerole": managerole.id}}, upsert=True
        )
        await interaction.send(
            embed=nextcord.Embed(
                title="完了",
                description=f"ユーザー上限コマンドを実行できるロールを{managerole.mention}に設定しました。",
                color=self.bot.color.NORMAL,
            ),
            ephemeral=True,
        )

    @application_checks.guild_only()
    @vclimit_slash.subcommand(
        name="change",
        description="Changes the user limit of the voice channel.",
        description_localizations={
            nextcord.Locale.ja: "ボイスチャンネルのユーザー上限を変更します。",
        },
    )
    async def vclimit_change_slash(
        self,
        interaction: nextcord.Interaction,
        userlimit: int = nextcord.SlashOption(
            name="userlimit",
            description="The user limit of the voice channel.",
            description_localizations={
                nextcord.Locale.ja: "ボイスチャンネルのユーザー上限。",
            },
            default=0,
            required=False,
        ),
    ):
        assert isinstance(interaction.user, nextcord.Member)
        assert isinstance(interaction.guild, nextcord.Guild)
        # チャンネルがvclimit_channel_collectionで設定されているか確認
        if interaction.user.voice is None:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="このコマンドを実行するには、ボイスチャンネルに入室している必要があります。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        vc_channel = interaction.user.voice.channel
        assert isinstance(vc_channel, nextcord.VoiceChannel)
        vc_grants = await self.vclimit_channel_collection.find_one({"guild_id": interaction.guild.id})
        if vc_grants is None:
            vc_grants = {}
            asyncio.ensure_future(self.vclimit_channel_collection.update_one({"guild_id": interaction.guild.id}, {"$set": vc_grants}, upsert=True))
        if str(vc_channel.id) not in vc_grants:
            roledata = await self.vclimit_collection.find_one({"_id": interaction.guild.id})
            if roledata is None:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description="ユーザー上限コマンドを実行できるロールが設定されていません。\n事前に管理者が`/vclimit manage`コマンドでロールを設定してください。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
            manage_role = interaction.guild.get_role(roledata["managerole"])
            if manage_role is None:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description="ユーザー上限コマンドを実行できるロールが設定されていません。\n事前に管理者が`/vclimit manage`コマンドでロールを設定してください。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
            if manage_role not in interaction.user.roles:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"このコマンドを実行する権限がありません。\nこのコマンドを実行するには、ユーザー上限コマンドを実行できるロールとして「{manage_role.name}」が必要です。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
        elif not vc_grants[str(vc_channel.id)]:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="このコマンドを実行する権限がありません。\nこのチャンネルでの人数上限の変更が許可されているかご確認ください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        if userlimit < 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="ユーザー上限は0以上の整数で指定してください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        try:
            await vc_channel.edit(user_limit=userlimit)
        except nextcord.Forbidden:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="BOTが人数制限を変更する権限を持っていませんでした。\nBOTに適切な権限を付与してから再度試してください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        if userlimit == 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="完了",
                    description="ボイスチャンネルのユーザー上限を解除しました。",
                    color=self.bot.color.NORMAL,
                )
            )
        else:
            await interaction.send(
                embed=nextcord.Embed(
                    title="完了",
                    description=f"ボイスチャンネルのユーザー上限を{userlimit}人に設定しました。",
                    color=self.bot.color.NORMAL,
                )
            )

    @commands.command(name="vclimit", aliases=["vl", "人数制限"], help="""\
VCの人数制限を変更します。

引数には変更後の人数を指定してください。
0を指定するか指定しないと人数制限を解除します。

変更には、このコマンドを実行できるロールが必要です。
このコマンドを実行できるロールは、`/vclimit manage`コマンドで設定できます。

エイリアス: `vl`、`人数制限`""")
    async def vclimit_change(self, ctx: commands.Context, userlimit: int = 0):
        assert isinstance(ctx.author, nextcord.Member)
        assert isinstance(ctx.guild, nextcord.Guild)
        # チャンネルがvclimit_channel_collectionで設定されているか確認
        if ctx.author.voice is None:
            await ctx.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="このコマンドを実行するには、ボイスチャンネルに入室している必要があります。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        vc_channel = ctx.author.voice.channel
        assert isinstance(vc_channel, nextcord.VoiceChannel)
        vc_grants = await self.vclimit_channel_collection.find_one({"guild_id": ctx.guild.id})
        if vc_grants is None:
            vc_grants = {}
            asyncio.ensure_future(self.vclimit_channel_collection.update_one({"guild_id": ctx.guild.id}, {"$set": vc_grants}, upsert=True))
        if str(vc_channel.id) not in vc_grants:
            roledata = await self.vclimit_collection.find_one({"_id": ctx.guild.id})
            if roledata is None:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description="ユーザー上限コマンドを実行できるロールが設定されていません。\n事前に管理者が`/vclimit manage`コマンドでロールを設定してください。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
            manage_role = ctx.guild.get_role(roledata["managerole"])
            if manage_role is None:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description="ユーザー上限コマンドを実行できるロールが設定されていません。\n事前に管理者が`/vclimit manage`コマンドでロールを設定してください。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
            if manage_role not in ctx.author.roles:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"このコマンドを実行する権限がありません。\nこのコマンドを実行するには、ユーザー上限コマンドを実行できるロールとして「{manage_role.name}」が必要です。",
                        color=self.bot.color.ERROR,
                    )
                )
                return
        elif not vc_grants[str(vc_channel.id)]:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー",
                    description="このコマンドを実行する権限がありません。\nこのチャンネルでの人数上限の変更が許可されているかご確認ください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        if userlimit < 0:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー",
                    description="ユーザー上限は0以上の整数で指定してください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        try:
            await vc_channel.edit(user_limit=userlimit)
        except nextcord.Forbidden:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー",
                    description="BOTが人数制限を変更する権限を持っていませんでした。\nBOTに適切な権限を付与してから再度試してください。",
                    color=self.bot.color.ERROR,
                )
            )
            return
        if userlimit == 0:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="完了",
                    description="ボイスチャンネルのユーザー上限を解除しました。",
                    color=self.bot.color.NORMAL,
                )
            )
        else:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="完了",
                    description=f"ボイスチャンネルのユーザー上限を{userlimit}人に設定しました。",
                    color=self.bot.color.NORMAL,
                )
            )


def setup(bot: NIRA):
    bot.add_cog(ChannelUtil(bot))
