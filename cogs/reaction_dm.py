import asyncio
from typing import TypedDict

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, tasks

from util.nira import NIRA

# 特定のチャンネルにて特定のリアクションを付けたら、つけられた人にDMを送信する。


class ReactionDMData(TypedDict):
    emoji: str
    target_role: int | None
    dm_message: str
    fallback_channel: int | None


class ReactionDM(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "reaction_dm"
        ]
        self.reaction_dm_cache: dict[int, ReactionDMData] = {}
        self.load_reaction_dm_settings.start()

    @tasks.loop(hours=1.0)
    async def load_reaction_dm_settings(self):
        """
        ReactionDMの設定を、データベースからローカルへロードします。
        """
        self.reaction_dm_cache = {}
        async for reaction_dm in self.collection.find():
            self.reaction_dm_cache[int(reaction_dm["channel_id"])] = {
                "emoji": reaction_dm["emoji"],
                "target_role": reaction_dm.get("target_role"),
                "dm_message": reaction_dm["dm_message"],
                "fallback_channel": reaction_dm.get("fallback_channel"),
            }

    @nextcord.slash_command(name="reactdm", description="Reaction DM command")
    async def slash_reaction_dm(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_dm.subcommand(
        name="set", description="チャンネルのリアクションDMの設定をします"
    )
    async def slash_reaction_dm_set(
        self,
        interaction: Interaction,
        emoji: str = SlashOption(
            required=True,
            description="判定する絵文字",
        ),
        dm_message: str = SlashOption(
            required=True, description="送信したいDMのメッセージ本文です"
        ),
        target_role: nextcord.Role | None = SlashOption(
            required=False,
            description="ここにロールを指定すると、そのロールが付いている人がリアクションを行ったときのみロール付与/剥奪が行われます",
            default=None,
        ),
        fallback_channel: nextcord.TextChannel | None = SlashOption(
            required=False,
            description="DM送信に失敗した場合、ここに指定したチャンネルにて、DMに送信する予定だったメッセージをメンション付きで送信します。指定しない場合は、DM送信に失敗した場合は何も行いません。",
            default=None,
        ),
    ):
        await interaction.response.defer(ephemeral=False)

        assert isinstance(interaction.guild, nextcord.Guild)
        assert isinstance(interaction.channel, nextcord.TextChannel)

        emoji = emoji.strip()

        message = await interaction.followup.send(
            embed=nextcord.Embed(
                title="リアクションDMの設定",
                description="しばらくお待ちください......\n絵文字のチェックを行っています......",
                color=self.bot.color.ATTENTION,
            ),
            wait=True,
        )

        description = None

        try:
            await message.add_reaction(emoji)
        except nextcord.Forbidden:
            description = (
                "絵文字を追加する権限がないため、絵文字の確認ができませんでした。"
            )
        except nextcord.NotFound:
            description = "指定された絵文字が見つかりませんでした。"
        except nextcord.InvalidArgument:
            description = "絵文字が無効です。"
        except nextcord.HTTPException:
            description = "絵文字が不正です。"

        if description:
            await message.edit(
                embed=nextcord.Embed(
                    title="リアクションDMの設定",
                    description=f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n{description}",
                    color=self.bot.color.ERROR,
                )
            )
            return

        data: ReactionDMData = {
            "emoji": emoji,
            "target_role": target_role.id if target_role else None,
            "dm_message": dm_message,
            "fallback_channel": fallback_channel.id if fallback_channel else None,
        }
        await self.collection.update_one(
            {
                "guild_id": interaction.guild.id,
                "channel_id": interaction.channel.id,
            },
            {"$set": data},
            upsert=True,
        )

        self.reaction_dm_cache[interaction.channel.id] = data

        await message.edit(
            embed=nextcord.Embed(
                title="リアクションDMの設定",
                description=(
                    f"チャンネル:<#{interaction.channel.id}>に{f"<@&{target_role.id}>のロールを持つ人が" if target_role else ""}"
                    f"{emoji}のリアクションをしたとき、そのリアクションを受けた人にDMを送信します。\n\n"
                    f"```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(dm_message)}```"
                    f"\n\nDM送信に失敗した場合{'<#' + str(fallback_channel.id) + '>にフォールバックします。' if fallback_channel else 'でも何も行いません。'}"
                ),
                color=self.bot.color.NORMAL,
            )
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_dm.subcommand(
        name="del", description="チャンネルのリアクションDMの設定を削除します"
    )
    async def slash_reaction_dm_del(
        self,
        interaction: Interaction,
        channel: nextcord.TextChannel | None = SlashOption(
            required=False,
            description="削除したいリアクションDMの設定があるチャンネルを指定します。指定しない場合は、コマンドを実行したチャンネルの設定を削除します。",
            default=None,
        ),
    ):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(interaction.guild, nextcord.Guild)

        if channel is None:
            assert isinstance(interaction.channel, nextcord.TextChannel)
            channel = interaction.channel
        else:
            assert isinstance(channel, nextcord.TextChannel)

        result = await self.collection.delete_one(
            {"guild_id": interaction.guild.id, "channel_id": channel.id}
        )

        if result.deleted_count == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="リアクションDMの設定",
                    description="このチャンネルにはリアクションDMの設定がありません。",
                    color=self.bot.color.ERROR,
                )
            )
        else:
            self.reaction_dm_cache.pop(channel.id, None)

            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="リアクションDMの設定",
                    description=f"チャンネル:<#{channel.id}>\nリアクションDMの設定を削除しました。",
                    color=self.bot.color.NORMAL,
                )
            )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_dm.subcommand(
        name="list", description="リアクションDMの設定を表示します"
    )
    async def slash_reaction_dm_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(interaction.guild, nextcord.Guild)
        assert isinstance(interaction.channel, nextcord.TextChannel)

        reactdmdatas = await self.collection.find(
            {"guild_id": interaction.guild.id}
        ).to_list(length=None)

        if len(reactdmdatas) == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="リアクションDMの設定",
                    description="このサーバーにはリアクションDMの設定がありません。",
                    color=self.bot.color.NORMAL,
                )
            )
        else:
            embed = nextcord.Embed(
                title="リアクションDMの設定",
                description=interaction.guild.name,
                color=self.bot.color.NORMAL,
            )
            for reactdmdata in reactdmdatas:
                embed.add_field(
                    name=f"チャンネル: <#{reactdmdata['channel_id']}>",
                    value=(
                        f"判定リアクション絵文字: {reactdmdata['emoji']}"
                        f"{'\n<@&' + str(reactdmdata['target_role']) + '>のロールを持つ人のみが対象です。' if reactdmdata['target_role'] else ''}\n"
                        f"送信するDM: ```\n{(lambda x: x if len(x) <= 100 else f'{x[:50]}...')(reactdmdata['dm_message'])}```\n\n"
                        f"DM送信に失敗した場合{'<#' + str(reactdmdata['fallback_channel']) + '>にフォールバックします。' if reactdmdata['fallback_channel'] else 'でも何も行いません。'}"
                    ),
                    inline=False,
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: nextcord.Reaction, member: nextcord.Member
    ):
        if isinstance(reaction.message.channel, nextcord.DMChannel):
            return
        assert isinstance(reaction.message.guild, nextcord.Guild)

        if member.bot:
            return

        if reaction.message.channel.id not in self.reaction_dm_cache:
            return
        result = self.reaction_dm_cache[reaction.message.channel.id]

        if result["target_role"]:
            if not any(role.id == result["target_role"] for role in member.roles):
                return

        message = result["dm_message"]

        try:
            await member.send(message)
        except nextcord.Forbidden:
            if result["fallback_channel"]:
                fallback_channel = await self.bot.resolve_channel(
                    result["fallback_channel"]
                )

                if isinstance(fallback_channel, nextcord.TextChannel):
                    await fallback_channel.send(f"{member.mention}\n\n{message}")

        if "\u2705" not in [r.emoji for r in reaction.message.reactions]:
            await reaction.message.add_reaction("\u2705")
            await asyncio.sleep(5)
            try:
                await reaction.message.remove_reaction(
                    "\u2705", reaction.message.guild.me
                )
            except nextcord.NotFound:
                pass


def setup(bot: NIRA):
    bot.add_cog(ReactionDM(bot))
