from nextcord.ext import commands
import nextcord
import datetime
import pickle
import re
import random
import asyncio
import importlib
import sys
import listre
import os

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


home_dir = os.path.dirname(__file__)

from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh, web_api
import util.srtr as srtr

image_root = "https://team-i2021.github.io/nira_bot/images"
image_loc = "/home/nattyantv/nira_bot_rewrite/images"

#通常反応をまとめたもの。

nira_hantei = r'にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ'

reaction_list = [
    r"(?:(。∀ ﾟ))",
    r"(´・ω・｀)",
    r'草',
    r'https://www.nicovideo.jp',
    r'https://www.youtube.com',
    r'https://twitter.com',
    r'煮裸族|にらぞく|ニラゾク',
    r'コイキング|イトコイ|いとこい|こいきんぐ|itokoi',
    r'栽培|さいばい|サイバイ',
    r'伊藤|いとう|イトウ',
    r'ごはん|飯|らいす|ライス|rice|Rice',
    r'枯|かれ|カレ',
    r'魚|さかな|fish|サカナ|ざかな|ザカナ',
    r'独裁|どくさい|ドクサイ',
    r'成長|せいちょう|セイチョウ',
    r'なべ|鍋|ナベ',
    r'かりばー|カリバー|剣',
    r'あんど|and|アンド',
    r'らんど|ランド|rand|land',
    r'饅頭|まんじゅう|マンジュウ',
    r'レバ|れば',
    r'とり|トリ|bird|鳥',
    r'twitter|Twitter|TWITTER|ついったー|ツイッター',
    r'にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ',
    r'てぃらみす|ティラミス|tiramisu',
    r'ぴの|ピノ|pino',
    r'きつね|キツネ|狐',
    r'ういろ',
    r'いくもん|イクモン|ikumon|Ikumon',
    r'りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã',
    r'しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン',
    r'なつ|なっちゃん|Nattyan|nattyan',
    r'12pp|12PP',
    r'名前|なまえ|ナマエ|name',
    r'みけ|ミケ|三毛',
    r'あう|アウ',
    r'せろり|セロリ',
    r'ろり|ロリ',
    r'tasuren|たすれん|タスレン',
    r'ｸｧ|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ',
    r'ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり',
    r'かなしい|つらい|ぴえん|:pleading_face:|:cry:|:sob:|:weary:|:smiling_face_with_tear:|辛|悲しい|ピエン|泣く|泣きそう|いやだ|かわいそう|可哀そう',
    r'あすか|アスカ|飛鳥',
    r'しおりん',
    r'さばかん|鯖缶|サバカン',
    r'訴え|訴訟',
    r'しゅうじん|囚人|シュウジン|罪人'
    ]

# 0:メッセージ反応,1:添付ファイル反応,2:特殊反応(にら画像),3:特殊反応(にらテキスト),4:特殊反応(Guild指定画像),5:特殊反応(Guild指定文字)
# ファイル/反応数
# 反応ファイルなど
reaction_files = {
    0:[0,1,"おっ、かわいいな"],
    1:[0,1,"かわいいですね..."],
    2:[0,1,"くそわろたｧ!!!"],
    3:[0,1,"にーっこにこ動画？"],
    4:[0,1,"ようつべぇ...？"],
    5:[0,1,"ついったぁ！！！"],
    6:[1,1,"nira_zoku"],
    7:[1,2,"itokoi"],
    8:[2,2,"nira_saibai"],
    9:[2,1,"nira_itou"],
    10:[2,1,"nira_rice"],
    11:[2,1,"nira_kare"],
    12:[2,1,"nira_fish"],
    13:[2,1,"nira_dokusai"],
    14:[2,1,"nira_grow"],
    15:[3,1,"https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B"],
    16:[2,1,"nira_sword"],
    17:[2,1,"nira_and"],
    18:[3,1,"https://sites.google.com/view/nirand"],
    19:[2,1,"nira_manju"],
    20:[2,1,"rebanira"],
    21:[2,2,"nira_tori"],
    22:[3,1,"https://twitter.com/niranuranura"],
    23:[1,3,"nira"],
    24:[4,2,"tiramisu"],
    25:[1,3,"pino"],
    26:[4,2,"fox"],
    27:[1,1,"uiro"],
    28:[0,1,"https://www.youtube.com/IkumonTV"],
    29:[4,1,"apple"],
    30:[4,3,"sarmon"],
    31:[0,1,"<:natsu:908565532268179477>"],
    32:[4,1,"12pp"],
    33:[5,2,"https://twitter.com/namae_1216",":heart: by apple"],
    34:[1,1,"mike"],
    35:[4,1,"au"],
    36:[1,1,"serori"],
    37:[4,2,"rori"],
    38:[5,2,"全知全能なすごい人。\n多分お金と時間があれば何でもできる","毎晩10時は..."],
    39:[0,1,"ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww"],
    40:[0,1,"https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B"],
    41:[1,1,"kawaisou"],
    42:[5,1,"https://twitter.com/ribpggxcrmz74t6"],
    43:[5,1,"https://twitter.com/Aibell__game"],
    44:[1,1,"sabakan"],
    45:[4,1,"sosyou"],
    46:[1,1,"syuuzin"]
    }

# すべてが許されるGuild
allow_guild = [870642671415337001,906400213495865344]

# 通常反応をプログラム化したもの
def n_reaction(message: nextcord.Message, *custom: int):
    if custom == ():
        ans = listre.search(reaction_list, message.content)
        nrs = re.search(nira_hantei, message.content)
    else:
        ans = (0, custom[0], None)
        nrs = True

    if ans != None:
        # 通常テキスト
        if reaction_files[ans[1]][0] == 0:
            if reaction_files[ans[1]][1] == 1:
                return message.reply(reaction_files[ans[1]][2])
            else:
                rnd = random.randint(1, reaction_files[ans[1]][1])
                return message.reply(reaction_files[ans[1]][rnd+1])

        # 通常画像
        elif reaction_files[ans[1]][0] == 1:
            if reaction_files[ans[1]][1] == 1:
                if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
            else:
                rnd = random.randint(1, reaction_files[ans[1]][1])
                if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                    return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # ニラ画像
        elif reaction_files[ans[1]][0] == 2:
            if nrs:
                if reaction_files[ans[1]][1] == 1:
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # にらテキスト
        elif reaction_files[ans[1]][0] == 3:
            if nrs:
                if reaction_files[ans[1]][1] == 1:
                    return message.reply(reaction_files[ans[1]][2])
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    return message.reply(reaction_files[ans[1]][rnd+1])

        # Guild画像
        elif reaction_files[ans[1]][0] == 4:
            if message.guild.id in allow_guild:
                if reaction_files[ans[1]][1] == 1:
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                        return message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # Guildテキスト
        elif reaction_files[ans[1]][0] == 5:
            if message.guild.id in allow_guild:
                if reaction_files[ans[1]][1] == 1:
                    return message.reply(reaction_files[ans[1]][2])
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    return message.reply(reaction_files[ans[1]][rnd+1])


class normal_reaction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        # LINEでのメッセージ送信
        if message.guild == None:
            return
        if message.guild.id in n_fc.notify_token:
            if message.channel.id in n_fc.notify_token[message.guild.id]:
                web_api.notify_line(message, n_fc.notify_token[message.guild.id][message.channel.id])
        # 自分自身(BOT)には反応しない
        if message.author.bot:
            return
        if message.content[:2] == "n!" or message.content[-1:] == ".":
            return
        # if message.author.id in n_fc.py_admin and message.guild.id == 885410991234490408 and message.content[-1:] != ";" and message.content[:7] != "http://" and message.content[:8] != "https://":
        #     await self.bot.http.delete_message(message.channel.id, message.id)
        #     await message.channel.send(embed=nextcord.Embed(title=f"{message.author.name}",description=f"error: nextcord.c:0: parse(syntax) error before `send_message`\n{message.content}", color=0xff0000))
        #     return
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
            with open(f'{home_dir}/reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        if message.channel.id not in n_fc.reaction_bool_list[message.guild.id]:
            n_fc.reaction_bool_list[message.guild.id][message.channel.id] = 1
            with open(f'{home_dir}/reaction_bool_list.nira', 'wb') as f:
                pickle.dump(n_fc.reaction_bool_list, f)
        #########################################
        # 通常反応
        # 「n!nr [on/off]」で変更できます
        #########################################
        if n_fc.reaction_bool_list[message.guild.id]["all"] != 1:
            return
        if n_fc.reaction_bool_list[message.guild.id][message.channel.id] == 1:
            sended_mes = ""
            try:
                sended_mes = await n_reaction(message)
            except BaseException as err:
                if re.search("object NoneType can't be used in 'await' expression", str(err)) == None:
                    logging.error(err)
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
