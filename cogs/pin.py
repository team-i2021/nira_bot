import asyncio
from nextcord.ext import commands, tasks
import nextcord
import os
import sys
from nextcord import Interaction, SlashOption, ChannelType
import traceback
import logging

sys.path.append('../')
from util import admin_check, n_fc, eh

# ボトムアップ的な機能


async def MessagePin(bot: nextcord.ext.commands.bot.Bot):
    while True:
        try:
            for i in n_fc.pinMessage.keys():
                for j in n_fc.pinMessage[i].keys():
                    CHANNEL = await bot.fetch_channel(j)
                    if CHANNEL.last_message.content == n_fc.pinMessage[i][j] and CHANNEL.last_message.author.id == bot.user.id:
                        continue
                    messages = await CHANNEL.history(limit=10).flatten()
                    for message in messages:
                        if message.content == n_fc.pinMessage[i][j] and message.author.id == bot.user.id:
                            await message.delete()
                    await CHANNEL.send(n_fc.pinMessage[i][j])
            await asyncio.sleep(5)
        except BaseException:
            pass


class bottomup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="pin", aliases=("Pin","bottomup","ピン留め","ピン"), help="""\
特定のメッセージを一番下に持ってくることで、いつでもみれるようにする、ピン留めの改良版。

`n!pin on [メッセージ内容...(複数行可)]`

他の誰かがメッセージを送った場合、どんどんどんどんその特定ののメッセージを送ると言うような感じの機能です。
Webhookは使いたくない精神なので、ニラBOTが直々に送ってあげます。感謝しなさい。

offにするには、`n!pin off`と送信してください。

前に送ったピンメッセージが削除されずに送信されて、残っている場合は、にらBOTに適切な権限が与えられているか確認してみてください。
もしくは、周期内にめちゃくちゃメッセージを送信された場合はメッセージが削除されないです。仕様です。許してヒヤシンス。
""")
    async def pin(self, ctx: commands.Context):
        if ctx.author.id != 669178357371371522:
            return
        if admin_check.admin_check(ctx.guild, ctx.author):
            args = ctx.message.content.split(" ", 2)
            if len(args) == 1:
                await ctx.reply("`n!pin on [メッセージ内容...(複数行可)]` と送ってください。")
                return
            if args[1] == "on":
                if len(args) != 3:
                    await ctx.reply("・エラー\n引数が足りません。\n`n!pin on [メッセージ内容]`または`n!pin off`")
                    return
                if ctx.guild.id not in n_fc.pinMessage:
                    n_fc.pinMessage[ctx.guild.id] = {ctx.channel.id: args[2]}
                else:
                    n_fc.pinMessage[ctx.guild.id][ctx.channel.id] = args[2]
                await ctx.message.add_reaction("\U0001F197")
                await ctx.reply("Ok")
            elif args[1] == "off":
                if ctx.guild.id not in n_fc.pinMessage or ctx.channel.id not in n_fc.pinMessage[ctx.guild.id]:
                    await ctx.reply("このチャンネルにはpinメッセージはありません。")
                    return
                else:
                    messages = await ctx.channel.history(limit=10).flatten()
                    search_message = n_fc.pinMessage[ctx.guild.id][ctx.channel.id]
                    del n_fc.pinMessage[ctx.guild.id][ctx.channel.id]
                    for i in messages:
                        if i.content == search_message:
                            await i.delete()
                    await ctx.reply("登録を解除しました。")
                    return
            else:
                await ctx.reply("・エラー\n使い方が違います。\n`n!pin on [メッセージ内容]`または`n!pin off`")
                return
        else: await ctx.reply("あなたには権限がありません。"); return


    @nextcord.slash_command(name="pin", description="メッセージ下部ピン留め機能", guild_ids=n_fc.GUILD_IDS)
    async def pin_slash(self, interaction: Interaction):
        pass


    @pin_slash.subcommand(name="on", description="メッセージ下部ピン留め機能をONにする")
    async def on_slash(
            self,
            interaction: Interaction,
            messageContent: str = SlashOption(
                name="message_content",
                description="ピン留めするメッセージ",
                required=True,
            ),
        ):
        if interaction.user.id != 669178357371371522:
            await interaction.response.send_message("This command could used by admin.", ephemeral=True)
            return
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.author):
            if interaction.guild.id not in n_fc.pinMessage:
                n_fc.pinMessage[interaction.guild.id] = {interaction.channel.id: messageContent}
            else:
                n_fc.pinMessage[interaction.guild.id][interaction.channel.id] = messageContent
            await interaction.followup.send("設定を変更しました。", ephemeral=True)
        else: await interaction.followup.send("あなたには管理者権限がありません。", ephemeral=True); return


    @pin_slash.subcommand(name="off", description="メッセージ下部ピン留め機能をOFFにする")
    async def off_slash(
            self,
            interaction: Interaction,
        ):
        if interaction.user.id != 669178357371371522:
            await interaction.response.send_message("This command could used by admin.", ephemeral=True)
            return
        await interaction.response.defer()
        if admin_check.admin_check(interaction.guild, interaction.author):
            try:
                if interaction.guild.id not in n_fc.pinMessage or interaction.channel.id not in n_fc.pinMessage[interaction.guild.id]:
                    await interaction.followup.send("このチャンネルにはpinメッセージはありません。", ephemeral=True)
                else:
                    messages = await interaction.channel.history(limit=10).flatten()
                    search_message = n_fc.pinMessage[interaction.guild.id][interaction.channel.id]
                    del n_fc.pinMessage[interaction.guild.id][interaction.channel.id]
                    for i in messages:
                        if i.content == search_message:
                            await i.delete()
                    await interaction.followup.send("登録を解除しました。", ephemeral=True)
            except BaseException as err:
                await interaction.followup.send(f"エラーが発生しました。\n```sh\n{err}```", ephemeral=True)
                return
        else: await interaction.followup.send("あなたには管理者権限がありません。", ephemeral=True); return


    @tasks.loop(seconds=3)
    async def checkPin(self):
        await self.bot.wait_until_ready()
        for i in n_fc.pinMessage.keys():
            for j in n_fc.pinMessage[i].keys():
                CHANNEL = await self.bot.fetch_channel(j)
                try:
                    if CHANNEL.last_message.content == n_fc.pinMessage[i][j] and CHANNEL.last_message.author.id == self.bot.user.id:
                        continue
                except BaseException as err:
                    continue
                messages = await CHANNEL.history(limit=10).flatten()
                for message in messages:
                    if message.content == n_fc.pinMessage[i][j] and message.author.id == self.bot.user.id:
                        try:
                            await message.delete()
                        except BaseException as err:
                            continue
                await CHANNEL.send(n_fc.pinMessage[i][j])

# logging.error(traceback.format_exc())


def setup(bot):
    bot.add_cog(bottomup(bot))
    bottomup.checkPin.start(bottomup(bot))

def teardown(bot):
    logging.info("Pin teradown!")
    bottomup.checkPin.stop()
