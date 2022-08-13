import asyncio
import logging
import datetime
import sys

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks

from util import admin_check, n_fc, eh, database
from util.nira import NIRA

# 規定秒数以内に指定数メッセージを送信した人をミュートするモデレーター的な機能
# n!mod
# /mod

reset_time = ""

class mod_list:
    name = "mod_data"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

class counter:
    messageCounter = {}


class mod(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        asyncio.ensure_future(database.default_pull(self.bot.client, mod_list))
        self.counter_reset.start()

    def cog_unload(self):
        self.counter_reset.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.author.bot:
            return
        if message.guild.id not in mod_list.value:
            return
        if message.author.id not in counter.messageCounter:
            counter.messageCounter[message.author.id] = 0
        counter.messageCounter[message.author.id] = counter.messageCounter[message.author.id] + 1
        if counter.messageCounter[message.author.id] > mod_list.value[message.guild.id]["counter"] - 3 and counter.messageCounter[message.author.id] < mod_list.value[message.guild.id]["counter"]:
            await message.channel.send(f"{message.author.mention}\nメッセージ送信数が多いです。あまり多いとミュートされます。")
            return
        if counter.messageCounter[message.author.id] >= mod_list.value[message.guild.id]["counter"]:
            try:
                if mod_list.value[message.guild.id]["remove_role"]:
                    await message.author.remove_roles(*message.author.roles[1:], reason="にらBOTの荒らし対策機能")
                role = message.guild.get_role(mod_list.value[message.guild.id]["role"])
                await message.author.add_roles(role, reason="にらBOTの荒らし対策機能")
                await message.channel.send(f"{message.author.mention}は、メッセージ数が規定オーバーのため、ミュート用ロールを付与しました。\n{(lambda x: 'なお、ミュート用ロール以外の全ロールを剥奪しました。' if x else '')(mod_list.value[message.guild.id]['remove_role'])}")
                return
            except Exception as err:
                await message.channel.send(f"{message.author.name}をミュートしようとしましたがエラーが発生しました。\n```sh\n{err}```")
                logging.error(err, exc_info=True)
                return


    @commands.command(name="mod", help="""\
一定期間以内に特定のメッセージ数以上のメッセージを送った人をミュートします。

20秒間に指定された回数以上しゃべった人に対してロールの付与・剥奪を行います。

`n!mod on [counter] [role] [*remove]`
`n!mod off`

counter: メッセージ数
role: ロールの名前またはID
remove: ロールの剥奪を行うかどうか（`on`/`off`）（指定されない場合は無効です。）

・例
`n!mod on 10 mute on`
`n!mod on 5 892759276152573953`
`n!mod off`
""")
    async def mod(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 4)
        if len(args) == 1:
            if ctx.guild.id not in mod_list.value:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description=f"サーバーで機能は`無効`になっています。\n\n・機能の有効化\n`{self.bot.command_prefix}mod on [規定メッセージ数] [付与するロール]`\n\n・機能の無効化\n`{self.bot.command_prefix}mod off`", color=0x00ff00))
            else:
                counter = mod_list.value[ctx.guild.id]["counter"]
                role = mod_list.value[ctx.guild.id]["role"]
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description=f"サーバーで機能は`有効`になっています。\nメッセージカウンター:`{counter}`\nミュート用ロール:<@&{role}>\n\n・機能の有効化\n`n!mod on [規定メッセージ数] [付与するロール]`\n\n・機能の無効化\n`{self.bot.command_prefix}mod off`", color=0x00ff00))
        elif args[1] == "off":
            if admin_check.admin_check(ctx.guild, ctx.author):
                del mod_list.value[ctx.guild.id]
                await database.default_push(self.bot.client, mod_list)
                await ctx.reply("設定完了", embed=nextcord.Embed(title="荒らし対策", description=f"設定を削除しました。", color=0x00ff00))
            else:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000))
        elif len(args) >= 2 and len(args) <= 3:
            await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description=f"引数が足りません。\n`{self.bot.command_prefix}mod on [counter] [role] [*remove]`\n`{self.bot.command_prefix}mod off`\n`{self.bot.command_prefix}help mod`", color=0xff0000))
        elif args[1] == "on":
            if admin_check.admin_check(ctx.guild, ctx.author):
                remove = False
                if len(args) == 5:
                    if args[4] in n_fc.on_ali:
                        remove = True
                    elif args[4] in n_fc.off_ali:
                        remove = False
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description=f"引数が正しくありません。\n`{self.bot.command_prefix}mod on [counter] [role] [*remove]`\n`{self.bot.command_prefix}mod off`\n`{self.bot.command_prefix}help mod`", color=0xff0000))
                        return
                role_id = None
                try:
                    role_id = int(args[3])
                except ValueError:
                    roles = ctx.guild.roles
                    for i in range(len(roles)):
                        if roles[i].name == args[3]:
                            role_id = roles[i].id
                            break
                    if role_id == None:
                        await ctx.reply("ロールが見つかりませんでした。")
                        return
                if role_id == ctx.guild.id:
                    await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="@everyoneは使用できません。", color=0xff0000))
                    return
                mod_list.value[ctx.guild.id] = {
                    "counter": int(args[2]), "role": role_id, "remove_role": remove}
                await database.default_push(self.bot.client, mod_list)
                await ctx.reply(f"設定完了", embed=nextcord.Embed(title="荒らし対策", description=f"メッセージカウンター:`{args[2]}`\nミュート用ロール:<@&{role_id}>\n付与されてたロールの剥奪:{remove}", color=0x00ff00))
            else:
                await ctx.reply(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000))
        elif ctx.message.content == f"{self.bot.command_prefix}mod debug":
            if (await self.bot.is_owner(ctx.author)):
                await ctx.reply(f"messageCounter: `{counter.messageCounter}`\nmod_list: `{mod_list.value}`\nmod_check: `{counter.messageCounter[ctx.author.id] >= mod_list.value[ctx.guild.id]['counter']}`\nlast reset: `{reset_time}`")


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
        ),
        remove_role: bool = SlashOption(
            name="remove_role",
            description="付与されている全てのロールを剥奪するかどうか",
            required=False,
            default=0
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if role.id == interaction.guild.id:
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="@everyoneは指定できません。", color=0xff0000), ephemeral=True)
                return
            try:
                mod_list.value[interaction.guild.id] = {
                    "counter": counter,
                    "role": role.id,
                    "remove_role": remove_role
                }
                await database.default_push(self.bot.client, mod_list)
            except Exception as err:
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description=f"エラーが発生しました。\n```\n{err}```", color=0xff0000), ephemeral=True)
                return
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description=f"サーバーで機能を有効にしました。\nメッセージカウンター:`{counter}`\nミュート用ロール:<@&{role.id}>\nロールを剥奪するか:{remove_role}", color=0x00ff00), ephemeral=True)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000), ephemeral=True)

    @mod_slash.subcommand(name="off", description="荒らし対策機能を無効にします。")
    async def off_slash(
        self,
        interaction: Interaction
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in mod_list.value:
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="サーバーで機能は既に`無効`になっています。", color=0xff0000), ephemeral=True)
            else:
                try:
                    del mod_list.value[interaction.guild.id]
                    await database.default_push(self.bot.client, mod_list)
                except Exception as err:
                    await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description=f"エラーが発生しました。\n```\n{err}```", color=0xff0000), ephemeral=True)
                    return
                await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="サーバーで機能を無効にしました。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="あなたは管理者ではありません。", color=0xff0000), ephemeral=True)


    @mod_slash.subcommand(name="status", description="荒らし対策機能の状態を確認します。")
    async def status_slash(
        self,
        interaction: Interaction
    ):
        if interaction.guild.id not in mod_list.value:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description="サーバーで機能は`無効`になっています。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="荒らし対策", description=f"サーバーで機能は`有効`になっています。\nメッセージカウンター:`{mod_list.value[interaction.guild.id]['counter']}`\nミュート用ロール:<@&{mod_list.value[interaction.guild.id]['role']}>", color=0x00ff00), ephemeral=True)


    @tasks.loop(seconds=20.0)
    async def counter_reset(self):
        counter.messageCounter = {}


def setup(bot, **kwargs):
    bot.add_cog(mod(bot, **kwargs))
