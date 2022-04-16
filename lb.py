import discord
import asyncio
import websockets
from discord.ext import commands
from discord.ext.commands import Bot
import os, sys, json

ADDRESS = "raspberrypi.local"
SERVER_PORT = 45565
CLIENT_PORT = 45566


async def GetData(content):
    uri = f"ws://{ADDRESS}:{SERVER_PORT}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(str(content))
        return await websocket.recv()

HOME = os.path.dirname(__file__)
SETTING = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
TOKEN = SETTING["tokens"]["nira_bot"]
PREFIX = SETTING["prefix"]
ADMIN = SETTING["py_admin"]

intents = discord.Intents.all()
intents.typing = False
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
bot.remove_command("help")

@bot.commands()
async def lb(self, ctx: commands.Context):
    if ctx.author.id not in ADMIN:
        return
    args = ctx.message.content.split(" ")
    if len(args) == 1:
        await ctx.reply("引数が足りません。")
        return
    if args[1] == "load":
        if len(args) <= 2:
            await ctx.reply("引数が足りません。\n```\nlb load <モジュール名>```")
            return
        try:
            bot.load_extension("cogs." + args[2])
        except BaseException as err:
            await ctx.reply(f"モジュールの読み込みに失敗しました。\n```\n{err}```")
            return
        await ctx.reply(f"モジュール「{args[2]}」を読み込みました。")
        return