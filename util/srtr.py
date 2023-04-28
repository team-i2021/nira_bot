import copy
import logging
import random
import re
import sys
import traceback

import jaconv
import nextcord
import pykakasi

from motor import motor_asyncio

from util import word_data

re_hiragana = re.compile(r'^[あ-ん]+$')
re_katakana = re.compile(r'[\u30A1-\u30F4]+')
re_alpha = re.compile(r'^[a-zA-Z]+$')
re_kanji = re.compile(r'^[\u4E00-\u9FD0]+$')

global srtr_data
srtr_data = {}

SYSDIR = sys.path[0]

kks = pykakasi.kakasi()

async def on_srtr(message: nextcord.Message, collection: motor_asyncio.AsyncIOMotorCollection):
    """Process Siritori game"""
    if message.guild.id not in srtr_data:
        srtr_data[message.guild.id] = copy.deepcopy(word_data.words)
    try:
        ply_dt = []
        srtr_str = ""
        logging.info(ply_dt)
        if message.author.bot or message.content == "" or message.content == None:
            return
        for i in range(len(kks.convert(message.content))):
            srtr_str = srtr_str + kks.convert(message.content)[i]["hira"]
        logging.info(kks.convert(message.content))
        if not re.sub("[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str) == "":
            srtr_str = re.sub(
                "[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str)
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
                await message.reply(embed=nextcord.Embed(title="しりとり", description=f"にらBOTには`{lstr}`から始まる言葉がない！\nあなたの勝ちです！\n再度しりとりをするには、`n!srtr start`と入力してください！", color=0x00ff00))
                # 事後処理
                srtr_controller = await collection.find_one({"guild_id": message.guild.id})
                srtr_controller["channels"].remove(message.channel.id)
                await collection.update_one({"guild_id": message.guild.id}, {"$set": srtr_controller})
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
                lstr = re.sub(
                    "[^A-Za-z\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF\uF900-\uFA6D\uFF66-\uFF9D]+", "", srtr_str)[int(f"-{i+2}")]
                if len(srtr_data[message.guild.id][f"{lstr}_wd"]) == 0:
                    await message.reply(embed=nextcord.Embed(title="しりとり", description=f"にらBOTには`{lstr}`から始まる言葉がない！\nあなたの勝ちです！\n再度しりとりをするには、`n!srtr start`と入力してください！", color=0x00ff00))
                    srtr_controller = await collection.find_one({"guild_id": message.guild.id})
                    srtr_controller["channels"].remove(message.channel.id)
                    await collection.update_one({"guild_id": message.guild.id}, {"$set": srtr_controller})
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
    except Exception:
        await message.reply(f"エラーが発生しました。\n```sh\n{traceback.format_exc()}```")
        logging.error("Error", exc_info=True)
