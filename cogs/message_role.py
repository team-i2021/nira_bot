import asyncio
import datetime
import importlib
import json
import logging
import os
import re
import sys
import traceback

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh, dict_list

ROLE_ID = re.compile(r"<@&[0-9]+?>")

# 特定のチャンネルにて特定のメッセージが送信された場合にロールをつけるそれ。
# データ形式:HTTP_db

dir = sys.path[0]

MESSAGE_ROLE_SETTINGS = {}


async def pullData(client: HTTP_db.Client):
    global MESSAGE_ROLE_SETTINGS
    try:
        MESSAGE_ROLE_SETTINGS = dict_list.listToDict(await client.get("message_role"))
    except Exception:
        logging.error(traceback.format_exc())
        MESSAGE_ROLE_SETTINGS = {}


class MessageRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{dir}/setting.json', 'r'))["database_data"]
        self.client = HTTP_db.Client(
            url=datas["address"],
            port=datas["port"],
            intkey=True
        )
        asyncio.ensure_future(pullData(self.client))

    @nextcord.slash_command(name="mesrole", description="Message role command", guild_ids=n_fc.GUILD_IDS)
    async def slash_message_role(self, interaction: Interaction):
        pass

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

        if interaction.guild.id not in MESSAGE_ROLE_SETTINGS:
            MESSAGE_ROLE_SETTINGS[interaction.guild.id] = {
                interaction.channel.id: [regex, action_type, role.id]}
        else:
            MESSAGE_ROLE_SETTINGS[interaction.guild.id][interaction.channel.id] = [
                regex, action_type, role.id]

        await interaction.followup.send(
            embed=nextcord.Embed(
                title="メッセージロールの設定",
                description=f"チャンネル:<#{interaction.channel.id}>\n判定メッセージ:`{regex}`\nロール:<@&{role.id}>を{(lambda x: '付与' if x else '剥奪')(action_type)}します。",
                color=0x00ff00
            )
        )
        await self.client.post("message_role", dict_list.dictToList(MESSAGE_ROLE_SETTINGS))
        return

    @slash_message_role.subcommand(name="del", description="チャンネルのメッセージロールの設定を削除します")
    async def slash_message_role_del(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
            return

        if interaction.guild.id not in MESSAGE_ROLE_SETTINGS:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description="このサーバーにはメッセージロールの設定がありません。", color=0xff0000))
            return
        elif interaction.channel.id not in MESSAGE_ROLE_SETTINGS[interaction.guild.id]:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description="このチャンネルにはメッセージロールの設定がありません。", color=0xff0000))
            return
        else:
            del MESSAGE_ROLE_SETTINGS[interaction.guild.id][interaction.channel.id]
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{interaction.channel.id}>\nメッセージロールの設定を削除しました。", color=0x00ff00))
            await self.client.post("message_role", dict_list.dictToList(MESSAGE_ROLE_SETTINGS))
            return

    @slash_message_role.subcommand(name="list", description="メッセージロールの設定を表示します")
    async def slash_message_role_list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
            return

        if interaction.guild.id not in MESSAGE_ROLE_SETTINGS:
            await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description="このサーバーにはメッセージロールの設定がありません。", color=0x00ff00))
            return
        else:
            embed = nextcord.Embed(
                title="メッセージロールの設定", description=interaction.guild.name, color=0x00ff00)
            for channel_id, channel_setting in MESSAGE_ROLE_SETTINGS[interaction.guild.id].items():
                embed.add_field(
                    name=(await self.bot.fetch_channel(channel_id)).name,
                    value=f"判定メッセージ:`{channel_setting[0]}`\nロール:<@&{channel_setting[2]}>\nロール{(lambda x: '付与' if x else '剥奪')(channel_setting[1])}をします。",
                    inline=False
                )
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return

        if message.guild.id not in MESSAGE_ROLE_SETTINGS:
            return
        if message.channel.id not in MESSAGE_ROLE_SETTINGS[message.guild.id]:
            return
        if re.search(MESSAGE_ROLE_SETTINGS[message.guild.id][message.channel.id][0], message.content) is not None:
            if MESSAGE_ROLE_SETTINGS[message.guild.id][message.channel.id][1]:
                await message.author.add_roles(message.guild.get_role(MESSAGE_ROLE_SETTINGS[message.guild.id][message.channel.id][2]), reason="nira-bot MessageRole Service")
            else:
                await message.author.remove_roles(message.guild.get_role(MESSAGE_ROLE_SETTINGS[message.guild.id][message.channel.id][2]), reason="nira-bot MessageRole Service")
            await message.add_reaction("\u2705")

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
    async def mesrole(self, ctx: commands.Context, command_type: str, *args):
        # regex: str, action_type: str, role: str or int
        global MESSAGE_ROLE_SETTINGS
        if command_type not in ["set", "del", "list", "db"]:
            await ctx.reply(embed=nextcord.Embed(title="Error", description="コマンドが正しくありません。\n個所:第1引数(command_type)\n第1引数は`set`か`del`か`list`のみが許容されます。\n`n!help mesrole`", color=0xff0000))
            return
        if command_type == "set":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return
            if len(args) != 3:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="コマンドが正しくありません。\n引数の数が不正です。\n`n!mesrole set [判定メッセージ] [add/remove] [ロール]`", color=0xff0000))
                return
            if args[1] not in ["add", "remove"]:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="コマンドが正しくありません。\n個所:第3引数(動作タイプ)\n第2引数は`add`か`remove`のみが許容されます。\n`n!mesrole set [判定メッセージ] [add/remove] [ロール]`", color=0xff0000))
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

            if ctx.guild.id not in MESSAGE_ROLE_SETTINGS:
                MESSAGE_ROLE_SETTINGS[ctx.guild.id] = {
                    ctx.channel.id: [args[0], (lambda x: True if x == "add" else False)(args[1]), role.id]}
            else:
                MESSAGE_ROLE_SETTINGS[ctx.guild.id][ctx.channel.id] = [
                    args[0], (lambda x: True if x == "add" else False)(args[1]), role.id]

            await ctx.reply(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{ctx.channel.id}>\n判定メッセージ:`{args[0]}`\nロール:<@&{role.id}>を{(lambda x: '付与' if x else '剥奪')(args[1])}します。", color=0x00ff00))
            await self.client.post("message_role", dict_list.dictToList(MESSAGE_ROLE_SETTINGS))
            return

        elif command_type == "del":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。", color=0xff0000))
                return

            if ctx.guild.id not in MESSAGE_ROLE_SETTINGS:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="このサーバーには設定がありません。", color=0xff0000))
                return
            elif ctx.channel.id not in MESSAGE_ROLE_SETTINGS[ctx.guild.id]:
                await ctx.reply(embed=nextcord.Embed(title="Error", description="このチャンネルには設定がありません。", color=0xff0000))
                return

            del MESSAGE_ROLE_SETTINGS[ctx.guild.id][ctx.channel.id]
            await ctx.reply(embed=nextcord.Embed(title="メッセージロールの設定", description=f"チャンネル:<#{ctx.channel.id}>の設定を削除しました。", color=0x00ff00))
            await self.client.post("message_role", dict_list.dictToList(MESSAGE_ROLE_SETTINGS))
            return

        elif command_type == "list":
            if ctx.guild.id not in MESSAGE_ROLE_SETTINGS:
                await ctx.reply(embed=nextcord.Embed(title="メッセージロール", description="このサーバーには設定がありません。", color=0x00ff00))
                return
            else:
                embed = nextcord.Embed(
                    title="メッセージロールの設定", description=ctx.guild.name, color=0x00ff00)
                for channel_id, channel_setting in MESSAGE_ROLE_SETTINGS[ctx.guild.id].items():
                    embed.add_field(
                        name=f"<#{channel_id}>", value=f"判定メッセージ:`{channel_setting[0]}`\nロール:<@&{channel_setting[2]}>を{(lambda x: '付与' if x else '剥奪')(channel_setting[1])}します。")
                await ctx.reply(embed=embed)
                return

        elif command_type == "db":
            if ctx.author.id not in n_fc.py_admin:
                await ctx.reply(embed=nextcord.Embed(title="Forbidden", description="このコマンドの使用には、BOTの最高操作権限が必要です。", color=0xff0000))
                return
            if len(args) != 1:
                await ctx.reply(embed=nextcord.Embed(title="Bad Request", description=f"渡された引数が異常です。\n```sh\npull: pull from database\npush: push to database\nserver: check database's value\nclient: check current value```\nARGS:`{args}`", color=0xff0000))
                return
            if args[0] == "pull":
                try:
                    MESSAGE_ROLE_SETTINGS = dict_list.listToDict(await self.client.get("message_role"))
                except Exception:
                    MESSAGE_ROLE_SETTINGS = {}
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Pulled from database.", color=0x00ff00))
            elif args[0] == "push":
                try:
                    await self.client.post("message_role", dict_list.dictToList(MESSAGE_ROLE_SETTINGS))
                except Exception as err:
                    await ctx.reply(embed=nextcord.Embed(title="Internal Server Error", description=f"An error has occurred.\n```sh\n{err}```", color=0xff0000))
                    return
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Pushed to database.", color=0x00ff00))
            elif args[0] == "server":
                try:
                    await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Server\n```py\n{dict_list.listToDict(await self.client.get('message_role'))}```", color=0x00ff00))
                except Exception as err:
                    await ctx.reply(embed=nextcord.Embed(title="Internal Server Error", description=f"An error has occurred.\n```sh\n{err}```", color=0xff0000))
            elif args[0] == "client":
                await ctx.reply(embed=nextcord.Embed(title="OK", description=f"Client\n```py\n{MESSAGE_ROLE_SETTINGS}```", color=0x00ff00))
            else:
                await ctx.reply(embed=nextcord.Embed(title="Bad Request", description=f"渡された引数が異常です。\n```sh\npull: pull from database\npush: push to database\nserver: check database's value\nclient: check current value```\nARGS:`{args}`", color=0xff0000))
                return


def setup(bot):
    bot.add_cog(MessageRole(bot))
    importlib.reload(dict_list)
