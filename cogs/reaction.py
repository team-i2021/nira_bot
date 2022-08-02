import math
import os
import pickle
import sys

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import admin_check, n_fc, eh, web_api, slash_tool, database

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

async def changeSetting(
    client: HTTP_db.Client,
    ActionType: int,
    FunctionName: str,
    interaction: Interaction or commands.Context,
    **kwargs: dict
):
    """kwargs = {"key": key:str, "value": value:str}"""
    if ActionType == SET:
        try:
            getattr(reaction_datas, FunctionName)[interaction.guild.id][kwargs["key"]] = kwargs["value"]
            await database.default_push(client, getattr(reaction_datas, FunctionName))
            return True
        except BaseException as err:
            return [False, err]
    elif ActionType == DEL:
        try:
            del getattr(reaction_datas, FunctionName)[interaction.guild.id][kwargs["key"]]
            await database.default_push(client, getattr(reaction_datas, FunctionName))
            return True
        except BaseException as err:
            return [False, err]
    elif ActionType == STATUS:
        try:
            return getattr(reaction_datas, FunctionName)[interaction.guild.id][kwargs["key"]]
        except BaseException as err:
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
        if self.token.value == "" or self.token.value is None:
            await interaction.send("トークンは必須です。", ephemeral=True)
            return
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral=True)
        else:
            token_result = web_api.line_token_check(self.token.value)
            if token_result[0] == False:
                await interaction.send(f"そのトークンは無効なようです。\n```{token_result[1]}```", ephemeral=True)
                return
            if interaction.guild.id not in notify_token.value:
                notify_token.value[interaction.guild.id] = {interaction.channel.id: self.token.value}
            else:
                notify_token.value[interaction.guild.id][interaction.channel.id] = self.token.value
            await database.default_push(self.client, notify_token)
            await interaction.send(f"{interaction.guild.name}/{interaction.channel.name}で`{self.token.value}`を保存します。\nトークンが他のユーザーに見られないようにしてください。", ephemeral=True)


class reaction(commands.Cog):
    def __init__(self, bot: commands.Bot, client: HTTP_db.Client):
        self.bot = bot
        self.client = client

    @commands.command(name="er", help="""\
追加で新しいにらの反応を作り出すことが出来ます。
オートリプライとかって呼ばれるんですかね？まぁ、トリガーとリターンを指定することで、トリガーが送信された際に指定したリターンを送信することが出来ます。
トリガーには正規表現を使うことが出来ます。が、スペースを含むことはできませんのでご了承ください。""")
    async def er(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 3)
        if args[1] == "add":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if  len(args) == 2:
                await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er add [トリガー] [返信文]```")
                return
            try:
                if ctx.guild.id not in reaction_datas.ex_reaction_list.value:
                    reaction_datas.ex_reaction_list.value[ctx.guild.id] = {"value": 0}
                value = int(changeSetting(STATUS, ER, ctx, key="value"))
                ra = ctx.message.content[9:].split(" ", 1)
                react_trigger = ra[0]
                react_return = ra[1]
                changeSetting(SET, ER, ctx, key="value", value=value+1)
                changeSetting(SET, ER, ctx, key=f'{value+1}_tr', value=str(react_trigger))
                changeSetting(SET, ER, ctx, key=f'{value+1}_re', value=str(react_return))
                await ctx.reply(f"トリガー：{ra[0]}\nリターン：{ra[1]}")
                return
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
        elif args[1] == "list":
            if ctx.guild.id not in reaction_datas.ex_reaction_list.value or changeSetting(STATUS, ER, ctx, key="value") == 0:
                await ctx.reply("追加返答は設定されていません。")
                return
            else:
                embed = nextcord.Embed(title="追加返答リスト", description="- にらBOT", color=0x00ff00)
                for i in range(int(changeSetting(STATUS, ER, ctx, key="value"))):
                    embed.add_field(name=f"トリガー：{changeSetting(STATUS, ER, ctx, key=f'{i+1}_tr')}",
                                    value=f"リターン：{changeSetting(STATUS, ER, ctx, key=f'{i+1}_re')}",
                                    inline=False)
                await ctx.reply(embed=embed)
                return
        elif args[1] == "edit":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if len(args) != 4:
                await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er edit [トリガー] [返信文]```")
                return
            if ctx.guild.id not in reaction_datas.ex_reaction_list.value:
                await ctx.reply("追加反応は登録されていません。")
                return
            if changeSetting(STATUS, ER, ctx, key="value") == 0:
                await ctx.reply("追加反応は登録されていません。")
                return
            b_tr = args[2]
            b_re = args[3]
            try:
                rt_e = False
                for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[ctx.guild.id])-1)/2)):
                    if changeSetting(STATUS, ER, ctx, key=f"{i+1}_tr") == b_tr:
                        changeSetting(SET, ER, ctx, key=f"{i+1}_re", value=b_re)
                        rt_e = True
                        break
                if rt_e:
                    await ctx.reply(f"トリガー:{b_tr}\nリターン:{b_re}")
                else:
                    await ctx.reply("そのトリガーは登録されていません！")
                return
            except Exception as err:
                await ctx.reply(embed=eh.eh(err))
                return
        elif args[1] == "del":
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if ctx.guild.id not in reaction_datas.ex_reaction_list.value:
                await ctx.reply("追加返答は設定されていません。")
                return
            else:
                if len(args) != 3:
                    await ctx.reply("コマンドの引数が足りません。\n全削除:`n!er del all`\n特定の返答を削除:`n!er del [トリガー]`")
                    return
                elif args[2] == "all":
                    del reaction_datas.ex_reaction_list.value[ctx.guild.id]
                    await database.default_push(self.client, reaction_datas.ex_reaction_list)
                    await ctx.reply(f"`{ctx.guild.name}`での追加反応の設定を削除しました。")
                    return
                else:
                    result = None
                    trigger = args[2]
                    for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[ctx.guild.id])-1)/2)):
                        if changeSetting(STATUS, ER, ctx, key=f"{i+1}_tr") == trigger:
                            result = i
                            break
                        continue
                    if result == None:
                        await ctx.reply(f"`{trigger}`というトリガーが見つかりませんでした。\n不具合がある場合は全消しするか、サポートサーバーへご連絡ください。")
                        return
                    for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[ctx.guild.id])-1)/2)-(result+1)):
                        for suf in ("tr", "re"):
                            changeSetting(SET, ER, ctx,
                                          key=f"{result+i+1}_{suf}",
                                          value=changeSetting(STATUS, ER, ctx, key=f"{result+i+2}_{suf}"))
                    for i in ("tr", "re"):
                        del reaction_datas.ex_reaction_list.value[ctx.guild.id][f"{reaction_datas.ex_reaction_list.value[ctx.guild.id]['value']}_{i}"]
                    reaction_datas.ex_reaction_list.value[ctx.guild.id]["value"] -= 1
                    await database.default_push(self.client, reaction_datas.ex_reaction_list)
                    await ctx.reply(f"`{trigger}`を削除しました。")
                    return
        return

    @nextcord.slash_command(name="er", description="追加反応設定", guild_ids=n_fc.GUILD_IDS)
    async def er_slash(self, interaction: Interaction):
        pass

    @er_slash.subcommand(name="add", description="追加反応の設定追加")
    async def add_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            description="トリガー",
            required=True
        ),
        returnMessage: str = SlashOption(
            name="return_message",
            description="返答文",
            required=True
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            try:
                if interaction.guild.id not in reaction_datas.ex_reaction_list.value:
                    reaction_datas.ex_reaction_list.value[interaction.guild.id] = {"value": 0}
                value = int(changeSetting(STATUS, ER, interaction, key="value"))
                react_trigger = triggerMessage
                react_return = returnMessage
                changeSetting(SET, ER, interaction, key="value", value=value+1)
                changeSetting(SET, ER, interaction, key=f'{value+1}_tr', value=str(react_trigger))
                changeSetting(SET, ER, interaction, key=f'{value+1}_re', value=str(react_return))
                await interaction.send(f"トリガー：{react_trigger}\nリターン：{react_return}")
                return
            except BaseException as err:
                await interaction.send(embed=eh.eh(err))
        else:
            await interaction.send("管理者権限がありません。", ephemeral=True)
            return

    @er_slash.subcommand(name="list", description="追加反応の一覧")
    async def list_er_slash(self, interaction: Interaction):
        if interaction.guild.id not in reaction_datas.ex_reaction_list.value or changeSetting(STATUS, ER, interaction, key="value") == 0:
            await interaction.send("追加返答は設定されていません。")
            return
        else:
            embed = nextcord.Embed(title="追加返答リスト", description="- にらBOT", color=0x00ff00)
            for i in range(int(changeSetting(STATUS, ER, interaction, key="value"))):
                    embed.add_field(name=f"トリガー：{changeSetting(STATUS, ER, interaction, key=f'{i+1}_tr')}",
                                    value=f"リターン：{changeSetting(STATUS, ER, interaction, key=f'{i+1}_re')}",
                                    inline=False)
            await interaction.send(embed=embed)
            return

    @er_slash.subcommand(name="del", description="追加反応の削除")
    async def del_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            description="トリガー。`all`と入力するとすべての反応を削除します。",
            required=True
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in reaction_datas.ex_reaction_list.value:
                await interaction.send(f"`{interaction.guild.name}`では追加返答は設定されていません。", ephemeral=True)
            else:
                if triggerMessage == "all":
                    await interaction.response.defer()
                    del reaction_datas.ex_reaction_list.value[interaction.guild.id]
                    await database.default_push(self.client, reaction_datas.ex_reaction_list)
                    await interaction.send(f"`{interaction.guild.name}`での追加反応の設定を削除しました。")
                else:
                    await interaction.response.defer()
                    result = None
                    trigger = triggerMessage
                    for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[interaction.guild.id])-1)/2)):
                        if changeSetting(STATUS, ER, interaction, key=f"{i+1}_tr") == trigger:
                            result = i
                            break
                        continue
                    if result == None:
                        await interaction.send(f"`{trigger}`というトリガーが見つかりませんでした。\n不具合がある場合は全消しするか、サポートサーバーへご連絡ください。", ephemeral=True)
                        return
                    for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[interaction.guild.id])-1)/2)-(result+1)):
                        for suf in ("tr", "re"):
                            changeSetting(SET, ER, interaction,
                                          key=f"{result+i+1}_{suf}",
                                          value=changeSetting(STATUS, ER, interaction, key=f"{result+i+2}_{suf}"))
                    for i in ("tr", "re"):
                        del reaction_datas.ex_reaction_list.value[interaction.guild.id][f"{reaction_datas.ex_reaction_list.value[interaction.guild.id]['value']}_{i}"]
                    reaction_datas.ex_reaction_list.value[interaction.guild.id]["value"] -= 1
                    await database.default_push(self.client, reaction_datas.ex_reaction_list)
                    await interaction.send(f"`{trigger}`を削除しました。")
                    return
        else:
            await interaction.send("管理者権限がありません。", ephemeral=True)
            return

    @er_slash.subcommand(name="edit", description="追加反応の編集")
    async def edit_er_slash(
        self,
        interaction: Interaction,
        triggerMessage: str = SlashOption(
            name="trigger_message",
            description="トリガー",
            required=True
        ),
        returnMessage: str = SlashOption(
            name="return_message",
            description="返答文",
            required=True
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in reaction_datas.ex_reaction_list.value:
                await interaction.send("追加反応は登録されていません。", ephemeral=True)
                return
            if changeSetting(STATUS, ER, interaction, key="value") == 0:
                await interaction.send("追加反応は登録されていません。", ephemeral=True)
                return
            await interaction.response.defer()
            b_tr = triggerMessage
            b_re = returnMessage
            try:
                rt_e = False
                for i in range(math.floor((len(reaction_datas.ex_reaction_list.value[interaction.guild.id])-1)/2)):
                    if changeSetting(STATUS, ER, interaction, key=f"{i+1}_tr") == b_tr:
                        changeSetting(SET, ER, interaction, key=f"{i+1}_re", value=b_re)
                        rt_e = True
                        break
                if rt_e:
                    await interaction.send(f"トリガー：{b_tr}\nリターン：{b_re}")
                else:
                    await interaction.send("そのトリガーは登録されていません！", ephemeral=True)
                return
            except BaseException as err:
                await interaction.send(embed=eh.eh(err))
                return
        else:
            await interaction.send("管理者権限がありません。", ephemeral=True)
            return

    @commands.command(name="nr", help="""\
にらBOTの通常反応（にらとか）を無効にしたりすることが出来ます。
`n!nr`:今の状態を表示
`n!nr off`:通常反応を無効化
`n!nr on`:通常反応を有効化
`n!nr all off`:通常反応を**サーバーで**無効化
`n!nr all on`:通常反応を**サーバーで**有効化""")
    async def nr(self, ctx: commands.Context):
        try:
            if ctx.guild.id not in reaction_datas.reaction_bool_list.value:  # 通常反応のブール値存在チェック
                reaction_datas.reaction_bool_list.value[ctx.guild.id] = {}
                reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] = 1
                reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 1
                await database.default_push(self.client, reaction_datas.reaction_bool_list)
            if ctx.message.channel.id not in reaction_datas.reaction_bool_list.value[ctx.guild.id]:
                reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] = 1
                await database.default_push(self.client, reaction_datas.reaction_bool_list)
            if ctx.message.content == "n!nr":
                if reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] == 0:
                    setting = "サーバーで無効になっている為、チャンネルごとの設定は無効です。\n(`n!help nr`でご確認ください。)"
                elif reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] == 1:
                    setting = "有効"
                elif reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`n!nr [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.message.guild, ctx.message.author):
                nr_setting = str((ctx.message.content).split(" ", 1)[1])
                if nr_setting in n_fc.on_ali:
                    reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] = 1
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を有効にしました。", color=0x00ff00))
                elif nr_setting in n_fc.off_ali:
                    reaction_datas.reaction_bool_list.value[ctx.guild.id][ctx.message.channel.id] = 0
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を無効にしました。", color=0x00ff00))
                elif nr_setting[:3] == "all":
                    if nr_setting in n_fc.on_ali:
                        reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 1
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を有効にしました。", color=0x00ff00))
                    elif nr_setting in n_fc.off_ali:
                        reaction_datas.reaction_bool_list.value[ctx.guild.id]["all"] = 0
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を無効にしました。", color=0x00ff00))
                    else:
                        await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except Exception as err:
            await ctx.reply(embed=eh.eh(err))
            return

    @nextcord.slash_command(name="nr", description="通常反応設定", guild_ids=n_fc.GUILD_IDS)
    async def nr_slash(self, interaction):
        pass

    @nr_slash.subcommand(name="channel", description="チャンネルでの通常反応設定")
    async def channel_nr_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            description="チャンネルでの通常設定の有効化/無効化",
            choices={"有効": 1, "無効": 0}
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in reaction_datas.reaction_bool_list.value:
                reaction_datas.reaction_bool_list.value[interaction.guild.id] = {interaction.channel.id: setting}
            else:
                reaction_datas.reaction_bool_list.value[interaction.guild.id][interaction.channel.id] = setting
            await interaction.send(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"チャンネル <#{interaction.channel.id}> での通常反応を変更しました。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
            return

    @nr_slash.subcommand(name="server", description="サーバーでの通常反応設定")
    async def server_nr_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            description="サーバーでの通常設定の有効化/無効化",
            choices={"有効": 1, "無効": 0}
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in reaction_datas.reaction_bool_list.value:
                reaction_datas.reaction_bool_list.value[interaction.guild.id] = {
                    "all": setting, interaction.channel.id: 1}
            else:
                reaction_datas.reaction_bool_list.value[interaction.guild.id]["all"] = setting
            await interaction.send(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"サーバー `{interaction.guild.name}` での通常反応を変更しました。", color=0x00ff00), ephemeral=True)
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
            if ctx.guild.id not in reaction_datas.all_reaction_list.value:
                print(reaction_datas.all_reaction_list.value)
                reaction_datas.all_reaction_list.value[ctx.guild.id] = {}
                await database.default_push(self.client, reaction_datas.all_reaction_list)
            if ctx.message.channel.id not in reaction_datas.all_reaction_list.value[ctx.guild.id]:
                reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.message.channel.id] = 1
                await database.default_push(self.client, reaction_datas.all_reaction_list)
            if ctx.message.content == "n!ar":
                if reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.message.channel.id] == 1:
                    setting = "有効"
                elif reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.message.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description=f"「通常反応」及び「追加反応」（Bump通知および各種コマンドは除く）の設定:{setting}\n\n`n!ar [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.message.guild, ctx.message.author):
                ar_setting = str((ctx.message.content).split(" ", 1)[1])
                if ar_setting in n_fc.on_ali:
                    reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.message.channel.id] = 1
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を有効にしました。", color=0x00ff00))
                elif ar_setting in n_fc.off_ali:
                    reaction_datas.all_reaction_list.value[ctx.guild.id][ctx.message.channel.id] = 0
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を無効にしました。", color=0x00ff00))
                else:
                    await ctx.reply(embed=nextcord.Embed(title="All Reaction Setting", description="コマンド使用方法:`n!ar [all] [on/off]`", color=0xff0000))
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except BaseException as err:
            await ctx.reply(embed=eh.eh(err))
            return

    @nextcord.slash_command(name="ar", description="チャンネル全体反応設定", guild_ids=n_fc.GUILD_IDS)
    async def ar_slash(
        self,
        interaction: Interaction,
        setting: int = SlashOption(
            name="setting",
            description="チャンネルでの全体設定の有効化/無効化",
            choices={"有効": 1, "無効": 0}
        )
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            if interaction.guild.id not in reaction_datas.all_reaction_list.value:
                reaction_datas.all_reaction_list.value[interaction.guild.id] = {interaction.channel.id: setting}
            else:
                reaction_datas.all_reaction_list.value[interaction.guild.id][interaction.channel.id] = setting
            await interaction.send(embed=nextcord.Embed(title="All Reaction Setting", description=f"チャンネル <#{interaction.channel.id}> での全体反応を変更しました。", color=0x00ff00), ephemeral=True)
        else:
            await interaction.send(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000), ephemeral=True)
            return

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

    # imadake...
    @nextcord.slash_command(name="line", description="LINE Notifyの設定")
    async def line_slash(self, interaction: Interaction):
        pass

    @line_slash.subcommand(name="set", description="LINE Notifyのトークンを設定します。")
    async def line_set_slash(self, interaction: Interaction):
        modal = NotifyTokenSet()
        await interaction.response.send_modal(modal=modal)

    @line_slash.subcommand(name="del", description="LINE Notifyのトークンを削除します。")
    async def line_del_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral=True)
        else:
            if interaction.guild.id not in notify_token.value:
                await interaction.send(f"{interaction.guild.name}では、LINEトークンが設定されていません。", ephemeral=True)
                return
            if interaction.channel.id not in notify_token.value[interaction.guild.id]:
                await interaction.send(f"{interaction.channel.name}では、LINEトークンが設定されていません。", ephemeral=True)
                return
            del notify_token.value[interaction.guild.id][interaction.channel.id]
            await database.default_push(self.client, notify_token)
            await interaction.send(f"{interaction.channel.name}でのLINEトークンを削除しました。", ephemeral=True)


def setup(bot, **kwargs):
    bot.add_cog(reaction(bot, **kwargs))
