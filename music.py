import niconico_dl
import discord
import asyncio
import re
import subprocess
from subprocess import PIPE
import math
import time
import sys
import youtube_dl
import datetime
music_list = {}
music_f = {}
url_type = {}

# Suppress noise about console usage from errors
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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
 #   import traceback
  #  traceback.print_exc()
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

async def mess(message, played_type, close_obj):
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


async def join_channel(message, bot):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        else:
            await message.author.voice.channel.connect()
            await message.reply(embed=discord.Embed(title="にら",description="今はまだ、テスト中なので動作が不安定です！\n`n!play [URL]`/`n!pause`/`n!resume`/`n!stop`/`n!leave`",color=0x00ff00))
            print(f"{datetime.datetime.now()} - {message.guild.name}でVCに接続")
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
        print(f"[VC接続時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
        return


async def play_music(message, bot):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif message.guild.voice_bot is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            music_list[message.guild.id] = "none"
            url_type[message.guild.id] = "none"
            if len(message.content) <= 7:
                await message.reply(embed=discord.Embed(title="エラー",description="`n!play [URL]`という形で送信してください。",color=0xff0000))
                return
            else:
                url = message.content[7:]
                if re.search("nicovideo.jp",url) or re.search("nico.ms",url):
                    music_f[message.guild.id] = niconico_dl.NicoNicoVideo(url)
                    music_f[message.guild.id].connect()
                    music_list[message.guild.id] = music_f[message.guild.id].get_download_link()
                    url_type[message.guild.id] = "nc"
                elif re.search("youtube.com", url) or re.search("youtu.be", url):
                    music_list[message.guild.id] = await YTDLSource.from_url(url, stream=True)
                    url_type[message.guild.id] = "yt"
                    music_f[message.guild.id] = None
            if music_list[message.guild.id] == "none":
                await message.reply(embed=discord.Embed(title="エラー",description="ニコニコ動画かYouTubeのリンクを入れてね！",color=0xff0000))
                return
            print(f"{datetime.datetime.now()} - {url} {url_type[message.guild.id]} {music_list[message.guild.id]}")
            message.guild.voice_bot.play(discord.FFmpegPCMAudio(music_list[message.guild.id].url,**options), after = lambda e: bot.loop.create_task(mess(message, url_type[message.guild.id], music_f[message.guild.id])))
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))
        print(f"[楽曲再生時or再生中のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
        return


async def pause_music(message, bot):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_bot is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_bot.pause()
            await message.reply("paused")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            print(f"[楽曲中断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return


async def resume_music(message, bot):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_bot is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_bot.resume()
            await message.reply("resume!")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            print(f"[楽曲中断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return


async def stop_music(message, bot):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_bot is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_bot.stop()
            await message.reply("stopped")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            print(f"[楽曲停止時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
            return


async def leave_channel(message, bot):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif message.guild.voice_bot is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            await message.guild.voice_bot.disconnect()
            await message.reply(embed=discord.Embed(title="にら",description="Disconnected",color=0x00ff00))
            print(f"{datetime.datetime.now()} - {message.guild.name}のVCから切断")
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
        print(f"[VC切断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}")
        return