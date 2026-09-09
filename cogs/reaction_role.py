import asyncio
from typing import TypedDict

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, tasks

from util.nira import NIRA

# 特定のチャンネルにて特定のリアクションを付けたら、つけられた人にロールを付与するみたいな。ロールパネルとはまた少し違うやつ。


class ReactionRoleData(TypedDict):
    emoji: str
    target_role: int | None
    action_type: bool
    grant_role: int


class ReactionRole(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[
            "reaction_role"
        ]
        self.reaction_role_cache: dict[int, ReactionRoleData] = {}
        self.load_reaction_role_settings.start()

    def cog_unload(self):
        self.load_reaction_role_settings.cancel()

    @tasks.loop(hours=1.0)
    async def load_reaction_role_settings(self):
        self.reaction_role_cache = {}
        async for reaction_role in self.collection.find():
            self.reaction_role_cache[int(reaction_role["channel_id"])] = {
                "emoji": reaction_role["emoji"],
                "target_role": reaction_role.get("target_role"),
                "action_type": reaction_role["action_type"],
                "grant_role": reaction_role["grant_role"],
            }

    @nextcord.slash_command(name="reactrole", description="Reaction role command")
    async def slash_reaction_role(self, interaction: Interaction):
        pass

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_role.subcommand(
        name="set", description="チャンネルのリアクションロールの設定をします"
    )
    async def slash_reaction_role_set(
        self,
        interaction: Interaction,
        emoji: str = SlashOption(
            required=True,
            description="判定する絵文字",
        ),
        action_type: int = SlashOption(
            required=True,
            description="ロールを付与するか剥奪するか",
            choices={"付与": 1, "剥奪": 0},
        ),
        grant_role: nextcord.Role = SlashOption(
            required=True, description="付与/剥奪するロール"
        ),
        target_role: nextcord.Role | None = SlashOption(
            required=False,
            description="ここにロールを指定すると、そのロールが付いている人がリアクションを行ったときのみロール付与/剥奪が行われます",
            default=None,
        ),
    ):
        await interaction.response.defer(ephemeral=False)

        assert isinstance(interaction.guild, nextcord.Guild)
        assert isinstance(interaction.channel, nextcord.TextChannel)

        emoji = emoji.strip()

        message = await interaction.followup.send(
            embed=nextcord.Embed(
                title="リアクションロールの設定",
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
                    title="リアクションロールの設定",
                    description=f"絵文字 {emoji} (`{emoji}`)の確認時にエラーが発生しました。\n{description}",
                    color=self.bot.color.ERROR,
                )
            )
            return

        action_type = (lambda x: True if x else False)(action_type)

        data: ReactionRoleData = {
            "emoji": emoji,
            "target_role": target_role.id if target_role else None,
            "action_type": action_type,
            "grant_role": grant_role.id,
        }
        await self.collection.update_one(
            {
                "guild_id": interaction.guild.id,
                "channel_id": interaction.channel.id,
            },
            {"$set": data},
            upsert=True,
        )

        self.reaction_role_cache[interaction.channel.id] = data

        await message.edit(
            embed=nextcord.Embed(
                title="リアクションロールの設定",
                description=f"チャンネル:<#{interaction.channel.id}>に{f"<@&{target_role.id}>のロールを持つ人が" if target_role else ""}{emoji}のリアクションをしたとき、そのリアクションを受けた人に<@&{grant_role.id}>を{(lambda x: '付与' if x else '剥奪')(action_type)}します。",
                color=self.bot.color.NORMAL,
            ),
        )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_role.subcommand(
        name="del", description="チャンネルのリアクションロールの設定を削除します"
    )
    async def slash_reaction_role_del(
        self,
        interaction: Interaction,
        channel: nextcord.TextChannel | None = SlashOption(
            required=False,
            description="削除したいリアクションロールの設定があるチャンネルを指定します。指定しない場合は、コマンドを実行したチャンネルの設定を削除します。",
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
                    title="リアクションロールの設定",
                    description="このチャンネルにはリアクションロールの設定がありません。",
                    color=self.bot.color.ERROR,
                )
            )
        else:
            self.reaction_role_cache.pop(channel.id, None)

            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="リアクションロールの設定",
                    description=f"チャンネル:<#{channel.id}>\nリアクションロールの設定を削除しました。",
                    color=self.bot.color.NORMAL,
                )
            )

    @application_checks.guild_only()
    @application_checks.has_permissions(manage_roles=True)
    @slash_reaction_role.subcommand(
        name="list", description="リアクションロールの設定を表示します"
    )
    async def slash_reaction_role_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(interaction.guild, nextcord.Guild)
        assert isinstance(interaction.channel, nextcord.TextChannel)

        reactroledatas = await self.collection.find(
            {"guild_id": interaction.guild.id}
        ).to_list(length=None)

        if len(reactroledatas) == 0:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="リアクションロールの設定",
                    description="このサーバーにはリアクションロールの設定がありません。",
                    color=self.bot.color.NORMAL,
                )
            )
        else:
            embed = nextcord.Embed(
                title="リアクションロールの設定",
                description=interaction.guild.name,
                color=self.bot.color.NORMAL,
            )
            for reactroledata in reactroledatas:
                embed.add_field(
                    name=f"チャンネル: <#{reactroledata['channel_id']}>",
                    value=f"判定リアクション絵文字: {reactroledata['emoji']}\nロール: <@&{reactroledata['grant_role']}>を{'付与' if reactroledata['action_type'] else '剥奪'}する。\n{'<@&' + str(reactroledata['target_role']) + '>のロールを持つ人のみが対象です。' if reactroledata['target_role'] else ''}",
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

        if reaction.message.channel.id not in self.reaction_role_cache:
            return
        result = self.reaction_role_cache[reaction.message.channel.id]

        if result["target_role"]:
            if not any(role.id == result["target_role"] for role in member.roles):
                return

        if str(reaction.emoji) != result["emoji"]:
            return

        target_member = reaction.message.author
        if target_member.bot:
            return

        assert isinstance(target_member, nextcord.Member)

        role = await reaction.message.guild.fetch_role(result["grant_role"])

        if result["action_type"]:
            await target_member.add_roles(
                role,
                reason="nira-bot ReactionRole Service",
            )
        else:
            await target_member.remove_roles(
                role,
                reason="nira-bot ReactionRole Service",
            )

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
    bot.add_cog(ReactionRole(bot))
