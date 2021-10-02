import discord
from os import getenv
import re
import random
import time

TOKEN = getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('ニラbot v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="現在起動準備中...", type=2))
    time.sleep(10)
    await client.change_presence(activity=discord.Game(name="ニラの栽培ゲーム", type=1))

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    if re.search(r'(?:にら|ニラ|garlic)', message.content):
        await message.channel.send('https://media.discordapp.net/attachments/885154539769036831/893843337130426398/image0.png')
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
