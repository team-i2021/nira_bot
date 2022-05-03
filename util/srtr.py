# coding: utf-8
import nextcord
from os import getenv
import re
import random
import jaconv
from util import word_data, n_fc
import pykakasi
import sys
import traceback
import importlib
import copy
import pickle



re_hiragana = re.compile(r'^[あ-ん]+$')
re_katakana = re.compile(r'[\u30A1-\u30F4]+')
re_alpha = re.compile(r'^[a-zA-Z]+$')
re_kanji = re.compile(r'^[\u4E00-\u9FD0]+$')

global srtr_data
srtr_data = {}

home_dir = sys.path[0]

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


kks = pykakasi.kakasi()

async def on_srtr(message):
    if message.guild.id not in srtr_data:
        srtr_data[message.guild.id] = copy.deepcopy(word_data.words)
    try:
        ply_dt = []
        srtr_str = ""
        logging.info(ply_dt)
        if message.author.bot:
            return
        for i in range(len(kks.convert(message.content))):
            srtr_str = srtr_str + kks.convert(message.content)[i]["hira"]
        logging.info(kks.convert(message.content))
        if not re.sub("[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str) == "":
            srtr_str = re.sub("[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str)
            last_str = srtr_str[-1]
        else:
            last_str = srtr_str[-1]
        logging.info(last_str)
        if re_katakana.fullmatch(last_str):
            lstr = jaconv.kata2hira(last_str)
        elif re_hiragana.fullmatch(last_str):
            lstr = last_str
        elif re_alpha.fullmatch(last_str):
            lstr = last_str.lower()
        else:
            return
        logging.info(lstr)
        if lstr in word_data.chara_ary:
            if len(srtr_data[message.guild.id][f"{lstr}_wd"]) == 0:
                await message.reply(embed=nextcord.Embed(title="しりとり",description=f"にらBOTには`{lstr}`から始まる言葉がない！\nあなたの勝ちです！\n再度しりとりをするには、`n!srtr start`と入力してください！",color=0x00ff00))
                del n_fc.srtr_bool_list[message.guild.id][message.channel.id]
                del srtr_data[message.guild.id]
                with open(f'{home_dir}/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
                return
            w_rn = []
            while True:
                ply_dt = srtr_data[message.guild.id][f"{lstr}_wd"]
                rnd = random.randint(1, len(ply_dt))
                rnd = rnd - 1
                if rnd not in w_rn:
                    reply_mes = ply_dt[rnd]
                    srtr_data[message.guild.id][f"{lstr}_wd"].remove(reply_mes)
                    await message.reply(reply_mes)
                    return
                else:
                    continue
        else:
            for i in range(len(re.sub("[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str))-1):
                w_rn = []
                lstr = re.sub("[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str)[int(f"-{i+2}")]
                if len(srtr_data[message.guild.id][f"{lstr}_wd"]) == 0:
                    await message.reply(embed=nextcord.Embed(title="しりとり",description=f"にらBOTには`{lstr}`から始まる言葉がない！\nあなたの勝ちです！\n再度しりとりをするには、`n!srtr start`と入力してください！",color=0x00ff00))
                    del n_fc.srtr_bool_list[message.guild.id][message.channel.id]
                    del srtr_data[message.guild.id]
                    with open(f'{home_dir}/srtr_bool_list.nira', 'wb') as f:
                        pickle.dump(n_fc.srtr_bool_list, f)
                    return
                ply_dt = srtr_data[message.guild.id][f"{lstr}_wd"]
                for _ in range(len(ply_dt)):
                    rnd = random.randint(1, len(ply_dt))
                    rnd = rnd - 1
                    if rnd not in w_rn:
                        reply_mes = ply_dt[rnd]
                        srtr_data[message.guild.id][f"{lstr}_wd"].remove(reply_mes)
                        await message.reply(reply_mes)
                        return
                    else:
                        continue
            return
    except BaseException as err:
        await message.reply(f"エラーが発生しました。\n```sh\n{traceback.format_exc()}```")
