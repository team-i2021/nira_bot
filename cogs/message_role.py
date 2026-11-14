import re
import sys

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands

from util import admin_check
from util.nira import NIRA

ROLE_ID = re.compile(r"<@&[\d]+?>")

# 特定のチャンネルにて特定のメッセージが送信された場合にロールをつけるそれ。
# データ形式:MongoDB

SYSDIR = sys.path[0]


class MessageRole(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "message_role"
        ]

    @nextcord.slash_command(name="mesrole", description="Message role command")
    async def slash_message_role(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="set", description="チャンネルのメッセージロールの設定をします"
    )
    async def slash_message_role_set(
        self,
        interaction: Interaction,
        regex: str = SlashOption(
            required=True,
            description="判定するメッセージです。正規表現型で書き込めます。",
        ),
        action_type: int = SlashOption(
            required=True,
            description="ロールを付与するか剥奪するか",
            choices={"付与": 1, "剥奪": 0},
        ),
        role: nextcord.Role = SlashOption(
            required=True, description="付与/剥奪するロール"
        ),
    ):
        assert interaction.guild and interaction.channel

        action_type = (lambda x: True if x else False)(action_type)
        await interaction.response.defer(ephemeral=True)

        data = {"regex": regex, "role_id": role.id, "action_type": action_type}
        await self.collection.update_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id},
            {"$set": data},
            upsert=True,
        )

        await interaction.followup.send(
            embed=nextcord.Embed(
                title="メッセージロールの設定",
                description=(
                    f"チャンネル:<#{interaction.channel.id}>\n"
                    f"判定メッセージ:`{regex}`\n"
                    f"ロール:<@&{role.id}>を{(lambda x: '付与' if x else '剥奪')(action_type)}します。"
                ),
                color=0x00FF00,
            )
        )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="del", description="チャンネルのメッセージロールの設定を削除します"
    )
    async def slash_message_role_del(self, interaction: Interaction):
        assert (
            interaction.guild
            and interaction.channel
            and isinstance(interaction.user, nextcord.Member)
        )

        await interaction.response.defer(ephemeral=True)

        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description="あなたは管理者ではありません。",
                    color=0xFF0000,
                )
            )
            return

        result = await self.collection.delete_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id}
        )

        if result.deleted_count == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description="このサーバーにはメッセージロールの設定がありません。",
                    color=0xFF0000,
                )
            )
        else:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description=(
                        f"チャンネル:<#{interaction.channel.id}>\n"
                        "メッセージロールの設定を削除しました。"
                    ),
                    color=0x00FF00,
                )
            )

    @application_checks.has_permissions(manage_roles=True)
    @application_checks.guild_only()
    @slash_message_role.subcommand(
        name="list", description="メッセージロールの設定を表示します"
    )
    async def slash_message_role_list(self, interaction: Interaction):
        assert (
            interaction.guild
            and interaction.channel
            and isinstance(interaction.user, nextcord.Member)
        )

        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Error",
                    description="あなたは管理者ではありません。",
                    color=0xFF0000,
                )
            )
            return

        mesroledatas = await self.collection.find(
            {"guild_id": interaction.guild.id}
        ).to_list(length=None)

        if len(mesroledatas) == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="メッセージロールの設定",
                    description="このサーバーにはメッセージロールの設定がありません。",
                    color=0x00FF00,
                )
            )
        else:
            embed = nextcord.Embed(
                title="メッセージロールの設定",
                description=interaction.guild.name,
                color=0x00FF00,
            )
            for mesroledata in mesroledatas:
                channel = await self.bot.fetch_channel(mesroledata["channel_id"])
                assert isinstance(channel, nextcord.abc.GuildChannel | nextcord.Thread)
                embed.add_field(
                    name=channel.name,
                    value=(
                        f"判定メッセージ:`{mesroledata['regex']}`\n"
                        f"ロール:<@&{mesroledata['role_id']}>\n"
                        f"ロール{'付与' if mesroledata['action_type'] else '剥奪'}をします。"
                    ),
                    inline=False,
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not isinstance(message.channel, nextcord.abc.GuildChannel | nextcord.Thread):
            return
        if message.author.bot:
            return
        assert message.guild and isinstance(message.author, nextcord.Member)

        result = await self.collection.find_one(
            {"guild_id": message.guild.id, "channel_id": message.channel.id}
        )
        if result is None:
            return
        if re.search(result["regex"], message.content) is not None:
            if result["action_type"]:
                await message.author.add_roles(
                    message.guild.get_role(result["role_id"]),
                    reason="nira-bot MessageRole Service",
                )
            else:
                await message.author.remove_roles(
                    message.guild.get_role(result["role_id"]),
                    reason="nira-bot MessageRole Service",
                )
            await message.add_reaction("\u2705")


def setup(bot):
    bot.add_cog(MessageRole(bot))
