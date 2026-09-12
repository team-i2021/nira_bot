import datetime
import logging
import uuid
from typing import Any, TypedDict, override

import nextcord
from motor import motor_asyncio
from nextcord import Interaction
from nextcord.ext import application_checks, commands, tasks
from nextcord.types import interactions

from util.nira import NIRA

_logger = logging.getLogger(__name__)


class ModConfig(TypedDict):
    "MessageModerationの設定"

    counter: int
    "規定メッセージ数"

    exempted_roles: list[int]
    "免除されるロールID"

    timeout: int
    "タイムアウトする時間"


class ModConfigDB(ModConfig):
    "MessageModerationの設定(DB用)"

    guild_id: int
    "サーバーID"


class ModSettingModal(nextcord.ui.Modal):
    def __init__(self, cog: "MessageModeration"):
        super().__init__(
            "モデレーション設定",
            timeout=None,
        )

        self.message_counter = nextcord.components.TextInput(
            label="タイムアウトにする基準のメッセージ数 (20秒間の間の送信数)",
            style=nextcord.TextInputStyle.short,
            placeholder="15",
            min_length=1,
            max_length=5,
            required=True,
        )
        self.exempted_roles = nextcord.components.RoleSelect(
            min_values=0, max_values=25
        )
        self.timeout_timer = nextcord.components.TextInput(
            label="ユーザーをタイムアウトする時間 (単位: 時間) (最大で 672 まで指定可能)",
            style=nextcord.TextInputStyle.short,
            placeholder="1",
            min_length=1,
            max_length=3,
            required=True,
        )

        self.cog: "MessageModeration" = cog

    @override
    def to_dict(self) -> dict[str, Any]:
        d = {
            "title": self.title,
            "custom_id": self.custom_id,
            "components": [
                nextcord.components.Label(
                    label=self.message_counter.label,
                    component=self.message_counter,
                ).to_dict(),
                nextcord.components.Label(
                    label="このタイムアウトの制限を受けない除外ロール",
                    component=self.exempted_roles,
                ).to_dict(),
                nextcord.components.Label(
                    label=self.timeout_timer.label,
                    component=self.timeout_timer,
                ).to_dict(),
            ],
        }
        try:  # 現状のDiscord側が要求しているコンポーネント型と、nextcordの現状の実装は少し異なるため修正
            del d["components"][0]["component"]["label"]
            d["components"][1]["component"]["required"] = False
            del d["components"][2]["component"]["label"]
        except (KeyError, IndexError, TypeError):
            pass
        return d

    def get_component(
        self, data: interactions.InteractionData, custom_id: str
    ) -> interactions.ComponentInteractionData | None:
        """インタラクションのレスポンスデータから、`custom_id`を使ってコンポーネントのデータを引きます。

        Returns
        -------
        Optional[interactions.ComponentInteractionData]
            コンポーネントの返答データ。

            指定された`custom_id`のコンポーネントが返答データに見つからなかった場合には None になります。
        """
        return next(
            (
                c
                for c in data.get("components", [])
                if c.get("component", {}).get("custom_id") == custom_id
            ),
            {},
        ).get("component", None)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert isinstance(interaction.guild, nextcord.Guild)
        assert interaction.data

        counter_component = self.get_component(
            interaction.data, self.message_counter.custom_id
        )
        role_component = self.get_component(
            interaction.data, self.exempted_roles.custom_id
        )
        timeout_component = self.get_component(
            interaction.data, self.timeout_timer.custom_id
        )

        assert counter_component and role_component and timeout_component

        try:
            counter = int(
                counter_component.get("value", "None")
            )  # `str | None`なので、直で`int`キャストするには`None`を除外しなければいけない。

            if counter <= 0:
                raise ValueError("自然数 (0より大きい値) を指定してください。")
        except (TypeError, ValueError):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="エラーが発生しました。\n「タイムアウトにする基準のメッセージ数 (20秒間の間の送信数)」には有効な正の整数を入れてください。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return

        try:
            timeout_duration = int(timeout_component.get("value", "None"))

            if timeout_duration <= 0:
                raise ValueError("自然数 (0より大きい値) を指定してください。")
            elif timeout_duration > 672:
                raise ValueError("672 (28日間) までの値を指定してください。")
        except (TypeError, ValueError):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description="エラーが発生しました。\n「ユーザーをタイムアウトする時間 (単位: 時間)」には有効な672までの正の整数を入れてください。",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return

        role_ids = [int(i) for i in role_component.get("values", [])]

        try:
            await self.cog.collection.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$set": {
                        "counter": counter,
                        "exempted_roles": role_ids,
                        "timeout": timeout_duration,
                    }
                },
                upsert=True,
            )
            await self.cog.load_config()
        except Exception as _:
            contact_id = uuid.uuid4()
            _logger.exception(f"An error has occurred! Contact ID: {contact_id}")
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="荒らし対策",
                    description=f"エラーが発生しました。\n\n・問い合わせ用ID (問い合わせの際はこのスクリーンショット又は以下のIDをご提示ください)\n```\n{contact_id}```",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            embed=nextcord.Embed(
                title="荒らし対策",
                description=(
                    f"20秒間に`{counter}`回メッセージを送ったユーザーは{timeout_duration}時間の間タイムアウトされます。\n"
                    "免除されるロール: "
                    + (
                        ", ".join([f"<@&{r}>" for r in role_ids])
                        if len(role_ids) > 0
                        else "なし"
                    )
                ),
                color=0x00FF00,
            ),
            ephemeral=True,
        )


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

        if len(self.MOD_LIST[message.guild.id]["exempted_roles"]) > 0:
            if isinstance(message.author, nextcord.Member) and bool(
                set([r.id for r in message.author.roles])
                & set(self.MOD_LIST[message.guild.id]["exempted_roles"])
            ):
                return

        if message.author.id not in self.messageCounter:
            self.messageCounter[message.author.id] = 0

        self.messageCounter[message.author.id] = (
            self.messageCounter[message.author.id] + 1
        )

        if (
            self.messageCounter[message.author.id]
            >= int(self.MOD_LIST[message.guild.id]["counter"] * 0.8)
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
                    timeout=datetime.timedelta(
                        hours=self.MOD_LIST[message.guild.id]["timeout"]
                    ),
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

    @nextcord.slash_command(
        name="mod", description="荒らし対策機能の設定を変更します。"
    )
    async def mod_slash(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(moderate_members=True)
    @mod_slash.subcommand(name="on", description="荒らし対策機能を有効にします。")
    async def on_slash(self, interaction: Interaction):
        assert isinstance(interaction.guild, nextcord.Guild)
        await interaction.response.send_modal(ModSettingModal(self))

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
                        f"20秒間に`{self.MOD_LIST[interaction.guild.id]['counter']}`回メッセージを送ったユーザーは{self.MOD_LIST[interaction.guild.id]['timeout']}時間の間タイムアウトされます。\n"
                        "免除されるロール: "
                        + (
                            ", ".join(
                                [
                                    f"<@&{r}>"
                                    for r in self.MOD_LIST[interaction.guild.id][
                                        "exempted_roles"
                                    ]
                                ]
                            )
                            if len(
                                self.MOD_LIST[interaction.guild.id]["exempted_roles"]
                            )
                            > 0
                            else "なし"
                        )
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
