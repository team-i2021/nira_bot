import datetime
import logging
from util import admin_check, n_fc, eh, dict_list
import asyncio
from nextcord.ext import commands
import nextcord
import traceback
import os
import re
import sys
from nextcord import Interaction, SlashOption, ChannelType
import HTTP_db
import json
import importlib

ROLE_ID = re.compile(r"<@&[0-9]+?>")

# 特定のチャンネルにて特定のメッセージが送信された場合にDMを送信する
# データ形式:HTTP_db

# loggingの設定
SYSDIR = sys.path[0]

MESSAGE_DM_SETTINGS = {}


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message


logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=formatter, filename=f'{SYSDIR}/nira.log', level=logging.INFO)


async def pullData(client: HTTP_db.Client):
    global MESSAGE_DM_SETTINGS
    try:
        MESSAGE_DM_SETTINGS = dict_list.listToDict(await client.get("message_dm"))
    except Exception:
        logging.error(traceback.format_exc())
        MESSAGE_DM_SETTINGS = {}


class MessageDM(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{SYSDIR}/setting.json', 'r'))["database_data"]
        self.client: HTTP_db.Client = database.openClient()
        asyncio.ensure_future(pullData(self.client))

    @nextcord.slash_command(name="mesdm", description="Send DM when a set message is sent", guild_ids=n_fc.GUILD_IDS)
    async def slash_message_dm(self, interaction: Interaction):
        pass

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

        if interaction.guild.id not in MESSAGE_DM_SETTINGS:
            MESSAGE_DM_SETTINGS[interaction.guild.id] = {
                interaction.channel.id: [
                    regex,
                    dm_message
                ]
            }
        else:
            MESSAGE_DM_SETTINGS[interaction.guild.id][interaction.channel.id] = [
                regex,
                dm_message
            ]

        await interaction.followup.send(
            embed=nextcord.Embed(
                title="メッセージDMの設定",
                description=f"チャンネル:<#{interaction.channel.id}>\n判定メッセージ:`{regex}`\n下記メッセージを送信します。```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(dm_message)}```",
                color=0x00ff00
            )
        )
        await self.client.post("message_dm", dict_list.dictToList(MESSAGE_DM_SETTINGS))
        return

    @slash_message_dm.subcommand(name="del", description="チャンネルのメッセージDMの設定を削除します")
    async def slash_message_dm_del(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
            return

        if interaction.guild.id not in MESSAGE_DM_SETTINGS:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージの設定", description="このサーバーにはメッセージDMの設定がありません。", color=0xff0000))
            return
        elif interaction.channel.id not in MESSAGE_DM_SETTINGS[interaction.guild.id]:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージDMの設定", description="このチャンネルにはメッセージDMの設定がありません。", color=0xff0000))
            return
        else:
            del MESSAGE_DM_SETTINGS[interaction.guild.id][interaction.channel.id]
            if len(MESSAGE_DM_SETTINGS[interaction.guild.id]) == 0:
                del MESSAGE_DM_SETTINGS[interaction.guild.id]
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{interaction.channel.id}>\nメッセージDMの設定を削除しました。", color=0x00ff00))
            await self.client.post("message_dm", dict_list.dictToList(MESSAGE_DM_SETTINGS))
            return

    @slash_message_dm.subcommand(name="list", description="メッセージDMの設定を表示します")
    async def slash_message_dm_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.guild.id not in MESSAGE_DM_SETTINGS:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージDMの設定", description="このサーバーにはメッセージDMの設定がありません。", color=0x00ff00))
            return
        else:
            embed = nextcord.Embed(
                title="メッセージDMの設定", description=interaction.guild.name, color=0x00ff00)
            for channel_id, channel_setting in MESSAGE_DM_SETTINGS[interaction.guild.id].items():
                embed.add_field(
                    name=(await self.bot.fetch_channel(channel_id)).name,
                    value=f"判定メッセージ:`{channel_setting[0]}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(channel_setting[1])}```",
                    inline=False
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return

        if message.guild.id not in MESSAGE_DM_SETTINGS:
            return
        if message.channel.id not in MESSAGE_DM_SETTINGS[message.guild.id]:
            return
        if re.search(MESSAGE_DM_SETTINGS[message.guild.id][message.channel.id][0], message.content) is not None:
            await message.author.send(MESSAGE_DM_SETTINGS[message.guild.id][message.channel.id][1])
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
    async def mesdm(self, ctx: commands.Context, command_type: str, *args):
        # regex: str, action_type: str, role: str or int

        global MESSAGE_DM_SETTINGS
        if command_type not in ["set", "del", "list", "db"]:
            await ctx.reply(embed=nextcord.Embed(title="Error", description="コマンドが正しくありません。\n個所:第1引数(command_type)\n第1引数は`set`か`del`か`list`のみが許容されます。\n`n!help mesdm`", color=0xff0000))
            return
        if command_type == "set":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return
            if len(args) != 2:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="コマンドが正しくありません。\n引数の数が不正です。\n`n!mesdm set [判定メッセージ] [送信するDMのメッセージ]`", color=0xff0000))
                return

            if ctx.guild.id not in MESSAGE_DM_SETTINGS:
                MESSAGE_DM_SETTINGS[ctx.guild.id] = {
                    ctx.channel.id: [
                        args[0],
                        args[1]
                    ]
                }
            else:
                MESSAGE_DM_SETTINGS[ctx.guild.id][ctx.channel.id] = [
                    args[0],
                    args[1]
                ]

            await ctx.reply(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{ctx.channel.id}>\n判定メッセージ:`{args[0]}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(args[1])}```", color=0x00ff00))
            await self.client.post("message_dm", dict_list.dictToList(MESSAGE_DM_SETTINGS))
            return

        elif command_type == "del":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return

            if ctx.guild.id not in MESSAGE_DM_SETTINGS:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="このサーバーには設定がありません。", color=0xff0000))
                return
            elif ctx.channel.id not in MESSAGE_DM_SETTINGS[ctx.guild.id]:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="このチャンネルには設定がありません。", color=0xff0000))
                return

            del MESSAGE_DM_SETTINGS[ctx.guild.id][ctx.channel.id]
            if len(MESSAGE_DM_SETTINGS[ctx.guild.id]) == 0:
                del MESSAGE_DM_SETTINGS[ctx.guild.id]
            await ctx.reply(embed=nextcord.Embed(title="メッセージDMの設定", description=f"チャンネル:<#{ctx.channel.id}>の設定を削除しました。", color=0x00ff00))
            await self.client.post("message_dm", dict_list.dictToList(MESSAGE_DM_SETTINGS))
            return

        elif command_type == "list":
            if ctx.guild.id not in MESSAGE_DM_SETTINGS:
                await ctx.reply(embed=nextcord.Embed(title="メッセージDM", description="このサーバーには設定がありません。", color=0x00ff00))
                return
            else:
                embed = nextcord.Embed(
                    title="メッセージDMの設定", description=ctx.guild.name, color=0x00ff00)
                for channel_id, channel_setting in MESSAGE_DM_SETTINGS[ctx.guild.id].items():
                    embed.add_field(
                        name=(await self.bot.fetch_channel(channel_id)).name,
                        value=f"判定メッセージ:`{channel_setting[0]}`\n・メッセージ内容```\n{(lambda x: x if len(x) <= 1000 else f'{x[:1000]}...')(channel_setting[1])}```"
                    )
                await ctx.reply(embed=embed)
                return

        elif command_type == "db":
            if ctx.author.id not in n_fc.py_admin:
                await ctx.reply(embed=nextcord.Embed(title="Forbidden", description="このコマンドの使用には、BOTのオーナー権限が必要です。", color=0xff0000))
                return
            if len(args) != 1:
                await ctx.reply(embed=nextcord.Embed(title="Bad Request", description=f"渡された引数が異常です。\n```sh\npull: pull from database\npush: push to database\nserver: check database's value\nclient: check current value```\nARGS:`{args}`", color=0xff0000))
                return
            if args[0] == "pull":
                try:
                    MESSAGE_DM_SETTINGS = dict_list.listToDict(await self.client.get("message_dm"))
                except Exception:
                    MESSAGE_DM_SETTINGS = {}
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Pulled from database.", color=0x00ff00))
            elif args[0] == "push":
                try:
                    await self.client.post("message_dm", dict_list.dictToList(MESSAGE_DM_SETTINGS))
                except Exception as err:
                    await ctx.reply(embed=nextcord.Embed(title="Internal Server Error", description=f"An error has occurred.\n```sh\n{err}```", color=0xff0000))
                    return
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Pushed to database.", color=0x00ff00))
            elif args[0] == "server":
                try:
                    await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Server\n```py\n{dict_list.listToDict(await self.client.get('message_dm'))}```", color=0x00ff00))
                except Exception as err:
                    await ctx.reply(embed=nextcord.Embed(title="Internal Server Error", description=f"An error has occurred.\n```sh\n{err}```", color=0xff0000))
            elif args[0] == "client":
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Client\n```py\n{MESSAGE_DM_SETTINGS}```", color=0x00ff00))
            else:
                await ctx.reply(embed=nextcord.Embed(title="Bad Request", description=f"渡された引数が異常です。\n```sh\npull: pull from database\npush: push to database\nserver: check database's value\nclient: check current value```\nARGS:`{args}`", color=0xff0000))
                return


def setup(bot):
    bot.add_cog(MessageDM(bot))
