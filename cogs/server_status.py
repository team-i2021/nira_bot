import asyncio
import datetime
import importlib
import logging
import re
import traceback

import nextcord
from motor import motor_asyncio
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks

from util import admin_check, server_check
from util.nira import NIRA
from util.semiembed import SemiEmbed


STEAM_SERVER_COLLECTION_NAME = "steam_server"


async def ss_force(bot: NIRA, message: nextcord.Message):
    await message.edit(content="Loading status...", view=None)
    try:
        assert isinstance(message.guild, nextcord.Guild)
        servers = (
            await bot.database[STEAM_SERVER_COLLECTION_NAME].find({"guild_id": message.guild.id}).to_list(length=None)
        )
        semi_embed = SemiEmbed(
            title="ServerStatus Checker",
            description=f"最終更新: `{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}`",
            color=0x00FF00,
        )
        for server in sorted(servers, key=lambda x: x['server_id']):
            semi_embed.add_field(**(await server_check.ss_pin_embed(server)))
        await message.edit(
            content=(
                "AutoSS実行中\n"
                f"止めるには`{bot.command_prefix}ss auto off`または`/ss off`\n"
                "リロードするには下の`再読み込み`ボタンか`/ss reload`\n"
                "止まった場合は一度オフにしてから再度オンにしてください"
            ),
            embeds=semi_embed.get_embeds(),
            view=Reload_SS_Auto(bot, message),
        )
        logging.info("Status loaded.(Not scheduled)")
    except Exception as err:
        logging.error(err, exc_info=True)
        await message.edit(content=f"err:{err}")


async def get_mes(bot, channel_id, message_id):
    ch_obj = await bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    return messs


async def launch_ss(self, channel_id, message_id):
    ch_obj = await self.bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    await ss_force(self.bot, messs)


# コマンド内部
async def ss_base(
        bot: NIRA,
        ss_collection: motor_asyncio.AsyncIOMotorCollection,
        auto_collection: motor_asyncio.AsyncIOMotorCollection,
        ctx: commands.Context,
    ):

    assert isinstance(ctx.guild, nextcord.Guild)
    assert isinstance(ctx.author, nextcord.Member)

    servers = await ss_collection.find({"guild_id": ctx.guild.id}).to_list(length=None)
    if ctx.message.content == f"{bot.command_prefix}ss":
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにSteam非公式サーバーは登録されていません。")
        else:
            async with ctx.channel.typing():
                semi_embed = SemiEmbed(
                    title="Server Status Checker",
                    description=f"{ctx.author.mention}\n:globe_with_meridians: Status",
                    color=0x00FF00,
                )
                for server in sorted(servers, key=lambda x: x['server_id']):
                    semi_embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.NORMAL)))
                await asyncio.sleep(1)
                await ctx.reply(embeds=semi_embed.get_embeds(), view=Recheck_SS_Embed(bot))
        return

    args = ctx.message.content.split(" ")

    if args[1] == "add":
        if len(args) == 1:
            await ctx.reply(f"構文が異なります。\n```{ctx.prefix}ss add [表示名] [IPアドレス],[ポート番号]```")
        else:
            try:
                ad_name = str(args[2])
                address = " ".join(args[3:])
                ad_ip = str(re.sub("[^0-9a-zA-Z._-]", "", address.split(",")[0]))
                ad_port = int(re.sub("[^0-9]", "", address.split(",")[1]))
                await ss_collection.insert_one(
                    {
                        "guild_id": ctx.guild.id,
                        "sv_nm": ad_name,
                        "sv_ad": (ad_ip, ad_port),
                        "server_id": len(servers) + 1,
                    }
                )

                await ctx.reply(
                    "Steam非公式サーバーを追加しました。",
                    embed=nextcord.Embed(title=f"サーバー名：`{ad_name}`", description=f"サーバーアドレス:`{ad_ip}:{ad_port}`"),
                )
                return
            except Exception as err:
                await ctx.reply(f"サーバー追加時にエラーが発生しました。\n```sh\n{err}```")
                return

    elif args[1] == "list":
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにSteam非公式サーバーは登録されていません。")
        else:
            if admin_check.admin_check(ctx.guild, ctx.author):
                user = await bot.fetch_user(ctx.author.id)
                embed = nextcord.Embed(
                    title="Steam Server List",
                    description=f"「{ctx.guild.name}」のサーバーリスト\n```保存数：{len(servers)}```",
                    color=0x00FF00,
                )
                for server in servers:
                    embed.insert_field_at(
                        index=server["server_id"] - 1,
                        name=f"ID: `{server['server_id']}`\n保存名: `{server['sv_nm']}`",
                        value=f"アドレス：`{server['sv_ad'][0]}:{server['sv_ad'][1]}`",
                    )
                await user.send(embed=embed)
                await ctx.message.add_reaction("\U00002705")
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xFF0000))

    elif args[1] == "auto":
        auto_doc = await auto_collection.find_one({"guild_id": ctx.guild.id})

        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xFF0000))
            return
        if ctx.message.content == f"{bot.command_prefix}ss auto":
            await ctx.reply(
                embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{bot.command_prefix}ss auto on/off`")
            )
            return

        elif ctx.message.content[10:12] == "on":
            if auto_doc is not None:
                await ctx.reply(
                    f"既に`{ctx.guild.name}`でAutoSSタスクが実行されています。\n`{bot.command_prefix}ss auto off`で終了してください。",
                )
                return
            if len(servers) == 0:
                await ctx.reply("このDiscordサーバーにSteam非公式サーバーは登録されていません。")
                return
            mes_ss = await ctx.channel.send(
                "設定したメッセージをご確認ください！\n（メッセージが指定されていない場合はこのメッセージがすぐに切り替わります...）",
            )
            if ctx.message.content == f"{bot.command_prefix}ss auto on":
                await auto_collection.update_one(
                    {"guild_id": ctx.guild.id},
                    {"$set": {"channel_id": ctx.channel.id, "message_id": mes_ss.id}},
                    upsert=True,
                )
                asyncio.ensure_future(ss_force(bot, mes_ss))
                return
            else:
                cl, ms = int(ctx.message.content[16:].split(" ", 1)[0]), int(ctx.message.content[16:].split(" ", 1)[1])
                try:
                    messs = await (await bot.fetch_channel(cl)).fetch_message(ms)
                except Exception as err:
                    logging.error(err)
                    await ctx.reply("メッセージが見つかりませんでした。")
                    return
                await messs.edit(content="現在変更をしています...")
                await auto_collection.update_one(
                    {"guild_id": ctx.guild.id},
                    {
                        "$set": {
                            "channel_id": int(ctx.message.content[16:].split(" ", 1)[0]),
                            "message_id": int(ctx.message.content[16:].split(" ", 1)[1]),
                        }
                    },
                    upsert=True,
                )
                asyncio.ensure_future(ss_force(bot, messs))
                return

        elif ctx.message.content[10:13] == "off":
            if auto_doc is None:
                await ctx.reply("AutoSSは実行されていません。")
                return
            try:
                await auto_collection.delete_one({"guild_id": ctx.guild.id})
                await ctx.reply(
                    f"AutoSSを無効にしました。\n再度有効にするには`{ctx.prefix}ss auto on`または`/ss auto on`を使用してください。",
                )
                return
            except Exception as err:
                await ctx.reply(embed=bot.error_embed(err))
                return

        else:
            if auto_doc is not None:
                await ctx.reply(f"`{ctx.prefix}ss auto [on/off]`\nAutoSSは有効になっています。")
                return
            else:
                await ctx.reply(f"`{ctx.prefix}ss auto [on/off]`\nAutoSSは無効になっています。")
                return

    elif args[1] == "edit":
        if ctx.message.content == f"{bot.command_prefix}ss edit":
            await ctx.reply(f"構文が異なります。\n```{ctx.prefix}ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
            return
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにはSteam非公式サーバーは登録されていません。")
            return

        adre = ctx.message.content[10:].split(" ", 3)
        s_id = int("".join(re.findall(r"[\d]", adre[0])))
        s_nm = str(adre[1])
        s_adre = str(adre[2]).split(",", 2)
        s_port = int(s_adre[1])
        s_ip = str(re.sub("[^0-9a-zA-Z._-]", "", s_adre[0]))

        if len(servers) < s_id:
            await ctx.reply(f"指定されたIDのSteam非公式サーバーは登録されていません！\n`{ctx.prefix}ss list`で確認してみてください。")
            return
        try:
            await ss_collection.update_one(
                {"guild_id": ctx.guild.id, "server_id": s_id},
                {"$set": {"sv_nm": s_nm, "sv_ad": (s_ip, s_port)}},
            )
            await ctx.reply(
                f"サーバーID:`{s_id}`の情報を編集しました。",
                embed=nextcord.Embed(title=f"サーバー名:`{s_nm}`", description=f"サーバーアドレス:`{s_ip}:{s_port}`"),
            )
            return
        except Exception as err:
            await ctx.reply(embed=bot.error_embed(err))
            return

    elif args[1] == "sort":
        if len(args) != 4:
            await ctx.reply(f"引数が足りないか多いです。\n`{bot.command_prefix}ss sort [サーバーID1] [サーバーID2]`")
            return
        try:
            args[2] = int(args[2])
            args[3] = int(args[3])
        except ValueError:
            await ctx.reply("サーバーIDの欄には数値が入ります。")
            return
        if args[2] > len(servers) or args[3] > len(servers):
            await ctx.reply(
                f"{ctx.guild.name}に登録されているサーバーの数は{len(servers)}個です。\n指定されたサーバーIDは無効です。",
            )
            return
        if args[2] <= 0 or args[3] <= 0:
            await ctx.reply("サーバーIDは1から順につけられます。\n指定されたサーバーIDは無効です。")
            return
        try:
            # いい書き方にいつか変えたい
            await ss_collection.update_one(
                {"guild_id": ctx.guild.id, "server_id": args[2]},
                {"$set": {"server_id": 0}},
            )
            await ss_collection.update_one(
                {"guild_id": ctx.guild.id, "server_id": args[3]},
                {"$set": {"server_id": args[2]}},
            )
            await ss_collection.update_one(
                {"guild_id": ctx.guild.id, "server_id": 0},
                {"$set": {"server_id": args[3]}},
            )
            await ctx.reply("入れ替えが完了しました。")
            return
        except Exception as err:
            await ctx.reply(f"入れ替え中にエラーが発生しました。\n{err}")
            return

    elif args[1] == "del":
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにはSteam非公式サーバーは登録されていません。")
            return
        if ctx.message.content != f"{bot.command_prefix}ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except Exception as err:
                await ctx.reply(embed=bot.error_embed(err))
                return
            if admin_check.admin_check(ctx.guild, ctx.author):
                if del_num > len(servers):
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="エラー",
                            description=f"指定されたIDのSteam非公式サーバーは登録されていません！\n`{ctx.prefix}ss list`で確認してみてください！",
                            color=0xFF0000,
                        )
                    )
                    return
                if del_num <= 0:
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="エラー",
                            description="リストで0以下のナンバーは振り当てられていません。",
                            color=0xFF0000,
                        )
                    )
                    return
                try:
                    await ss_collection.delete_one({"guild_id": ctx.guild.id, "server_id": del_num})
                    await ss_collection.update_many(
                        {"guild_id": ctx.guild.id, "server_id": {"$gt": del_num}},
                        {"$inc": {"server_id": -1}},
                    )
                    await ctx.reply(
                        embed=nextcord.Embed(
                            title="削除",
                            description=f"ID:{del_num}のサーバーを削除しました。",
                            color=0xFF0000,
                        )
                    )
                except Exception as err:
                    logging.error(traceback.format_exc())
                    await ctx.reply(embed=bot.error_embed(err))
                    return
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xFF0000))
        else:
            await ss_collection.delete_many({"guild_id": ctx.guild.id})
            await ctx.reply(
                embed=nextcord.Embed(
                    title="リスト削除",
                    description=f"{ctx.author.mention}\n{ctx.guild.name}のSteam非公式サーバーは全て削除されました。",
                    color=0xFFFFFF,
                )
            )

    elif args[1] == "all":
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにはSteam非公式サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            semi_embed = SemiEmbed(
                title="Server Status Checker",
                description=f"{ctx.author.mention}\n:globe_with_meridians: Status",
                color=0x00FF00,
            )
            for server in sorted(servers, key=lambda x: x['server_id']):
                semi_embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.DETAIL)))
            await asyncio.sleep(1)
            await ctx.reply(embeds=semi_embed.get_embeds(), view=Recheck_SS_Embed(bot))

    elif len(args) > 2:
        await ctx.reply(
            f"""\
引数とか何かがおかしいです。

・SS系コマンド一覧
`{bot.command_prefix}ss`: 登録されているサーバーのステータスを表示します。
`{bot.command_prefix}ss add [表示名] [アドレス],[ポート]`: サーバーを追加します。
`{bot.command_prefix}ss list`: 登録されているサーバーの一覧を表示します。
`{bot.command_prefix}ss auto on`: 10分毎にステータスを更新するAutoSSのメッセージを送信します。
`{bot.command_prefix}ss auto off`: AutoSSを停止します。
`{bot.command_prefix}ss edit [サーバーID] [表示名] [アドレス],[ポート]`: 指定したサーバーIDの表示名やアドレスなどを修正します。\
事前に`{bot.command_prefix}ss list`などで確認しておくことを推奨します。
`{bot.command_prefix}ss sort [サーバーID1] [サーバーID2]`: サーバーID1とサーバID2の場所を入れ替えます。
`{bot.command_prefix}ss del [サーバーID]`: 指定したサーバーIDの情報を削除します。
`{bot.command_prefix}ss del all`: 登録されているサーバーをすべて削除します。
`{bot.command_prefix}ss all`: 登録されているサーバーのステータスをより詳細に表示します。\
あまりにサーバー数があると、メッセージ数規定に引っかかって送れない場合があります。
`{bot.command_prefix}ss [サーバーID]`: 指定したサーバーIDのステータスのみを表示します。"""
        )
        return

    else:
        if len(servers) == 0:
            await ctx.reply("このDiscordサーバーにはSteam非公式サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(
                title="Server Status Checker",
                description=f"{ctx.author.mention}\n:globe_with_meridians: Status",
                color=0x00FF00,
            )
            server = await ss_collection.find_one({"guild_id": ctx.guild.id, "server_id": int(args[1])})
            embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.NORMAL)))
            await asyncio.sleep(1)
            await ctx.reply(embed=embed)


class Reload_SS_Auto(nextcord.ui.View):
    def __init__(self, bot: NIRA, message: nextcord.Message):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = message

    @nextcord.ui.button(label="再読み込み", style=nextcord.ButtonStyle.green)
    async def reload(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            asyncio.ensure_future(ss_force(self.bot, self.message))
            await interaction.followup.send("Reloaded!", ephemeral=True)

        except Exception as err:
            await interaction.followup.send(
                f"エラーが発生しました。\n`{err}`\n```sh\n{traceback.format_exc()}```",
                ephemeral=True,
            )
            logging.error(traceback.format_exc())


class Recheck_SS_Embed(nextcord.ui.View):
    def __init__(self, bot: NIRA):
        super().__init__(timeout=None)
        self.bot = bot
        self.ss_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[STEAM_SERVER_COLLECTION_NAME]

    @nextcord.ui.button(label="もう一度チェックする", style=nextcord.ButtonStyle.green)
    async def recheck(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer(with_message=True)
        try:
            semi_embed = SemiEmbed(
                title="Server Status Checker",
                description=":globe_with_meridians: Status",
                color=self.bot.color.NORMAL,
            )
            servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
            for server in servers:
                semi_embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.NORMAL)))
            await interaction.followup.send(
                f"{interaction.user.mention} - Server Status",
                embeds=semi_embed.get_embeds(),
                view=Recheck_SS_Embed(self.bot),
            )
            logging.info("rechecked")

        except Exception:
            await interaction.followup.send(f"エラーが発生しました。\n```\n{traceback.format_exc()}```")
            logging.error(traceback.format_exc())


class server_status(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.ss_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database[STEAM_SERVER_COLLECTION_NAME]
        self.auto_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["auto_ss"]
        self.check_status_pin_loop.start()

    def cog_unload(self):
        self.check_status_pin_loop.stop()

    @nextcord.message_command(
        name="Start AutoSS",
        name_localizations={nextcord.Locale.ja: "AutoSSのスタート"},
    )
    async def start_auto_ss(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer(ephemeral=True)
        try:
            if message.author.id != self.bot.user.id:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"{self.bot.user.mention}が送信したメッセージにのみこのコマンドを使用できます。",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                return
            CHANNEL_ID = message.channel.id
            MESSAGE_ID = message.id
            await self.auto_collection.update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"channel_id": CHANNEL_ID, "message_id": MESSAGE_ID}},
                upsert=True,
            )
            asyncio.ensure_future(ss_force(self.bot, message))
            await interaction.followup.send("指定されたメッセージでAutoSSをスタートしました。")
        except Exception as err:
            await interaction.followup.send(f"エラーが発生しました。\n```\n{err}```")

    @commands.guild_only()
    @commands.command(
        name="ss",
        help="""\
Steam非公式サーバーのステータスを表示します
このコマンドは、**user毎**で**10秒**のクールダウンがあります。
このコマンドのヘルプは別ページにあります。
[ヘルプはこちら](https://sites.google.com/view/nira-bot/%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89/ss)""")
    @commands.cooldown(1, 10, type=commands.BucketType.user)
    async def ss(self, ctx: commands.Context):
        await ss_base(self.bot, self.ss_collection, self.auto_collection, ctx)

    @nextcord.slash_command(name="ss", description="Show Steam Dedicated Server's status")
    async def ss_slash(self, interaction: Interaction):
        pass

    @ss_slash.subcommand(
        name="add",
        description="Add Steam Dedicated Server",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーを追加します"},
    )
    async def add_slash(
        self,
        interaction: Interaction,
        ServerName: str = SlashOption(
            name="name",
            name_localizations={nextcord.Locale.ja: "サーバー名"},
            description="Name of server (if server is offline, it shows.)",
            description_localizations={nextcord.Locale.ja: "オフライン時に表示されるサーバーの名前"},
            required=True,
        ),
        ServerAddress: str = SlashOption(
            name="address",
            name_localizations={nextcord.Locale.ja: "サーバーアドレス"},
            description="Address of server",
            description_localizations={nextcord.Locale.ja: "サーバーのIPアドレスまたはドメイン名"},
            required=True,
        ),
        ServerPort: int = SlashOption(
            name="port",
            name_localizations={nextcord.Locale.ja: "サーバーポート"},
            description="Port of server",
            description_localizations={nextcord.Locale.ja: "サーバーのポート番号"},
            required=True,
        ),
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
                await self.ss_collection.insert_one(
                    {
                        "guild_id": interaction.guild.id,
                        "sv_nm": ServerName,
                        "sv_ad": (ServerAddress, ServerPort),
                        "server_id": len(servers) + 1,
                    }
                )

                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="SteamDedicatedServer",
                        description=(
                            f"サーバーの追加に成功しました。\nサーバー名：`{ServerName}`\nサーバーアドレス: `{ServerAddress}:{ServerPort}`"
                        ),
                        color=0x00FF00,
                    ),
                    ephemeral=True,
                )
                return
            else:
                await interaction.followup.send(
                    embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xFF0000),
                    ephemeral=True,
                )
                return
        except Exception as err:
            await interaction.followup.send(f"Steam非公式サーバー追加時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(
        name="del",
        description="Delete Steam Dedicated Server",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーを削除します"},
    )
    async def del_slash(
        self,
        interaction: Interaction,
        ServerID: int = SlashOption(
            name="server_id",
            name_localizations={nextcord.Locale.ja: "サーバーid"},
            description="Server ID of want to delete",
            description_localizations={nextcord.Locale.ja: "削除するサーバーのID"},
            required=True,
        ),
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
                if ServerID <= 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="サーバーIDは1以上の整数である必要があります。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if ServerID > len(servers):
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="指定されたIDのサーバーは存在しません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return

                await self.ss_collection.delete_one({"guild_id": interaction.guild.id, "server_id": ServerID})
                await self.ss_collection.update_many(
                    {"guild_id": interaction.guild.id, "server_id": {"$gt": ServerID}},
                    {"$inc": {"server_id": -1}},
                )
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="SteamDedicatedServer",
                        description="サーバーの削除に成功しました。",
                        color=0x00FF00,
                    ),
                    ephemeral=True,
                )
                return
            else:
                await interaction.followup.send(
                    embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xFF0000),
                    ephemeral=True,
                )
                return
        except Exception as err:
            await interaction.followup.send(f"サーバー削除時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(
        name="list",
        description="Show list of Steam Dedicated Server",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーの一覧を表示します"},
    )
    async def list_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
                if len(servers) == 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="このDiscordサーバーにはSteam非公式サーバーは追加されていません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                embed = nextcord.Embed(
                    title="SteamDedicatedServer", description=interaction.guild.name, color=0x00FF00
                )
                for server in servers:
                    embed.insert_field_at(
                        index=server["server_id"] - 1,
                        name=f"ID: `{server['server_id']}`\n保存名: `{server['sv_nm']}`",
                        value=f"アドレス：`{server['sv_ad'][0]}:{server['sv_ad'][1]}`",
                    )
                await interaction.user.send(embed=embed)
                await interaction.followup.send("Sended!", ephemeral=True)
                return
            else:
                await interaction.followup.send(
                    embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xFF0000),
                    ephemeral=True,
                )
                return
        except Exception as err:
            await interaction.followup.send(f"Steam非公式サーバーの一覧表示時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(
        name="sort",
        description="Replace servers",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーの一覧を入れ替えます"},
    )
    async def sort_slash(
        self,
        interaction: Interaction,
        SortSource: int = SlashOption(
            name="source",
            name_localizations={nextcord.Locale.ja: "置き替え元のサーバーid"},
            description="Source server ID",
            description_localizations={nextcord.Locale.ja: "置き換え元のサーバーID"},
            required=True,
        ),
        SortDestination: int = SlashOption(
            name="destination",
            name_localizations={nextcord.Locale.ja: "置き替え先のサーバーid"},
            description="Destination server ID",
            description_localizations={nextcord.Locale.ja: "置き換え先のサーバーID"},
            required=True,
        ),
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
                if len(servers) == 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="このDiscordサーバーにはSteam非公式サーバーは追加されていません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if SortSource > len(servers) or SortDestination > len(servers):
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="指定されたIDのSteam非公式サーバーは存在しません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if SortSource == SortDestination:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="置き換え元と置き換え先が同じです。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if SortSource <= 0 or SortDestination <= 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xFF0000),
                        ephemeral=True,
                    )
                    return
                await self.ss_collection.update_one(
                    {"guild_id": interaction.guild.id, "server_id": SortSource},
                    {"$set": {"server_id": 0}},
                )
                await self.ss_collection.update_one(
                    {"guild_id": interaction.guild.id, "server_id": SortDestination},
                    {"$set": {"server_id": SortSource}},
                )
                await self.ss_collection.update_one(
                    {"guild_id": interaction.guild.id, "server_id": 0},
                    {"$set": {"server_id": SortDestination}},
                )
                await interaction.followup.send("ソートが完了しました。", ephemeral=True)
                return
            else:
                await interaction.followup.send(
                    embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xFF0000),
                    ephemeral=True,
                )
                return
        except Exception as err:
            await interaction.followup.send(f"ソート時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(
        name="edit",
        description="Edit Steam Dedicated Server Setting",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーの設定を編集します"},
    )
    async def edit_slash(
        self,
        interaction: Interaction,
        EditSource: int = SlashOption(
            name="server_id",
            name_localizations={nextcord.Locale.ja: "サーバーid"},
            description="Server ID of want to edit",
            description_localizations={nextcord.Locale.ja: "編集するSteam非公式サーバーID"},
            required=True,
        ),
        ServerName: str = SlashOption(
            name="name",
            name_localizations={nextcord.Locale.ja: "サーバー名"},
            description="Name of server (if server is offline, it shows.)",
            description_localizations={nextcord.Locale.ja: "オフライン時に表示されるSteam非公式サーバーの名前"},
            required=True,
        ),
        ServerAddress: str = SlashOption(
            name="address",
            name_localizations={nextcord.Locale.ja: "サーバーアドレス"},
            description="Address of server",
            description_localizations={nextcord.Locale.ja: "Steam非公式サーバーのIPアドレスまたはドメイン名"},
            required=True,
        ),
        ServerPort: int = SlashOption(
            name="port",
            name_localizations={nextcord.Locale.ja: "サーバーポート"},
            description="Port of server",
            description_localizations={nextcord.Locale.ja: "Steam非公式サーバーのポート番号"},
            required=True,
        ),
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
                if len(servers) == 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="このDiscordサーバーにはSteam非公式サーバーは追加されていません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if EditSource > len(servers):
                    await interaction.followup.send(
                        embed=nextcord.Embed(
                            title="SteamDedicatedServer",
                            description="指定されたIDのSteam非公式サーバーは存在しません。",
                            color=0xFF0000,
                        ),
                        ephemeral=True,
                    )
                    return
                if EditSource <= 0:
                    await interaction.followup.send(
                        embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xFF0000),
                        ephemeral=True,
                    )
                    return
                await self.ss_collection.update_one(
                    {"guild_id": interaction.guild.id, "server_id": EditSource},
                    {"$set": {"sv_nm": ServerName, "sv_ad": (ServerAddress, ServerPort)}},
                )
                await interaction.followup.send("編集が完了しました。", ephemeral=True)
            else:
                await interaction.followup.send(
                    embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xFF0000),
                    ephemeral=True,
                )
                return
        except Exception as err:
            await interaction.followup.send(f"編集時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="auto", description="Get Steam Dedicated Server's status automatically.")
    async def auto_slash(self, interaction: Interaction):
        pass

    @auto_slash.subcommand(
        name="on",
        description="Enable to display Steam Dedicated Server's Realtime Status",
        description_localizations={nextcord.Locale.ja: "鯖のステータスをリアルタイム表示します"},
    )
    async def auto_on_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
        if len(servers) == 0:
            await interaction.followup.send("このDiscordサーバーにはSteam非公式サーバーが登録されていません。", ephemeral=True)
            return
        auto_doc = await self.auto_collection.find_one({"guild_id": interaction.guild.id})
        if auto_doc is not None:
            await interaction.followup.send(f"既に{interaction.guild.name}で他のAutoSSタスクが実行されています。", ephemeral=True)
            return
        mes_ss = await interaction.channel.send("AutoSSの準備をしています...")
        asyncio.ensure_future(ss_force(self.bot, mes_ss))
        await self.auto_collection.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"channel_id": interaction.channel.id, "message_id": mes_ss.id}},
            upsert=True,
        )
        await interaction.followup.send("AutoSSを開始しました。")

    @auto_slash.subcommand(
        name="off",
        description="Disable to display Steam Dedicated Server's Realtime Status",
        description_localizations={nextcord.Locale.ja: "鯖のステータスをリアルタイム表示を無効にします。"},
    )
    async def auto_off_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        auto_doc = await self.auto_collection.find_one({"guild_id": interaction.guild.id})
        if auto_doc is None:
            await interaction.followup.send(f"既に{interaction.guild.name}で他のAutoSSタスクが実行されています。", ephemeral=True)
            return
        try:
            await self.auto_collection.delete_one({"guild_id": interaction.guild.id})
            await interaction.followup.send("AutoSSを無効にしました。", ephemeral=True)
            return
        except Exception as err:
            await interaction.followup.send(embed=self.bot.error_embed(err), ephemeral=True)
            return

    @ss_slash.subcommand(
        name="status",
        description="Display Steam Dedicated Server's Status",
        description_localizations={nextcord.Locale.ja: "Steam非公式サーバーのステータスを表示します"},
    )
    async def status_slash(
        self,
        interaction: Interaction,
        server_id: str = SlashOption(
            name="server_id",
            description="デフォルトは空白。特定のSteam非公式サーバーだけ指定したい場合はIDを入力してください。又はallで詳細に表示します。",
            required=False,
        ),
    ):
        await interaction.response.defer()
        servers = await self.ss_collection.find({"guild_id": interaction.guild.id}).to_list(length=None)
        try:
            if server_id == "all":
                if len(servers) == 0:
                    await interaction.followup.send("このDiscordサーバーにはSteam非公式サーバーが登録されていません。", ephemeral=True)
                    return
                semi_embed = SemiEmbed(
                    title="Server Status Checker",
                    description=f"{interaction.user.mention}\n:globe_with_meridians: Status",
                    color=0x00FF00,
                )
                for server in sorted(servers, key=lambda x: x['server_id']):
                    semi_embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.DETAIL)))
                await interaction.followup.send(embeds=semi_embed.get_embeds(), view=Recheck_SS_Embed(self.bot))
                return

            elif server_id is not None:
                if len(servers) == 0:
                    await interaction.followup.send("このDiscordサーバーにはSteam非公式サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(
                    title="Server Status Checker",
                    description=f"{interaction.user.mention}\n:globe_with_meridians: Status",
                    color=0x00FF00,
                )
                server = await self.ss_collection.find_one({"guild_id": interaction.guild.id, "server_id": server_id})
                embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.NORMAL)))
                await interaction.followup.send(embed=embed)
                return

            else:
                if len(servers) == 0:
                    await interaction.followup.send("このDiscordサーバーにはSteam非公式サーバーは登録されていません。", ephemeral=True)
                    return
                semi_embed = SemiEmbed(
                    title="Server Status Checker",
                    description=f"{interaction.user.mention}\n:globe_with_meridians: Status",
                    color=0x00FF00,
                )
                for server in sorted(servers, key=lambda x: x['server_id']):
                    semi_embed.add_field(**(await server_check.server_check(server, server_check.EmbedType.NORMAL)))
                await interaction.followup.send(embeds=semi_embed.get_embeds(), view=Recheck_SS_Embed(self.bot))
                return

        except Exception as err:
            await interaction.followup.send(f"ステータス取得時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(
        name="reload",
        description="Reload AutoSS Status",
        description_localizations={nextcord.Locale.ja: "AutoSSを更新します。"},
    )
    async def ss_reload(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        auto_doc = await self.auto_collection.find_one({"guild_id": interaction.guild.id})

        if auto_doc is None:
            await interaction.send(f"{interaction.guild.name}では、AutoSSは実行されていません。", ephemeral=True)
        else:
            channel = await self.bot.resolve_channel(auto_doc["channel_id"])
            message = await channel.fetch_message(auto_doc["message_id"])
            asyncio.ensure_future(ss_force(self.bot, message))
            await interaction.send("リロードしました。", ephemeral=True)

    @tasks.loop(minutes=5.0)
    async def check_status_pin_loop(self):
        await self.bot.wait_until_ready()
        async for autoConfig in self.auto_collection.find():
            message = None
            try:
                servers = await self.ss_collection.find({"guild_id": autoConfig["guild_id"]}).to_list(length=None)
                if len(servers) == 0:
                    logging.info(f"Steam非公式サーバーが設定されていないため、設定を削除します。\nGuildID:{autoConfig['guild_id']}\nChannelID:{autoConfig['channel_id']}\nMessageID:{autoConfig['message_id']}")
                    await self.auto_collection.delete_one({"guild_id": autoConfig["guild_id"]})
                    continue

                channel = await self.bot.resolve_channel(autoConfig["channel_id"])
                assert isinstance(channel, nextcord.TextChannel)

                message = await channel.fetch_message(autoConfig["message_id"])
                semi_embed = SemiEmbed(
                    title="ServerStatus Checker",
                    description=f"最終更新: `{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}`",
                    color=0x00FF00,
                )
                for server in sorted(servers, key=lambda x: x['server_id']):
                    semi_embed.add_field(**(await server_check.ss_pin_embed(server)))
                await message.edit(
                    content=(
                        "AutoSS実行中\n"
                        f"止めるには`{self.bot.command_prefix}ss auto off`または`/ss off`\n"
                        "リロードするには下の`再読み込み`ボタンか`/ss reload`\n"
                        "止まった場合は一度オフにしてから再度オンにしてください"
                    ),
                    embeds=semi_embed.get_embeds(),
                    view=Reload_SS_Auto(self.bot, message),
                )
                logging.info("Status loaded.(Scheduled)")
            except nextcord.errors.NotFound | nextcord.errors.Forbidden | nextcord.errors.InvalidData | AssertionError:
                # auto_collectionのデータベースから指定Guildのデータを消す
                logging.info(f"チャンネルにアクセスできなかったため、設定を削除します。\nGuildID:{autoConfig['guild_id']}\nChannelID:{autoConfig['channel_id']}\nMessageID:{autoConfig['message_id']}")
                await self.auto_collection.delete_one({"guild_id": autoConfig["guild_id"]})
                continue
            except nextcord.errors.HTTPException:
                # HTTPのエラーのため本当はやめなきゃいけないけどとりあえず10秒で進めておく
                logging.error("HTTPException", traceback.format_exc())
                await asyncio.sleep(10)
                continue
            except Exception as err:
                logging.error("ServerStatusAutoSSError", err, traceback.format_exc())
                if message is not None:
                    await message.edit(
                        content=(
                            "AutoSSのループ内でエラーが発生しました。\n"
                            "`再読み込み`ボタン又は`/ss reload`コマンドでリロードしてください。\n"
                            f"```sh\n{traceback.format_exc()}```"
                        ),
                        embed=None,
                    )
                continue

def setup(bot: NIRA, **kwargs):
    bot.add_cog(server_status(bot, **kwargs))
    importlib.reload(server_check)
    logging.info("Setup `server_status` cog.")


def teardown(bot):
    logging.info("Teardown `server_status` cog.")
