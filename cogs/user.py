import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import slash_tool, n_fc
from util.nira import NIRA

SET, DEL, STATUS = (0, 1, 2)

# ユーザー情報表示系


class User(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.rk_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["role_keeper"]
        self.winfo_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["welcome_info"]

    def UserInfoEmbed(self, member: nextcord.Member or nextcord.User):
        if member.bot:
            embed = nextcord.Embed(
                title="User Info",
                description=f"名前：`{member.name}` __[BOT]__\nID：`{member.id}`",
                color=0x00ff00
            )
        else:
            embed = nextcord.Embed(
                title="User Info",
                description=f"名前：`{member.name}`\nID：`{member.id}`",
                color=0x00ff00
            )
        if member.banner is not None:
            embed.set_image(url=member.banner.url)
        if member.avatar is not None:
            embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(
            name="アカウント製作日",
            value=f"`{member.created_at}`"
        )
        if type(member) is nextcord.Member:
            embed.add_field(
                name="サーバー参加日",
                value=f"`{member.joined_at}`"
            )
            if len(member.roles) > 1:
                embed.add_field(
                    name="ロール",
                    value=" ".join([r.mention for r in member.roles if r.id != member.guild.id])
                )

        return embed

    @nextcord.user_command(name="Display user info", name_localizations={nextcord.Locale.ja: "ユーザー情報表示"})
    async def member_info(self, interaction: Interaction, member: nextcord.Member):
        await interaction.response.send_message(embed=self.UserInfoEmbed(member))

    @nextcord.slash_command(name="afk", description="Change afk status.")
    async def afk_turn(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        nick = interaction.user.display_name
        if interaction.user.display_name[-5:] == "[AFK]":
            nick = nick[:-5]
            AFK = False
        else:
            nick = nick + "[AFK]"
            AFK = True
        try:
            await interaction.user.edit(nick=nick)
            if AFK:
                await interaction.send("AFKを有効にしたよ。\n戻すにはもっかい`/afk`ってやればいいと思うよ。")
            else:
                await interaction.send("AFKを無効にしたよ。\n有効にするにはもっかい`/afk`ってやればいいと思うよ。")
        except Exception as err:
            await interaction.send(f"BOTにあなたのニックネームを変更できる権限がないなどの理由で、コマンドを実行できませんでした。\nサーバーの管理者にお問い合わせください。\nERR: `{err}`\n（あなたがサーバーの管理者の場合はこのコマンドが実行できません。仕様なんで。）")

    @nextcord.slash_command(name="user", description="Display user info", description_localizations={nextcord.Locale.ja: "ユーザー情報表示"})
    async def user_slash(
        self,
        interaction: Interaction,
        user: nextcord.User = SlashOption(
            name="user",
            description="User of want to display",
            description_localizations={nextcord.Locale.ja: "表示したいユーザー"},
            required=False
        )
    ):
        if user is None:
            user = interaction.user
        await interaction.response.send_message(embed=self.UserInfoEmbed(user))


    @commands.command(name="d", help="""\
ユーザーの情報を表示します。
引数を指定せずに`n!d`とだけ指定するとあなた自身の情報を表示します。
`n!d [ユーザーID]`という風に指定すると、そのユーザーの情報を表示することが出来ます。
ユーザーIDの指定方法は...多分調べれば出てきます。
**メンションでも指定できますが、いざこざとかにつながるかもしれないのでしないほうが得策です。**""")
    async def show_user(self, ctx: commands.Context, req_user: int | None = None):
        if req_user is None:
            user = await self.bot.fetch_user(ctx.author.id)
            await ctx.reply(embed=self.UserInfoEmbed(user))
        else:
            try:
                user = await self.bot.fetch_user(req_user)
                await ctx.reply(embed=self.UserInfoEmbed(user))
                return
            except Exception:
                try:
                    channel = await self.bot.fetch_channel(req_user)
                    if type(channel) == nextcord.channel.TextChannel:
                        embed = nextcord.Embed(
                            title="TextChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\n{(lambda x: '__NSFW__' if x else '')(channel.is_nsfw())}\n",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="チャンネルトピック",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            channel.topic
                        )
                    elif type(channel) == nextcord.channel.VoiceChannel:
                        embed = nextcord.Embed(
                            title="VoiceChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\nビットレート:`{channel.bitrate/1000}`kbps\n人数:`{len(channel.voice_states.keys())}/{channel.user_limit}`人",
                            color=0x00ff00
                        )
                    elif type(channel) == nextcord.channel.StageChannel:
                        embed = nextcord.Embed(
                            title="StageChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nカテゴリ:`{channel.category}`\nビットレート:`{channel.bitrate/1000}`kbps\n人数:`{len(channel.voice_states.keys())}/{channel.user_limit}`人",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="チャンネルトピック",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            channel.topic
                        )
                    elif type(channel) == nextcord.channel.CategoryChannel:
                        embed = nextcord.Embed(
                            title="CategoryChannel Info",
                            description=f"名前:`{channel.name}`\nID:`{channel.id}`\nテキストチャンネル数:`{len(channel.text_channels)}`\nボイスチャンネル数:`{len(channel.voice_channels)}`\nステージチャンネル数:`{len(channel.stage_channels)}`",
                            color=0x00ff00
                        )
                    await ctx.reply(embed=embed)
                    return
                except Exception:
                    try:
                        # Forbidden.....?????
                        guild = await self.bot.fetch_guild(req_user)
                        embed = nextcord.Embed(
                            title="Guild Info",
                            description=f"名前:`{guild.name}`\nID:`{guild.id}`\n人数:`{len(guild.members)}`人(そのうちのBOT数:`{len(guild.bots)}`)\nオーナー:{guild.owner.mention}",
                            color=0x00ff00
                        )
                        (
                            lambda x: embed.add_field(
                                name="説明文",
                                value=f"```\n{x}```"
                            ) if x is not None else None
                        )(
                            guild.description
                        )
                        await ctx.reply(embed=embed)
                        return
                    except Exception:
                        await ctx.reply(embed=nextcord.Embed(title="Error", description="ユーザー、チャンネル、またはサーバーのデータが取得できませんでした。", color=0xff0000))
                        return

    @application_checks.has_permissions(manage_guild=True)
    @nextcord.slash_command(name="rk", description="Setting of role-keeper", description_localizations={nextcord.Locale.ja: "ロールキーパーの設定"})
    async def rk_slash(
        self,
        interaction: Interaction,
        SettingValue: bool = SlashOption(
            name="setting_value",
            name_localizations={nextcord.Locale.ja: "設定値"},
            description="Value of setting",
            description_localizations={nextcord.Locale.ja: "設定値"},
            required=True,
            choices={"有効にする": True, "無効にする": False}
        )
    ):
        await interaction.response.defer(ephemeral=True)
        await self.rk_collection.update_one({"guild_id": interaction.guild.id}, {"$set": {"setting": SettingValue}})
        await interaction.send(f"ロールキーパー機能を{'有効' if SettingValue else '無効'}にしました。\n※この機能への過信はやめましょう。", ephemeral=True)

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="rk", help="""\
ロールキーパー機能です。
AutoMod等の機能を活用したうえで、過信しすぎずに使用してください。

`n!rk [on/off]`でロールキーパー機能の設定が可能です。ただ、ロールキーパー機能を有効にするには`n!ui`の、ユーザー情報表示を有効にしないと有効になりません。""")
    async def rk(self, ctx: commands.Context, setting: str | None = None):
        if setting is None:
            result = await self.rk_collection.find_one({"guild_id": ctx.guild.id})
            await ctx.reply(f"ロールキーパー機能は{'有効' if result['setting'] else '無効'}です。")
        elif setting in n_fc.on_ali:
            await self.rk_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"setting": True}})
            await ctx.reply("ロールキーパー機能を有効にしました。\n**※本機能への過信はおやめください。**")
        elif setting in n_fc.off_ali:
            await self.rk_collection.update_one({"guild_id": ctx.guild.id}, {"$set": {"setting": False}})
            await ctx.reply("ロールキーパー機能を無効にしました。")
        else:
            await ctx.reply(f"引数が不正です。\n`{ctx.prefix}rk [on/off]`")

    async def ui_config(self, interaction: Interaction or commands.Context, type: int, guild_id: int, channel: nextcord.abc.GuildChannel | None):
        if isinstance(channel, nextcord.ForumChannel):
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description="フォーラムチャンネルは指定できません。", color=self.bot.color.ERROR), ephemeral=True)
            return
        if isinstance(channel, nextcord.StageChannel):
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description="ステージチャンネルは指定できません。", color=self.bot.color.ERROR), ephemeral=True)
            return
        if isinstance(channel, nextcord.CategoryChannel):
            await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description="カテゴリチャンネルは指定できません。", color=self.bot.color.ERROR), ephemeral=True)
            return
        result = await self.winfo_collection.find_one({"guild_id": guild_id})
        if type == SET:
            try:
                await self.winfo_collection.update_one({"guild_id": guild_id}, {"$set": {"channel_id": channel.id}}, upsert=True)
                CHANNEL = await self.bot.fetch_channel(channel.id)
                await CHANNEL.send("このチャンネルが、ユーザー情報表示チャンネルとして指定されました。")
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"<#{channel.id}>に指定されました。", color=self.bot.color.NORMAL), ephemeral=True)
            except Exception as err:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"エラーが発生しました。\n```\n{err}```", color=self.bot.color.ERROR), ephemeral=True)
        elif type == DEL:
            try:
                if result is None:
                    await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"このサーバーには登録されていません。", color=self.bot.color.ATTENTION), ephemeral=True)
                    return
                await self.winfo_collection.delete_one({"guild_id": guild_id})
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"設定を削除しました。", color=self.bot.color.NORMAL), ephemeral=True)
            except Exception as err:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"エラーが発生しました。\n```\n{err}```", color=self.bot.color.ERROR), ephemeral=True)
        elif type == STATUS:
            if result is None:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"サーバーで設定は`無効`です", color=self.bot.color.NORMAL), ephemeral=True)
            else:
                await slash_tool.messages.mreply(interaction, "", embed=nextcord.Embed(title="ユーザー情報表示設定", description=f"サーバーで設定は`有効`です\n設定チャンネル: <#{result['channel_id']}>", color=self.bot.color.NORMAL), ephemeral=True)


    @nextcord.slash_command(name="ui", description="Send a message when user join/leave")
    async def ui_slash(self, interaction):
        pass


    @application_checks.has_permissions(manage_guild=True)
    @ui_slash.subcommand(name="set", description="Set channel of sent user info", description_localizations={nextcord.Locale.ja: "ユーザー表示チャンネルをセットします"})
    async def set_slash(
            self,
            interaction: Interaction,
            channel: nextcord.abc.GuildChannel = SlashOption(
                name="channel",
                description="Channel of sent user info",
                description_localizations={nextcord.Locale.ja: "メッセージを送信するチャンネルです"},
                required=True
            )
        ):
        await self.ui_config(interaction, SET, interaction.guild.id, channel)


    @application_checks.has_permissions(manage_guild=True)
    @ui_slash.subcommand(name="del", description="Delete channel of sent user info", description_localizations={nextcord.Locale.ja: "ユーザー表示チャンネル設定を削除します"})
    async def del_slash(
            self,
            interaction: Interaction
        ):
        await self.ui_config(interaction, DEL, interaction.guild.id, None)


    @application_checks.has_permissions(manage_guild=True)
    @ui_slash.subcommand(name="status", description="Check channel of sent user info", description_localizations={nextcord.Locale.ja: "ユーザー表示チャンネル設定を確認します"})
    async def status_slash(
            self,
            interaction: Interaction
        ):
        await self.ui_config(interaction, STATUS, interaction.guild.id, None)


    @commands.has_permissions(manage_guild=True)
    @commands.command(name="ui", help="""\
誰かがDiscordサーバーに加入/離脱した際に、指定したチャンネルにそのユーザーの情報を表示します。
それだけです。

`n!ui set [チャンネル]`
`n!ui del`""")
    async def ui(self, ctx: commands.Context, setting: str | None = None, channel: str | int | None = None):
        if setting is None:
            await self.ui_config(ctx, STATUS, ctx.guild.id, None)
        elif setting == "set":
            CHANNEL = None
            try:
                CHANNEL = await self.bot.fetch_channel(int(channel))
            except Exception:
                for c in ctx.guild.channels:
                    if c.name == channel:
                        CHANNEL = c
                        break
            if CHANNEL is None:
                await ctx.reply(f"指定されたンネル`{channel}`が見つかりませんでした。")
                return
            await self.ui_config(ctx, SET, ctx.guild.id, CHANNEL)
        elif setting == "del":
            await self.ui_config(ctx, DEL, ctx.guild.id, None)
        else:
            await self.ui_config(ctx, STATUS, ctx.guild.id, None)



def setup(bot, **kwargs):
    bot.add_cog(User(bot, **kwargs))
