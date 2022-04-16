import nextcord
from nextcord import Interaction
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
import re

import sys
sys.path.append('../')
from util import n_fc, mc_status, tts_convert
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

global tts_channel, speaker_author
tts_channel = {}
speaker_author = {}


class VoiceSelect(nextcord.ui.Select):
    def __init__(self):

        options = [
            nextcord.SelectOption(label='四国めたん/あまあま', value=0),
            nextcord.SelectOption(label='ずんだもん/あまあま', value=1),
            nextcord.SelectOption(label='四国めたん/ノーマル', value=2),
            nextcord.SelectOption(label='ずんだもん/ノーマル', value=3),
            nextcord.SelectOption(label='四国めたん/セクシー', value=4),
            nextcord.SelectOption(label='ずんだもん/セクシー', value=5),
            nextcord.SelectOption(label='四国めたん/ツンツン', value=6),
            nextcord.SelectOption(label='ずんだもん/ツンツン', value=7),
            nextcord.SelectOption(label='春日部つむぎ/ノーマル', value=8),
            nextcord.SelectOption(label='波音リツ/ノーマル', value=9),
            nextcord.SelectOption(label='雨晴はう/ノーマル', value=10),
            nextcord.SelectOption(label='玄野武宏/ノーマル', value=11),
            nextcord.SelectOption(label='白上虎太郎/ノーマル', value=12),
            nextcord.SelectOption(label='青山龍星/ノーマル', value=13),
            nextcord.SelectOption(label='冥鳴ひまり/ノーマル', value=14),
            nextcord.SelectOption(label='九州そら/あまあま', value=15),
            nextcord.SelectOption(label='九州そら/ノーマル', value=16),
            nextcord.SelectOption(label='九州そら/セクシー', value=17),
            nextcord.SelectOption(label='九州そら/ツンツン', value=18),
            nextcord.SelectOption(label='九州そら/ささやき', value=19)
        ]

        super().__init__(placeholder='Please select voice type.', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        speaker_author[interaction.user.id] = self.values[0]
        try:
            await interaction.message.channel.send(f'{interaction.user.mention}、設定しました。')
            await interaction.message.delete()
        except BaseException as err:
            logging.error(err)


class tts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='tts', aliases=("読み上げ","よみあげ"), help="""\
VCに乱入して、代わりに読み上げてくれる機能。

`n!tts join`で、今あなたが入っているVCチャンネルににらが乱入します。
あとは、コマンドを打ったチャンネルでテキストを入力すれば、それを読み上げます。
`n!tts leave`で、乱入しているVCチャンネルから出ます。

なお、既に音楽再生機能としてにらBOTがVCに入っている場合は、どっちかしか使えないので、どっちかにしてください。はい。

声の種類を選ぶには`n!tts voice`と入力してください。

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
                    await ctx.reply("接続しました" ,embed=nextcord.Embed(title="TTS",description="""\
TTSの読み上げ音声には、VOICEVOXが使われています。  
[各キャラクターについて](https://voicevox.hiroshiba.jp/)  
キャラクターボイス: `VOICEVOX: 四国めたん`/`VOICEVOX: ずんだもん`/`VOICEVOX: 春日部つむぎ`/`雨晴はう`/`VOICEVOX: 波音リツ`/`VOICEVOX: 玄野武宏`/`VOICEVOX: 白上虎太郎`/`VOICEVOX: 青山龍星`/`VOICEVOX: 冥鳴ひまり`/`VOICEVOX: 九州そら`

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。""",color=0x00ff00))
                    ctx.guild.voice_client.play(
                        nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                            f"https://api.su-shiki.com/v2/voicevox/audio/?text=接続しました&key={keys[random.randint(0,len(keys)-1)]}&speaker=2"
                        ),
                        volume=0.5)
                    )
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
        elif args[1] == "voice":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                    return
                else:
                    if ctx.message.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description="僕...入ってないっす...(´・ω・｀)",color=0xff0000))
                        return
                    view = nextcord.ui.View(timeout=None)
                    view.add_item(VoiceSelect())
                    await ctx.reply("下のプルダウンから声を選択してください。", view=view)
                    print(f"{datetime.datetime.now()} - {ctx.guild.name} voice change")
                    return
            except BaseException as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
                print(f"[TTS voice change時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return

        else:
            await ctx.reply("・読み上げ機能\nエラー：書き方が間違っています。\n\n`n!tts join`: 参加\n`n!tts leave`: 退出\n`n!tts voice`: 声選択")
            return
    


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
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
            if message.author.id not in speaker_author:
                speaker_author[message.author.id] = 2
            if message.guild.voice_client.is_playing():
                while True:
                    if message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.1)
                    else:
                        break
            message.guild.voice_client.play(
                nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                    f"https://api.su-shiki.com/v2/voicevox/audio/?text={tts_convert.convert(message.content)}&key={keys[random.randint(0,len(keys)-1)]}&speaker={speaker_author[message.author.id]}"
                ),
                volume=0.5)
            )
        except BaseException as err:
            await message.channel.send(embed=nextcord.Embed(title="TTSエラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
            print(f"[TTS送信時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return


def setup(bot):
    bot.add_cog(tts(bot))
    importlib.reload(tts_convert)
