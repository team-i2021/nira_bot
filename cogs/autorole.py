from re import compile

import nextcord
from nextcord import Interaction, SlashOption, Role
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import admin_check
from util.n_fc import GUILD_IDS
from util.slash_tool import messages
from util.nira import NIRA

# Autorole

MESSAGE, SLASH = (0, 1)
STATUS, ON, OFF = (0, 1, 2)
ROLE_ID = compile(r"<@&[0-9]+?>")



class autorole(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["autorole"]

    @nextcord.slash_command(name="autorole", description="自動ロール")
    async def autorole(self, interaction: Interaction):
        pass

    async def autorole_message(self, type, mode, user, guild, role: Role = None):
        if not admin_check.admin_check(guild, user):
            return ("自動ロール\nエラー：権限がありません。", None)

        if mode == ON:
            if role.name == "@everyone":
                return ("自動ロール\nエラー：@everyone は無効です。", None)


            await self.collection.update_one({"guild_id": guild.id}, {"$set": {"role_id": role.id}}, upsert=True)
            return (None, nextcord.Embed(title="自動ロール", description=f"設定完了：{role.mention}を自動的に付与します。", color=0x00ff00))

        elif mode == OFF:
            result = await self.collection.delete_one({"guild_id": guild.id})
            if result.deleted_count == 0:
                return ("サーバーで自動ロールは設定されていません。", None)
            else:
                return ("サーバーで自動ロールを無効にしました。", None)

        else:
            result = await self.collection.delete_one({"guild_id": guild.id})
            if result is not None:
                msg = f"自動ロールは有効です。\n自動付与されるロールは{guild.get_role(result['role_id']).mention}です。"
            else:
                msg = "自動ロールは無効です。"

            if type == SLASH:
                usage = "`/autorole on [ロール]` / `/autorole off` / `/autorole status`"
            else:
                usage = f"`{self.bot.command_prefix}autorole on [ロール名/ロールID/メンション]` / `{self.bot.command_prefix}autorole off`"

            return (None, nextcord.Embed(title="自動ロール", description=f"{msg}\n{usage}", color=0x00ff00))

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="autorole", aliases=("自動ロール", "オートロール"), help="""\
    ユーザーが加入したときに、指定したロールを自動的に付与することが出来ます。
    ・使い方
    設定: `n!autorole on [ロール名/ロールID/ロールへのメンション]`
    無効化: `n!autorole off`

    ・例
    ```
    n!autorole on にら民
    ```


    """)
    async def autorole_ctx(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 2)
        if len(args) == 1:
            msg = await self.autorole_message(MESSAGE, STATUS, ctx.author, ctx.guild)

        elif args[1] == "off":
            msg = await self.autorole_message(MESSAGE, OFF, ctx.author, ctx.guild)

        elif args[1] == "on":
            if len(args) < 3 or args[2] == "":
                msg = ("自動ロール\nエラー：ロールを指定してください。", None)

            # 空のリストは False になる
            elif ctx.message.mentions or ctx.channel_mentions:
                msg = ("自動ロール\nエラー：ロールでないメンションが含まれています。", None)

            # ロールのメンション数が1より多いか、ロールのメンションとそうでない文字列が混在している
            elif len(ctx.message.role_mentions) > 1 or \
                    ctx.message.role_mentions and ROLE_ID.fullmatch(args[2]) is None:
                msg = ("自動ロール\nエラー：ロールは１つのみ指定できます。", None)

            elif ctx.message.role_mentions:
                msg = await self.autorole_message(
                    MESSAGE,
                    ON,
                    ctx.author,
                    ctx.guild,
                    ctx.message.role_mentions[0]
                )

            else:
                role = None

                try:
                    role = ctx.guild.get_role(int(args[2]))
                except ValueError:
                    pass

                if role is None:
                    for r in ctx.guild.roles:
                        if r.name == args[2]:
                            role = r
                            break

                if role is None:
                    msg = ("自動ロール\nエラー：指定したロールが見つかりません。", None)
                else:
                    msg = await self.autorole_message(
                        MESSAGE,
                        ON,
                        ctx.author,
                        ctx.guild,
                        role
                    )

        else:
            msg = (
                None,
                nextcord.Embed(
                    title="自動ロール",
                    description=f"コマンドの使用方法が不正です。\n`{self.bot.command_prefix}autorole on [ロール名又はロールID]`/`{self.bot.command_prefix}autorole off`",
                    color=0x00ff00
                )
            )

        await messages.mreply(ctx, msg[0], embed=msg[1])

    @application_checks.has_permissions(manage_roles=True)
    @autorole.subcommand(name="off", description="自動ロールを無効にします")
    async def autorole_off(self, interaction: Interaction):
        msg = await self.autorole_message(
            SLASH,
            OFF,
            interaction.user,
            interaction.guild
        )
        await messages.mreply(interaction, msg[0], embed=msg[1], ephemeral=True)

    @application_checks.has_permissions(manage_roles=True)
    @autorole.subcommand(name="on", description="ユーザーが加入したときに自動的にロールを付与します")
    async def autorole_on(
            self,
            interaction: Interaction,
            role: Role = SlashOption(
                name="role",
                description="自動的に付与するロールです",
                required=True
            )
    ):
        msg = await self.autorole_message(
            SLASH,
            ON,
            interaction.user,
            interaction.guild,
            role
        )
        await messages.mreply(interaction, msg[0], embed=msg[1], ephemeral=True)

    @autorole.subcommand(name="status", description="自動ロールの設定状態を確認します")
    async def autorole_status(self, interaction: Interaction):
        msg = await self.autorole_message(
            SLASH,
            STATUS,
            interaction.user,
            interaction.guild
        )
        await messages.mreply(interaction, msg[0], embed=msg[1], ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        result = await self.collection.find_one({"guild_id": member.guild.id})
        if result is not None:
            role = member.guild.get_role(result["role_id"])
            await member.add_roles(role, reason="NiraBOT AutoRole")


def setup(bot, **kwargs):
    bot.add_cog(autorole(bot, **kwargs))
