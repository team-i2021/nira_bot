import asyncio
import logging
import os
import sys
import traceback

import HTTP_db
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands, tasks

from util import admin_check, n_fc, eh, dict_list, database
from util.nira import NIRA

# ボトムアップ的な機能

class pin_message:
    name = "bottom_up"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


#async def MessagePin(client, bot):
#    while True:
#        try:
#            for i in pin_message.value.keys():
#                for j in pin_message.value[i].keys():
#                    CHANNEL = bot.fetch_channel(j)
#                    if CHANNEL.last_message.content == pin_message.value[i][j] and CHANNEL.last_message.author.id == bot.user.id:
#                        continue
#                    messages = await CHANNEL.history(limit=10).flatten()
#                    for message in messages:
#                        if message.content == pin_message.value[i][j] and message.author.id == bot.user.id:
#                            await message.delete()
#                    await CHANNEL.send(pin_message.value[i][j])
#            await asyncio.sleep(5)
#        except Exception:
#            pass



class BottomModal(nextcord.ui.Modal):
    def __init__(self, client: HTTP_db.Client):
        super().__init__(
            "下部ピン留め",
            timeout=None,
        )

        self.client = client

        self.mes = nextcord.ui.TextInput(
            label="ピン留めしたい文章",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="このチャンネルでたくさん話したらずんだ餅にするよ！",
            required=True,
        )
        self.add_item(self.mes)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        if interaction.guild.id not in pin_message.value:
            pin_message.value[interaction.guild.id] = {
                interaction.channel.id: self.mes.value}
        else:
            pin_message.value[interaction.guild.id][interaction.channel.id] = self.mes.value
        await database.default_push(self.client, pin_message)
        await interaction.response.send_message(f"ピン留めを保存しました。", embed=nextcord.Embed(title="ピン留め", description=self.mes.value), ephemeral=True)


class Bottomup(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self._queue = {}
        asyncio.ensure_future(database.default_pull(self.bot.client, pin_message))
        if not self.checkPin.is_running():
            self.checkPin.start()

    def cog_unload(self):
        self.checkPin.stop()

    @commands.command(name="pin", aliases=("Pin", "bottomup", "ピン留め", "ピン"), help="""\
特定のメッセージを一番下に持ってくることで、いつでもみれるようにする、ピン留めの改良版。

`n!pin on [メッセージ内容...(複数行可)]`

他の誰かがメッセージを送った場合、どんどんどんどんその特定のメッセージを送ると言うような感じの機能です。
Webhookは使いたくない精神なので、ニラBOTが直々に送ってあげます。感謝しなさい。

offにするには、`n!pin off`と送信してください。

前に送ったピンメッセージが削除されずに送信されて、残っている場合は、にらBOTに適切な権限が与えられているか確認してみてください。
もしくは、周期内にめちゃくちゃメッセージを送信された場合はメッセージが削除されないです。仕様です。許してヒヤシンス。""")
    async def pin(self, ctx: commands.Context):
        if admin_check.admin_check(ctx.guild, ctx.author):
            args = ctx.message.content.split(" ", 2)
            if len(args) == 1:
                await ctx.reply(f"セットするには`{self.bot.command_prefix}pin on [メッセージ内容...(複数行可)]` と送ってください。\nセット解除するには`{self.bot.command_prefix}pin off`と送ってください。")
                return
            if args[1] == "on":
                if len(args) != 3:
                    await ctx.reply(f"・エラー\n引数が足りません。\n`{self.bot.command_prefix}pin on [メッセージ内容]`または`{self.bot.command_prefix}pin off`")
                    return
                if ctx.guild.id not in pin_message.value:
                    pin_message.value[ctx.guild.id] = {ctx.channel.id: args[2]}
                else:
                    pin_message.value[ctx.guild.id][ctx.channel.id] = args[2]
                await database.default_push(self.bot.client, pin_message)
                await ctx.message.add_reaction("\U0001F197")
                await ctx.reply("Ok")
            elif args[1] == "off":
                if ctx.guild.id not in pin_message.value or ctx.channel.id not in pin_message.value[ctx.guild.id]:
                    await ctx.reply("このチャンネルにはpinメッセージはありません。")
                    return
                else:
                    messages = await ctx.channel.history(limit=10).flatten()
                    search_message = pin_message.value[ctx.guild.id][ctx.channel.id]
                    del pin_message.value[ctx.guild.id][ctx.channel.id]
                    await database.default_push(self.bot.client, pin_message)
                    for i in messages:
                        if i.content == search_message:
                            await i.delete()
                    await ctx.reply("登録を解除しました。")
                    return
            elif args[1] == "debug":
                if not await self.bot.is_owner(ctx.author):
                    await ctx.reply("権限があります。じゃなかった...ありません。")
                    return
                if args[2] == "next":
                    await ctx.reply(self.checkPin.next_iteration)
                    return
                elif args[2] == "check":
                    await ctx.reply(self.checkPin.failed())
                    return
                elif args[2] == "start":
                    self.checkPin.start()
                    await ctx.reply("start")
                    return
                elif args[2] == "stop":
                    self.checkPin.stop()
                    await ctx.reply("stop")
                    return
                elif args[2] == "get":
                    await ctx.reply(self.checkPin.get_task())
                elif args[2] == "queue":
                    await ctx.reply(embed=nextcord.Embed(title="Queue", description=str(self._queue)))
                    logging.info(self._queue)
            else:
                await ctx.reply(f"・エラー\n使い方が違います。\n`{self.bot.command_prefix}pin on [メッセージ内容]`または`{self.bot.command_prefix}pin off`")
                return
        else:
            await ctx.reply("あなたには権限がありません。")
            return

    @nextcord.message_command(name="Set BottomPin", name_localizations={nextcord.Locale.ja: "下部ピン留めする"} ,guild_ids=n_fc.GUILD_IDS)
    async def pin_message_command(self, interaction: Interaction, message: nextcord.Message):
        if not admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.response.send_message("あなたには管理者権限がありません。", ephemeral=True)
        if message.content is None or message.content == "":
            await interaction.response.send_message(f"指定されたメッセージには本文がありません。", ephemeral=True)
        if interaction.guild.id not in pin_message.value:
            pin_message.value[interaction.guild.id] = {
                interaction.channel.id: message.content}
        else:
            pin_message.value[interaction.guild.id][interaction.channel.id] = message.content
        await database.default_push(self.bot.client, pin_message)
        await interaction.response.send_message(f"ピン留めを保存しました。", embed=nextcord.Embed(title="ピン留め", description=message.content), ephemeral=True)

    @nextcord.slash_command(name="pin", description="BottomUp command", guild_ids=n_fc.GUILD_IDS)
    async def pin_slash(self, interaction: Interaction):
        pass

    @pin_slash.subcommand(name="on", description="Turn ON the bottom pin message", description_localizations={nextcord.Locale.ja: "下部ピン留めをONにする"})
    async def on_slash(
        self,
        interaction: Interaction
    ):
        if admin_check.admin_check(interaction.guild, interaction.user):
            await interaction.response.send_modal(BottomModal(self.bot.client))
        else:
            await interaction.response.send_message("あなたには管理者権限がありません。", ephemeral=True)
            return

    @pin_slash.subcommand(name="off", description="Turn OFF the bottom pin message", description_localizations={nextcord.Locale.ja: "下部ピン留めをOFFにする"})
    async def off_slash(
        self,
        interaction: Interaction,
    ):
        await interaction.response.defer(ephemeral=True)
        if admin_check.admin_check(interaction.guild, interaction.user):
            try:
                if interaction.guild.id not in pin_message.value or interaction.channel.id not in pin_message.value[interaction.guild.id]:
                    await interaction.followup.send("このチャンネルにはpinメッセージはありません。", ephemeral=True)
                else:
                    messages = await interaction.channel.history(limit=10).flatten()
                    search_message = pin_message.value[interaction.guild.id][interaction.channel.id]
                    del pin_message.value[interaction.guild.id][interaction.channel.id]
                    for i in messages:
                        if i.content == search_message:
                            await i.delete()
                    await database.default_push(self.bot.client, pin_message)
                    await interaction.followup.send("登録を解除しました。", ephemeral=True)
            except Exception:
                await interaction.followup.send(f"エラーが発生しました。\n```sh\n{traceback.format_exc()}```", ephemeral=True)
                return
        else:
            await interaction.followup.send("あなたには管理者権限がありません。", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.id == self.bot.user.id:
            return
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if isinstance(message.channel, nextcord.GroupChannel):
            return
        if message.guild.id not in pin_message.value:
            return
        self._queue[message.channel.id] = message



    @tasks.loop(seconds=3)
    async def checkPin(self):
        await self.bot.wait_until_ready()
        for i in pin_message.value.keys():
            for j in pin_message.value[i].keys():
                CHANNEL = self.bot.get_channel(j)
                if CHANNEL is None:
                    try:
                        CHANNEL = await self.bot.fetch_channel(j)
                    except Exception:
                        continue
                    continue
                if j not in self._queue:
                    self._queue[j] = await CHANNEL.fetch_message(CHANNEL.last_message_id)

                if self._queue is not None:
                    try:
                        if CHANNEL.last_message is not None:
                            if (CHANNEL.last_message.content == pin_message.value[i][j] and CHANNEL.last_message.author.id == self.bot.user.id):
                                continue
                    except Exception:
                        logging.error(traceback.format_exc())
                        continue
                    messages = await CHANNEL.history(limit=10).flatten()
                    if messages[0].content == pin_message.value[i][j] and messages[0].author.id == self.bot.user.id:
                        continue
                    for message in messages:
                        if message.content == pin_message.value[i][j] and message.author.id == self.bot.user.id:
                            try:
                                await message.delete()
                            except Exception:
                                logging.error(traceback.format_exc())
                                continue
                    await CHANNEL.send(pin_message.value[i][j])
                    self._queue[j] = None


# logging.error(traceback.format_exc())


def setup(bot, **kwargs):
    bot.add_cog(Bottomup(bot, **kwargs))

def teardown(bot, **kwargs):
    print("Pin: teardown!")
