import asyncio
import logging
from collections.abc import Sequence
from typing import TypeVar

import nextcord
from motor import motor_asyncio
from nextcord.ext import application_checks, commands

from util import modal
from util.nira import NIRA

GuildChannelT_co = TypeVar(
    "GuildChannelT_co", bound=nextcord.abc.GuildChannel, covariant=True
)

_logger = logging.getLogger(__name__)


class VCLimitManageModal(modal.Modal):
    def __init__(
        self,
        cog: "ChannelUtil",
        *,
        default_roles: Sequence[nextcord.Role | int] | None = None,
        has_deleted_roles: bool = False,
    ) -> None:
        super().__init__("ユーザー上限コマンドの設定", timeout=None)

        self.cog = cog

        self.roles = modal.ModalLabel(
            text="コマンドを実行できるロール (25個まで)",
            description=(
                "利用できなくなった一部のロールは一覧から削除されています。"
                if has_deleted_roles
                else None
            ),
            component=modal.ModalRoleSelect(
                placeholder="ロールを選択してください",
                default_values=default_roles,
                max_values=25,
                required=True,
            ),
        )

        self.add_item(self.roles)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        assert isinstance(interaction.guild, nextcord.Guild)

        await interaction.response.defer(ephemeral=True)

        try:
            await self.cog.vclimit_collection.update_one(
                {"_id": interaction.guild.id},
                {
                    "$set": {
                        "managerole": [r.id for r in self.roles.component.values.roles]
                    }
                },
                upsert=True,
            )

            roles = self.roles.component.values.roles
            roles_desc = "、".join(r.mention for r in roles[:-1])
            roles_desc = f"{roles_desc and f'{roles_desc}および'}{roles[-1].mention}"

            await interaction.send(
                embed=nextcord.Embed(
                    title="完了",
                    description=f"ユーザー上限コマンドを実行できるロールを{roles_desc}に設定しました。",
                    color=self.cog.bot.color.NORMAL,
                ),
                ephemeral=True,
            )

        except Exception:
            _logger.exception("An error has occurred when setting vclimit manage roles")
            await interaction.send(
                f"申し訳ございません。エラーが発生しました。\n```\n{self.cog.bot.format_exc()}```",
                ephemeral=True,
            )


class ChannelUtil(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.vclimit_collection: motor_asyncio.AsyncIOMotorCollection = (
            self.bot.database["vclimit_role"]
        )
        self.vclimit_channel_collection: motor_asyncio.AsyncIOMotorCollection = (
            self.bot.database["vclimit_channel"]
        )

    def which_channel(
        self, a: nextcord.abc.GuildChannel, b: nextcord.abc.GuildChannel
    ) -> nextcord.abc.GuildChannel:
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
        category: nextcord.CategoryChannel | None = nextcord.SlashOption(
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
            c
            for c in sorted_channels
            if isinstance(c, nextcord.TextChannel)
            or isinstance(c, nextcord.ForumChannel)
        ]
        voice_channels = [
            c
            for c in sorted_channels
            if isinstance(c, nextcord.VoiceChannel)
            or isinstance(c, nextcord.StageChannel)
        ]

        for pos in range(len(text_channels)):
            if text_channels[pos].position == pos:
                continue
            await text_channels[pos].move(beginning=True, offset=pos, category=category)
            await asyncio.sleep(1)

        for pos in range(len(voice_channels)):
            if voice_channels[pos].position == pos:
                continue
            await voice_channels[pos].move(
                beginning=True, offset=pos, category=category
            )
            await asyncio.sleep(1)

        await interaction.send(
            embed=nextcord.Embed(
                title="完了",
                description="チャンネルの並べ替えが完了しました。",
                color=self.bot.color.NORMAL,
            )
        )

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
            await self.vclimit_channel_collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {str(channel.id): True}},
                upsert=True,
            )
        else:
            await self.vclimit_channel_collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$unset": {str(channel.id): True}},
                upsert=True,
            )
        await interaction.send(
            embed=nextcord.Embed(
                title="完了",
                description=(
                    f"{channel.mention}で、ロールが付与されていないユーザーによる、"
                    f"ユーザー上限コマンドの実行が{'出来るように' if grant else '出来なく'}なりました。"
                ),
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
    async def vclimit_manage_slash(self, interaction: nextcord.Interaction):
        assert isinstance(interaction.guild, nextcord.Guild)

        roledata = await self.vclimit_collection.find_one({"_id": interaction.guild.id})
        roles = []
        has_deleted_roles = False
        if roledata and (role_ids := roledata["managerole"]):
            if not isinstance(role_ids, list):  # 旧フォーマット (単一ロール設定)
                role_ids = (role_ids,)

            for role_id in role_ids:
                if role := interaction.guild.get_role(role_id):
                    # 旧スラッシュコマンドでは@everyoneを選択することができた
                    # モーダルのRole Selectでは選択できないため除外しておく
                    if role.name != "@everyone":
                        roles.append(role)
                else:
                    has_deleted_roles = True

        await interaction.response.send_modal(
            VCLimitManageModal(
                self,
                default_roles=roles or None,
                has_deleted_roles=has_deleted_roles,
            )
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
                ),
                ephemeral=True,
            )
            return
        vc_channel = interaction.user.voice.channel
        assert isinstance(vc_channel, nextcord.VoiceChannel)
        vc_grants = await self.vclimit_channel_collection.find_one(
            {"guild_id": interaction.guild.id},
        )
        if vc_grants is None:
            vc_grants = {}
            await self.vclimit_channel_collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": vc_grants},
                upsert=True,
            )
        if str(vc_channel.id) not in vc_grants:
            roledata = await self.vclimit_collection.find_one(
                {"_id": interaction.guild.id},
            )
            if roledata is None:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "ユーザー上限コマンドを実行できるロールが設定されていません。\n"
                            "事前に管理者が`/vclimit manage`コマンドでロールを設定してください。"
                        ),
                        color=self.bot.color.ERROR,
                    ),
                    ephemeral=True,
                )
                return
            roledata = roledata["managerole"]
            manage_roles = [
                role
                for role_id in (roledata if isinstance(roledata, list) else (roledata,))
                if (role := interaction.guild.get_role(role_id))
            ]
            if not manage_roles:
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "ユーザー上限コマンドを実行できるロールが設定されていません。\n"
                            "事前に管理者が`/vclimit manage`コマンドでロールを設定してください。"
                        ),
                        color=self.bot.color.ERROR,
                    ),
                    ephemeral=True,
                )
                return
            if not (set(interaction.user.roles) & set(manage_roles)):
                roles_desc = "、".join(r.mention for r in manage_roles[:-1])
                roles_desc = (
                    f"{roles_desc and f'{roles_desc}または'}{manage_roles[-1].mention}"
                )
                await interaction.send(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "このコマンドを実行する権限がありません。\n"
                            f"このコマンドを実行するには、ユーザー上限コマンドを実行できるロールとして{roles_desc}が必要です。"
                        ),
                        color=self.bot.color.ERROR,
                    ),
                    allowed_mentions=nextcord.AllowedMentions.none(),
                    ephemeral=True,
                )
                return
        elif not vc_grants[str(vc_channel.id)]:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description=(
                        "このコマンドを実行する権限がありません。\n"
                        "このチャンネルでの人数上限の変更が許可されているかご確認ください。"
                    ),
                    color=self.bot.color.ERROR,
                ),
                ephemeral=True,
            )
            return
        if userlimit < 0:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="ユーザー上限は0以上の整数で指定してください。",
                    color=self.bot.color.ERROR,
                ),
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        try:
            await vc_channel.edit(user_limit=userlimit)
        except nextcord.Forbidden:
            await interaction.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description=(
                        "BOTが人数制限を変更する権限を持っていませんでした。\n"
                        "BOTに適切な権限を付与してから再度試してください。"
                    ),
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

    @commands.command(
        name="vclimit",
        aliases=["vl", "人数制限"],
        help="""\
VCの人数制限を変更します。

引数には変更後の人数を指定してください。
0を指定するか指定しないと人数制限を解除します。

変更には、このコマンドを実行できるロールが必要です。
このコマンドを実行できるロールは、`/vclimit manage`コマンドで設定できます。

エイリアス: `vl`、`人数制限`""",
    )
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
        vc_grants = await self.vclimit_channel_collection.find_one(
            {"guild_id": ctx.guild.id}
        )
        if vc_grants is None:
            vc_grants = {}
            await self.vclimit_channel_collection.update_one(
                {"guild_id": ctx.guild.id}, {"$set": vc_grants}, upsert=True
            )
        if str(vc_channel.id) not in vc_grants:
            roledata = await self.vclimit_collection.find_one({"_id": ctx.guild.id})
            if roledata is None:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "ユーザー上限コマンドを実行できるロールが設定されていません。\n"
                            "事前に管理者が`/vclimit manage`コマンドでロールを設定してください。"
                        ),
                        color=self.bot.color.ERROR,
                    )
                )
                return
            roledata = roledata["managerole"]
            manage_roles = [
                role
                for role_id in (roledata if isinstance(roledata, list) else (roledata,))
                if (role := ctx.guild.get_role(role_id))
            ]
            if not manage_roles:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "ユーザー上限コマンドを実行できるロールが設定されていません。\n"
                            "事前に管理者が`/vclimit manage`コマンドでロールを設定してください。"
                        ),
                        color=self.bot.color.ERROR,
                    )
                )
                return
            if not (set(ctx.author.roles) & set(manage_roles)):
                roles_desc = "、".join(r.mention for r in manage_roles[:-1])
                roles_desc = (
                    f"{roles_desc and f'{roles_desc}または'}{manage_roles[-1].mention}"
                )
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=(
                            "このコマンドを実行する権限がありません。\n"
                            f"このコマンドを実行するには、ユーザー上限コマンドを実行できるロールとして{roles_desc}が必要です。"
                        ),
                        color=self.bot.color.ERROR,
                    ),
                    allowed_mentions=nextcord.AllowedMentions.none(),
                )
                return
        elif not vc_grants[str(vc_channel.id)]:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー",
                    description=(
                        "このコマンドを実行する権限がありません。\n"
                        "このチャンネルでの人数上限の変更が許可されているかご確認ください。"
                    ),
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
                    description=(
                        "BOTが人数制限を変更する権限を持っていませんでした。\n"
                        "BOTに適切な権限を付与してから再度試してください。"
                    ),
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
