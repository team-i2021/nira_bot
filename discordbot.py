import discord
from os import getenv
import requests
import re
import random

line_url = 'https://notify-api.line.me/api/notify'

#def notify_line(message):
#    payload = {'message': (f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{message.content}')}
#    headers = {'Authorization': 'Bearer ' + line_token}
#    requests.post(line_url, headers=headers, params=payload)

TOKEN = getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('でぃすこたん v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="にゃんこのでぃすこたん", type=1))



# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    global mes_memo
    global line_token
    line_token = ""
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    # 猫系のワードに反応するにゃ
    if re.search(r'(?:nyanko|neko|cat|cats|猫|ねこ|ネコ|にゃんこ|ニャンコ|NYANKO|NEKO|CAT|CATS|にゃん|にゃー|にゃ～)', message.content):
        neko_rnd = random.randint(1, 3)
        if neko_rnd == 1:
            await message.channel.send('にゃ、にゃーん？')
        elif neko_rnd == 2:
            await message.channel.send('ねこだにゃーん？')
        elif neko_rnd == 3:
            await message.channel.send('ごろにゃーん！')
        return
    if re.search(r'(?:LINE_TOKEN:)', message.content):
        mes_cnt = message.content
        line_token = mes_cnt.split(":", 2)[1]
        await message.channel.send(line_token)
        await message.channel.send("TOKENを記録しました。")
        requests.post(line_url, headers={'Authorization': 'Bearer ' + line_token}, params={'message': (f'\n{message.author}\n[{message.channel.category}/{message.channel}]\nConnect')})
        return
    if re.search(r'(?:$ )', message.content):
        mes = message.content
        mess = mes.split(" ", 2)[1]
        requests.post(line_url, headers={'Authorization': 'Bearer ' + line_token}, params={'message': (f'\n{message.author}\n[{message.channel.category}/{message.channel}]\n{mess}')})
        return
    mes_memo = message.content
    return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
