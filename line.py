import requests
import bot_token

tokens = {}

line_url = 'https://notify-api.line.me/api/notify'
test_token = bot_token.line_token

def notify_line(message, token):
   if message.author.bot:
      if message.author.nick == None:
         mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.name}@{message.author.discriminator}[BOT]\n\n{message.content}"
      else:
         mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.nick}@{message.author.discriminator}[BOT]\n\n{message.content}"
   else:
      if message.author.nick == None:
         mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.name}@{message.author.discriminator}\n\n{message.content}"
      else:
         mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.nick}@{message.author.discriminator}\n\n{message.content}"
   headers = {'Authorization' : 'Bearer ' + token}
   payload = { 'message' : mes}
   requests.post(line_url ,headers = headers ,params=payload)