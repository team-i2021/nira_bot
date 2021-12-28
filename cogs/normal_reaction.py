from discord.ext import commands
import discord
import datetime
import pickle
import re
import random
import asyncio
import importlib
import sys

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



from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh, web_api
import util.srtr as srtr

image_root = "https://team-i2021.github.io/nira_bot/images"

#通常反応をまとめたもの。

class normal_reaction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # LINEでのメッセージ送信
        if message.guild.id in n_fc.notify_token:
            if message.channel.id in n_fc.notify_token[message.guild.id]:
                web_api.notify_line(message, n_fc.notify_token[message.guild.id][message.channel.id])
        # 自分自身(BOT)には反応しない
        if message.author.bot:
            return
        if message.content[:2] == "n!" or message.content[-1:] == ".":
            return
        if message.author.id in n_fc.py_admin and message.guild.id == 885410991234490408 and message.content[-1:] != ";" and message.content[:7] != "http://" and message.content[:8] != "https://":
            await self.bot.http.delete_message(message.channel.id, message.id)
            await message.channel.send(embed=discord.Embed(title=f"{message.author.name}",description=f"error: discord.c:0: parse(syntax) error before `send_message`\n{message.content}", color=0xff0000))
            return
        # AllReactionSetting
        if message.guild.id in n_fc.all_reaction_list:
            if message.channel.id in n_fc.all_reaction_list[message.guild.id]:
                if n_fc.all_reaction_list[message.guild.id][message.channel.id] != 1:
                    return
        # しりとりブール
        if message.guild.id in n_fc.srtr_bool_list:
            if message.channel.id in n_fc.srtr_bool_list[message.guild.id]:
                await srtr.on_srtr(message)
                return
        # 追加反応
        if message.guild.id in n_fc.ex_reaction_list:
            if n_fc.ex_reaction_list[message.guild.id]["value"] != 0:
                for i in range(n_fc.ex_reaction_list[message.guild.id]["value"]):
                    if re.search(rf'{n_fc.ex_reaction_list[message.guild.id][f"{i+1}_tr"]}', message.content):
                        sended_mes = await message.reply(n_fc.ex_reaction_list[message.guild.id][f"{i+1}_re"])
                        return
        ###############################
        # 通常反応のブール値存在チェック #
        ###############################
        if message.guild.id not in n_fc.reaction_bool_list:
            n_fc.reaction_bool_list[message.guild.id] = {"all": 1, message.channel.id: 1}
            with open('/home/nattyantv/nira_bot_rewrite/reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        if message.channel.id not in n_fc.reaction_bool_list[message.guild.id]:
            n_fc.reaction_bool_list[message.guild.id][message.channel.id] = 1
            with open('/home/nattyantv/nira_bot_rewrite/reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        #########################################
        # 通常反応
        # 「n!nr [on/off]」で変更できます
        #########################################
        if n_fc.reaction_bool_list[message.guild.id]["all"] != 1:
            return
        if n_fc.reaction_bool_list[message.guild.id][message.channel.id] == 1:
            sended_mes = ""
            if re.search(r'(?:(。∀ ﾟ))', message.content):
                sended_mes = await message.reply("おっ、かわいいな")
            if re.search(r'(?:（´・ω・｀）)', message.content):
                sended_mes = await message.reply("かわいいですね...")
            if re.search(r'(?:草)', message.content):
                sended_mes = await message.reply("面白いなぁ（便乗）")
            if re.search(r'(?:https://www.nicovideo.jp)', message.content):
                sended_mes = await message.reply("にーっこにっこどうがっ？")
            if re.search(r'(?:https://www.youtube.com)', message.content):
                sended_mes = await message.reply("ようつべぇ？")
            if re.search(r'(?:https://twitter.com)', message.content):
                sended_mes = await message.reply("ついったあだあーわーい")
            if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
                if message.guild == 870642671415337001:
                    sended_mes = await message.reply(f'{image_root}/nira_zoku.mp4')
            if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
                sended_mes = await message.reply(f'{image_root}/koikingu.jpg')
            if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
                if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
                    if re.search(r'(?:水|みず|ミズ)', message.content):
                        sended_mes = await message.reply(f'{image_root}/nira_water.jpg')
                    else:
                        sended_mes = await message.reply(f'{image_root}/nira_sand.jpg')
                elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_itou.jpg')
                elif re.search(r'(?:ごはん|飯|らいす|ライス|rice|Rice)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_rice.jpg')
                elif re.search(r'(?:枯|かれ|カレ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_kare.jpg')
                elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_fish.jpg')
                elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_dokusai.jpg')
                elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_seityou.jpg')
                elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_nabe.jpg')
                    sended_mes = await message.reply('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
                elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_sword.jpg')
                elif re.search(r'(?:あんど|and|アンド)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_and.jpg')
                elif re.search(r'(?:にらんど|ニランド|nirand|niland)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_land.jpg')
                    sended_mes = await sended_mes.reply('https://sites.google.com/view/nirand/%E3%83%9B%E3%83%BC%E3%83%A0')
                elif re.search(r'(?:饅頭|まんじゅう|マンジュウ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/nira_manju.jpg')
                elif re.search(r'(?:レバ|れば)', message.content):
                    sended_mes = await message.reply(f'{image_root}/rebanira.jpg')
                elif re.search(r'(?:とり|トリ|bird|鳥)', message.content):
                    rnd = random.randint(1, 2)
                    if rnd == 1:
                        sended_mes = await message.reply(f'{image_root}/nirabird_a.jpg')
                    elif rnd == 2:
                        sended_mes = await message.reply(f'{image_root}/nirabird_b.jpg')
                elif re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
                    if message.guild.id == 870642671415337001:
                        sended_mes = await message.reply('https://twitter.com/DR36Hl04ZUwnEnJ')
                else:
                    rnd = random.randint(1, 3)
                    if rnd == 1:
                        sended_mes = await message.reply(f'{image_root}/nira_a.jpg')
                    elif rnd == 2:
                        sended_mes = await message.reply(f'{image_root}/nira_b.jpg')
                    elif rnd == 3:
                        sended_mes = await message.reply(f'{image_root}/nira_c.png')
            if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
                if message.guild.id == 870642671415337001:
                    rnd = random.randint(1, 2)
                else:
                    rnd = 1
                if rnd == 1:
                    sended_mes = await message.reply(f'{image_root}/tiramisu_a.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply(f'{image_root}/tiramisu_b.jpg')
            if re.search(r'(?:ぴの|ピノ|pino)', message.content):
                rnd = random.randint(1, 3)
                if rnd == 1:
                    sended_mes = await message.reply(f'{image_root}/pino_nm.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply(f'{image_root}/pino_st.jpg')
                elif rnd == 3:
                    sended_mes = await message.reply(f'{image_root}/pino_cool.jpg')
            if re.search(r'(?:きつね|キツネ|狐)', message.content):
                if message.guild.id == 870642671415337001:
                    rnd = random.randint(1, 3)
                else:
                    rnd = 1
                if rnd == 1:
                    sended_mes = await message.reply(f'{image_root}/kitune_a.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply(f'{image_root}/kitune_b.jpg')
                elif rnd == 3:
                    sended_mes = await message.reply('https://twitter.com/rougitune')
            if re.search(r'(?:ういろ)', message.content):
                sended_mes = await message.reply(f'{image_root}/uiro.jpg')
            if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://www.youtube.com/IkumonTV')
            if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
                if message.guild.id == 870642671415337001:
                    rnd = random.randint(1, 2)
                else:
                    rnd = 1
                if rnd == 1:
                    sended_mes = await message.reply(f'{image_root}/apple.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply('https://twitter.com/RINGODESU4321')
            if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
                if re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
                    sended_mes = await message.reply('https://twitter.com/Shake_Yuyu')
                else:
                    if message.guild.id == 870642671415337001:
                        rnd = random.randint(1, 3)
                    else:
                        rnd = random.randint(1, 2)
                    if rnd == 1:
                        sended_mes = await message.reply(f'{image_root}/sarmon_a.jpg')
                    elif rnd == 2:
                        sended_mes = await message.reply(f'{image_root}/sarmon_b.jpg')
                    elif rnd == 3:
                        sended_mes = await message.reply(f'{image_root}/sarmon_c.jpg')
            if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
                await message.add_reaction("<:natsu:908565532268179477>")
            if re.search(r'(?:12pp|12PP)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply(f'{image_root}/12pp.jpg')
            if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
                if message.guild.id == 870642671415337001:
                    rnd = random.randint(1, 2)
                    if rnd == 1:
                        sended_mes = await message.reply('https://twitter.com/namae_1216')
                    elif rnd == 2:
                        sended_mes = await message.reply(':heart: by apple')
            if re.search(r'(?:みけ|ミケ|三毛)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply(f'{image_root}/mike.mp4')
            if re.search(r'(?:あう)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply(f'{image_root}/au.jpg')
            if re.search(r'(?:ろり|ロリ)', message.content):
                if re.search(r'(?:せろり|セロリ)', message.content):
                    sended_mes = await message.reply(f'{image_root}/serori.jpg')
                else:
                    if message.guild.id == 870642671415337001:
                        sended_mes = await message.reply(f'{image_root}/ri_par.png')
            if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
                if message.guild.id == 870642671415337001:
                    rnd = random.randint(1, 2)
                else:
                    rnd = 2
                if rnd == 1:
                    sended_mes = await message.reply('毎晩10時が全盛期')
                elif rnd == 2:
                    sended_mes = await message.reply('すごいひと')
            if re.search(r'(?:ｸｧ|きよわらい|きよ笑い|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)', message.content):
                sended_mes = await message.reply('ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww')
            if re.search(r'(?:ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply("https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B&oq=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B")
            if re.search(r'(?:かなしい|つらい|ぴえん|:pleading_face:|:cry:|:sob:|:weary:|:smiling_face_with_tear:|辛|悲しい|ピエン|泣く|泣きそう|いやだ|かわいそうに|可哀そうに)', message.content):
                sended_mes = await message.reply(f"{image_root}/kawaisou.png")
            if re.search(r'(?:あすか|アスカ|飛鳥)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply("https://twitter.com/ribpggxcrmz74t6")
            if re.search(r'(?:しおりん)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply("https://twitter.com/Aibell__game")
            if sended_mes != "":
                await sended_mes.add_reaction("<:trash:908565976407236608>")
                await asyncio.sleep(3)
                try:
                    await sended_mes.remove_reaction("<:trash:908565976407236608>", self.bot.user)
                    return
                except BaseException:
                    return

def setup(bot):
    bot.add_cog(normal_reaction(bot))
    importlib.reload(srtr)
    importlib.reload(web_api)