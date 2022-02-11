from calendar import c
from lib2to3.pytree import Base
from discord.ext import commands
import discord

import asyncio
import datetime
import sys

import re
import niconico_dl
import youtube_dl
import sys
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh, server_check

import urllib.request
import urllib.parse


# 音楽再生

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


music_list = dict()
music_f = dict()
url_type = dict()

youtube_dl.utils.bug_reports_message = lambda: ''

options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': f'{dir}/util/youtube-cookies.txt'
}

# ヨシ！
ffmpeg_options = {
    'options': '-vn'
}



ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


#def get_redirect(src_url):
#    with urllib.request.urlopen(src_url) as res:
#        url = res.geturl()
#        if src_url == url:
#            return url
#        else:
#            return url
#
#
#async def get_sclink(url):
#    track_url = urllib.parse.unquote(get_redirect(f"https://w.soundcloud.com/player/?url={url}")[37:])
#    track_id = track_url[]




async def end_mes(message: discord.Message, close_obj: niconico_dl.NicoNicoVideo or None, bot: discord.Bot):
    try:
        if re.search("nicovideo.jp",music_list[message.guild.id][0]) or re.search("nico.ms",music_list[message.guild.id][0]):
            close_obj.close()
        if len(music_list[message.guild.id]) != 0:
            music_list[message.guild.id].pop(0)
            music_f[message.guild.id].pop(0)
        await asyncio.sleep(3)
        logging.info(f"end play:{message.guild.name}, {len(music_list[message.guild.id])}")
        if len(music_list[message.guild.id]) >= 1:
            return await play_source(message, bot)
        del music_list[message.guild.id]
        del music_f[message.guild.id]
        return await message.channel.send("すべての曲の再生が終わりました！")
    except BaseException as err:
        logging.error(err)

async def play_source(message: discord.Message, bot: discord.Bot):
    try:
        await message.add_reaction("\U00002705")
        if re.search("nicovideo.jp",music_list[message.guild.id][0]) or re.search("nico.ms",music_list[message.guild.id][0]):
            music_f[message.guild.id][0].connect()
            music_list[message.guild.id][0] = music_f[message.guild.id].get_download_link()
        await message.add_reaction("\U0001F3B5")
        logging.info(f"Play source:{len(music_list[message.guild.id])} {music_f[message.guild.id][0]} {music_list[message.guild.id][0]}")
        message.guild.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_list[message.guild.id][0], **options), volume=0.45), after = lambda e: bot.loop.create_task(end_mes(message, music_f[message.guild.id][0], bot)))
        await message.add_reaction("\U0001F197")
    except BaseException as err:
        logging.error(err)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="list")
    async def show_list(self, ctx: commands.Context):
        if ctx.guild.id not in music_list or len(music_list[ctx.guild.id]) == 0:
            await ctx.reply("音楽はないです！\n`n!play [URL]`で曲をじゃんじゃん再生しましょう！\n（本音：サーバー負荷やばいからな...うぅ...）")
            return
        else:
            await ctx.reply(f"プレイリストの曲数:`{len(music_list[ctx.guild.id])}`曲\n\n(あとはここに曲の題名とかを...ふっふっふっ...(未完成))")
            return
    
    @commands.command()
    async def music_debug(self, ctx: commands.Context):
        if ctx.author.id in n_fc.py_admin:
            try:
                if ctx.message.content == "n!music_debug 1":
                    await ctx.reply(f"・music_list(on your guild)\n```{music_list[ctx.guild.id]}```")
                elif ctx.message.content == "n!music_debug 2":
                    await ctx.reply(f"・music_f(on your guild)\n```{music_f[ctx.guild.id]}```")
                elif ctx.message.content == "n!music_debug 3":
                    await ctx.reply(f"・Music play status\n```py\n{ctx.message.guild.voice_client.is_playing()}```")
            except KeyError:
                await ctx.reply("KeyError.\n曲データは存在しません。")
    
    @commands.command()
    async def join(self, ctx: commands.Context):
        try:
            if ctx.message.author.voice is None:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                return
            else:
                await ctx.message.author.voice.channel.connect()
                await ctx.message.reply(embed=discord.Embed(title="にら",description="今はまだ、テスト中なので動作が不安定です！\n`n!play [URL]`/`n!pause`/`n!resume`/`n!stop`/`n!leave`",color=0x00ff00))
                print(f"{datetime.datetime.now()} - {ctx.message.guild.name}でVCに接続")
                return
        except BaseException as err:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
            print(f"[VC接続時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return
    
    @commands.command()
    async def play(self, ctx: commands.Context):
        try:
            if ctx.message.author.voice is None:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                return
            elif ctx.message.guild.voice_client is None:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
                return
            else:
                if len(ctx.message.content) <= 7:
                    await ctx.message.reply(embed=discord.Embed(title="エラー",description="`n!play [URL]`という形で送信してください。",color=0xff0000))
                    return
                else:
                    url = ctx.message.content[7:]
                    if ctx.guild.id not in music_list or len(music_list[ctx.guild.id]) == 0:
                        music_list[ctx.guild.id] = []
                        music_f[ctx.guild.id] = []
                        if re.search("nicovideo.jp",url) or re.search("nico.ms",url):
                            music_f[ctx.guild.id].append(niconico_dl.NicoNicoVideo(url))
                            music_f[ctx.guild.id][0].connect()
                            music_list[ctx.guild.id].append(music_f[ctx.guild.id].get_download_link())
                        elif re.search("youtube.com", url) or re.search("youtu.be", url):
                            music_f[ctx.guild.id].append(await YTDLSource.from_url(url, stream=True))
                            music_list[ctx.guild.id].append(music_f[ctx.guild.id][0].url)
                        else:
                            await ctx.message.reply(embed=discord.Embed(title="エラー",description="ニコニコ動画かYouTubeのリンクを入れてね！",color=0xff0000))
                            return
                        logging.info(f"{url} {music_f[ctx.guild.id][0]} {music_list[ctx.guild.id][0]}")
                        await ctx.message.add_reaction("\U0001F3B5")
                        ctx.message.guild.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_list[ctx.guild.id][0], **options), volume=0.45), after = lambda e: self.bot.loop.create_task(end_mes(ctx.message, music_f[ctx.guild.id][0], self.bot)))
                        await ctx.message.add_reaction("\U0001F197")
                        # discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_list[ctx.guild.id].url,**options), volume=0.5)
                        return
                    else:
                        if re.search("nicovideo.jp",url) or re.search("nico.ms",url):
                            music_f[ctx.guild.id].append(niconico_dl.NicoNicoVideo(url))
                            music_list[ctx.guild.id].append(None)
                        elif re.search("youtube.com", url) or re.search("youtu.be", url):
                            music_f[ctx.guild.id].append(await YTDLSource.from_url(url, stream=True))
                            music_list[ctx.guild.id].append(music_f[ctx.guild.id][-1].url)
                        else:
                            await ctx.message.reply(embed=discord.Embed(title="エラー",description="ニコニコ動画かYouTubeのリンクを入れてね！",color=0xff0000))
                            return
                        await ctx.reply(f"追加したよ！\nあなたの曲は{len(music_list[ctx.guild.id])}番目！")
                        return
        except BaseException as err:
            await ctx.reply(embed=eh.eh(err))
            logging.error(f"[楽曲再生時or再生中のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return
    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        if ctx.message.author.voice is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif ctx.message.guild.voice_client is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            try:
                ctx.message.guild.voice_client.pause()
                await ctx.message.reply("paused")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                print(f"[楽曲中断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
    
    @commands.command()
    async def resume(self, ctx: commands.Context):
        if ctx.message.author.voice is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif ctx.message.guild.voice_client is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            try:
                ctx.message.guild.voice_client.resume()
                await ctx.message.reply("resume!")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                print(f"[楽曲中断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
    
    @commands.command()
    async def stop(self, ctx: commands.Context):
        if ctx.message.author.voice is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif ctx.message.guild.voice_client is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            try:
                del music_list[ctx.guild.id]
                del music_f[ctx.guild.id]
                ctx.guild.voice_client.stop()
                await ctx.reply("曲をすべて止めました！ :eject:")
                return
            except BaseException as err:
                await ctx.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                print(f"[楽曲停止時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
    
    @commands.command()
    async def leave(self, ctx: commands.Context):
        try:
            if ctx.message.author.voice is None:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
                return
            elif ctx.message.guild.voice_client is None:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
                return
            else:
                await ctx.message.guild.voice_client.disconnect()
                await ctx.message.reply(embed=discord.Embed(title="にら",description="Disconnected",color=0x00ff00))
                print(f"{datetime.datetime.now()} - {ctx.message.guild.name}のVCから切断")
                return
        except BaseException as err:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            print(f"[VC切断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return
    
    @commands.command()
    async def skip(self, ctx: commands.Context):
        if ctx.message.author.voice is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif ctx.message.guild.voice_client is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            try:
                if len(music_list[ctx.guild.id]) != 1:
                    ctx.message.guild.voice_client.stop()
                    await ctx.message.reply("Skip! :track_next:")
                else:
                    ctx.message.guild.voice_client.stop()
                    await ctx.message.reply("今のが最後の曲でした！ :stop_button:")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                print(f"[楽曲停止時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return
    
    @commands.command()
    async def pop(self, ctx: commands.Context):
        if ctx.message.author.voice is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif ctx.message.guild.voice_client is None:
            await ctx.message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            try:
                if len(music_list[ctx.guild.id]) == 1:
                    await ctx.reply("既にプレイリストには1曲しかありません。\n`n!stop`で止めることができます。")
                else:
                    music_f[ctx.guild.id].pop(-1)
                    music_list[ctx.guild.id].pop(-1)
                    await ctx.reply("プレイリストの最後の曲を削除しました！ :information_source:")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                print(f"[楽曲停止時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
                return

def setup(bot):
    bot.add_cog(music(bot))