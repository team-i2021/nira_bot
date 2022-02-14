from nextcord.ext import commands
import nextcord, datetime

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh

import asyncio
#モデレーター的なーね？

class counter():
    messageCounter = {}

reset_time = ""

async def counterReset():
    while True:
        await asyncio.sleep(60*60)
        reset_time = datetime.datetime.now()
        del counter.messageCounter


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
                await message.author.add_roles(role, reason="にらBOTのmod機能")
                await message.channel.send(f"{message.author.mention}は、メッセージ数が規定オーバーのため、ミュートしました。")
                return
            except BaseException as err:
                await message.channel.send(f"{message.author.name}をミュートしようとしましたがエラーが発生しました。\n{err}")
                return

    @commands.command()
    async def mod(self, ctx: commands.Context):
        if ctx.author.id not in n_fc.py_admin:
            await ctx.reply("荒らし対策機能\nいつか搭載予定")
            return
        if ctx.message.content[:8] == "n!mod on":
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
            n_fc.mod_list[ctx.guild.id] = {"counter": int(arg[0]), "role": role_id}
            await ctx.reply(f"設定完了",embed=nextcord.Embed(title="荒らし対策",description=f"メッセージカウンター:`{arg[0]}`\nミュート用ロール:<@&{role_id}>"))
            return
        elif ctx.message.content == "n!mod off":
            del n_fc.mod_list[ctx.guild.id]
            await ctx.reply("設定完了",embed=nextcord.Embed(title="荒らし対策",description=f"設定を削除しました。"))
            return
        elif ctx.message.content == "n!mod debug":
            await ctx.reply(f"messageCounter: `{counter.messageCounter}`\nmod_list: `{n_fc.mod_list}`\nmod_check: `{counter.messageCounter[ctx.author.id] >= n_fc.mod_list[ctx.guild.id]['counter']}`\nlast reset: `{reset_time}`")
            return
        else:
            await ctx.reply("`n!mod on 既定のメッセージ数 付与するロール`\n`n!mod off`\n`n!mod debug`")
            return

def setup(bot):
    bot.loop.create_task(counterReset())
    bot.add_cog(mod(bot))
