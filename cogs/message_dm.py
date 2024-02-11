import re
import sys

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from util import admin_check, n_fc
from util.nira import NIRA

from motor import motor_asyncio

# 特定のチャンネルにて特定のメッセージが送信された場合にDMを送信する
# データ形式:MongoDB

# loggingの設定
SYSDIR = sys.path[0]


class MessageDM(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["message_dm"]

    @nextcord.slash_command(name="mesdm", description="Send DM when a set message is sent")
    async def slash_message_dm(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_guild=True)
    @slash_message_dm.subcommand(name="set", description="チャンネルのメッセージDMの設定をします")
    async def slash_message_dm_set(
            self,
            interaction: Interaction,
            regex: str = SlashOption(
                required=True,
                description="判定するメッセージです。正規表現型で書き込めます。"
            ),
            dm_message: str = SlashOption(
                required=True,
                description="送信したいDMのメッセージ本文です"
            )
        ):
        await interaction.response.defer(ephemeral=True)

        await self.collection.update_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id, "regex": regex},
            {"$set": {"message": dm_message}},
            upsert=True
        )

        await interaction.followup.send(
            embed=nextcord.Embed(
                title="メッセージDMの設定",
                description=f"チャンネル:<#{interaction.channel.id}>\n判定メッセージ:`{regex}`\n下記メッセージを送信します。```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(dm_message)}```",
                color=0x00ff00
            )
        )

    @application_checks.has_permissions(manage_guild=True)
    @slash_message_dm.subcommand(name="del", description="チャンネルのメッセージDMの設定を削除します")
    async def slash_message_dm_del(self, interaction: Interaction, regex: str = SlashOption(description="判定メッセージです", required=True)):
        await interaction.response.defer(ephemeral=True)

        result = await self.collection.delete_one({"guild_id": interaction.guild.id, "channel_id": interaction.channel.id, "regex": regex})

        if result is None:
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description=f"このチャンネルには`{regex}`という判定メッセージは存在しません。", color=0xff0000))
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{interaction.channel.id}>\n`{regex}`の設定を削除しました。", color=0x00ff00))


    @application_checks.has_permissions(manage_roles=True)
    @slash_message_dm.subcommand(name="list", description="メッセージDMの設定を表示します")
    async def slash_message_dm_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        results = await self.collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
        if len(results) == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージDMの設定", description="このサーバーにはメッセージDMの設定がありません。", color=0x00ff00))
        else:
            embed = nextcord.Embed(
                title="メッセージDMの設定", description=interaction.guild.name, color=0x00ff00
            )

            contents = {}
            for result in results:
                if result["channel_id"] not in contents:
                    contents[result["channel_id"]] = [f"判定メッセージ:`{result['regex']}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 100 else f'{x[:50]}...')(result['message'])}```"]
                else:
                    contents[result['channel_id']].append(f"判定メッセージ:`{result['regex']}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 100 else f'{x[:50]}...')(result['message'])}```")

            for channel, config in contents.items():
                embed.add_field(
                    name=(await self.bot.fetch_channel(channel)).name,
                    value="\n".join(config),
                    inline=False
                )

            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.author.bot:
            return
        results = await self.collection.find({"guild_id": message.guild.id, "channel_id": message.channel.id}).to_list(length=None)
        if len(results) == 0:
            return
        SEND = False
        for result in results:
            if re.search(result["regex"], message.content) is not None:
                await message.author.send(result["message"])
                SEND = True
        if SEND:
            await message.add_reaction("\U0001F4E8")

    @commands.command(name="mesdm", help="""\
チャンネルで特定のメッセージを送信した人にDMを送信します。

・追加
`n!mesdm set [判定メッセージ] [送信するDMのメッセージ]`

[判定メッセージ]
判定メッセージを指定します。
そのメッセージが送信されたらロール付与/剥奪を行います。
判定メッセージには`正規表現`を用いることができます。
正規表現については[こちら](https://qiita.com/tossh/items/635aea9a529b9deb3038)をご確認ください。
判定メッセージ内にスペース（空白）を入れたい場合は、判定メッセージをダブルクオーテーションで囲ってください。

[送信するDMのメッセージ]
送信したいDMのメッセージ本文です。

・削除
`n!mesdm del`

・設定一覧表示
`n!mesdm list`

・例
`n!mesdm set ([Nn][Ii][Rr][Aa]|[にニﾆ][らラﾗ]) にらといってくれてありがとうね！！！！\nこれからもよろしく！`
`n!mesdm del`
`n!mesdm list`""")
    async def mesdm(self, ctx: commands.Context, command_type: str = "list", *args):
        # regex: str, action_type: str, role: str or int

        if command_type not in ["set", "del", "list", "db"]:
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"コマンドが正しくありません。\n個所:第1引数(command_type)\n第1引数は`set`か`del`か`list`のみが許容されます。\n`{self.bot.command_prefix}help mesdm`", color=0xff0000))
            return
        if command_type == "set":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return
            if len(args) != 2:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"コマンドが正しくありません。\n引数の数が不正です。\n`{self.bot.command_prefix}mesdm set [判定メッセージ] [送信するDMのメッセージ]`", color=0xff0000))
                return

            await self.collection.update_one(
                {"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "regex": args[0]},
                {"$set": {"message": args[1]}},
                upsert=True
            )

            await ctx.reply(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{ctx.channel.id}>\n判定メッセージ:`{args[0]}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(args[1])}```", color=0x00ff00))

        elif command_type == "del":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return

            result = await self.collection.delete_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "regex": args[0]})

            if result is None:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"このチャンネルには`{args[0]}`という判定メッセージは存在しません。", color=0xff0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{ctx.channel.id}>での`{args[0]}`を削除しました。", color=0x00ff00))

        elif command_type == "list":
            results = await self.collection.find({"guild_id": ctx.guild.id}).to_list(length=None)
            if len(results) == 0:
                await ctx.reply(embed=nextcord.Embed(title="メッセージDM", description="このサーバーには設定がありません。", color=0x00ff00))
            else:
                embed = nextcord.Embed(
                    title="メッセージDMの設定",
                    description=ctx.guild.name,
                    color=0x00ff00
                )
                contents = {}
                for result in results:
                    if result["channel_id"] not in contents:
                        contents[result["channel_id"]] = [f"判定メッセージ:`{result['regex']}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 100 else f'{x[:50]}...')(result['message'])}```"]
                    else:
                        contents[result['channel_id']].append(f"判定メッセージ:`{result['regex']}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 100 else f'{x[:50]}...')(result['message'])}```")

                for channel, config in contents.items():
                    embed.add_field(
                        name=(await self.bot.fetch_channel(channel)).name,
                        value="\n".join(config),
                        inline=False
                    )
                await ctx.reply(embed=embed)

def setup(bot):
    bot.add_cog(MessageDM(bot))
