from lib2to3.pytree import Base
from nextcord.embeds import Embed
import requests
import sys
import nextcord
import os

tokens = {}

lineNotify_url = 'https://notify-api.line.me/api/notify'
lineTokenCheck_url = 'https://notify-api.line.me/api/status'

server_req_url = 'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v1/?format=json&addr='

image_4 = [".jpg", ".png", ".bmp"]
image_5 = [".jpeg", ".jtif"]

#loggingの設定
import logging
dir = sys.path[0]
class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message

logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{dir}/nira.log', level=logging.INFO)

def notify_line(message: nextcord.Message, token):
    channel = f"[{message.guild.name}]/[{message.channel.name}]"
    try:
        if message.author.nick == None:
            user = f"{message.author.name}@{message.author.discriminator}"
        else:
            user = f"{message.author.nick}"
    except BaseException:
        user = f"{message.author.name}@{message.author.discriminator}"
    try:
        if message.author.bot:
            user = user + "[BOT]"
        if message.attachments != [] or ((message.content[:8] == "https://" or message.content[:7] == "http://") and (message.content[-5:] == ".jpeg" or message.content[-4:] == ".jpg" or message.content[-4:] == ".png")):
            if message.attachments == []:
                image = message.content
            elif message.attachments[0].url[-5:] == ".jpeg" or message.attachments[0].url[-4:] == ".jpg" or message.attachments[0].url[-4:] == ".png":
                image = message.attachments[0].url
        else:
            image = ""
        if message.embeds != [] and message.embeds[0].title != Embed.Empty:
            embed = f"{message.embeds[0].title}\n{message.embeds[0].description}"
        else:
            embed = ""
        mes = f"\n{channel}\n{user}\n{message.content}\n{embed}"
        if len(mes) > 1000:
            over = len(mes) - 1000
            mes = f"\n{channel}\n{user}\n{message.content[-over:]}...\n{embed}\n※本文が長いため省略されました。"
        # mes = f"\n[{message.guild.name}]/[{message.channel.name}]\n{message.author.nick}\n\n{message.content}"
        headers = {'Authorization' : 'Bearer ' + token}
        if image == "":
            payload = {'message' : mes}
        else:
            payload = {'message' : mes, 'imageFullsize' : image, 'imageThumbnail': image}
        # print(payload)
        requests.post(lineNotify_url ,headers = headers ,params=payload)
    except BaseException as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}\n\n[サポートサーバー](https://nextcord.gg/awfFpCYTcP)")

def line_token_check(token):
    headers = {'Authorization' : 'Bearer ' + token}
    rt = requests.get(lineTokenCheck_url ,headers = headers)
    if rt.status_code == 200:
        return (True, rt.text)
    else:
        return (False, rt.text)


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