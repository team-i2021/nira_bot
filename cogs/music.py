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

async def end_mes(message, played_type, close_obj):
    if played_type == "nc":
        close_obj.close()
    return await message.reply(embed=discord.Embed(title="Finished.", description="再生が終わったよ！\n次は何の曲が流れるのかな～？", color=0x00ff00))

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
                music_list[ctx.message.guild.id] = "none"
                url_type[ctx.message.guild.id] = "none"
                if len(ctx.message.content) <= 7:
                    await ctx.message.reply(embed=discord.Embed(title="エラー",description="`n!play [URL]`という形で送信してください。",color=0xff0000))
                    return
                else:
                    url = ctx.message.content[7:]
                    if re.search("nicovideo.jp",url) or re.search("nico.ms",url):
                        music_f[ctx.message.guild.id] = niconico_dl.NicoNicoVideo(url)
                        music_f[ctx.message.guild.id].connect()
                        music_list[ctx.message.guild.id] = music_f[ctx.message.guild.id].get_download_link()
                        url_type[ctx.message.guild.id] = "nc"
                    elif re.search("youtube.com", url) or re.search("youtu.be", url):
                        music_list[ctx.message.guild.id] = await YTDLSource.from_url(url, stream=True)
                        url_type[ctx.message.guild.id] = "yt"
                        music_f[ctx.message.guild.id] = None
                        music_list[ctx.message.guild.id] = music_list[ctx.message.guild.id].url
                if music_list[ctx.message.guild.id] == "none":
                    await ctx.message.reply(embed=discord.Embed(title="エラー",description="ニコニコ動画かYouTubeのリンクを入れてね！",color=0xff0000))
                    return
                logging.info(f"{url} {url_type[ctx.message.guild.id]} {music_list[ctx.message.guild.id]}")
                ctx.message.guild.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_list[ctx.message.guild.id], **options), volume=0.45), after = lambda e: self.bot.loop.create_task(end_mes(ctx.message, url_type[ctx.message.guild.id], music_f[ctx.message.guild.id])))
                await ctx.message.add_reaction("\U0001F197")
                # discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(music_list[ctx.message.guild.id].url,**options), volume=0.5)
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
                ctx.message.guild.voice_client.stop()
                await ctx.message.reply("stopped")
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
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

def setup(bot):
    bot.add_cog(music(bot))