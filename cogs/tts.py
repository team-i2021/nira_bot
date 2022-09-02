import asyncio
import datetime
import importlib
import json
import logging
import random
import re
import subprocess
import sys
import traceback
from os import getenv

import nextcord
import websockets
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util import n_fc, mc_status, tts_convert, tts_dict, database
from util.nira import NIRA

# Text To Speech

SYSDIR = sys.path[0]

SETTING = json.load(open(f'{SYSDIR}/setting.json', 'r'))
keys = SETTING["voicevox"]

Effective = True
if len(keys) == 0:
    Effective = False

global tts_channel, speaker_author

class speaker_author:
    name = "speaker_author"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE

class tts_channel:
    name = "tts_channel"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE

class VoiceSelect(nextcord.ui.Select):
    def __init__(self, client, author: nextcord.Member | nextcord.User):

        options = [
            nextcord.SelectOption(label='四国めたん/あまあま', value=0),
            nextcord.SelectOption(label='四国めたん/ノーマル', value=2),
            nextcord.SelectOption(label='四国めたん/セクシー', value=4),
            nextcord.SelectOption(label='四国めたん/ツンツン', value=6),
            nextcord.SelectOption(label='ずんだもん/あまあま', value=1),
            nextcord.SelectOption(label='ずんだもん/ノーマル', value=3),
            nextcord.SelectOption(label='ずんだもん/セクシー', value=5),
            nextcord.SelectOption(label='ずんだもん/ツンツン', value=7),
            nextcord.SelectOption(label='ずんだもん/ささやき', value=22),
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
            nextcord.SelectOption(label='九州そら/ささやき', value=19),
            nextcord.SelectOption(label='もち子さん/ノーマル', value=20),
            nextcord.SelectOption(label='剣崎雌雄/ノーマル', value=21),
        ]

        super().__init__(
            placeholder='Please select voice type.',
            min_values=1,
            max_values=1,
            options=options
        )

        self.client = client
        self.author = author

    async def callback(self, interaction: nextcord.Interaction):
        if self.author.id != interaction.user.id:
            await interaction.send("あなたが送信した声選択メニューではありません。\n`/tts voice`と送信して、声選択メニューを表示してください。", ephemeral=True)
            return
        speaker_author.value[interaction.user.id] = self.values[0]
        try:
            await interaction.message.channel.send(f'{interaction.user.mention}、設定しました。')
            await interaction.message.delete()
            await database.default_push(self.client, speaker_author)
        except Exception as err:
            logging.error(err)


class tts(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.VOICEVOX_VERSION = "0.12.5"


    @nextcord.slash_command(name="tts", description="Text-To-Speech", guild_ids=n_fc.GUILD_IDS)
    async def tts_slash(self, interaction: Interaction):
        pass

    @tts_slash.subcommand(name="join", description="Join VC (for TTS)", description_localizations={nextcord.Locale.ja: "BOTを読み上げ用にVCに参加させます"})
    async def join_slash(self, interaction: Interaction):
        if not Effective:
            await interaction.response.send_message(embed=nextcord.Embed(title="エラー", description="管理者にお伝えください。\n`VOICEVOX API Key doesn't exist.`\nVOICEVOX WebAPIのキーが存在しません。\n`setting.json`の`voicevox`欄にAPIキーを入力してから、`cogs/tts.py`をリロードしてください。", color=0xff0000))
            return
        if interaction.user.voice is None:
            await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="先にVCに接続してください。", color=0xff0000), ephemeral=True)
        else:
            if interaction.guild.voice_client is not None:
                await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description=f"既にVCに入っています。\n音楽再生から切り替える場合は、`{self.bot.command_prefix}leave`->`{self.bot.command_prefix}tts join`の順に入力してください。", color=0xff0000), ephemeral=True)
                return
            await interaction.user.voice.channel.connect()
            tts_channel.value[interaction.guild.id] = interaction.channel.id
            await database.default_push(self.bot.client, tts_channel)
            await interaction.response.send_message("接続しました", embed=nextcord.Embed(title="TTS", description="""\
TTSの読み上げ音声には、VOICEVOXが使われています。  
[各キャラクターについて](https://voicevox.hiroshiba.jp/)  
キャラクターボイス: `VOICEVOX: 四国めたん`/`VOICEVOX: ずんだもん`/`VOICEVOX: 春日部つむぎ`/`雨晴はう`/`VOICEVOX: 波音リツ`/`VOICEVOX: 玄野武宏`/`VOICEVOX: 白上虎太郎`/`VOICEVOX: 青山龍星`/`VOICEVOX: 冥鳴ひまり`/`VOICEVOX: 九州そら`

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。""", color=0x00ff00))
            interaction.guild.voice_client.play(
                nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                    f"https://api.su-shiki.com/v2/voicevox/audio/?text=接続しました&key={keys[random.randint(0,len(keys)-1)]}&speaker=2"
                ),
                    volume=0.5)
            )


    @tts_slash.subcommand(name="leave", description="Leave from VC", description_localizations={nextcord.Locale.ja: "BOTからVCを離脱させます"})
    async def leave_slash(self, interaction: Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000), ephemeral=True)
        else:
            if interaction.guild.voice_client is None:
                await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="そもそも入ってないっす...(´・ω・｀)", color=0xff0000), ephemeral=True)
                return
            await interaction.guild.voice_client.disconnect()
            del tts_channel.value[interaction.guild.id]
            await database.default_push(self.bot.client, tts_channel)
            await interaction.response.send_message(embed=nextcord.Embed(title="TTS", description="あっ...ばいばーい...", color=0x00ff00))


    @tts_slash.subcommand(name="voice", description="Change TTS Voice", description_localizations={nextcord.Locale.ja: "読み上げの声の種類を変更します"})
    async def voice_slash(self, interaction: Interaction):
        view = nextcord.ui.View(timeout=None)
        view.add_item(VoiceSelect(self.bot.client, interaction.user))
        await interaction.response.send_message(f"下のプルダウンから声を選択してください。\n選択可能声種類: `v{self.VOICEVOX_VERSION}`基準", view=view, ephemeral=True)



    @tts_slash.subcommand(name="reload", description="Reload Modules for TTS")
    async def reload_slash(self, interaction: Interaction):
        if await self.bot.is_owner(interaction.user):
            importlib.reload(tts_convert)
            importlib.reload(tts_dict)
            await interaction.response.send_message(nextcord.Embed(title="Reloaded.", description="TTS modules were reloaded.", color=0x00ff00), ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()


    @commands.command(name='tts', aliases=("読み上げ", "よみあげ"), help="""\
VCに乱入して、代わりに読み上げてくれる機能。

`n!tts join`で、今あなたが入っているVCチャンネルににらが乱入します。
あとは、コマンドを打ったチャンネルでテキストを入力すれば、それを読み上げます。
`n!tts leave`で、乱入しているVCチャンネルから出ます。

なお、既に音楽再生機能としてにらBOTがVCに入っている場合は、どっちかしか使えないので、どっちかにしてください。はい。

声の種類を選ぶには`n!tts voice`と入力してください。

TTSは、(暫定的だけど)[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。
API制限などが来た場合はご了承ください。許せ。""")
    async def tts(self, ctx: commands.Context, action: str = None):
        if not Effective:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="管理者にお伝えください。\n`VOICEVOX API Key doesn't exist.`\nVOICEVOX WebAPIのキーが存在しません。\n`setting.json`の`voicevox`欄にAPIキーを入力してから、`cogs/tts.py`をリロードしてください。", color=0xff0000))
            return

        if action is None:
            await ctx.reply(f"・読み上げ機能 `VOICEVOX: v{self.VOICEVOX_VERSION}`\nエラー：書き方が間違っています。\n\n`{ctx.prefix}tts join`: 参加\n`{ctx.prefix}tts leave`: 退出\n`{ctx.prefix}tts voice`: 声選択")
            return

        if action == "join":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is not None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"既にVCに入っています。\n音楽再生から読み上げに切り替える場合は、`{ctx.prefix}leave`->`{ctx.prefix}tts join`の順に入力してください。", color=0xff0000))
                        return
                    await ctx.author.voice.channel.connect()
                    tts_channel.value[ctx.guild.id] = ctx.channel.id
                    await database.default_push(self.bot.client, tts_channel)
                    await ctx.reply("接続しました", embed=nextcord.Embed(title="TTS", description="""\
TTSの読み上げ音声には、VOICEVOXが使われています。  
[各キャラクターについて](https://voicevox.hiroshiba.jp/)  
キャラクターボイス: `VOICEVOX: 四国めたん`/`VOICEVOX: ずんだもん`/`VOICEVOX: 春日部つむぎ`/`雨晴はう`/`VOICEVOX: 波音リツ`/`VOICEVOX: 玄野武宏`/`VOICEVOX: 白上虎太郎`/`VOICEVOX: 青山龍星`/`VOICEVOX: 冥鳴ひまり`/`VOICEVOX: 九州そら`

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。""", color=0x00ff00))
                    ctx.guild.voice_client.play(
                        nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                            f"https://api.su-shiki.com/v2/voicevox/audio/?text=接続しました&key={keys[random.randint(0,len(keys)-1)]}&speaker=2"
                        ),
                            volume=0.5)
                    )
                    logging.info(f"Connect TTS at {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
                logging.error(traceback.format_exc())
                return

        elif action == "leave":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="そもそも入ってないっす...(´・ω・｀)", color=0xff0000))
                        return
                    await ctx.guild.voice_client.disconnect()
                    del tts_channel.value[ctx.guild.id]
                    await database.default_push(self.bot.client, tts_channel)
                    await ctx.reply(embed=nextcord.Embed(title="TTS", description="あっ...ばいばーい...", color=0x00ff00))
                    logging.info(f"Leave TTS from {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000))
                print(
                    f"[TTS切断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return

        elif action == "voice":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="僕...入ってないっす...(´・ω・｀)", color=0xff0000))
                        return
                    view = nextcord.ui.View(timeout=None)
                    view.add_item(VoiceSelect(self.bot.client, ctx.author))
                    await ctx.reply(f"{ctx.author.mention}下のプルダウンから声を選択してください。\n選択可能声種類: `v{self.VOICEVOX_VERSION}`基準", view=view)
                    logging.info(f"Change TTS {ctx.author.name}'s Voice at {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000))
                print(
                    f"[TTS voice change時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return

        elif action == "reload" and await self.bot.is_owner(ctx.author):
            importlib.reload(tts_convert)
            importlib.reload(tts_dict)
            await ctx.reply("Reloaded.")

        else:
            await ctx.reply(f"・読み上げ機能\nエラー：書き方が間違っています。\n\n`{ctx.prefix}tts join`: 参加\n`{ctx.prefix}tts leave`: 退出\n`{ctx.prefix}tts voice`: 声選択")


    #@nextcord.message_command(name="メッセージを読み上げる", guild_ids=n_fc.GUILD_IDS)
    async def speak_message(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer(ephemeral=True)
        try:
            if interaction.user.voice is None:
                await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                return
            else:
                if interaction.guild.voice_client is None:
                    await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="にらBOTがボイスチャンネルに接続されていません。", color=0xff0000))
                    return

                if message.content == "" or message.content is None:
                    await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="メッセージが空です。", color=0xff0000))
                    return
                if interaction.user.id not in speaker_author.value:
                    speaker_author.value[interaction.user.id] = 2
                if interaction.guild.voice_client.is_playing():
                    while True:
                        if interaction.guild.voice_client.is_playing():
                            await asyncio.sleep(0.1)
                        else:
                            break
                await interaction.followup.send(embed=nextcord.Embed(title="TTS", description=f"```\n{message.content}```\nを読み上げます...", color=0x00ff00))
                interaction.guild.voice_client.play(
                    nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                        f"https://api.su-shiki.com/v2/voicevox/audio/?text={tts_convert.convert(message.content)}&key={keys[random.randint(0,len(keys)-1)]}&speaker={speaker_author.value[interaction.user.id]}"
                    ),
                        volume=0.5)
                )
                return
        except Exception as err:
            await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
            logging.error(traceback.format_exc())
            return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if message.author.bot:
            return
        if message.content is None or message.content == "":
            return
        if message.guild.id not in tts_channel.value:
            return
        if message.channel.id != tts_channel.value[message.guild.id]:
            return
        if getattr(message.guild, 'voice_client', None) is None:
            return
        if message.content.startswith(f"{self.bot.command_prefix}"):
            return

        try:
            if message.author.id not in speaker_author.value:
                speaker_author.value[message.author.id] = 2
            if message.guild.voice_client.is_playing():
                while True:
                    if message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.1)
                    else:
                        break
            message.guild.voice_client.play(
                nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                    f"https://api.su-shiki.com/v2/voicevox/audio/?text={tts_convert.convert(message.content)}&key={keys[random.randint(0,len(keys)-1)]}&speaker={speaker_author.value[message.author.id]}"
                ),
                    volume=0.5)
            )
        except Exception as err:
            await message.channel.send(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
            logging.error(traceback.format_exc())
            return


def setup(bot, **kwargs):
    bot.add_cog(tts(bot, **kwargs))
