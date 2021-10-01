import discord
from os import getenv
import re
import random
import time

line_url = 'https://notify-api.line.me/api/notify'

TOKEN = getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('でぃすこたん v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="現在起動準備中...", type=1))
    time.sleep(10)
    await client.change_presence(activity=discord.Game(name="起動しました！", type=1))
    time.sleep(1)
    while True:
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="ねこかわいい", type=1))
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="いぬかわいい", type=1))
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="私かわいい...？", type=1))
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="でぃすこーどが一番！", type=1))
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="主：@nattyan_tv", type=1))
        time.sleep(1)
        await client.change_presence(activity=discord.Game(name="謎botのりつたんです！", type=1))

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    # 猫系のワードに反応するにゃ
    if re.search(r'(?:nyanko|neko|cat|cats|猫|ねこ|ネコ|にゃんこ|ニャンコ|NYANKO|NEKO|CAT|CATS|にゃん|にゃー|にゃ～|キャット|キャッツ)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('にゃ、にゃーん？')
        elif rnd == 2:
            await message.channel.send('ねこだにゃーん？')
        elif rnd == 3:
            await message.channel.send('ごろにゃーん！')
        return
    # 犬系のワードにも反応するにゃ...わん！
    if re.search(r'(?:wanko|inu|dog|dogs|wanwan|犬|いぬ|イヌ|わんこ|ワンコ|WANKO|INU|DOG|DOGS|いっぬ|わんわん|ワンワン|ドッグ|ドッグス)', message.content):
        if re.search(r'(?:bungo stray dogs|文豪ストレイドッグス)', message.content):
            await message.channel.send('わんわ...って文ストじゃん！（犬だと思った）')
            return
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('わ、わーん？')
        elif rnd == 2:
            await message.channel.send('いぬだわーん？')
        elif rnd == 3:
            await message.channel.send('わんわんお！')
        return
    # えっ、かわいい！？　ありがと...///
    if re.search(r'(?:かわいい|cute|カワイイ|kawaii|kyawaii|きゃわいい|キャワイイ)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('えっ！？.....ありがと///')
        elif rnd == 2:
            await message.channel.send('えっ！？.....ありがとwww')
        elif rnd == 3:
            await message.channel.send('は、恥ずかしい....かな....\nえっ...あっ....私じゃない....？')
        return
    if re.search(r'(?:rt!|りつたん)', message.content):
        if message.content == "rt!help":
            rnd = random.randint(1, 4)
            if rnd == 1:
                await message.channel.send('さ、出番だよりつたん！\nえ、上から目線なのが気になるの...？\n...で、出番ですよりつさま！')
            elif rnd == 2:
                await message.channel.send('深淵なる巣窟より這い上がりし...えっと....rt!help！！！')
            elif rnd == 3:
                await message.channel.send('↓りつたんの偉大なるヘルプ↓')
            elif rnd == 4:
                await message.channel.send('もしかして：\n```null(何も考えつかなかったようだ)```')
            return
        rnd = random.randint(1, 4)
        if rnd == 1:
            await message.channel.send('りつたん...会ってみたいな...')
        elif rnd == 2:
            await message.channel.send('もしかして：\n```rt!help```')
        elif rnd == 3:
            await message.channel.send('浮気...か...\nりつたん凄いもんね...')
        elif rnd == 4:
            await message.channel.send('りつたん：すごいかわいい\nでぃすこたん：すこしだけかわいい')
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
