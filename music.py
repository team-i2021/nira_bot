import niconico_dl
import discord
import asyncio
import re
import subprocess
from subprocess import PIPE
import math
import time
music_list = {}
music_f = {}

async def join_channel(message, client):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        else:
            await message.author.voice.channel.connect()
            await message.reply(embed=discord.Embed(title="にら",description="今はまだ、テスト中なので動作が不安定です！\n`n!play [URL]`/`n!pause`/`n!resume`/`n!stop`/`n!leave`",color=0x00ff00))
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
        return

async def play_music(message, client):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif message.guild.voice_client is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            music_list[message.guild.id] = "none"
            if len(message.content) <= 7:
                await message.reply(embed=discord.Embed(title="エラー",description="`n!play [URL]`という形で送信してください。",color=0xff0000))
                return
            else:
                url = message.content[7:]
                if re.search("nicovideo.jp",url):
                    try:
                            music_f[message.guild.id] = niconico_dl.NicoNicoVideo(url)
                            music_f[message.guild.id].connect()
                            music_list[message.guild.id] = music_f[message.guild.id].get_download_link()
                    except BaseException as err:
                        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
                        return
            if music_list[message.guild.id] == "none":
                await message.reply(embed=discord.Embed(title="エラー",description="ニコニコ動画のリンクを入れてね！",color=0xff0000))
                return
            music_time = subprocess.run(f'ffprobe "{music_list[message.guild.id]}" -show_entries format=duration -v quiet -of csv="p=0"', stdout=PIPE, stderr=PIPE, shell=True, text=True)
            prti = music_time.stdout.find(".")
            message.guild.voice_client.play(discord.FFmpegPCMAudio(music_list[message.guild.id]))
            await asyncio.sleep(math.floor(int(music_time.stdout[:prti])))
            music_f[message.guild.id].close()
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
        return

async def pause_music(message, client):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_client is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_client.pause()
            await message.reply("paused")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            return

async def resume_music(message, client):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_client is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_client.resume()
            await message.reply("resume!")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            return

async def stop_music(message, client):
    if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
    elif message.guild.voice_client is None:
        await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
        return
    else:
        try:
            message.guild.voice_client.stop()
            await message.reply("stopped")
            return
        except BaseException as err:
            await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
            return

async def leave_channel(message, client):
    try:
        if message.author.voice is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先にボイスチャンネルに接続してください。",color=0xff0000))
            return
        elif message.guild.voice_client is None:
            await message.reply(embed=discord.Embed(title="エラー",description="先に`n!join`でボイスチャンネルに入れてください！",color=0xff0000))
            return
        else:
            await message.guild.voice_client.disconnect()
            await message.reply(embed=discord.Embed(title="にら",description="Disconnected",color=0x00ff00))
            return
    except BaseException as err:
        await message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```",color=0xff0000))
        return