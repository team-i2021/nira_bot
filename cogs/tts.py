import nextcord
from nextcord import Interaction, message
from nextcord.ext import commands
from nextcord.utils import get
from os import getenv
import sys
import asyncio
import subprocess
import websockets
import traceback
import importlib
import json
global task
from cogs import server_status
import re

import sys
sys.path.append('../')
from util import n_fc, mc_status
import random
import datetime

# Text To Speech

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

SETTING = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
keys = SETTING["voicevox"]

global tts_channel
tts_channel = {}

class tts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='tts', aliases=("読み上げ","よみあげ"), help="""\
VCに乱入して、代わりに読み上げてくれる機能。

`n!tts join`で、今あなたが入っているVCチャンネルににらが乱入します。
あとは、コマンドを打ったチャンネルでテキストを入力すれば、それを読み上げます。
`n!tts leave`で、乱入しているVCチャンネルから出ます。

なお、既に音楽再生機能としてにらBOTがVCに入っている場合は、どっちかしか使えないので、どっちかにしてください。はい。

TTSは、(暫定的だけど)[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。
API制限などが来た場合はご了承ください。許せ。""")
    async def tts(self, ctx: commands.Context):
        args = ctx.message.content.split(" ",2)
        if len(args) != 2:
            await ctx.reply("・読み上げ機能\nエラー：書き方が間違っています。\n\n`n!tts join`: 参加\n`n!tts leave`: 退出")
            return
        if args[1] == "join":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                    return
                else:
                    if not ctx.message.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="既にVCに入っています。\n音楽再生から切り替える場合は、`n!leave`->`n!tts join`の順に入力してください。",color=0xff0000))
                        return
                    await ctx.author.voice.channel.connect()
                    tts_channel[ctx.guild.id] = ctx.channel.id
                    await ctx.reply(embed=nextcord.Embed(title="TTS",description="""\
TTSの読み上げ音声には、VOICEVOXの四国めたんが使われています。  
[利用規約](https://zunko.jp/con_ongen_kiyaku.html)  
ボイス:「VOICEVOX: 四国めたん」

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。""",color=0x00ff00))
                    print(f"{datetime.datetime.now()} - {ctx.guild.name}でTTSに接続")
                    return
            except BaseException as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
                print(f"[TTS接続時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
        elif args[1] == "leave":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                    return
                else:
                    if ctx.message.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="そもそも入ってないっす...(´・ω・｀)",color=0xff0000))
                        return
                    await ctx.message.guild.voice_client.disconnect()
                    del tts_channel[ctx.guild.id]
                    await ctx.reply(embed=nextcord.Embed(title="TTS",description="あっ...ばいばーい...",color=0x00ff00))
                    print(f"{datetime.datetime.now()} - {ctx.guild.name}でTTSから切断")
                    return
            except BaseException as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
                print(f"[TTS切断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
        else:
            await ctx.reply("・読み上げ機能\nエラー：書き方が間違っています。\n\n`n!tts join`: 参加\n`n!tts leave`: 退出")
            return
    


    @commands.Cog.listener()
    async def on_message(self, message: message):
        if message.guild.voice_client is None:
            return
        if message.author.bot:
            return
        if message.guild.id not in tts_channel:
            return
        if message.channel.id != tts_channel[message.guild.id]:
            return
        if message.content.startswith("n!"):
            return
        try:
            message.guild.voice_client.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(f"https://api.su-shiki.com/v2/voicevox/audio/?text={message.content}&key={keys[random.randint(0,len(keys)-1)]}"), volume=0.5))
        except BaseException as err:
            await message.channel.send(embed=nextcord.Embed(title="TTSエラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
            print(f"[TTS送信時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return


def setup(bot):
    bot.add_cog(tts(bot))
