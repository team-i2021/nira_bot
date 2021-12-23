import requests
import sys

tokens = {}

lineNotify_url = 'https://notify-api.line.me/api/notify'

server_req_url = 'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v1/?format=json&addr='


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
    requests.post(lineNotify_url ,headers = headers ,params=payload)

def server_status(ip, port):
        option = ip + ":" + str(port)
        url = server_req_url + option
        req = requests.get(url)
        server_list = req.json()
        if "servers" not in server_list["response"]:
            return False
        if len(server_list["response"]["servers"]) >= 1:
            return True
        else:
            return False