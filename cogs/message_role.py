import re
import sys

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import admin_check, n_fc
from util.nira import NIRA

ROLE_ID = re.compile(r"<@&[\d]+?>")

# 特定のチャンネルにて特定のメッセージが送信された場合にロールをつけるそれ。
# データ形式:MongoDB

SYSDIR = sys.path[0]

class MessageRole(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["message_role"]

    @nextcord.slash_command(name="mesrole", description="Message role command")
    async def slash_message_role(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_roles=True)
    @slash_message_role.subcommand(name="set", description="チャンネルのメッセージロールの設定をします")
    async def slash_message_role_set(
        self,
        interaction: Interaction,
        regex: str = SlashOption(
            required=True,
            description="判定するメッセージです。正規表現型で書き込めます。"
        ),
        action_type: int = SlashOption(
            required=True,
            description="ロールを付与するか剥奪するか",
            choices={"付与": 1, "剥奪": 0}
        ),
        role: nextcord.Role = SlashOption(
            required=True,
            description="付与/剥奪するロール"
        )
    ):
        action_type = (lambda x: True if x else False)(action_type)
        await interaction.response.defer(ephemeral=True)

        data = {"regex": regex, "role_id": role.id, "action_type": action_type}
        await self.collection.update_one({"guild_id": interaction.guild.id, "channel_id": interaction.channel.id}, {"$set": data}, upsert=True)

        await interaction.followup.send(
            embed=nextcord.Embed(
                title="メッセージロールの設定",
                description=f"チャンネル:<#{interaction.channel.id}>\n判定メッセージ:`{regex}`\nロール:<@&{role.id}>を{(lambda x: '付与' if x else '剥奪')(action_type)}します。",
                color=0x00ff00
            )
        )


    @application_checks.has_permissions(manage_roles=True)
    @slash_message_role.subcommand(name="del", description="チャンネルのメッセージロールの設定を削除します")
    async def slash_message_role_del(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
            return

        result = await self.collection.delete_one({"guild_id": interaction.guild.id, "channel_id": interaction.channel.id})

        if result.deleted_count == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description="このサーバーにはメッセージロールの設定がありません。", color=0xff0000))
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{interaction.channel.id}>\nメッセージロールの設定を削除しました。", color=0x00ff00))

    @application_checks.has_permissions(manage_roles=True)
    @slash_message_role.subcommand(name="list", description="メッセージロールの設定を表示します")
    async def slash_message_role_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
            return

        mesroledatas = await self.collection.find({"guild_id": interaction.guild.id}).to_list(length=None)

        if len(mesroledatas) == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description="このサーバーにはメッセージロールの設定がありません。", color=0x00ff00))
        else:
            embed = nextcord.Embed(
                title="メッセージロールの設定", description=interaction.guild.name, color=0x00ff00)
            for mesroledata in mesroledatas:
                embed.add_field(
                    name=(await self.bot.fetch_channel(mesroledata['channel_id'])).name,
                    value=f"判定メッセージ:`{mesroledata['regex']}`\nロール:<@&{mesroledata['role_id']}>\nロール{'付与' if mesroledata['action_type'] else '剥奪'}をします。",
                    inline=False
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.author.bot:
            return
        result = await self.collection.find_one({"guild_id": message.guild.id, "channel_id": message.channel.id})
        if result is None:
            return
        if re.search(result['regex'], message.content) is not None:
            if result['action_type']:
                await message.author.add_roles(message.guild.get_role(result["role_id"]), reason="nira-bot MessageRole Service")
            else:
                await message.author.remove_roles(message.guild.get_role(result["role_id"]), reason="nira-bot MessageRole Service")
            await message.add_reaction("\u2705")

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="mesrole", help="""\
チャンネルで特定のメッセージを送信した人にロールを付与します。

・追加
`n!mesrole set [判定メッセージ] [add/remove] [ロール]`

[判定メッセージ]
判定メッセージを指定します。
そのメッセージが送信されたらロール付与/剥奪を行います。
判定メッセージには`正規表現`を用いることができます。
正規表現については[こちら](https://qiita.com/tossh/items/635aea9a529b9deb3038)をご確認ください。
判定メッセージ内にスペース（空白）を入れたい場合は、判定メッセージをダブルクオーテーションで囲ってください。

[add/remove]
ロールを付与するのか剥奪するのかの動作タイプを指定します。
`add`か`remove`のみで指定できます。
`add`:ロールを付与する
`remove`:ロールを剥奪する

[ロール]
付与/剥奪したいロールの名前又はIDを指定します。

・削除
`n!mesrole del`

・設定一覧表示
`n!mesrole list`

・例
`n!mesrole add おはよう add 挨拶する人`
`n!mesrole add "You Tube"` add YouTubeの間に空白入れるタイプの人`
`n!mesrole remove ([Nn][Ii][Rr][Aa]|[にニﾆ][らラﾗ]) remove にらと言ってない人`
`n!mesrole list`""")
    async def mesrole(self, ctx: commands.Context, command_type: str = "list", *args):
        # regex: str, action_type: str, role: str or int

        if command_type not in ["set", "del", "list", "db"]:
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"コマンドが正しくありません。\n個所:第1引数(command_type)\n第1引数は`set`か`del`か`list`のみが許容されます。\n`{self.bot.command_prefix}help mesrole`", color=0xff0000))
            return
        if command_type == "set":
            if len(args) != 3:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"コマンドが正しくありません。\n引数の数が不正です。\n`{self.bot.command_prefix}mesrole set [判定メッセージ] [add/remove] [ロール]`", color=0xff0000))
                return
            if args[1] not in ["add", "remove"]:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"コマンドが正しくありません。\n個所:第3引数(動作タイプ)\n第2引数は`add`か`remove`のみが許容されます。\n`{self.bot.command_prefix}mesrole set [判定メッセージ] [add/remove] [ロール]`", color=0xff0000))
                return

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
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"指定したロール`{args[2]}`が見つかりませんでした。\nロール名又はロールIDが正しく指定されてることを確認してください。", color=0xff0000))
                return

            await self.collection.update_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id}, {"$set": {"regex": args[0], "role_id": role.id, "action_type": True if args[1] == 'add' else False}}, upsert=True)

            await ctx.reply(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{ctx.channel.id}>\n判定メッセージ:`{args[0]}`\nロール:<@&{role.id}>を{(lambda x: '付与' if x else '剥奪')(args[1])}します。", color=0x00ff00))

        elif command_type == "del":
            result = await self.collection.delete_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id})

            if result.deleted_count == 0:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="このチャンネルには設定がありません。", color=0xff0000))
                return

            await ctx.reply(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{ctx.channel.id}>の設定を削除しました。", color=0x00ff00))

        elif command_type == "list":
            results = await self.collection.find({"guild_id": ctx.guild.id}).to_list(length=None)
            if len(results) == 0:
                await ctx.reply(embed=nextcord.Embed(title="メッセージロール", description="このサーバーには設定がありません。", color=0x00ff00))
            else:
                embed = nextcord.Embed(
                    title="メッセージロールの設定", description=ctx.guild.name, color=0x00ff00)
                for result in results:
                    embed.add_field(
                        name=(await self.bot.fetch_channel(result['channel_id'])).name,
                        value=f"判定メッセージ:`{result['regex']}`\nロール:<@&{result['role_id']}>\nロール{'付与' if result['action_type'] else '剥奪'}をします。",
                        inline=False
                    )
                await ctx.reply(embed=embed)

def setup(bot, **kwargs):
    bot.add_cog(MessageRole(bot, **kwargs))
