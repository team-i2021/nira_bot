import asyncio
import datetime
import importlib
import logging
import os
import re
import sys
import traceback

import HTTP_db
import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands, tasks

from util import admin_check, eh, n_fc, server_check, database
from util.nira import NIRA

# loggingの設定

SYSDIR = sys.path[0]

ss_check_result = {}

class steam_server:
    name = "steam_server"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

class autoss_list:
    name = "autoss_check"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE

async def ss_force(self, message: nextcord.Message):
    await message.edit(content="Loading status...", view=None)
    try:
        embed = nextcord.Embed(
            title="ServerStatus Checker", description=f"LastCheck:`{datetime.datetime.now()}`", color=0x00ff00)
        for i in range(int(steam_server.value[message.guild.id]["value"])):
            await server_check.ss_pin_embed(self.bot.client, embed, message.guild.id, i + 1)
        embed.set_footer(text="pingは参考値です")
        await message.edit(
            f"AutoSS実行中\n止めるには`{self.bot.command_prefix}ss auto off`または`/ss off`\nリロードするには下の`再読み込み`ボタンか`/ss reload`\n止まった場合は一度オフにしてから再度オンにしてください",
            embed=embed,
            view=Reload_SS_Auto(self.bot, message, self.bot.client)
        )
        logging.info("Status loaded.(Not scheduled)")
    except Exception as err:
        logging.info(err, traceback.format_exc())
        await message.edit(content=f"err:{err}")


# async def ss_pin(self, ment_id, message):
#    ss_check_result[message.guild.id] = {}
#    await message.edit(content=f"チェックシステムを有効化しています...")
#    logging.info(f"{message.guild.name}にてAutoSSが有効になりました。")
#    while True:
#        await message.edit(content=f"現在チェックを行っています...\n最終チェック時刻：`{datetime.datetime.now()}`")
#        logging.info(f"{message.guild.name}でのAutoSSチェックを実行します。")
#        for i in map(str, range(1, int(steam_server.value[message.guild.id]["value"])+1)):
#            if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                # 鯖落ちしてかもるよ
#                await message.edit(content=f"チェック結果：失敗(1/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（1/3回目）")
#                await asyncio.sleep(5)
#                if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                    await message.edit(content=f"チェック結果：失敗(2/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                    logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（2/3回目）")
#                    await asyncio.sleep(5)
#                    if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                        await message.edit(content=f"チェック結果：失敗(3/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（3/3回目）")
#                        await message.edit(content=f"チェック結果：失敗(メッセージを送信して終了します。)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        await message.channel.send(f"<@{ment_id}> - もしかして鯖落ちしてたりしません...？\n\nAutoSSが無効になりました。\n一応`{self.bot.command_prefix}ss`で確認してみましょう！")
#                        del n_fc.pid_ss[message.guild.id]
#                        return False
#            # 正常だよ
#            logging.info(f"{message.guild.name}でのAutoSSチェック結果：成功")
#            await message.edit(content=f"最後のチェック結果：成功\n最終チェック時刻：`{datetime.datetime.now()}`")
#            await asyncio.sleep(5)
#        await asyncio.sleep(60*30) # 60秒*30＝30分


async def get_mes(bot, channel_id, message_id):
    ch_obj = await bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    return messs


async def launch_ss(self, channel_id, message_id):
    ch_obj = await self.bot.fetch_channel(channel_id)
    messs = await ch_obj.fetch_message(message_id)
    await ss_force(self, messs)


# async def ss_loop_goes(self, ment_id, message):
#    ss_check_result[message.guild.id] = {}
#    await message.edit(content=f"実行されています。")
#    logging.info(f"{message.guild.name}にてAutoSSが有効になりました。")
#    while True:
#        await message.edit(content=f"現在チェックを行っています...\n最終チェック時刻：`{datetime.datetime.now()}`")
#        logging.info(f"{message.guild.name}でのAutoSSチェックを実行します。")
#        for i in map(str, range(1, int(steam_server.value[message.guild.id]["value"])+1)):
#            if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                # 鯖落ちしてかもるよ
#                await message.edit(content=f"チェック結果：失敗(1/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                logging.error(f"{message.guild.name}でのAutoSSチェック結果：失敗（1/3回目）")
#                await asyncio.sleep(5)
#                if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                    await message.edit(content=f"チェック結果：失敗(2/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                    logging.error(
#                        f"{message.guild.name}でのAutoSSチェック結果：失敗（2/3回目）")
#                    await asyncio.sleep(5)
#                    if await server_check.server_check_loop(self.bot.loop, message.guild.id, i) == False:
#                        await message.edit(content=f"チェック結果：失敗(3/3)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        logging.error(
#                            f"{message.guild.name}でのAutoSSチェック結果：失敗（3/3回目）")
#                        await message.edit(content=f"チェック結果：失敗(メッセージを送信して終了します。)\n最終チェック時刻：`{datetime.datetime.now()}`")
#                        await message.channel.send(f"<@{ment_id}> - もしかして鯖落ちしてたりしません...？\n\nAutoSSが無効になりました。\n一応`{self.bot.command_prefix}ss`で確認してみましょう！")
#                        return False
#            # 正常だよ
#            logging.info(f"{message.guild.name}でのAutoSSチェック結果：成功")
#            await message.edit(content=f"最後のチェック結果：成功\n最終チェック時刻：`{datetime.datetime.now()}`")
#            await asyncio.sleep(5)
#        await asyncio.sleep(60*30)  # 60秒*30＝30分


# コマンド内部
async def ss_base(self, ctx: commands.Context):
    if ctx.message.content == f"{self.bot.command_prefix}ss":
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(
                title="Server Status Checker",
                description=f"{ctx.author.mention}\n:globe_with_meridians:Status\n==========",
                color=0x00ff00
            )
            for i in map(str, range(1, int(steam_server.value[ctx.guild.id]["value"])+1)):
                await server_check.server_check(self.bot.client, embed, 0, ctx.guild.id, i)
            await asyncio.sleep(1)
            await ctx.reply(embed=embed, view=Recheck_SS_Embed())
        return
    args = ctx.message.content.split(" ")

    if args[1] == "add":
        if len(args) == 1:
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}ss add [表示名] [IPアドレス],[ポート番号]```")
            return
        else:
            try:
                if ctx.guild.id not in steam_server.value:
                    steam_server.value[ctx.guild.id] = {"value": "0"}
                ad_name = str(args[2])
                address = " ".join(args[3:])
                ad_ip = str(re.sub("[^0-9a-zA-Z._-]",
                            "", address.split(",")[0]))
                ad_port = int(re.sub("[^0-9]", "", address.split(",")[1]))
                sset_point = int(steam_server.value[ctx.guild.id]["value"])
                steam_server.value[ctx.guild.id][f"{sset_point + 1}_ad"] = (
                    ad_ip, ad_port)
                steam_server.value[ctx.guild.id][f"{sset_point + 1}_nm"] = ad_name
                steam_server.value[ctx.guild.id]["value"] = str(
                    sset_point + 1)
                await ctx.reply(f"サーバー名：{ad_name}\nサーバーアドレス: ({ad_ip},{ad_port})")
                await database.default_push(self.bot.client, steam_server)
                return
            except Exception as err:
                await ctx.reply(f"サーバー追加時にエラーが発生しました。\n```sh\n{err}```")
                return

    elif args[1] == "list":
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        else:
            if admin_check.admin_check(ctx.guild, ctx.author):
                user = await self.bot.fetch_user(ctx.author.id)
                embed = nextcord.Embed(
                    title="Steam Server List", description=f"「{ctx.guild.name}」のサーバーリスト\n```保存数：{str(steam_server.value[ctx.guild.id]['value'])}```", color=0x00ff00)
                for i in range(int(steam_server.value[ctx.guild.id]['value'])):
                    embed.add_field(
                        name=f"ID: `{i+1}`\n保存名: `{str(steam_server.value[ctx.guild.id][f'{i+1}_nm'])}`", value=f"アドレス：`{str(steam_server.value[ctx.guild.id][f'{i+1}_ad'])}`")
                await user.send(embed=embed)
                await ctx.message.add_reaction("\U00002705")
                return
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return

    elif args[1] == "auto":
        if admin_check.admin_check(ctx.guild, ctx.author) == False:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
            return
        if ctx.message.content == f"{self.bot.command_prefix}ss auto":
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}ss auto on/off`"))
            return

        elif ctx.message.content[10:12] == "on":
            if ctx.guild.id in autoss_list.value:
                await ctx.reply(f"既に`{ctx.guild.name}`でAutoSSタスクが実行されています。\n`{self.bot.command_prefix}ss auto off`で終了してください。")
                return
            if ctx.guild.id not in steam_server.value:
                await ctx.reply("`SteamDedicated`サーバーが登録されていません。")
                return
            mes_ss = await ctx.channel.send(f"設定したメッセージをご確認ください！\n（メッセージが指定されていない場合はこのメッセージがすぐに切り替わります...）")
            if ctx.message.content == f"{self.bot.command_prefix}ss auto on":
                autoss_list.value[ctx.guild.id] = [ctx.channel.id, mes_ss.id]
                await database.default_push(self.bot.client, autoss_list)
                asyncio.ensure_future(ss_force(self, mes_ss))
                return
            else:
                cl, ms = int(ctx.message.content[16:].split(" ", 1)[0]), int(ctx.message.content[16:].split(" ", 1)[1])
                try:
                    messs = await (await self.bot.fetch_channel(cl)).fetch_message(ms)
                except Exception as err:
                    logging.error(err)
                    await ctx.reply("メッセージが見つかりませんでした。")
                    return
                await messs.edit(content="現在変更をしています...")
                autoss_list.value[ctx.guild.id] = [
                    int(ctx.message.content[16:].split(" ", 1)[0]),
                    int(ctx.message.content[16:].split(" ", 1)[1])
                ]
                await database.default_push(self.bot.client, autoss_list)
                asyncio.ensure_future(ss_force(self, messs))
                return

        elif ctx.message.content[10:13] == "off":
            if ctx.guild.id not in autoss_list.value:
                await ctx.reply("AutoSSは実行されていません。")
                return
            try:
                if ctx.guild.id in autoss_list.value:
                    del autoss_list.value[ctx.guild.id]
                    await database.default_push(self.bot.client, autoss_list)
                    await ctx.reply(f"AutoSSを無効にしました。\n再度有効にするには`{self.bot.command_prefix}ss auto on`または`/ss auto on`を使用してください。")
                    return
                else:
                    await ctx.reply("AutoSSは実行されていません。")
            except Exception as err:
                await ctx.reply(embed=eh.eh(self.bot.client, err))
                return

        else:
            if ctx.guild.id in autoss_list.value:
                await ctx.reply(f"`{self.bot.command_prefix}ss auto [on/off]`\nAutoSSは有効になっています。")
                return
            else:
                await ctx.reply(f"`{self.bot.command_prefix}ss auto [on/off]`\nAutoSSは無効になっています。")
                return
        return

    elif args[1] == "edit":
        if ctx.message.content == f"{self.bot.command_prefix}ss edit":
            await ctx.reply(f"構文が異なります。\n```{self.bot.command_prefix}ss edit [サーバーナンバー] [名前] [IPアドレス],[ポート番号]```")
            return
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        adre = ctx.message.content[10:].split(" ", 3)
        s_id = int("".join(re.findall(r'[0-9]', adre[0])))
        s_nm = str(adre[1])
        s_adre = str(adre[2]).split(",", 2)
        s_port = int(s_adre[1])
        s_ip = str(re.sub("[^0-9a-zA-Z._-]", "", s_adre[0]))
        b_value = int(steam_server.value[ctx.guild.id]["value"])
        if b_value < s_id:
            await ctx.reply(f"そのサーバーナンバーのサーバーは登録されていません！\n`{self.bot.command_prefix}ss list`で確認してみてください。")
            return
        try:
            steam_server.value[ctx.guild.id][f"{s_id}_ad"] = (s_ip, s_port)
            steam_server.value[ctx.guild.id][f"{s_id}_nm"] = s_nm
            await ctx.reply(f"サーバーナンバー：{s_id}\nサーバー名: {s_nm}\nサーバーアドレス: ({s_ip},{s_port})")
            await database.default_push(self.bot.client, steam_server)
            return
        except Exception as err:
            await ctx.reply(embed=eh.eh(self.bot.client, err))
            return

    elif args[1] == "sort":
        if len(args) != 4:
            await ctx.reply(f"引数が足りないか多いです。\n`{self.bot.command_prefix}ss sort [サーバーID1] [サーバーID2]`")
            return
        try:
            args[2] = int(args[2])
            args[3] = int(args[3])
        except ValueError:
            await ctx.reply("サーバーIDの欄には数値が入ります。")
            return
        if args[2] > int(steam_server.value[ctx.guild.id]["value"]) or args[3] > int(steam_server.value[ctx.guild.id]["value"]):
            await ctx.reply(f"{ctx.guild.name}に登録されているサーバーの数は{steam_server.value[ctx.guild.id]['value']}個です。\n無効なサーバーIDを指定しないでください。")
            return
        if args[2] <= 0 or args[3] <= 0:
            await ctx.reply(f"サーバーIDは1から順につけられます。\n無効なサーバーIDを指定しないでください。")
            return
        try:
            steam_server.value[ctx.guild.id][f"{args[2]}_nm"], steam_server.value[ctx.guild.id][f"{args[2]}_ad"], steam_server.value[ctx.guild.id][f"{args[3]}_nm"], steam_server.value[ctx.guild.id][
                f"{args[3]}_ad"] = steam_server.value[ctx.guild.id][f"{args[3]}_nm"], steam_server.value[ctx.guild.id][f"{args[3]}_ad"], steam_server.value[ctx.guild.id][f"{args[2]}_nm"], steam_server.value[ctx.guild.id][f"{args[2]}_ad"]
            await database.default_push(self.bot.client, steam_server)
            await ctx.reply("入れ替えが完了しました。")
            return
        except Exception as err:
            await ctx.reply(f"入れ替え中にエラーが発生しました。\n{err}")
            return

    elif args[1] == "del":
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        if ctx.message.content != f"{self.bot.command_prefix}ss del all":
            try:
                del_num = int(ctx.message.content[9:])
            except Exception as err:
                await ctx.reply(embed=eh.eh(self.bot.client, err))
                return
            if admin_check.admin_check(ctx.guild, ctx.author):
                if del_num > int(steam_server.value[ctx.guild.id]["value"]):
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"そのサーバーは登録されていません！\n`{self.bot.command_prefix}ss list`で確認してみてください！", color=0xff0000))
                    return
                if del_num <= 0:
                    await ctx.reply(embed=nextcord.Embed(title="エラー", description="リストで0以下のナンバーは振り当てられていません。", color=0xff0000))
                    return
                try:
                    all_value = int(
                        steam_server.value[ctx.guild.id]["value"])
                    for i in range(all_value - del_num):
                        steam_server.value[ctx.guild.id][
                            f"{del_num + i}_nm"] = steam_server.value[ctx.guild.id][f"{del_num + i + 1}_nm"]
                        steam_server.value[ctx.guild.id][
                            f"{del_num + i}_ad"] = steam_server.value[ctx.guild.id][f"{del_num + i + 1}_ad"]
                    del steam_server.value[ctx.guild.id][f"{all_value}_nm"]
                    del steam_server.value[ctx.guild.id][f"{all_value}_ad"]
                    steam_server.value[ctx.guild.id]["value"] = str(
                        all_value - 1)
                    await database.default_push(self.bot.client, steam_server)
                    await ctx.reply(embed=nextcord.Embed(title="削除", description=f"ID:{del_num}のサーバーをリストから削除しました。", color=0xff0000))
                except Exception as err:
                    logging.error(traceback.format_exc())
                    await ctx.reply(embed=eh.eh(self.bot.client, err))
                    return
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者権限がありません。", color=0xff0000))
                return
        else:
            del steam_server.value[ctx.guild.id]
            await database.default_push(self.bot.client, steam_server)
            await ctx.reply(embed=nextcord.Embed(title="リスト削除", description=f"{ctx.author.mention}\nリストは正常に削除されました。", color=0xffffff))
            return
        return

    elif args[1] == "all":
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(
                title="Server Status Checker",
                description=f"{ctx.author.mention}\n:globe_with_meridians:Status\n==========",
                color=0x00ff00
            )
            for i in map(str, range(1, int(steam_server.value[ctx.guild.id]["value"])+1)):
                await server_check.server_check(self.bot.client, embed, 1, ctx.guild.id, i)
            await asyncio.sleep(1)
            await ctx.reply(embed=embed)
            return

    elif args[1] == "debug":
        if not await self.bot.is_owner(ctx.author):
            raise NIRA.Forbidden()
        if len(args) == 2:
            await ctx.reply("Missing Arguments...")
        elif args[2] == "loop":
            await ctx.reply(embed=nextcord.Embed(
                title="Loop",
                description=f"Running: `{self.check_status_pin_loop.is_running()}`\nFailed: `{self.check_status_pin_loop.failed()}`\nNext Iteration: `{self.check_status_pin_loop.next_iteration}`",
                color=0x00ff00
            ))
        elif args[2] == "steam_server":
            await ctx.reply(embed=nextcord.Embed(
                title="Steam Server",
                description=f"{steam_server.value}",
                color=0x00ff00
            ))
        elif args[2] == "autoss_list":
            await ctx.reply(embed=nextcord.Embed(
                title="Auto Server Status List",
                description=f"{autoss_list.value}",
                color=0x00ff00
            ))


    elif len(args) > 2:
        await ctx.reply(f"""\
引数とか何かがおかしいです。

・SS系コマンド一覧
`{self.bot.command_prefix}ss`: 登録されているサーバーのステータスを表示します。
`{self.bot.command_prefix}ss add [表示名] [アドレス],[ポート]`: サーバーを追加します。
`{self.bot.command_prefix}ss list`: 登録されているサーバーの一覧を表示します。
`{self.bot.command_prefix}ss auto on`: 10分毎にステータスを更新するAutoSSのメッセージを送信します。
`{self.bot.command_prefix}ss auto off`: AutoSSを停止します。
`{self.bot.command_prefix}ss edit [サーバーID] [表示名] [アドレス],[ポート]`: 指定したサーバーIDの表示名やアドレスなどを修正します。事前に`{self.bot.command_prefix}ss list`などで確認しておくことを推奨します。
`{self.bot.command_prefix}ss sort [サーバーID1] [サーバーID2]`: サーバーID1とサーバID2の場所を入れ替えます。
`{self.bot.command_prefix}ss del [サーバーID]`: 指定したサーバーIDの情報を削除します。
`{self.bot.command_prefix}ss del all`: 登録されているサーバーをすべて削除します。
`{self.bot.command_prefix}ss all`: 登録されているサーバーのステータスをより詳細に表示します。あまりにサーバー数があると、メッセージ数規定に引っかかって送れない場合があります。
`{self.bot.command_prefix}ss [サーバーID]`: 指定したサーバーIDのステータスのみを表示します。""")
        return

    else:
        if ctx.guild.id not in steam_server.value:
            await ctx.reply("サーバーは登録されていません。")
            return
        async with ctx.channel.typing():
            embed = nextcord.Embed(
                title="Server Status Checker",
                description=f"{ctx.author.mention}\n:globe_with_meridians:Status\n==========",
                color=0x00ff00
            )
            await server_check.server_check(self.bot.client, embed, 0, ctx.guild.id, args[1])
            await asyncio.sleep(1)
            await ctx.reply(embed=embed)
            return


class Reload_SS_Auto(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, message: nextcord.Message, client: HTTP_db.Client):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = message
        self.client = client

    @nextcord.ui.button(label='再読み込み', style=nextcord.ButtonStyle.green)
    async def reload(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            asyncio.ensure_future(ss_force(self, self.message))
            await interaction.followup.send('Reloaded!', ephemeral=True)

        except Exception as err:
            await interaction.followup.send(f'エラーが発生しました。\n`{err}`\n```sh\n{traceback.format_exc()}```', ephemeral=True)
            logging.error(traceback.format_exc())


class Recheck_SS_Embed(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label='もう一度チェックする', style=nextcord.ButtonStyle.green)
    async def recheck(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer(with_message=True)
        try:
            embed = nextcord.Embed(
                title="Server Status Checker",
                description=f":globe_with_meridians:Status\n==========",
                color=0x00ff00
            )
            for i in map(str, range(1, int(steam_server.value[interaction.guild.id]["value"])+1)):
                await server_check.server_check(self.bot.client, embed, 0, interaction.guild.id, i)
            await interaction.followup.send(f'{interaction.user.mention} - Server Status', embed=embed, view=Recheck_SS_Embed())
            logging.info("rechecked")

        except Exception:
            await interaction.followup.send(f"エラーが発生しました。\n```\n{traceback.format_exc()}```")
            logging.err(traceback.format_exc())


class server_status(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.check_status_pin_loop.start()
        asyncio.ensure_future(database.default_pull(self.bot.client, steam_server))
        asyncio.ensure_future(database.default_pull(self.bot.client, autoss_list))

    def cog_unload(self):
        self.check_status_pin_loop.stop()

    @nextcord.message_command(name="AutoSSのスタート", guild_ids=n_fc.GUILD_IDS)
    async def start_auto_ss(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer(ephemeral=True)
        try:
            if message.author.id != self.bot.user.id:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="エラー",
                        description=f"{self.bot.user.mention}が送信したメッセージにのみこのコマンドを使用できます。",
                        color=0xff0000
                    ),
                    ephemeral=True
                )
                return
            CHANNEL_ID = message.channel.id
            MESSAGE_ID = message.id
            autoss_list.value[message.guild.id] = [
                CHANNEL_ID,
                MESSAGE_ID
            ]
            asyncio.ensure_future(ss_force(self, message))
            await interaction.followup.send(f"指定されたメッセージでAutoSSをスタートしました。")
        except Exception as err:
            await interaction.followup.send(f"エラーが発生しました。\n```\n{err}```")
        return

    @commands.command(name="ss", help="""\
Steam非公式サーバーのステータスを表示します
このコマンドは、**user毎**で**10秒**のクールダウンがあります。
このコマンドのヘルプは別ページにあります。
[ヘルプはこちら](https://sites.google.com/view/nira-bot/%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89/ss)""")
    @commands.cooldown(1, 10, type=commands.BucketType.user)
    async def ss(self, ctx: commands.Context):
        await ss_base(self, ctx)

    @nextcord.slash_command(name="ss", description="Show Steam Dedicated Server's status", guild_ids=n_fc.GUILD_IDS)
    async def ss_slash(self, interaction: Interaction):
        pass

    @ss_slash.subcommand(name="add", description="Steam非公式サーバーを追加します")
    async def add_slash(
        self,
        interaction: Interaction,
        ServerName: str = SlashOption(
            name="name",
            description="オフライン時に表示されるサーバーの名前",
            required=True
        ),
        ServerAddress: str = SlashOption(
            name="address",
            description="サーバーのIPアドレスまたはドメイン名",
            required=True
        ),
        ServerPort: int = SlashOption(
            name="port",
            description="サーバーのポート番号",
            required=True
        )
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in steam_server.value:
                    steam_server.value[interaction.guild.id] = {
                        "value": "0"}
                SSValue = int(
                    steam_server.value[interaction.guild.id]["value"])
                steam_server.value[interaction.guild.id][f"{SSValue + 1}_ad"] = (
                    ServerAddress, ServerPort)
                steam_server.value[interaction.guild.id][f"{SSValue + 1}_nm"] = ServerName
                steam_server.value[interaction.guild.id]["value"] = str(
                    SSValue + 1)
                await database.default_push(self.bot.client, steam_server)
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description=f"サーバーの追加に成功しました。\nサーバー名：`{ServerName}`\nサーバーアドレス: `{ServerAddress}:{ServerPort}`", color=0x00ff00), ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(f"サーバー追加時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="del", description="Steam非公式サーバーを削除します")
    async def del_slash(
        self,
        interaction: Interaction,
        ServerID: int = SlashOption(
            name="server_id",
            description="削除するサーバーのID",
            required=True
        )
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                if f"{ServerID}_ad" not in steam_server.value[interaction.guild.id]:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                    return
                all_count = int(steam_server.value[interaction.guild.id]["value"])
                for i in range(all_count - ServerID):
                    steam_server.value[interaction.guild.id][
                        f"{ServerID + i}_nm"] = steam_server.value[interaction.guild.id][f"{ServerID + i + 1}_nm"]
                    steam_server.value[interaction.guild.id][
                        f"{ServerID + i}_ad"] = steam_server.value[interaction.guild.id][f"{ServerID + i + 1}_ad"]
                del steam_server.value[interaction.guild.id][f"{ServerID}_nm"]
                del steam_server.value[interaction.guild.id][f"{ServerID}_ad"]
                steam_server.value[interaction.guild.id]["value"] = int(steam_server.value[interaction.guild.id]["value"]) - 1
                await database.default_push(self.bot.client, steam_server)
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description=f"サーバーの削除に成功しました。", color=0x00ff00), ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(f"サーバー削除時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="list", description="Steam非公式サーバーの一覧を表示します")
    async def list_slash(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(
                    steam_server.value[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                embed = nextcord.Embed(
                    title="SteamDedicatedServer", description=f"{interaction.guild.name}", color=0x00ff00)
                for i in range(1, SSValue + 1):
                    embed.add_field(
                        name=f"{i}番目のサーバー", value=f"サーバー名：`{steam_server.value[interaction.guild.id][f'{i}_nm']}`\nサーバーアドレス：`{steam_server.value[interaction.guild.id][f'{i}_ad'][0]}:{steam_server.value[interaction.guild.id][f'{i}_ad'][1]}`", inline=False)
                await interaction.user.send(embed=embed)
                await interaction.followup.send("Sended!", ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(f"サーバー一覧表示時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="sort", description="Steam非公式サーバーの一覧をソートします")
    async def sort_slash(
        self,
        interaction: Interaction,
        SortSource: int = SlashOption(
            name="source",
            description="置き換え元のサーバーID",
            required=True
        ),
        SortDestination: int = SlashOption(
            name="destination",
            description="置き換え先のサーバーID",
            required=True
        )
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(
                    steam_server.value[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                if SortSource > SSValue or SortDestination > SSValue:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                    return
                if SortSource == SortDestination:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="置き換え元と置き換え先が同じです。", color=0xff0000), ephemeral=True)
                    return
                if SortSource <= 0 or SortDestination <= 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xff0000), ephemeral=True)
                    return
                steam_server.value[interaction.guild.id][f"{SortSource}_nm"], steam_server.value[interaction.guild.id][f"{SortSource}_ad"], steam_server.value[interaction.guild.id][f"{SortDestination}_nm"], steam_server.value[interaction.guild.id][f"{SortDestination}_ad"] = steam_server.value[
                    interaction.guild.id][f"{SortDestination}_nm"], steam_server.value[interaction.guild.id][f"{SortDestination}_ad"], steam_server.value[interaction.guild.id][f"{SortSource}_nm"], steam_server.value[interaction.guild.id][f"{SortSource}_ad"]
                await database.default_push(self.bot.client, steam_server)
                await interaction.followup.send("ソートが完了しました。", ephemeral=True)
                return
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(f"ソート時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="edit", description="Steam非公式サーバーの一覧を編集します")
    async def edit_slash(
        self,
        interaction: Interaction,
        EditSource: int = SlashOption(
            name="server_id",
            description="編集するサーバーID",
            required=True
        ),
        ServerName: str = SlashOption(
            name="name",
            description="サーバー名",
            required=True
        ),
        ServerAddress: str = SlashOption(
            name="address",
            description="サーバーアドレス",
            required=True
        ),
        ServerPort: int = SlashOption(
            name="port",
            description="サーバーポート",
            required=True
        )
    ):
        await interaction.response.defer()
        try:
            if admin_check.admin_check(interaction.guild, interaction.user):
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="このサーバーにはSteam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                SSValue = int(
                    steam_server.value[interaction.guild.id]["value"])
                if SSValue == 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="Steam Dedicated Serverは追加されていません。", color=0xff0000), ephemeral=True)
                    return
                if EditSource > SSValue:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定されたIDのサーバーは存在しません。", color=0xff0000), ephemeral=True)
                    return
                if EditSource <= 0:
                    await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="指定したIDは不正です。", color=0xff0000), ephemeral=True)
                    return
                steam_server.value[interaction.guild.id][f"{EditSource}_nm"] = ServerName
                steam_server.value[interaction.guild.id][f"{EditSource}_ad"] = (
                    ServerAddress, ServerPort)
                await database.default_push(self.bot.client, steam_server)
                await interaction.followup.send("編集が完了しました。", ephemeral=True)
            else:
                await interaction.followup.send(embed=nextcord.Embed(title="SteamDedicatedServer", description="管理者権限がありません。", color=0xff0000), ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(f"編集時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="auto", description="Get Steam Dedicated Server's status automatically.")
    async def auto_slash(self, interaction: Interaction):
        pass

    @auto_slash.subcommand(name="on", description="鯖のステータスをリアルタイム表示します")
    async def auto_on_slash(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer(ephemeral=True)
        if interaction.guild.id in autoss_list.value:
            await interaction.followup.send(f"既に{interaction.guild.name}で他のAutoSSタスクが実行されています。", ephemeral=True)
            return
        if interaction.guild.id not in steam_server.value:
            await interaction.followup.send("サーバーが登録されていません。", ephemeral=True)
            return
        mes_ss = await interaction.channel.send(f"AutoSSの準備をしています...")
        asyncio.ensure_future(ss_force(self, mes_ss))
        autoss_list.value[interaction.guild.id] = [
            mes_ss.channel.id,
            mes_ss.id
        ]
        await database.default_push(self.bot.client, autoss_list)
        await interaction.followup.send("AutoSSを開始しました。")

    @auto_slash.subcommand(name="off", description="鯖のリアルタイムステータス表示をオフにします")
    async def auto_off_slash(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            if interaction.guild.id not in autoss_list.value:
                await interaction.followup.send("既に無効になっているか、コマンドが実行されていません。", ephemeral=True)
                return
            else:
                del autoss_list.value[interaction.guild.id]
                await database.default_push(self.bot.client, steam_server)
                await interaction.followup.send("AutoSSを無効にしました。", ephemeral=True)
                return
        except Exception as err:
            await interaction.followup.send(embed=eh.eh(self.bot.client, err), ephemeral=True)
            return

    @ss_slash.subcommand(name="status", description="Steam非公式サーバーのステータスを表示します")
    async def status_slash(
        self,
        interaction: Interaction,
        server_id: str = SlashOption(
            name="server_id",
            description="デフォルトは空白。特定のサーバーだけ指定したい場合はIDを入力してください。又はallで詳細に表示します。",
            required=False
        )
    ):
        await interaction.response.defer()

        try:
            if server_id == "all":
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(
                    title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server.value[interaction.guild.id]["value"])+1)):
                    await server_check.server_check(self.bot.client, embed, 1, interaction.guild.id, i)
                await interaction.followup.send(embed=embed)
                return

            elif server_id is not None:
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(
                    title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                server_check.server_check(self.bot.client, embed, 0, interaction.guild.id, server_id)
                await interaction.followup.send(embed=embed)
                return

            else:
                if interaction.guild.id not in steam_server.value:
                    await interaction.followup.send("サーバーは登録されていません。", ephemeral=True)
                    return
                embed = nextcord.Embed(
                    title="Server Status Checker", description=f"{interaction.user.mention}\n:globe_with_meridians:Status\n==========", color=0x00ff00)
                for i in map(str, range(1, int(steam_server.value[interaction.guild.id]["value"])+1)):
                    await server_check.server_check(self.bot.client, embed, 0, interaction.guild.id, i)
                await interaction.followup.send(embed=embed, view=Recheck_SS_Embed())
                return

        except Exception as err:
            await interaction.followup.send(f"ステータス取得時にエラーが発生しました。\n```sh\n{err}```", ephemeral=True)
            return

    @ss_slash.subcommand(name="reload", description="AutoSSを更新します。")
    async def reload(self, interaction: Interaction):
        if interaction.guild.id not in autoss_list.value:
            await interaction.response.send_message(f"{interaction.guild.name}では、AutoSSは実行されていません。", ephemeral=True)
            return
        else:
            message = await (await self.bot.fetch_channel(autoss_list.value[interaction.guild.id][0])).fetch_message(autoss_list.value[interaction.guild.id][1])
            asyncio.ensure_future(ss_force(self, message))
            await interaction.response.send_message("リロードしました。", ephemeral=True)
            return

    @tasks.loop(minutes=5.0)
    async def check_status_pin_loop(self):
        await self.bot.wait_until_ready()
        for CHANNEL, MESSAGE in autoss_list.value.values():
            try:
                message: nextcord.PartialMessage = (self.bot.get_channel(CHANNEL)).get_partial_message(MESSAGE)
                embed = nextcord.Embed(
                    title="ServerStatus Checker",
                    description=f"LastCheck:`{datetime.datetime.now()}`",
                    color=0x00ff00
                )
                for i in range(int(steam_server.value[message.guild.id]["value"])):
                    await server_check.ss_pin_embed(self.bot.client, embed, message.guild.id, i + 1)
                embed.set_footer(text="pingは参考値です")
                await message.edit(
                    f"AutoSS実行中\n止めるには`{self.bot.command_prefix}ss auto off`または`/ss off`\nリロードするには下の`再読み込み`ボタンか`/ss reload`\n止まった場合は一度オフにしてから再度オンにしてください",
                    embed=embed,
                    view=Reload_SS_Auto(self.bot, message, self.bot.client)
                )
                logging.info("Status loaded.(Scheduled)")
            except Exception as err:
                logging.info(err, traceback.format_exc())
                await message.edit(content=f"AutoSSのループ内でエラーが発生しました。\n`再読み込み`ボタン又は`/ss reload`コマンドでリロードしてください。\n```sh\n{traceback.format_exc()}```", embed=None)


def setup(bot, **kwargs):
    bot.add_cog(server_status(bot, **kwargs))
    importlib.reload(server_check)
    logging.info("Setup `server_status` cog.")


def teardown(bot):
    logging.info("Teardown `server_status` cog.")
