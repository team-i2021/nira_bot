import math
import os
import sys

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import admin_check, n_fc, eh, web_api, slash_tool, database
from util.nira import NIRA

DIR = sys.path[0]

SET, DEL, STATUS = (0, 1, 2)
AR, ER, NR = ("all_reaction_list", "ex_reaction_list", "reaction_bool_list")

# 通常反応や追加反応の反応系

class reaction_datas:
    class all_reaction_list:
        name = "all_reaction_list"
        value = {}
        default = {}
        value_type = database.CHANNEL_VALUE

    class ex_reaction_list:
        name = "ex_reaction_list"
        value = {}
        default = {}
        value_type = database.CHANNEL_VALUE

    class reaction_bool_list:
        name = "reaction_bool_list"
        value = {}
        default = {}
        value_type = database.CHANNEL_VALUE


class notify_token:
    name = "notify_token"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


def changeSetting(
    ActionType: int,
    FunctionName: str,
    interaction: Interaction or commands.Context,
    **kwargs: dict
):
    """kwargs = {"key": key:str, "value": value:str}"""
    if ActionType == SET:
        try:
            getattr(reaction_datas, FunctionName).value[interaction.guild.id][kwargs["key"]] = kwargs["value"]
            return True
        except Exception as err:
            return [False, err]
    elif ActionType == DEL:
        try:
            del getattr(reaction_datas, FunctionName).value[interaction.guild.id][kwargs["key"]]
            return True
        except Exception as err:
            return [False, err]
    elif ActionType == STATUS:
        try:
            return getattr(reaction_datas, FunctionName).value[interaction.guild.id][kwargs["key"]]
        except Exception as err:
            return [False, err]


class NotifyTokenSet(nextcord.ui.Modal):
    def __init__(self, client: HTTP_db.Client):
        super().__init__(
            "LINE Notify設定",
            timeout=None
        )

        self.client = client

        self.token = nextcord.ui.TextInput(
            label="LINE Notify TOKEN",
            style=nextcord.TextInputStyle.short,
            placeholder="トークンを入力してください",
            required=True
        )
        self.add_item(self.token)
        #self.add_item(nextcord.ui.Button("トークンを設定する", style=nextcord.ButtonStyle.green, custom_id="token_set"))
        #self.add_item(nextcord.ui.Button("キャンセル", style=nextcord.ButtonStyle.red, custom_id="cancel"))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        await database.default_pull(self.client, notify_token)
        if self.token.value == "" or self.token.value is None:
            await interaction.send("トークンは必須です。", ephemeral=True)
            return
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral=True)
        else:
            token_result = web_api.line_token_check(self.token.value)
            if token_result[0] == False:
                await interaction.send(f"そのトークンは無効なようです。\n```sh\n{token_result[1]}```", ephemeral=True)
                return
            if interaction.guild.id not in notify_token.value:
                notify_token.value[interaction.guild.id] = {interaction.channel.id: self.token.value}
            else:
                notify_token.value[interaction.guild.id][interaction.channel.id] = self.token.value
            await database.default_push(self.client, notify_token)
            await interaction.send(f"{interaction.guild.name}/{interaction.channel.name}で`{self.token.value}`を保存します。\nトークンが他のユーザーに見られないようにしてください。", ephemeral=True)


class reaction(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.er_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["ex_reaction"]

    @commands.has_permissions(manage_guild=True)
    @commands.group(name="er", help="""\
追加で新しいにらの反応を作り出すことが出来ます。
オートリプライとかって呼ばれるんですかね？まぁ、トリガーとリターンを指定することで、トリガーが送信された際に指定したリターンを送信することが出来ます。
トリガーには正規表現を使うことが出来ます。が、スペースを含むことはできませんのでご了承ください。

`n!er add [トリガー] [返信文] [メンション]`で追加できます。
`n!er del [トリガー]`で削除できます。
`n!er list`でリストを表示できます。
`n!er edit [トリガー] [新反応]`でトリガーを編集できます。
""")
    async def er_command(self, ctx):
        pass

    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="add")
    async def er_add(self, ctx: commands.Context, trigger: str | None = None, return_text: str | None = None, mention: str = "False"):
        if trigger is None or return_text is None:
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er add [トリガー] [返信文] [メンション(True/False)]```")
        else:
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if mention in n_fc.on_ali:
                mention = True
            elif mention in n_fc.off_ali:
                mention = False
            else:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"返信に対するメンションの指定が不正です。\n`yes`や`True`又は、`off`や`False`で指定してください。", color=0xff0000))
                return
            await self.er_collection.update_one({"guild_id": ctx.guild.id, "trigger": trigger}, {"$set": {"return": return_text, "mention": mention}}, upsert=True)
            await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を追加しました。\nメンションは{'有効' if mention else '無効'}です。", color=0x00ff00))

    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="del")
    async def er_del(self, ctx: commands.Context, trigger: str | None = None):
        if trigger is None:
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er del [トリガー]```")
        else:
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if trigger == "all":
                await self.er_collection.delete_many({"guild_id": ctx.guild.id})
                await ctx.reply(embed=nextcord.Embed(title="Success", description=f"全てのトリガーを削除しました。", color=0x00ff00))
            else:
                delete_status = await self.er_collection.delete_one({"guild_id": ctx.guild.id, "trigger": trigger})
                if delete_status.deleted_count == 1:
                    await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を削除しました。", color=0x00ff00))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="Error", description=f"トリガー`{trigger}`は存在しませんでした。", color=0xff0000))

    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="list")
    async def er_list(self, ctx: commands.Context):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return
        er_list: list = await self.er_collection.find({"guild_id": ctx.guild.id}).to_list(length=None)
        if len(er_list) == 0:
            await ctx.reply(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しません。", color=0xff0000))
            return
        embed = nextcord.Embed(title="追加反応リスト", description=f"追加反応のリストです。", color=0x00ff00)
        for er in er_list:
            embed.add_field(name=er["trigger"], value=f"- 返信文\n{er['return']}\n\n- メンション\n{'有効' if er['mention'] else '無効'}", inline=False)
        await ctx.author.send(embed=embed)

    @commands.has_permissions(manage_guild=True)
    @er_command.command(name="edit")
    async def er_edit(self, ctx: commands.Context, trigger: str | None = None, return_text: str | None = None):
        if trigger is None or return_text is None:
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er edit [トリガー] [新反応]```")
        else:
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            update_result = await self.er_collection.update_one({"guild_id": ctx.guild.id, "trigger": trigger}, {"$set": {"return": return_text}})
            if update_result.modified_count == 0:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"トリガー`{trigger}`は存在しませんでした。", color=0xff0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を編集しました。", color=0x00ff00))


    @application_checks.has_permissions(manage_guild=True)
    @nextcord.slash_command(name="er", description="Extended Reaction Setting", guild_ids=n_fc.GUILD_IDS)
    async def er_slash(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(name="add", description="Add Extended Reaction Setting", description_localizations={nextcord.Locale.ja: "追加反応の設定追加"})
    async def add_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={
                nextcord.Locale.ja: "トリガーメッセージ"
            },
            description="Trigger message",
            description_localizations={
                nextcord.Locale.ja: "反応する部分です"
            },
            required=True
        ),
        returnMessage: str = SlashOption(
            name="return_message",
            name_localizations={
                nextcord.Locale.ja: "返信メッセージ"
            },
            description="Return message",
            description_localizations={
                nextcord.Locale.ja: "返信するメッセージ内容です"
            },
            required=True
        ),
        mention: bool = SlashOption(
            name="mention",
            name_localizations={
                nextcord.Locale.ja: "メンション"
            },
            description="Mention",
            description_localizations={
                nextcord.Locale.ja: "メンションするかどうかです"
            },
            required=False,
            choices={
                "True": True,
                "False": False
            },
            choice_localizations={
                nextcord.Locale.ja: {
                    "有効": True,
                    "無効": False
                }
            },
            default=False
        )
    ):
        await interaction.response.defer(ephemeral=True)
        if admin_check.admin_check(interaction.guild, interaction.user):
            await self.er_collection.update_one({"guild_id": interaction.guild.id, "trigger": triggerMessage}, {"$set": {"return": returnMessage, "mention": mention}}, upsert=True)
            await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応を追加しました。", color=0x00ff00))
        else:
            raise NIRA.Forbidden()


    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(name="list", description="List of Extended Reaction List", description_localizations={nextcord.Locale.ja: "追加反応の一覧"})
    async def list_er_slash(self, interaction: Interaction):
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
            return
        await interaction.response.defer(ephemeral=True)
        er_list: list = await self.er_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
        if len(er_list) == 0:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しません。", color=0xff0000), ephemeral=True)
            return
        embed = nextcord.Embed(title="追加反応リスト", description=f"追加反応のリストです。", color=0x00ff00)
        for er in er_list:
            embed.add_field(name=er["trigger"], value=f"- 返信文\n{er['return']}\n\n- メンション\n{'有効' if er['mention'] else '無効'}", inline=False)
        await interaction.user.send(embed=embed)
        await interaction.send("DMに送信しました。", ephemeral=True)


    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(name="del", description="Delete Extended Reaction Setting", description_localizations={nextcord.Locale.ja: "追加反応の削除"})
    async def del_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={
                nextcord.Locale.ja: "トリガーメッセージ"
            },
            description="Trigger message. (if you want to delete all, please input 'all')",
            description_localizations={
                nextcord.Locale.ja: "トリガー。「all」と入力するとすべての反応を削除します。"
            },
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        if triggerMessage == "all":
            await self.er_collection.delete_many({"guild_id": interaction.guild.id})
            await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応をすべて削除しました。", color=0x00ff00))
        else:
            delete_result = await self.er_collection.delete_one({"guild_id": interaction.guild.id, "trigger": triggerMessage})
            if delete_result.deleted_count == 0:
                await interaction.followup.send(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しませんでした。", color=0xff0000))
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応を削除しました。", color=0x00ff00))


    @application_checks.has_permissions(manage_guild=True)
    @er_slash.subcommand(name="edit", description="Edit Extended Reaction Setting", description_localizations={nextcord.Locale.ja: "追加反応の編集"})
    async def edit_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            name_localizations={
                nextcord.Locale.ja: "トリガーメッセージ"
            },
            description="Trigger message",
            description_localizations={
                nextcord.Locale.ja: "反応する部分です"
            },
            required=True
        ),
        returnMessage: str = SlashOption(
            name="return_message",
            name_localizations={
                nextcord.Locale.ja: "返信メッセージ"
            },
            description="Return message",
            description_localizations={
                nextcord.Locale.ja: "返信するメッセージ内容です"
            },
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        edit_result = await self.er_collection.update_one({"guild_id": interaction.guild.id, "trigger": triggerMessage}, {"$set": {"return": returnMessage}})
        if edit_result.modified_count == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しませんでした。", color=0xff0000))
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応を編集しました。", color=0x00ff00))


    @commands.command(name="nr", help="""\
にらBOTの通常反応（にらとか）を無効にしたりすることが出来ます。
`n!nr`:今の状態を表示
`n!nr off`:通常反応を無効化
`n!nr on`:通常反応を有効化
`n!nr all off`:通常反応を**サーバーで**無効化
`n!nr all on`:通常反応を**サーバーで**有効化""")
    async def nr(self, ctx: commands.Context):
        try:
            await database.default_pull(self.bot.client, reaction_datas.reaction_bool_list)
            if ctx.guild.id not in reaction_datas.reaction_bool_list.value:  # 通常反応のブール値存在チェック
                reaction_datas.reaction_bool_list.value[ctx.guild.id] = {}
                reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] = 1
                reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 1
                await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
            if ctx.channel.id not in reaction_datas.reaction_bool_list.value[ctx.guild.id]:
                reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] = 1
                await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
            if ctx.message.content == f"{self.bot.command_prefix}nr":
                if reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] == 0:
                    setting = f"サーバーで無効になっている為、チャンネルごとの設定は無効です。\n(`{self.bot.command_prefix}help nr`でご確認ください。)"
                elif reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] == 1:
                    setting = "有効"
                elif reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
                await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`{self.bot.command_prefix}nr [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.guild, ctx.author):
                nr_setting = str((ctx.message.content).split(" ", 1)[1])
                if nr_setting in n_fc.on_ali:
                    reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] = 1
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を有効にしました。", color=0x00ff00))
                elif nr_setting in n_fc.off_ali:
                    reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.channel.id] = 0
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を無効にしました。", color=0x00ff00))
                elif nr_setting[:3] == "all":
                    if nr_setting in n_fc.on_ali:
                        reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 1
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を有効にしました。", color=0x00ff00))
                    elif nr_setting in n_fc.off_ali:
                        reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 0
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を無効にしました。", color=0x00ff00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"コマンド使用方法:`{self.bot.command_prefix}nr [all] [on/off]`", color=0xff0000))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`{self.bot.command_prefix}nr [all] [on/off]`", color=0xff0000))
                await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except Exception as err:
            await ctx.reply(embed=eh.eh(self.bot.client, err))
            return


    @nextcord.slash_command(name="nr", description="Normal Reaction Setting", guild_ids=n_fc.GUILD_IDS)
    async def nr_slash(self, interaction):
        pass


    @nr_slash.subcommand(name="channel", description="Setting of Normal Reaction in Channel", description_localizations={nextcord.Locale.ja: "チャンネルでの通常反応設定"})
    async def channel_nr_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            name_localizations={
                nextcord.Locale.ja: "設定"
            },
            description="Value of Setting Normal Reaction in Channel",
            description_localizations={
                nextcord.Locale.ja: "チャンネルでの通常設定の有効化/無効化"
            },
            choices={"Enable": 1, "Disable": 0},
            choice_localizations={
                nextcord.Locale.ja: {"有効": 1, "無効": 0}
            }
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await database.default_pull(self.bot.client, reaction_datas.reaction_bool_list)
            if interaction.guild.id not in reaction_datas.reaction_bool_list.value:
                reaction_datas.reaction_bool_list.value[interaction.guild.id] = {interaction.channel.id: setting}
            else:
                reaction_datas.reaction_bool_list.value[interaction.guild.id][interaction.channel.id] = setting
            await interaction.send(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"チャンネル <#{interaction.channel.id}> での通常反応を変更しました。", color=0x00ff00), ephemeral=True)
            await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
        else:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
            return


    @nr_slash.subcommand(name="server", description="Setting of Normal Reaction in Server", description_localizations={nextcord.Locale.ja: "サーバーでの通常反応設定"})
    async def server_nr_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            name_localizations={
                nextcord.Locale.ja: "設定"
            },
            description="Value of Setting Normal Reaction in Server",
            description_localizations={
                nextcord.Locale.ja: "サーバーでの通常設定の有効化/無効化"
            },
            choices={"Enable": 1, "Disable": 0},
            choice_localizations={
                nextcord.Locale.ja: {"有効": 1, "無効": 0}
            }
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await database.default_pull(self.bot.client, reaction_datas.reaction_bool_list)
            if interaction.guild.id not in reaction_datas.reaction_bool_list.value:
                reaction_datas.reaction_bool_list.value[interaction.guild.id] = {
                    "all": setting, interaction.channel.id: 1}
            else:
                reaction_datas.reaction_bool_list.value[interaction.guild.id]["all"] = setting
            await interaction.send(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"サーバー `{interaction.guild.name}` での通常反応を変更しました。", color=0x00ff00), ephemeral=True)
            await database.default_push(self.bot.client, reaction_datas.reaction_bool_list)
        else:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
            return


    @commands.command(name="ar", help="""\
にらBOTの通常反応及び追加反応(Bump通知および`n!`コマンド以外のすべて)を無効にしたりすることが出来ます。
`n!ar`:今の状態を表示
`n!ar off`:全反応を無効化
`n!ar on`:全反応を有効化

チャンネルトピックに`nira-off`と入れておくと、そのチャンネルでは反応を無効化します。""")
    async def ar(self, ctx: commands.Context):
        try:
            await database.default_pull(self.bot.client, reaction_datas.all_reaction_list)
            if ctx.guild.id not in reaction_datas.all_reaction_list.value:
                print(reaction_datas.all_reaction_list.value)
                reaction_datas.all_reaction_list.value[ctx.guild.id] = {}
            if ctx.channel.id not in reaction_datas.all_reaction_list.value[ctx.guild.id]:
                reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.channel.id] = 1
            if ctx.message.content == f"{self.bot.command_prefix}ar":
                if reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.channel.id] == 1:
                    setting = "有効"
                elif reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await database.default_push(self.bot.client, reaction_datas.all_reaction_list)
                await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description=f"「通常反応」及び「追加反応」（Bump通知および各種コマンドは除く）の設定:{setting}\n\n`{self.bot.command_prefix}ar [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.guild, ctx.author):
                ar_setting = str((ctx.message.content).split(" ", 1)[1])
                if ar_setting in n_fc.on_ali:
                    reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.channel.id] = 1
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を有効にしました。", color=0x00ff00))
                elif ar_setting in n_fc.off_ali:
                    reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.channel.id] = 0
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を無効にしました。", color=0x00ff00))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description=f"コマンド使用方法:`{self.bot.command_prefix}ar [all] [on/off]`", color=0xff0000))
                await database.default_push(self.bot.client, reaction_datas.all_reaction_list)
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except Exception as err:
            await ctx.reply(embed=eh.eh(self.bot.client, err))
            return


    @nextcord.slash_command(name="ar", description="チャンネル全体反応設定", guild_ids=n_fc.GUILD_IDS)
    async def ar_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            name_localizations={
                nextcord.Locale.ja: "設定"
            },
            description="Value of Setting All Reaction in Channel",
            description_localizations={
                nextcord.Locale.ja: "チャンネルでの全体設定の有効化/無効化"
            },
            choices={"Enable": 1, "Disable": 0},
            choice_localizations={
                nextcord.Locale.ja: {"有効": 1, "無効": 0}
            }
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.response.defer(ephemeral=True)
            await database.default_pull(self.bot.client, reaction_datas.all_reaction_list)
            if interaction.guild.id not in reaction_datas.all_reaction_list.value:
                reaction_datas.all_reaction_list.value[interaction.guild.id] = {interaction.channel.id: setting}
            else:
                reaction_datas.all_reaction_list.value[interaction.guild.id][interaction.channel.id] = setting
            await database.default_push(self.bot.client, reaction_datas.all_reaction_list)
            await interaction.send(embed=nextcord.Embed(title="All Reaction Setting", description=f"チャンネル <#{interaction.channel.id}> での全体反応を変更しました。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)


    @commands.command(name="line", help="""\
DiscordのメッセージをLINEに送信します。
LINE Notifyという機能を用いて、DiscordのメッセージをLINEに送信します。""")
    async def line(self, ctx: commands.Context):
        embed = nextcord.Embed(title="DiscordのメッセージをLINEに送信する機能", description="使い方", color=0x00ff00)
        embed.add_field(name="**このコマンドはスラッシュコマンドです**", value="""\
`/line set`というスラッシュコマンドを送ると、TOKENを入力する画面が表示されるので、そこにTOKENを入力してください。
ちなみにTOKENの流出はとんでもないことにつながるので、気をつけてください。""", inline=False)
        embed.add_field(name="**TOKENって何？**", value="""\
TOKENとは簡単に言えばパスワードです。LINE Notifyのページから発行してきてください。
[TOKENの発行方法](https://qiita.com/nattyan_tv/items/33ac7a7269fe12e49198)""", inline=False)
        await ctx.reply(embed=embed)


    # 今だけGuild指定しない...
    @nextcord.slash_command(name="line", description="Setting of Line Notify")
    async def line_slash(self, interaction: Interaction):
        pass


    @line_slash.subcommand(name="set", description="Set LINE Notify's TOKEN", description_localizations={nextcord.Locale.ja: "LINE Notifyのトークンを設定します。"})
    async def line_set_slash(self, interaction: Interaction):
        modal = NotifyTokenSet()
        await interaction.response.send_modal(modal=modal)


    @line_slash.subcommand(name="del", description="Delete LINE Notify's TOKEN", description_localizations={nextcord.Locale.ja: "LINE Notifyのトークンを削除します。"})
    async def line_del_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral=True)
        else:
            await database.default_pull(self.bot.client, notify_token)
            if interaction.guild.id not in notify_token.value:
                await interaction.send(f"{interaction.guild.name}では、LINEトークンが設定されていません。", ephemeral=True)
                return
            if interaction.channel.id not in notify_token.value[interaction.guild.id]:
                await interaction.send(f"{interaction.channel.name}では、LINEトークンが設定されていません。", ephemeral=True)
                return
            del notify_token.value[interaction.guild.id][interaction.channel.id]
            await database.default_push(self.bot.client, notify_token)
            await interaction.send(f"{interaction.channel.name}でのLINEトークンを削除しました。", ephemeral=True)


def setup(bot, **kwargs):
    bot.add_cog(reaction(bot, **kwargs))
