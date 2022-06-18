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

sys.path.append('../')

# 特定のチャンネルにて特定のメッセージが送信された場合にロールをつけるそれ。

# loggingの設定
dir = sys.path[0]


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message


logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(
    format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)


class MessageRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        datas = json.load(open(f'{dir}/setting.json', 'r'))["database_data"]
        self.client = HTTP_db.Client(
            url=datas["address"], port=datas["port"], intkey=True)

    @nextcord.slash_command(name="message_role", description="Message role command", guild_ids=n_fc.GUILD_IDS)
    async def slash_genshin(self, interaction: Interaction):
        pass

    @slash_genshin.subcommand(name="set", description="メッセージロールの設定をします")
    async def slash_genshin_stats(
        self,
        interaction: Interaction,
        message: str = SlashOption(
            required=True,
            description="判定するメッセージです。正規表現型で書き込めます。"
        ),
        role: nextcord.Role = SlashOption(
            required=True,
            description="付与するロール"
        )
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            settings: list = await self.client.get("message_role")
        except Exception:
            settings = []
        key = dict_list.listKey(settings, interaction.guild.id)
        if key is not None:
            key2 = dict_list.listKey(settings[key][1], interaction.channel.id)
            if key2 is not None:
                settings[key][1][key2][0] = message
                settings[key][1][key2][1] = role.id
            else:
                settings[key][1].append(
                    [[interaction.channel.id, [message, role.id]]])
        else:
            settings.append(
                [interaction.guild.id, [[interaction.channel.id, [message, role.id]]]]
            )
        await self.client.post("message_role", settings)
        await interaction.followup.send(embed=nextcord.Embed(title="メッセージロールの設定", description=f"判定メッセージ:`{message}`\nロール:<@&{role.id}>"))
        return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        try:
            settings: list = await self.client.get("message_role")
        except Exception:
            return
        key = dict_list.listKey(settings, message.guild.id)
        if key is not None:
            key2 = dict_list.listKey(settings[key][1], message.channel.id)
            if key2 is not None:
                if re.search(settings[key][1][key2][1][0], message.content):
                    print([key, key2])
                    await message.author.add_roles(message.guild.get_role(settings[key][1][key2][1][1]), reason="nira-bot MessageRole Service")
                    await message.add_reaction("\u2705")

    @commands.command(name="mesrole", help="""\
チャンネルで特定のメッセージを送信した人にロールを付与します。
設定かきかきこちゅう""")
    async def mesrole(self, ctx: commands.Context, regex: str, role: str):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply(embed=nextcord.Embed(title="Error", description="あなたは管理者ではありません。"))
            return
        role_id = None
        try:
            role_id = int(role)
        except ValueError:
            roles = ctx.guild.roles
            for i in range(len(roles)):
                if roles[i].name == role:
                    role_id = roles[i].id
                    break
        if role_id is None:
            await ctx.reply(f"`{role}`というIDまたは名前のロールは存在しません")
            return
        try:
            settings: list = await self.client.get("message_role")
        except Exception:
            settings = []
        key = dict_list.listKey(settings, ctx.guild.id)
        if key is not None:
            key2 = dict_list.listKey(settings[key][1], ctx.channel.id)
            if key2 is not None:
                settings[key][1][key2][0] = regex
                settings[key][1][key2][1] = role_id
            else:
                settings[key][1].append(
                    [[ctx.channel.id, [regex, role_id]]])
        else:
            settings.append(
                [ctx.guild.id, [[ctx.channel.id, [regex, role_id]]]]
            )
        await self.client.post("message_role", settings)
        await ctx.reply(embed=nextcord.Embed(title="メッセージロールの設定", description=f"判定メッセージ:`{regex}`\nロール:<@&{role_id}>"))


def setup(bot):
    bot.add_cog(MessageRole(bot))
    importlib.reload(dict_list)
