import datetime
import logging
import uuid
from typing import TypedDict

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, tasks

from util.nira import NIRA

_logger = logging.getLogger(__name__)


class ModConfig(TypedDict):
    "MessageModerationの設定"

    counter: int
    "規定メッセージ数"

    exempted_role: int | None
    "免除されるロールID"


class ModConfigDB(ModConfig):
    "MessageModerationの設定(DB用)"

    guild_id: int
    "サーバーID"


# 規定秒数以内に指定数メッセージを送信した人をミュートするモデレーター的な機能
# n!mod
# /mod
class MessageModeration(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection[ModConfigDB] = (
            self.bot.database["message_mod"]
        )

        self.MOD_LIST: dict[int, ModConfig] = {}
        self.message_counter: dict[int, int] = {}

        self.counter_reset.start()
        self.bot.schedule_task(self.load_config())

    async def load_config(self):
        """Load configs from database"""
        data = await self.collection.find().to_list(length=None)
        for i in data:
            self.MOD_LIST[i["guild_id"]] = i

    def cog_unload(self):
        self.counter_reset.stop()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        if not message.guild or message.guild.id not in self.MOD_LIST:
            return

        if message.author.id not in self.messageCounter:
            self.messageCounter[message.author.id] = 0

        self.messageCounter[message.author.id] = (
            self.messageCounter[message.author.id] + 1
        )

        if (
            self.messageCounter[message.author.id]
            > int(self.MOD_LIST[message.guild.id]["counter"] * 0.8)
            and self.messageCounter[message.author.id]
            < self.MOD_LIST[message.guild.id]["counter"]
        ):
            await message.channel.send(
                f"{message.author.mention}\n一度に送信しているメッセージ数が多いです。あまり多いとタイムアウトされます。"
            )
            return

        if (
            self.messageCounter[message.author.id]
            >= self.MOD_LIST[message.guild.id]["counter"]
        ):
            try:
                assert isinstance(message.guild, nextcord.Guild)
                assert isinstance(message.author, nextcord.Member)

                await message.author.timeout(
                    timeout=datetime.timedelta(minutes=1),
                    reason="にらBOTの荒らし対策機能",
                )

                await message.channel.send(
                    f"{message.author.mention}は、メッセージ数が規定オーバーになったため60秒間タイムアウトされました。"
                )
            except Exception as _:
                contact_id = uuid.uuid4()
                _logger.exception(f"An error has occurred! Contact ID: {contact_id}")
                await message.channel.send(
                    f"{message.author.name}をミュートしようとしましたがエラーが発生しました。\n\n・問い合わせ用ID (問い合わせの際はこのスクリーンショット又は以下のIDをご提示ください)\n```\n{contact_id}```"
                )

    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.command(
        name="mod",
        help="""\
一定期間以内に特定のメッセージ数以上のメッセージを送った人をDiscordのMOD機能のタイムアウトを行います。
20秒間に指定された回数以上しゃべった人に対して処理が行われます。

なお、サーバーにつき1つの設定しかできません。

`n!mod on [counter] [*exempted_role]
`n!mod off`

counter: 規定するメッセージの送信数
exempted_role: 免除されるロールのIDまたは名前

・例
`n!mod on 10 管理者ロール`
`n!mod on 5 1007301686022381609`
`n!mod off`
""",
    )
    async def mod(
        self,
        ctx: commands.Context,
        flag: bool | None = None,
        counter: int | None = None,
        exempted_role: str | None = None,
        *args,
    ):
        assert isinstance(ctx.guild, nextcord.Guild)
        assert isinstance(ctx.author, nextcord.Member)

        if not ctx.guild.me.guild_permissions.moderate_members:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="Botにユーザーをタイムアウトする権限がありません。\nロールなどで「メンバーをタイムアウト」という権限を付与してください。",
                    color=0xFF0000,
                )
            )
            return

        if ctx.author.guild_permissions.moderate_members is False:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="あなたはユーザーをタイムアウトする権限がありません。\n安全上、すでにメンバーをタイムアウトすることができるユーザーのみがこのコマンドを使用できます。",
                    color=0xFF0000,
                )
            )
            return

        if flag is None:
            if ctx.guild.id not in self.MOD_LIST:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description=f"サーバーで機能は`無効`になっています。\n\n・機能の有効化\n`{ctx.prefix}mod on [規定メッセージ数] [免除されるロールの名前かID]`\n\n・機能の無効化\n`{ctx.prefix}mod off`",
                        color=0x00FF00,
                    )
                )
            else:
                counter = self.MOD_LIST[ctx.guild.id]["counter"]
                role_id = self.MOD_LIST[ctx.guild.id]["exempted_role"]
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description=(
                            f"サーバーで機能は`有効`になっています。\n"
                            f"20秒間に`{counter}`回メッセージを送ったユーザーはタイムアウトされます。\n"
                            "免除されるロール: "
                            f"<@&{role_id}>"
                            if role_id is not None
                            else "なし"
                            "\n\n・機能の有効化\n"
                            f"`{ctx.prefix}mod on [規定メッセージ数] [免除されるロールの名前かID]`\n\n・機能の無効化\n`{ctx.prefix}mod off`"
                        ),
                        color=0x00FF00,
                    )
                )

        elif flag is False:
            result = await self.collection.delete_one({"guild_id": ctx.guild.id})
            del self.MOD_LIST[ctx.guild.id]
            if result.deleted_count == 0:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description=f"設定はすでに無効化されています。",
                        color=0x00FF00,
                    ),
                )
                return
            else:
                await ctx.reply(
                    "設定完了",
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description=f"設定を無効化しました。",
                        color=0x00FF00,
                    ),
                )

        elif flag and counter is None:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description=f"引数が正しくありません。\n`{ctx.prefix}mod on [規定メッセージ数] [免除されるロールの名前かID]`\n`{ctx.prefix}mod off`\n`{ctx.prefix}help mod`",
                    color=0xFF0000,
                )
            )

        elif flag and counter is not None:
            role_id: int | None = None

            if exempted_role is not None:
                try:
                    role_id = int(exempted_role)
                except ValueError:
                    roles = ctx.guild.roles
                    for i in range(len(roles)):
                        if roles[i].name == exempted_role:
                            role_id = roles[i].id
                            break
                    if role_id == None:
                        await ctx.reply(
                            f"指定されたロール `{exempted_role}` が見つかりませんでした。"
                        )
                        return

            if role_id == ctx.guild.id:
                await ctx.reply(
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description="@everyoneは指定できません。",
                        color=0xFF0000,
                    )
                )
                return

            self.MOD_LIST[ctx.guild.id] = {
                "counter": counter,
                "exempted_role": role_id,
            }

            await self.collection.update_one(
                {"guild_id": ctx.guild.id},
                {"$set": self.MOD_LIST[ctx.guild.id]},
                upsert=True,
            )

            await ctx.reply(
                "設定完了",
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description=(
                        f"メッセージカウンター:`{counter}`\n免除されるロール: "
                        f"<@&{role_id}>"
                        if role_id is not None
                        else "なし"
                    ),
                    color=0x00FF00,
                ),
            )

    @nextcord.slash_command(
        name="mod", description="荒らし対策機能の設定を変更します。"
    )
    async def mod_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(moderate_members=True)
    @mod_slash.subcommand(name="on", description="荒らし対策機能を有効にします。")
    async def on_slash(
        self,
        interaction: Interaction,
        counter: int = SlashOption(
            name="counter", description="規定するメッセージ送信数", required=True
        ),
        exempted_role: nextcord.Role | None = SlashOption(
            name="exempted_role", description="免除されるロール", required=False
        ),
    ):
        assert isinstance(interaction.guild, nextcord.Guild)

        if exempted_role and exempted_role.id == interaction.guild.id:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="@everyoneは指定できません。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        try:
            self.MOD_LIST[interaction.guild.id] = {
                "counter": counter,
                "exempted_role": exempted_role.id if exempted_role else None,
            }
            await self.collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": self.MOD_LIST[interaction.guild.id]},
                upsert=True,
            )
        except Exception as _:
            contact_id = uuid.uuid4()
            _logger.exception(f"An error has occurred! Contact ID: {contact_id}")
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description=f"エラーが発生しました。\n\n・問い合わせ用ID (問い合わせの際はこのスクリーンショット又は以下のIDをご提示ください)\n```\n{contact_id}```",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="荒らし対策",
                description=(
                    f"メッセージカウンター:`{counter}`\n免除されるロール: "
                    f"<@&{exempted_role.id}>"
                    if exempted_role
                    else "なし"
                ),
                color=0x00FF00,
            ),
            ephemeral=True,
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(moderate_members=True)
    @mod_slash.subcommand(name="off", description="荒らし対策機能を無効にします。")
    async def off_slash(self, interaction: Interaction):
        assert isinstance(interaction.guild, nextcord.Guild)

        if interaction.guild.id not in self.MOD_LIST:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="サーバーで機能は既に`無効`になっています。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
        else:
            try:
                del self.MOD_LIST[interaction.guild.id]
                await self.collection.delete_one({"guild_id": interaction.guild.id})
            except Exception as _:
                contact_id = uuid.uuid4()
                _logger.exception(f"An error has occurred! Contact ID: {contact_id}")
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="荒らし対策",
                        description=f"エラーが発生しました。\n\n・問い合わせ用ID (問い合わせの際はこのスクリーンショット又は以下のIDをご提示ください)\n```\n{contact_id}```",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="サーバーで機能を無効にしました。\n（既に無効になっている状態からこのコマンドを実行してもこの表示になります。）",
                    color=0x00FF00,
                ),
                ephemeral=True,
            )

    @application_checks.guild_only()
    @application_checks.has_permissions(moderate_members=True)
    @mod_slash.subcommand(
        name="status", description="荒らし対策機能の状態を確認します。"
    )
    async def status_slash(self, interaction: Interaction):
        assert isinstance(interaction.guild, nextcord.Guild)

        if interaction.guild.id not in self.MOD_LIST:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="サーバーで機能は`無効`になっています。",
                    color=0x00FF00,
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description=(
                        f"サーバーで機能は`有効`になっています。\n"
                        f"20秒間に`{self.MOD_LIST[interaction.guild.id]['counter']}`回メッセージを送ったユーザーはタイムアウトされます。\n"
                        "免除されるロール: "
                        f"<@&{self.MOD_LIST[interaction.guild.id]['exempted_role']}>"
                        if self.MOD_LIST[interaction.guild.id]["exempted_role"]
                        is not None
                        else "なし"
                    ),
                    color=0x00FF00,
                ),
                ephemeral=True,
            )

    @tasks.loop(seconds=20.0)
    async def counter_reset(self):
        self.messageCounter = {}


def setup(bot: NIRA):
    bot.add_cog(MessageModeration(bot))
