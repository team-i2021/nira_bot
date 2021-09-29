import discord
from os import getenv
import requests
import re

line_url = 'https://notify-api.line.me/api/notify'
line_token = 'AyXimujAkshsjUdFUAe36q7SUYpBYUU4BsqsqtcdHNG'
headers = {'Authorization': 'Bearer ' + line_token}

def notify_line(message):
    payload = {'message': message}
    requests.post(line_url, headers=headers, params=payload)


# 自分のBotのアクセストークンに置き換えてください
TOKEN = getenv('DISCORD_BOT_TOKEN')

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # 「/neko」と発言したら「にゃーん」が返る処理
    if re.search(r'[nyanko]|[neko]|[cat]|[cats]|[猫]|[ねこ]|[ネコ]|[にゃんこ]|[ニャンコ]|[NYANKO]|[NEKO]|[CAT]|[CATS]|[にゃん]|[にゃーん]|[にゃ～ん]', message.content):
        await message.channel.send('にゃ、にゃーん？')
    notify_line(f'{message.author}\n{message.content}')


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
