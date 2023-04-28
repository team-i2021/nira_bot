import aiohttp
import sys

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import admin_check, n_fc, eh, web_api, slash_tool
from util.nira import NIRA

DIR = sys.path[0]

# 通常反応や追加反応の反応系

class NotifyTokenSet(nextcord.ui.Modal):
    def __init__(self, collection: motor_asyncio.AsyncIOMotorCollection, session: aiohttp.ClientSession):
        super().__init__(
            "LINE Notify設定",
            timeout=None
        )
        self.session = session

        self.collection = collection

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
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral=True)
        else:
            token_result = await web_api.line_token_check(self.session, self.token.value)
            if token_result[0] == False:
                await interaction.send(f"そのトークンは無効なようです。\n```sh\n{token_result[1]}```", ephemeral=True)
                return
            await self.collection.update_one({"guild_id": interaction.guild.id}, {"$set": {"token": self.token.value}}, upsert=True)
            await interaction.send(f"{interaction.guild.name}/{interaction.channel.name}で`{self.token.value}`を保存します。\nトークンが他のユーザーに見られないようにしてください。\nこれで、このチャンネルのメッセージがLINEに送信されるようになりました。\n{self._atdb}", ephemeral=True)


class Reaction(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.er_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["er_setting"]
        self.nr_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["nr_setting"]
        self.ar_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["ar_setting"]
        self.line_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["notify_token"]
        self._atdb = "`(データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。)`"

    @commands.has_permissions(manage_guild=True)
    @commands.group(name="er", help="""\
追加で新しいにらの反応を作り出すことが出来ます。
オートリプライとかって呼ばれるんですかね？まぁ、トリガーとリターンを指定することで、トリガーが送信された際に指定したリターンを送信することが出来ます。
トリガーには正規表現を使うことが出来ます。が、スペースを含むことはできませんのでご了承ください。

`n!er add [トリガー] [返信文] [メンション]`で追加できます。
`n!er del [トリガー]`で削除できます。
`n!er list`でリストを表示できます。
`n!er edit [トリガー] [新反応]`でトリガーを編集できます。

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。
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
            await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を追加しました。\nメンションは{'有効' if mention else '無効'}です。\n{self._atdb}", color=0x00ff00))

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
                await ctx.reply(embed=nextcord.Embed(title="Success", description=f"全てのトリガーを削除しました。\n{self._atdb}", color=0x00ff00))
            else:
                delete_status = await self.er_collection.delete_one({"guild_id": ctx.guild.id, "trigger": trigger})
                if delete_status.deleted_count == 1:
                    await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を削除しました。\n{self._atdb}", color=0x00ff00))
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
    async def er_edit(self, ctx: commands.Context, trigger: str | None = None, return_text: str | None = None, mention: str | None = None):
        if trigger is None or return_text is None:
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}er edit [トリガー] [新反応] [*メンション]```")
        else:
            if not admin_check.admin_check(ctx.guild, ctx.author):
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
            if mention is None:
                set_value = {"return": return_text}
            else:
                if mention in n_fc.on_ali:
                    set_value = {"return": return_text, "mention": True}
                elif mention in n_fc.off_ali:
                    set_value = {"return": return_text, "mention": False}
                else:
                    await ctx.reply(embed=nextcord.Embed(title="Error", description=f"返信に対するメンションの指定が不正です。\n`yes`や`True`又は、`off`や`False`で指定してください。", color=0xff0000))
                    return
            update_result = await self.er_collection.update_one({"guild_id": ctx.guild.id, "trigger": trigger}, {"$set": set_value})
            if update_result.modified_count == 0:
                await ctx.reply(embed=nextcord.Embed(title="Error", description=f"トリガー`{trigger}`は存在しませんでした。", color=0xff0000))
            else:
                await ctx.reply(embed=nextcord.Embed(title="Success", description=f"トリガー`{trigger}`を編集しました。\n{self._atdb}", color=0x00ff00))


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
            await interaction.send(embed=nextcord.Embed(title="Success", description=f"追加反応を追加しました。\n{self._atdb}", color=0x00ff00))
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
            await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応をすべて削除しました。\n{self._atdb}", color=0x00ff00))
        else:
            delete_result = await self.er_collection.delete_one({"guild_id": interaction.guild.id, "trigger": triggerMessage})
            if delete_result.deleted_count == 0:
                await interaction.followup.send(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しませんでした。", color=0xff0000))
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応を削除しました。\n{self._atdb}", color=0x00ff00))


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
        ),
        mention: bool = SlashOption(
            name="mention",
            name_localizations={
                nextcord.Locale.ja: "メンション"
            },
            description="Mention",
            description_localizations={
                nextcord.Locale.ja: "メンションをするかどうかです"
            },
            required=False,
            default=False
        )
    ):
        await interaction.response.defer(ephemeral=True)
        edit_result = await self.er_collection.update_one({"guild_id": interaction.guild.id, "trigger": triggerMessage}, {"$set": {"return": returnMessage, "mention": mention}})
        if edit_result.modified_count == 0:
            await interaction.followup.send(embed=nextcord.Embed(title="Error", description=f"追加反応が存在しませんでした。", color=0xff0000))
        else:
            await interaction.followup.send(embed=nextcord.Embed(title="Success", description=f"追加反応を編集しました。\nメンションは{'有効' if mention else '無効'}です。\n{self._atdb}", color=0x00ff00))

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="nr", help="""\
にらBOTの通常反応（にらとか）を無効にしたりすることが出来ます。
`n!nr`:今の状態を表示
`n!nr off`:通常反応を無効化
`n!nr on`:通常反応を有効化
`n!nr all off`:通常反応を**サーバーで**無効化
`n!nr all on`:通常反応を**サーバーで**有効化

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。

※サーバーで反応が無効化された場合、チャンネルで有効化しても反応しません。""")
    async def nr(self, ctx: commands.Context):
        setting = ctx.message.content.split(" ", 2)
        if len(setting) == 3:
            if setting[1] != "all":
                await ctx.send(f"引数が不正です。\n`{ctx.prefix}nr [on/off]`または`{ctx.prefix}nr all [on/off]`")
            else:
                if setting[2] in n_fc.on_ali:
                    await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"all": True}}, upsert=True)
                    await ctx.send(f"サーバーでの通常反応を有効化しました。\n個別にチャンネルで無効化するには`{ctx.prefix}nr off`を設定したいチャンネルで実行してください。\n{self._atdb}")
                elif setting[2] in n_fc.off_ali:
                    await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"all": False}}, upsert=True)
                    await ctx.send(f"サーバーでの通常反応を無効化しました。\n個別で有効化することは出来ませんので、個別設定をしたい場合はまず、サーバーでの通常反応を有効化してください。\n{self._atdb}")
                else:
                    await ctx.send(f"引数が不正です。\n`{ctx.prefix}nr [on/off]`または`{ctx.prefix}nr all [on/off]`")
        elif len(setting) == 2:
            if setting[1] in n_fc.on_ali:
                await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {str(ctx.channel.id): True}}, upsert=True)
                await ctx.send("通常反応を有効化しました。\n※サーバーで反応が無効化されている場合は、個別で有効化しても反応しませんのでご注意ください。\n{self._atdb}")
            elif setting[1] in n_fc.off_ali:
                await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {str(ctx.channel.id): False}}, upsert=True)
                await ctx.send(f"通常反応を無効化しました。\n{self._atdb}")
            else:
                await ctx.send(f"引数が不正です。\n`{ctx.prefix}nr [on/off]`または`{ctx.prefix}nr all [on/off]`")
        elif len(setting) == 1:
            nr_setting = await self.nr_collection.find_one({"guild_id": ctx.guild.id})
            if nr_setting is None:
                await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {str(ctx.channel.id): True, "all": True}}, upsert=True)
                await ctx.send(embed=nextcord.Embed(title="通常反応", description="サーバーでの反応設定:`有効`\nチャンネルでの反応設定:`有効`", color=0x00ff00))
            else:
                # 存在しなかった場合の設定
                if "all" not in nr_setting:
                    await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"all": True}}, upsert=True)
                    nr_setting["all"] = True
                if str(ctx.channel.id) not in nr_setting:
                    await self.nr_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {str(ctx.channel.id): True}}, upsert=True)
                    nr_setting[str(ctx.channel.id)] = True

                # 実際のチェック
                embed = nextcord.Embed(title="通常反応", description=f"サーバーでの反応設定:`{'有効' if nr_setting['all'] else '無効'}`\nチャンネルでの反応設定:`{'有効' if nr_setting[str(ctx.channel.id)] else '無効'}`", color=0x00ff00)
                if not nr_setting["all"]:
                    embed.description += "\n※サーバーで反応が無効化されているため、個別で有効化しても反応しません。"
                await ctx.send(embed=embed)


    @nextcord.slash_command(name="nr", description="Normal Reaction Setting", guild_ids=n_fc.GUILD_IDS)
    async def nr_slash(self, interaction):
        pass


    @application_checks.has_permissions(manage_guild=True)
    @nr_slash.subcommand(name="channel", description="Setting of Normal Reaction in Channel", description_localizations={nextcord.Locale.ja: "チャンネルでの通常反応設定"})
    async def channel_nr_slash(
            self,
            interaction: Interaction,
            setting: bool = SlashOption(
                name="setting",
                name_localizations={
                    nextcord.Locale.ja: "設定"
                },
                description="Value of Setting Normal Reaction in Channel",
                description_localizations={
                    nextcord.Locale.ja: "チャンネルでの通常設定の有効化/無効化"
                },
                choices={"Enable": True, "Disable": False},
                choice_localizations={
                    nextcord.Locale.ja: {"有効": False, "無効": True}
                },
                required=True
            )
        ):
        await self.nr_collection.update_one({"guild_id": interaction.guild.id}, {"$set": {str(interaction.channel.id): setting}}, upsert=True)
        await interaction.response.send_message(f"{interaction.channel.name}での通常反応を{'有効化' if setting else '無効化'}しました。\n※サーバーで反応が無効化されている場合は、個別で有効化しても反応しませんのでご注意ください。\n{self._atdb}")


    @application_checks.has_permissions(manage_guild=True)
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
                choices={"Enable": True, "Disable": False},
                choice_localizations={
                    nextcord.Locale.ja: {"有効": True, "無効": False}
                },
                required=True
            )
        ):
        await self.nr_collection.update_one({"guild_id": interaction.guild.id}, {"$set": {"all": setting}}, upsert=True)
        await interaction.response.send_message(f"サーバーでの通常反応を{'有効化' if setting else '無効化'}しました。\n{self._atdb}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="ar", help="""\
にらBOTの通常反応及び追加反応(Bump通知および`n!`コマンド以外のすべて)をこのサーバーで無効にしたりすることが出来ます。
`n!ar`:今の状態を表示
`n!ar off`:全反応を無効化
`n!ar on`:全反応を有効化

チャンネルトピックに`nira-off`と入れておくと、そのチャンネルでは設定を無視して反応を無効化します。

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。""")
    async def ar(self, ctx: commands.Context, setting: str | None = None):
        if setting is None:
            ar_setting = await self.ar_collection.find_one({"guild_id": ctx.guild.id})
            if ar_setting is None:
                await self.ar_collection.udpate_one({"guild_id": ctx.guild.id, "all": True}, upsert=True)
                await ctx.send("このサーバーでの全体反応は有効です。")
            else:
                if ar_setting["all"]:
                    await ctx.send("このサーバーでの全体反応は有効です。")
                else:
                    await ctx.send("このサーバーでの全体反応は無効です。")
        elif setting in n_fc.on_ali:
            await self.ar_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"all": True}}, upsert=True)
            await ctx.send(f"このサーバーでの全体反応を有効化しました。\n{self._atdb}")
        elif setting in n_fc.off_ali:
            await self.ar_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"all": False}}, upsert=True)
            await ctx.send(f"このサーバーでの全体反応を無効化しました。\n{self._atdb}")
        else:
            await ctx.send(f"引数が不正です。\n`{ctx.prefix}ar [on/off]`")


    @application_checks.has_permissions(manage_guild=True)
    @nextcord.slash_command(name="ar", description="サーバー全体反応設定", guild_ids=n_fc.GUILD_IDS)
    async def ar_slash(
            self,
            interaction: Interaction,
            setting: int = SlashOption(
                name="setting",
                name_localizations={
                    nextcord.Locale.ja: "設定"
                },
                description="Value of Setting All Reaction in Guild",
                description_localizations={
                    nextcord.Locale.ja: "サーバーでの全体設定の有効化/無効化"
                },
                choices={"Enable": True, "Disable": False},
                choice_localizations={
                    nextcord.Locale.ja: {"有効": False, "無効": True}
                }
            )
        ):
        await self.ar_collection.update_one({"guild_id": interaction.guild.id}, {"$set": {"all": setting}}, upsert=True)
        await interaction.response.send_message(f"サーバーでの全体反応を{'有効化' if setting else '無効化'}しました。\n`{self._atdb}`")


    @commands.command(name="line", help="""\
DiscordのメッセージをLINEに送信します。
LINE Notifyという機能を用いて、DiscordのメッセージをLINEに送信します。

データベースへの接続の最適化のため、実際に設定が適応されるまでに最大で30秒程かかる場合があります。""")
    async def line(self, ctx: commands.Context):
        embed = nextcord.Embed(title="DiscordのメッセージをLINEに送信する機能", description="使い方", color=0x00ff00)
        embed.add_field(name="**このコマンドはスラッシュコマンドです**", value="""\
`/line set`というスラッシュコマンドを送ると、TOKENを入力する画面が表示されるので、そこにTOKENを入力してください。
ちなみにTOKENの流出はとんでもないことにつながるので、気をつけてください。""", inline=False)
        embed.add_field(name="**TOKENって何？**", value="""\
TOKENとは簡単に言えばパスワードです。LINE Notifyのページから発行してきてください。
[TOKENの発行方法](https://qiita.com/nattyan_tv/items/33ac7a7269fe12e49198)""", inline=False)
        embed.add_field(name="Q. LINEのオープンチャットで使えますか？", value="A. 申し訳ありませんができません。\n（もしLINEオープンチャットに関するAPIの新情報があったら教えてね）", inline=False)
        await ctx.reply(embed=embed)


    @nextcord.slash_command(name="line", description="Setting of Line Notify", guild_ids=n_fc.GUILD_IDS)
    async def line_slash(self, interaction: Interaction):
        pass


    @application_checks.has_permissions(manage_guild=True)
    @line_slash.subcommand(name="set", description="Set LINE Notify's TOKEN", description_localizations={nextcord.Locale.ja: "LINE Notifyのトークンを設定します。"})
    async def line_set_slash(self, interaction: Interaction):
        modal = NotifyTokenSet(self.line_collection, self.bot.session)
        await interaction.response.send_modal(modal=modal)


    @application_checks.has_permissions(manage_guild=True)
    @line_slash.subcommand(name="del", description="Delete LINE Notify's TOKEN", description_localizations={nextcord.Locale.ja: "LINE Notifyのトークンを削除します。"})
    async def line_del_slash(self, interaction: Interaction):
        await self.line_collection.delete_one({"guild_id": interaction.guild.id})
        await interaction.response.send_message(f"LINE Notifyのトークンを削除しました。\nこれでこのチャンネルのメッセージがLINEに送信されなくなりました。\n{self._atdb}")


def setup(bot, **kwargs):
    bot.add_cog(Reaction(bot, **kwargs))
