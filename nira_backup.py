# coding: utf-8
import discord
from os import getenv
import sys
import os
import re
import random
import a2s
import asyncio
import datetime
import bot_token
import n_cmd
import status_c

from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
from discord.flags import MessageFlags

# | N     N  IIIII  RRRR     A     BBBB   OOOOO  TTTTT
# | NN    N    I    R  R    A A    B   B  O   O    T
# | N N   N    I    R  R   A   A   B   B  O   O    T
# | N  N  N    I    RRRR   AAAAA   BBBB   O   O    T
# | N   N N    I    RR     A   A   B   B  O   O    T
# | N    NN    I    R R    A   A   B   B  O   O    T
# | N     N  IIIII  R  R   A   A   BBBB   OOOOO    T  v.永遠にβバージョン

py_admin = [669178357371371522]

intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.members = True # メンバーに関する情報を受け取る
client = discord.Client(intents=intents)

# 起動時処理
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="読み込み中...", type=1), status=discord.Status.dnd)
    try:
        with open('steam_server_list.nira', 'rb') as f:
            n_cmd.steam_server_list = pickle.load(f)
        print(n_cmd.steam_server_list)
        print("変数[steam_server_list]のファイル読み込みに成功しました。")
    except BaseException:
        print("変数[steam_server_list]のファイル読み込みに失敗しましたが続行します。")
    try:
        with open('reaction_bool_list.nira', 'rb') as f:
            n_cmd.reaction_bool_list = pickle.load(f)
        print("変数[reaction_bool_list]のファイル読み込みに成功しました。")
        print(n_cmd.reaction_bool_list)
    except BaseException:
        print("変数[reaction_bool_list]のファイル読み込みに失敗しましたが続行します。")
    try:
        with open('welcome_id_list.nira', 'rb') as f:
            n_cmd.welcome_id_list = pickle.load(f)
        print("変数[welcome_id_list]のファイル読み込みに成功しました。")
        print(n_cmd.welcome_id_list)
    except BaseException:
        print("変数[welcome_id_list]のファイル読み込みに失敗しましたが続行します。")
    try:
        with open('ex_reaction_list.nira', 'rb') as f:
            n_cmd.ex_reaction_list = pickle.load(f)
        print("変数[ex_reaction_list]のファイル読み込みに成功しました。")
        print(n_cmd.ex_reaction_list)
    except BaseException:
        print("変数[ex_reaction_list]のファイル読み込みに失敗しましたが続行します。")
    await status_c.change(client)
    print('Launched! NIRABOT v.永遠にβバージョン')

# メッセージ受信時処理
@client.event
async def on_message(message):
    # 自分自身には反応しない
    if message.author.bot:
        return
    # 略したけど、コマンド系
    if await n_cmd.nira_check(message, client) == "exec":
        return
    # 追加反応
    if str(message.guild.id) in n_cmd.ex_reaction_list:
        if n_cmd.ex_reaction_list[str(message.guild.id)]["value"] != 0:
            for i in range(n_cmd.ex_reaction_list[str(message.guild.id)]["value"]):
                if re.search(n_cmd.ex_reaction_list[str(message.guild.id)][f"{i+1}_tr"], message.content):
                    sended_mes = await message.reply(n_cmd.ex_reaction_list[str(message.guild.id)][f"{i+1}_re"])
                    return
    ###############################
    # 通常反応のブール値存在チェック #
    ###############################
    if str(message.guild.id) not in n_cmd.reaction_bool_list:
                n_cmd.reaction_bool_list[str(message.guild.id)] = 1
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_cmd.reaction_bool_list, f)
    #########################################
    # 通常反応
    # 「n!nr [on/off]」で変更できます
    #########################################
    if n_cmd.reaction_bool_list[str(message.guild.id)] == 1:
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
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_zoku.mp4')
        if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/koikingu.jpg')
        if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
            if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
                if re.search(r'(?:水|みず|ミズ)', message.content):
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_water.jpg')
                else:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sand.jpeg')
            elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_itou.png')
            elif re.search(r'(?:ごはん|飯|らいす|ライス|rice|Rice)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_rice.jpg')
            elif re.search(r'(?:枯|かれ|カレ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_kare.png')
            elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_fish.png')
            elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_dokusai.png')
            elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_seityou.jpeg')
            elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_nabe.jpg')
                sended_mes = await message.reply('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
            elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sword.png')
            elif re.search(r'(?:あんど|and|アンド)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_and.png')
            elif re.search(r'(?:にらんど|ニランド|nirand|niland)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_land.png')
                sended_mes = await sended_mes.reply('https://sites.google.com/view/nirand/%E3%83%9B%E3%83%BC%E3%83%A0')
            elif re.search(r'(?:饅頭|まんじゅう|マンジュウ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_manju.png')
            elif re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://twitter.com/DR36Hl04ZUwnEnJ')
            else:
                rnd = random.randint(1, 3)
                if rnd == 1:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg')
                elif rnd == 2:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_b.jpg')
                elif rnd == 3:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_c.png')
        if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_a.png')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_b.png')
        if re.search(r'(?:ぴの|ピノ|pino)', message.content):
            rnd = random.randint(1, 3)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_nm.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_st.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_cool.jpg')
        if re.search(r'(?:きつね|キツネ|狐)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 3)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
            elif rnd == 3:
                sended_mes = await message.reply('https://twitter.com/rougitune')
        if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://www.youtube.com/IkumonTV')
        if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
            else:
                rnd = 1
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://twitter.com/RINGOSANDAO')
        if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 4)
            else:
                rnd = random.randint(1, 3)
            if rnd == 1:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
            elif rnd == 2:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
            elif rnd == 3:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
            elif rnd == 4:
                sended_mes = await message.reply('https://twitter.com/Shake_Yuyu')
        if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
            await message.add_reaction("<:shiro:892787951673692161>")
        if re.search(r'(?:12pp|12PP)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
        if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
            if message.guild.id == 870642671415337001:
                rnd = random.randint(1, 2)
                if rnd == 1:
                    sended_mes = await message.reply('https://twitter.com/namae_1216')
                elif rnd == 2:
                    sended_mes = await message.reply(':heart: by apple')
        if re.search(r'(?:みけ|ミケ|三毛)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
        if re.search(r'(?:あう)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/au.png')
        if re.search(r'(?:ろり|ロリ)', message.content):
            if re.search(r'(?:せろり|セロリ)', message.content):
                sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
            else:
                if message.guild.id == 870642671415337001:
                    sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
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
            sended_mes = await message.reply("https://nattyan-tv.github.io/tensei_disko/images/kawaisou.png")
        if re.search(r'(?:あすか|アスカ|飛鳥)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/ribpggxcrmz74t6")
        if re.search(r'(?:しおりん)', message.content):
            if message.guild.id == 870642671415337001:
                sended_mes = await message.reply("https://twitter.com/Aibell__game")
        if sended_mes != "":
            await sended_mes.add_reaction("<:trash:896021635470082048>")
            await asyncio.sleep(3)
            try:
                await sended_mes.remove_reaction("<:trash:896021635470082048>", client.user)
                return
            except BaseException:
                return

                
# リアクション受信時
@client.event
async def on_reaction_add(react, mem):
    # SteamServerListのリスト
    try:
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "サーバーリストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
            if n_cmd.admin_check(react.message.guild, mem):
                if str(react.emoji) == "\U00002B55":
                    del n_cmd.steam_server_list[str(react.message.guild.id)]
                    with open('steam_server_list.nira', 'wb') as f:
                        pickle.dump(n_cmd.steam_server_list, f)
                    embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                    if mem.id == 669178357371371522:
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                    await react.message.channel.send(embed=embed)
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
                elif str(react.emoji) == "\U0000274C":
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
            else:
                user = await client.fetch_user(mem.id)
                await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーのカスタムサーバーリスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                return
    except KeyError as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
        return
    except BaseException as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
        return
    # 追加返答のリスト
    try:
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
            if n_cmd.admin_check(react.message.guild, mem):
                if str(react.emoji) == "\U00002B55":
                    del n_cmd.ex_reaction_list[str(react.message.guild.id)]
                    with open('ex_reaction_list.nira', 'wb') as f:
                        pickle.dump(n_cmd.ex_reaction_list, f)
                    embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                    if mem.id == 669178357371371522:
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                    await react.message.channel.send(embed=embed)
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
                elif str(react.emoji) == "\U0000274C":
                    await client.http.delete_message(react.message.channel.id, react.message.id)
                    return
            else:
                user = await client.fetch_user(mem.id)
                await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーの追加返答リスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                return
    except KeyError as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
        return
    except BaseException as err:
        await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
        return
    if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and str(react.emoji) == '<:trash:896021635470082048>':
        await client.http.delete_message(react.message.channel.id, react.message.id)
        return

@client.event
async def on_member_join(member):
    user_id = member.id
    try:
        user = await client.fetch_user(user_id)
        if str(member.guild.id) not in n_cmd.welcome_id_list:
            return
        channel = client.get_channel(n_cmd.welcome_id_list[str(member.guild.id)])
        embed = discord.Embed(title="User Info", description=f"名前：`{user.name}`\nID：`{user.id}`", color=0x00ff00)
        embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{str(user.avatar)}")
        embed.add_field(name="アカウント製作日", value=f"```{user.created_at}```")
        await channel.send(embed=embed)
        return
    except BaseException as err:
        print(err)
        return

# Botの起動とDiscordサーバーへの接続
client.run(bot_token.nira_token)
