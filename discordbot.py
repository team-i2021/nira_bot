import discord
from os import getenv
import re
import random

TOKEN = getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('ニラbot v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="ニラの栽培ゲーム", type=1))

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum)', message.content):
        if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
            if re.search(r'(?:水|みず|ミズ)', message.content):
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_water.jpg')
                return
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_sand.jpeg')
            return
        if re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_fish.png')
            return
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_b.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_c.png')
            return
    if re.search(r'(?:煮裸族)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_zoku.mp4')
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
