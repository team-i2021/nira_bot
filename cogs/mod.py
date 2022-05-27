import logging
from tkinter import E, W
from nextcord.ext import commands
import nextcord, datetime
from nextcord import Interaction, SlashOption
import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
from cogs.debug import save
import asyncio

# 規定秒数以内に指定数メッセージを送信した人をミュートするモデレーター的な機能
# n!mod
# /mod

import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

reset_time = ""

class counter:
    messageCounter = {}

reset_time = ""

async def counterReset():
    while True:
        await asyncio.sleep(20)
        global reset_time
        reset_time = str(datetime.datetime.now())
        counter.messageCounter = {}


class mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.author.bot:
            return
        if message.guild.id not in n_fc.mod_list:
            return
        if message.author.id not in counter.messageCounter:
            counter.messageCounter[message.author.id] = 0
        counter.messageCounter[message.author.id] = counter.messageCounter[message.author.id] + 1
        if counter.messageCounter[message.author.id] > n_fc.mod_list[message.guild.id]["counter"] - 3 and counter.messageCounter[message.author.id] < n_fc.mod_list[message.guild.id]["counter"]:
            await message.channel.send(f"{message.author.mention}\nメッセージ送信数が多いです。あまり多いとミュートされます。")
            return
        if counter.messageCounter[message.author.id] >= n_fc.mod_list[message.guild.id]["counter"]:
            try:
                role = message.guild.get_role(n_fc.mod_list[message.guild.id]["role"])
                await message.author.add_roles(role, reason="にらBOTの荒らし対策機能")
                await message.channel.send(f"{message.author.mention}は、メッセージ数が規定オーバーのため、ミュートしました。")
                return
            except BaseException as err:
                await message.channel.send(f"{message.author.name}をミュートしようとしましたがエラーが発生しました。\n```\n{err}```")
                return


    @commands.command(name="mod", help="""\
一応、特定数異常のメッセージを20秒以内に送信した人がミュートされていくはずです。
ちゃんと作ってません。はい。""")
    async def mod(self, ctx: commands.Context):
        if ctx.message.content[:8] == "n!mod on":
            if admin_check.admin_check(ctx.guild, ctx.author):
                arg = ctx.message.content[9:].split(" ",1)
                role_id = None
                try:
                    role_id = int(arg[1])
                except ValueError:
                    roles = ctx.guild.roles
                    for i in range(len(roles)):
                        if roles[i].name == arg[1]:
                            role_id = roles[i].id
                            break
                    if role_id == None:
                        await ctx.reply("ロールが見つかりませんでした。")
                        return
                if ctx.guild.get_role(role_id).name == "@everyone":
                    await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="@everyoneは使用できません。", color=0xff0000))
                    return
                n_fc.mod_list[ctx.guild.id] = {"counter": int(arg[0]), "role": role_id}
                await ctx.reply(f"設定完了",embed=nextcord.Embed(title="荒らし対策",description=f"メッセージカウンター:`{arg[0]}`\nミュート用ロール:<@&{role_id}>", color=0x00ff00))
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000))
                return
        elif ctx.message.content == "n!mod off":
            if admin_check.admin_check(ctx.guild, ctx.author):
                del n_fc.mod_list[ctx.guild.id]
                await ctx.reply("設定完了",embed=nextcord.Embed(title="荒らし対策",description=f"設定を削除しました。", color=0x00ff00))
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000))
                return
        elif ctx.message.content == "n!mod debug":
            if ctx.author.id in n_fc.py_admin:
                await ctx.reply(f"messageCounter: `{counter.messageCounter}`\nmod_list: `{n_fc.mod_list}`\nmod_check: `{counter.messageCounter[ctx.author.id] >= n_fc.mod_list[ctx.guild.id]['counter']}`\nlast reset: `{reset_time}`")
                return
        else:
            if ctx.guild.id not in n_fc.mod_list:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="サーバーで機能は`無効`になっています。\n\n・機能の有効化\n`n!mod on [規定メッセージ数] [付与するロール]`\n\n・機能の無効化\n`n!mod off`", color=0x00ff00))
            else:
                counter = n_fc.mod_list[ctx.guild.id]["counter"]
                role = n_fc.mod_list[ctx.guild.id]["role"]
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description=f"サーバーで機能は`有効`になっています。\nメッセージカウンター:`{counter}`\nミュート用ロール:<@&{role}>\n\n・機能の有効化\n`n!mod on [規定メッセージ数] [付与するロール]`\n\n・機能の無効化\n`n!mod off`", color=0x00ff00))
            return


    @nextcord.slash_command(name="mod", description="荒らし対策機能の設定を変更します。", guild_ids=n_fc.GUILD_IDS)
    async def mod_slash(self, interaction: Interaction):
        pass


    @mod_slash.subcommand(name="on", description="荒らし対策機能を有効にします。")
    async def on_slash(
        self,
        interaction: Interaction,
        counter: int = SlashOption(
            name="counter",
            description="規定するメッセージ数",
            required=True
        ),
        role: nextcord.Role = SlashOption(
            name="role",
            description="付与するロール",
            required=True
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if role.name == "@everyone":
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="@everyoneは指定できません。", color=0xff0000), ephemeral=True)
                return
            try:
                n_fc.mod_list[interaction.guild.id] = {"counter": counter, "role": role.id}
                save()
            except BaseException as err:
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description=f"エラーが発生しました。\n```\n{err}```", color=0xff0000), ephemeral=True)
                return
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description=f"サーバーで機能を有効にしました。\nメッセージカウンター:`{counter}`\nミュート用ロール:<@&{role.id}>", color=0x00ff00), ephemeral=True)
            return
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="あなたは管理者ではありません。", color=0xff0000), ephemeral=True)
            return


    @mod_slash.subcommand(name="off", description="荒らし対策機能を無効にします。")
    async def off_slash(
        self,
        interaction: Interaction
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in n_fc.mod_list:
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="サーバーで機能は既に`無効`になっています。", color=0xff0000), ephemeral=True)
                return
            else:
                try:
                    del n_fc.mod_list[interaction.guild.id]
                    save()
                except BaseException as err:
                    await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description=f"エラーが発生しました。\n```\n{err}```", color=0xff0000), ephemeral=True)
                    return
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="サーバーで機能を無効にしました。", color=0x00ff00), ephemeral=True)
                return
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="あなたは管理者ではありません。", color=0xff0000), ephemeral=True)
            return


    @mod_slash.subcommand(name="status", description="荒らし対策機能の状態を確認します。")
    async def status_slash(
        self,
        interaction: Interaction
    ):
        if interaction.guild.id not in n_fc.mod_list:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description="サーバーで機能は`無効`になっています。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策",description=f"サーバーで機能は`有効`になっています。\nメッセージカウンター:`{n_fc.mod_list[interaction.guild.id]['counter']}`\nミュート用ロール:<@&{n_fc.mod_list[interaction.guild.id]['role']}>", color=0x00ff00), ephemeral=True)
        return

def setup(bot):
    bot.loop.create_task(counterReset())
    bot.add_cog(mod(bot))
