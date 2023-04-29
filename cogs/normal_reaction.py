import asyncio
import importlib
import listre
import datetime
import logging
import os
import random
import re
import sys

from motor import motor_asyncio

import nextcord
from nextcord.ext import commands, tasks

import util.srtr as srtr
from util import web_api, n_fc
from util.nira import NIRA

SYSDIR = sys.path[0]

image_root = "https://team-i2021.github.io/nira_bot/images"
image_loc = f"{SYSDIR}/images"

# 通常反応をまとめたもの。


nira_hantei = r'にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ'

reaction_list = [
    r"(?:(。∀ ﾟ))",
    r"(´・ω・｀)",
    r'^(?=.*草)(?!.*元素).*$',
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
    r'しゅうじん|囚人|シュウジン|罪人',
    r'bsod|BSOD|ブルスク|ブルースクリーン|ブラックスクリーン',
    r'黒棺|くろひつぎ|藍染隊長|クロヒツギ|あいぜんそうすけ',
    r'昼ごはん|ひるごはん|昼ご飯|ひるご飯'
]

# 0:メッセージ反応,1:添付ファイル反応,2:特殊反応(にら画像),3:特殊反応(にらテキスト),4:特殊反応(Guild指定画像),5:特殊反応(Guild指定文字),6:リアクション
# ファイル/反応数/0
# 反応ファイルなど
reaction_files = {
    0: [0, 1, "おっ、かわいいな"],
    1: [0, 1, None],
    2: [0, 1, "くそわろたｧ!!!"],
    3: [0, 1, "にーっこにこ動画？"],
    4: [0, 1, "ようつべぇ...？"],
    5: [0, 1, "ついったぁ！！！"],
    6: [1, 1, "nira_zoku"],
    7: [1, 6, "itokoi"],
    8: [2, 2, "nira_saibai"],
    9: [2, 1, "nira_itou"],
    10: [2, 1, "nira_rice"],
    11: [2, 1, "nira_kare"],
    12: [2, 1, "nira_fish"],
    13: [2, 1, "nira_dokusai"],
    14: [2, 1, "nira_grow"],
    15: [3, 1, "https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B"],
    16: [2, 1, "nira_sword"],
    17: [2, 1, "nira_and"],
    18: [3, 1, "https://sites.google.com/view/nirand"],
    19: [2, 1, "nira_manju"],
    20: [2, 1, "rebanira"],
    21: [2, 2, "nira_tori"],
    22: [3, 1, "https://twitter.com/niranuranura"],
    23: [1, 4, "nira"],
    24: [4, 2, "tiramisu"],
    25: [1, 3, "pino"],
    26: [4, 2, "fox"],
    27: [1, 1, "uiro"],
    28: [0, 1, "https://www.youtube.com/IkumonTV"],
    29: [4, 1, "apple"],
    30: [4, 3, "sarmon"],
    31: [6, 0, "<:natsu:908565532268179477>"],
    32: [4, 1, "12pp"],
    33: [0, 1, None],
    34: [1, 1, "mike"],
    35: [0, 1, None],
    36: [1, 1, "serori"],
    37: [4, 2, "rori"],
    38: [5, 2, "全知全能なすごい人。\n多分お金と時間があれば何でもできる", "毎晩10時は..."],
    39: [0, 1, "ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww"],
    40: [0, 1, "https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B"],
    41: [1, 1, "kawaisou"],
    42: [5, 1, "https://twitter.com/ribpggxcrmz74t6"],
    43: [5, 1, "https://twitter.com/Aibell__game"],
    44: [1, 1, "sabakan"],
    45: [4, 1, "sosyou"],
    46: [1, 1, "syuuzin"],
    47: [1, 2, "bsod"],
    48: [0, 1, """滲み出す混濁の紋章、不遜なる狂気の器、
湧き上がり・否定し・痺れ・瞬き・眠りを妨げる
爬行する鉄の王女　絶えず自壊する泥の人形
結合せよ　反発せよ　地に満ち己の無力を知れ　破道の九十・黒棺！！！！！！
"""],
    49: [0, 1, "https://cookpad.com/search/%E4%BB%8A%E6%97%A5%E3%81%AE%E3%83%A9%E3%83%B3%E3%83%81"]
}

# すべてが許されるGuild
allow_guild = [870642671415337001, 906400213495865344]

# 通常反応をプログラム化したもの


async def n_reaction(message: nextcord.Message, *custom: int) -> nextcord.Message | None:
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
                if reaction_files[ans[1]][2] is not None:
                    await message.reply(reaction_files[ans[1]][2])
                else:
                    await asyncio.sleep(0)
            else:
                rnd = random.randint(1, reaction_files[ans[1]][1])
                await message.reply(reaction_files[ans[1]][rnd+1])

        # 通常画像
        elif reaction_files[ans[1]][0] == 1:
            if reaction_files[ans[1]][1] == 1:
                if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
            else:
                rnd = random.randint(1, reaction_files[ans[1]][1])
                if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                    await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # ニラ画像
        elif reaction_files[ans[1]][0] == 2:
            if nrs:
                if reaction_files[ans[1]][1] == 1:
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # にらテキスト
        elif reaction_files[ans[1]][0] == 3:
            if nrs:
                if reaction_files[ans[1]][1] == 1:
                    await message.reply(reaction_files[ans[1]][2])
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    await message.reply(reaction_files[ans[1]][rnd+1])

        # Guild画像
        elif reaction_files[ans[1]][0] == 4:
            if message.guild.id in allow_guild:
                if reaction_files[ans[1]][1] == 1:
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.png"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}.mp4"))
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    if os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.png"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.jpg"))
                    elif os.path.isfile(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"):
                        await message.reply(file=nextcord.File(f"{image_loc}/{reaction_files[ans[1]][2]}_{rnd}.mp4"))

        # Guildテキスト
        elif reaction_files[ans[1]][0] == 5:
            if message.guild.id in allow_guild:
                if reaction_files[ans[1]][1] == 1:
                    await message.reply(reaction_files[ans[1]][2])
                else:
                    rnd = random.randint(1, reaction_files[ans[1]][1])
                    await message.reply(reaction_files[ans[1]][rnd+1])

        # リアクション追加
        elif reaction_files[ans[1]][0] == 6:
            await message.add_reaction(reaction_files[ans[1]][2])

    return None


class normal_reaction(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.all_reaction_list = []
        self.ex_reaction_list = []
        self.reaction_bool_list = []
        self.notify_token = []
        self.SLEEP_TIMER = 3
        self.REACTION_ID = "<:trash:908565976407236608>"
        self.last_update: str | None = None
        self.er_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["er_setting"]
        self.nr_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["nr_setting"]
        self.ar_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["ar_setting"]
        self.line_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["notify_token"]
        asyncio.ensure_future(self.database_update())
        self.database_update_loop.start()

    def cog_unload(self):
        self.database_update_loop.cancel()

    async def database_update(self) -> None:
        self.all_reaction_list = await self.ar_collection.find().to_list(length=None)
        self.ex_reaction_list = await self.er_collection.find().to_list(length=None)
        self.reaction_bool_list = await self.nr_collection.find().to_list(length=None)
        self.notify_token = await self.line_collection.find().to_list(length=None)
        self.last_update = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    async def _after_reaction(self, message: nextcord.Message) -> None:
        await message.add_reaction(self.REACTION_ID)
        await asyncio.sleep(self.SLEEP_TIMER)
        try:
            await message.remove_reaction(self.REACTION_ID, self.bot.user)
            return
        except Exception as err:
            logging.error(f"Unknown error occurred during removing reaction.: {err}")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author == self.bot.user:
            return

        if isinstance(message.channel, nextcord.DMChannel) and message.author != self.bot.user:
            await n_reaction(message)
        if isinstance(message.channel, nextcord.Thread):
            return

        if self.bot.debug and message.guild.id not in n_fc.GUILD_IDS:
            return

        if len(notify_token := list(filter(lambda item: item["guild_id"] == message.guild.id and str(message.channel.id) in item, self.notify_token))) != 0:
            await web_api.notify_line(self.bot.session, message, notify_token[0]["token"])

        # BOTには反応しない
        if message.author.bot:
            return
        if message.content.startswith(self.bot.command_prefix) or message.content[-1:] == ".":
            return

        # AllReactionSetting
        # guild_idで指定しているから通常であれば長さは1または0になる。
        if len(all_reaction_list := list(filter(lambda item: item["guild_id"] == message.guild.id, self.all_reaction_list))) == 0:
            all_reaction_list = [{
                "guild_id": message.guild.id,
                "all": 1,
            }]
            asyncio.ensure_future(self.ar_correction.insert_one(all_reaction_list[0]))

        if not all_reaction_list[0]["all"]:
            return

        # if message.guild.id in reaction_datas.all_reaction_list.value:
        #     if message.channel.id in reaction_datas.all_reaction_list.value[message.guild.id]:
        #         if reaction_datas.all_reaction_list.value[message.guild.id][message.channel.id] != 1:
        #             return

        # Channel Topic Check
        if message.channel.topic is not None and re.search("nira-off", message.channel.topic):
            return

        # 追加反応
        if len(ex_reaction_list := list(filter(lambda item: item["guild_id"] == message.guild.id and re.search(item["trigger"], message.content), self.ex_reaction_list))):
            for reaction in ex_reaction_list:
                asyncio.ensure_future(self._after_reaction(await message.reply(reaction["return"], mention_author=reaction["mention"])))

        ###############################
        # 通常反応のブール値存在チェック #
        ###############################
        if len(reaction_bool_list := list(filter(lambda item: item["guild_id"] == message.guild.id, self.reaction_bool_list))) == 0:
            reaction_bool_list = {"guild_id": message.guild.id, "all": True, str(message.channel.id): True}
            self.reaction_bool_list.append(reaction_bool_list)
            await self.nr_collection.update_one({"guild_id": message.guild.id}, {"$set": reaction_bool_list}, upsert=True)
        else:
            reaction_bool_list = reaction_bool_list[0]

        if message.channel.id not in reaction_bool_list:
            reaction_bool_list[str(message.channel.id)] = True
            await self.nr_collection.update_one({str(message.channel.id): True}, {"$set": reaction_bool_list}, upsert=True)

        #########################################
        # 通常反応
        # 「$nr [on/off]」で変更できます
        #########################################
        if not reaction_bool_list["all"]:
            return
        if reaction_bool_list[str(message.channel.id)]:
            try:
                result = await n_reaction(message)
                if result:
                    await self._after_reaction(result)
            except Exception as err:
                logging.error(err, exc_info=True)

    @tasks.loop(seconds=30)
    async def database_update_loop(self):
        await self.database_update()


def setup(bot, **kwargs):
    bot.add_cog(normal_reaction(bot, **kwargs))
    importlib.reload(srtr)
    importlib.reload(web_api)
