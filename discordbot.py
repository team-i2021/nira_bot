import discord
from os import getenv
import requests
import re
import random

global line_token
line_url = 'https://notify-api.line.me/api/notify'
line_token = ''
headers = {'Authorization': 'Bearer ' + line_token}

def notify_line(message):
    payload = {'message': message}
    requests.post(line_url, headers=headers, params=payload)

TOKEN = getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('でぃすこたん v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="にゃんこのでぃすこたん", type=1))
    notify_line('\nでぃすこたん v0.9.2\n～故に彼女は猫だった～\n正常に起動しました。')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    global mes_memo
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        notify_line(f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{message.content}')
        return
    # 猫系のワードに反応するにゃ
    if re.search(r'(?:nyanko|neko|cat|cats|猫|ねこ|ネコ|にゃんこ|ニャンコ|NYANKO|NEKO|CAT|CATS|にゃん|にゃー|にゃ～)', message.content):
        notify_line(f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{message.content}')
        neko_rnd = random.randint(1,3)
        if neko_rnd == 1:
            await message.channel.send('にゃ、にゃーん？')
        elif neko_rnd == 2:
            await message.channel.send('ねこだにゃーん？')
        elif neko_rnd == 3:
            await message.channel.send('ごろにゃーん！')
        return
    if re.search(r'(?:LINE_TOKEN:)', message.content):
        mes_cnt = message.content
        await message.channel.send(mes_cnt.split(":",2)[1])
        notify_line(f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{mes_memo}')
        return
    notify_line(f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{message.content}')
    mes_memo = message.content
    notify_line(mes_memo)
    return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
