# coding: utf-8
import discord
from os import getenv
import re
import random
import a2s
import asyncio

# | N     N  IIIII  RRRR     A     BBBB   OOOOO  TTTTT
# | NN    N    I    R  R    A A    B   B  O   O    T
# | N N   N    I    R  R   A   A   B   B  O   O    T
# | N  N  N    I    RRRR   AAAAA   BBBB   O   O    T
# | N   N N    I    RR     A   A   B   B  O   O    T
# | N    NN    I    R R    A   A   B   B  O   O    T
# | N     N  IIIII  R  R   A   A   BBBB   OOOOO    T  v.永遠にβバージョン

ark_1 = ("60.114.86.249", 27015)  # アイランド
ark_1_nm = "The Island :free:"
ark_2 = ("60.114.86.249", 27016)  # アベレーション
ark_2_nm = "Aberration :dollar:"
ark_3 = ("60.114.86.249", 27017)  # エクスティンクション
ark_3_nm = "Extinction :dollar:"
ark_4 = ("60.114.86.249", 27018)  # ジェネシス1
ark_4_nm = "Genesis: Part 1 :dollar:"
ark_5 = ("60.114.86.249", 27019)  # ジェネシス2
ark_5_nm = "Genesis: Part 2 :dollar:"
ark_6 = ("60.114.86.249", 27020)  # ラグナロク
ark_6_nm = "Ragnarok :free:"


client = discord.Client()
TOKEN = getenv('DISCORD_BOT_TOKEN')

async def rmv_act(mes, usr):
    await asyncio.sleep(2)
    await mes.remove_reaction("<:trash:89021635470082048>", usr)

def server_check(embed, n):
    if n == "1":
        sv_ad = ark_1
        sv_nm = ark_1_nm
    elif n == "2":
        sv_ad = ark_2
        sv_nm = ark_2_nm
    elif n == "3":
        sv_ad = ark_3
        sv_nm = ark_3_nm
    elif n == "4":
        sv_ad = ark_4
        sv_nm = ark_4_nm
    elif n == "5":
        sv_ad = ark_5
        sv_nm = ark_5_nm
    elif n == "6":
        sv_ad = ark_6
        sv_nm = ark_6_nm
    try:
        print(f"{sv_nm}/{sv_ad} への接続")
        print(a2s.info(sv_ad))
        embed.add_field(name=f"> {sv_nm}", value=":white_check_mark:Success!", inline=False)
        user = ""
        print(a2s.players(sv_ad))
        if a2s.players(sv_ad) != []:
            sv_users_str = str(a2s.players(sv_ad)).replace("[", "").replace("]", "")
            sv_users_str = sv_users_str[7:]
            sv_users_str = sv_users_str + ", Player("
            sv_users_list = sv_users_str.split("), Player(")
            for i in range(len(a2s.players(sv_ad))):
                sp_info = sv_users_list[-2]
                splited = sp_info.split(", ", 4)[1]
                user_add = splited.replace("name='", "").replace("'", "")
                user = user + "\n" + f"```{user_add}```"
                sv_users_list.pop()
            embed.add_field(name="> Online User", value=f"ユーザー数:{len(a2s.players(sv_ad))}人{user}\n==========", inline=False)
        else:
            embed.add_field(name="> Online User", value=":information_source:オンラインユーザーはいません。\n==========", inline=False)
    except BaseException as err:
        embed.add_field(name=f"> {sv_nm}", value=":x: Failure\n==========", inline=False)
    return True

# 起動時処理
@client.event
async def on_ready():
    print('Launched! NIRABOT v.永遠にβバージョン')
    await client.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1))

# メッセージ受信時処理
@client.event
async def on_message(message):
    sended_mes = ""
    if message.content == "そうだよ(便乗)":
        await message.reply('黙れよ(便乗)')
        return
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    if message.content == "n!help":
        embed = discord.Embed(title="ニラbot HELP", description="ニラちゃんの扱い方", color=0x00ff00)
        embed.set_author(name="製作者：なつ", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.add_field(name="```にら系の単語```", value="なんかしらの反応を示します。", inline=False)
        embed.add_field(name="```ここの鯖の住民の3割の人(一部例外あり)の名前```", value="何かしら反応したり、Twitterが送られたりします。", inline=False)
        embed.add_field(name="```n!help```", value="このヘルプを表示します。", inline=False)
        embed.add_field(name="```n!ark [server]```", value="dinosaur鯖(ここでのメインARK鯖)に接続できるか表示します。", inline=False)
        embed.add_field(name="> Server list", value="`1`:The Island\n`2`:Aberration\n`3`:Exctinction\n`4`:Genesis: Part 1\n`5`:Genesis: Part 2\n`6`:Ragnarok", inline=False)
        embed.add_field(name="> [server]を指定しないと", value="全てのサーバーの状態が表示されます。", inline=False)
        embed.add_field(name="```n!embed [title] [descripition]```", value="Embedを生成して送信します。", inline=False)
        embed.add_field(name="```n!janken [グー/チョキ/パー]]```", value="じゃんけんで遊びます。確率操作はしてません。", inline=False)
        embed.add_field(name="```n!uranai```", value="あなたの運勢が占われます。同上。\n==========", inline=False)
        embed.add_field(name="・リアクションについて", value="このbotの発したメッセージの一部には、<:trash:896021635470082048>のリアクションが自動的に付きます。\nこのリアクションを押すとそのメッセージが削除されます。", inline=False)
        await message.reply(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?", description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko", color=0xff0000)
            await message.reply(embed=embed)
            return
        return
    if re.search(r'(?:n!janken)', message.content):
        if message.content == "n!janken":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 2)[1]
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```n!janken [グー/チョキ/パー]```\n{err}", color=0xff0000)
            await message.reply(embed=embed)
            return
        if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "ちょき" and mes_te != "パー" and mes_te != "ぱー":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!janken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        embed = discord.Embed(title="にらにらじゃんけん", description="```n!janken [グー/チョキ/パー]```", color=0x00ff00)
        if mes_te == "グー" or mes_te == "ぐー":
            mes_te = "```グー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
        elif mes_te == "チョキ" or mes_te == "ちょき":
            mes_te = "```チョキ```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
        elif mes_te == "パー" or mes_te == "ぱー":
            mes_te = "```パー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
        rnd_jyanken = random.randint(1, 3)
        if rnd_jyanken == 1:
            mes_te_e = "```グー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
            if mes_te == "```グー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```チョキ```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```パー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 2:
            mes_te_e = "```チョキ```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
            if mes_te == "```チョキ```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```パー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```グー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 3:
            mes_te_e = "```パー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
            if mes_te == "```パー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```グー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```チョキ```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        embed.add_field(name="\n```RESULT```\n", value=res_jyan, inline=False)
        await message.reply(embed=embed)
        return
    if message.content == "n!uranai":
        rnd_uranai = random.randint(0, 10)
        not_star = 10 - rnd_uranai
        stars = ""
        for i in range(rnd_uranai):
            stars = stars + '★'
        for i in range(not_star):
            stars = stars + '⭐︎'
        await message.reply(f"{stars}\nあなたの運勢は星10個中の{rnd_uranai}個です！")
        return
    if re.search(r'(?:n!embed)', message.content):
        if message.content == "n!embed":
            embed = discord.Embed(title="Error", description="構文が間違っています。\n```n!embed [title] [description(スペースなど利用可能)]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        try:
            mes_ch = message.content
            emb_title = mes_ch.split(" ", 4)[1]
            emb_desc = mes_ch.split(" ", 3)[2]
            embed = discord.Embed(title=emb_title, description=emb_desc, color=0x000000)
            await message.channel.send(embed=embed)
            return
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"エラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return
    if re.search(r'(?:n!ark)', message.content):
        if message.content == "n!ark":
            embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=":arrows_counterclockwise:Connecting...\nPlease wait...", color=0x333333)
            ark_emb = await message.reply(embed=embed)
            embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=":globe_with_meridians:Status\n==========", color=0x00ff00)
            server_check(embed, "1")
            server_check(embed, "2")
            server_check(embed, "3")
            server_check(embed, "4")
            server_check(embed, "5")
            server_check(embed, "6")
            await ark_emb.edit(embed=embed)
            await ark_emb.reply(f"{message.author.mention}")
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 2)[1]
            print(mes_te)
        except BaseException as err:
            embe = discord.Embed(title="Error", description=f"不明なエラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embe)
        if mes_te != "1" and mes_te != "2" and mes_te != "3" and mes_te != "4" and mes_te != "5" and mes_te != "6":
            embe = discord.Embed(title="Error", description="```n!ark [server]```\nServer引数を`1～6`で指定してください。\n\n> Server list\n`1`:The Island\n`2`:Aberration\n`3`:Exctinction\n`4`:Genesis: Part 1\n`5`:Genesis: Part 2\n`6`:Ragnarok", color=0xff0000)
            await message.reply(embed=embe)
            return
        embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=":arrows_counterclockwise:Connecting...\nPlease wait...", color=0x333333)
        ark_emb = await message.reply(embed=embed)
        embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=":globe_with_meridians:Status\n==========", color=0x00ff00)
        server_check(embed, mes_te)
        await ark_emb.edit(embed=embed)
        await ark_emb.reply(f"{message.author.mention}")
        return
    if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
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
        elif re.search(r'(?:んど|ンド|nd)', message.content):
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_land.png')
            sended_mes = await sended_mes.reply('https://sites.google.com/view/nirand/%E3%83%9B%E3%83%BC%E3%83%A0')
        elif re.search(r'(?:twitter|Twitter|TWITTER|ついったー|ツイッター)', message.content):
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
        rnd = random.randint(1, 2)
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
        rnd = random.randint(1, 3)
        if rnd == 1:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
        elif rnd == 2:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
        elif rnd == 3:
            sended_mes = await message.reply('https://twitter.com/rougitune')
    if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人|囚人)', message.content):
        sended_mes = await message.reply('https://www.youtube.com/IkumonTV')
    if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
        elif rnd == 2:
            sended_mes = await message.reply('https://twitter.com/RINGOSANDAO')
    if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
        rnd = random.randint(1, 4)
        if rnd == 1:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
        elif rnd == 2:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
        elif rnd == 3:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
        elif rnd == 4:
            sended_mes = await message.reply('https://twitter.com/Shake_Yuyu')
    if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
        if message.content == "なつき":
            channel = message.channel.id
            del_mes_id = message.id
            sended_mes = await client.http.delete_message(channel, del_mes_id)
            sended_mes = await message.reply('なつ....き...? :thinking:')
        elif re.search(r'(?:なつき)', message.content):
            sended_mes = await message.reply('なつ....き...? :thinking:')
        else:
            sended_mes = await message.reply('https://twitter.com/nattyan_tv')
            sended_mes = await message.reply('https://www.youtube.com/なっちゃんTV')
    if re.search(r'(?:12pp|12PP)', message.content):
        sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
    if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            sended_mes = await message.reply('https://twitter.com/namae_1216')
        elif rnd == 2:
            sended_mes = await message.reply('ｳﾋｮﾋｮﾋｮﾋﾋﾋｸﾞﾍｯﾍﾍ‪‪ :heart:')
    if re.search(r'(?:みけ|ミケ|三毛)', message.content):
        sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
    if re.search(r'(?:あう|アウ)', message.content):
        sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/au.png')
    if re.search(r'(?:りーぱー|リーパー|犯|罪|はんざい|つみ|ろり|ロリ)', message.content):
        if re.search(r'(?:せろり|セロリ)', message.content):
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
        else:
            sended_mes = await message.reply('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
    if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            sended_mes = await message.reply('毎晩10時が全盛期')
        elif rnd == 2:
            sended_mes = await message.reply('すごいひと')
    if re.search(r'(?:ｸｧ|きよわらい|きよ笑い|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)', message.content):
        sended_mes = await message.reply('ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww')
    if re.search(r'(?:ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり)', message.content):
        sended_mes = await message.reply("https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B&oq=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B")
    if re.search(r'(?:ark|ARK|あーく|アーク|Ark)', message.content):
        embed = discord.Embed(title="ARK: Survival Evolved", description="[Launch ARK(Steam)](https://nattyan-tv.github.io/tensei_disko/html/launch_ark_steam.html)", color=0x555555)
        sended_mes = await message.reply(embed=embed)
    if re.search(r'(?:かなしい|つらい|ぴえん|:pleading_face:|:cry:|:sob:|:weary:|:smiling_face_with_tear:|辛|悲しい|ピエン|泣く|泣きそう|いやだ|かわいそうに|可哀そうに)', message.content):
        sended_mes = await message.reply("https://nattyan-tv.github.io/tensei_disko/images/kawaisou.png")
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
    if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and str(react.emoji) == '<:trash:896021635470082048>':
        role_list = []
        for role in mem.roles:
            role_list.append(role.id)
        print(894843810566266900 in role_list, 876433165105897482 in role_list, 894365538724237353 in role_list, 885492941261524992 in role_list, 890861951842942978 in role_list)
        if 894843810566266900 in role_list or 876433165105897482 in role_list or 894365538724237353 in role_list or 885492941261524992 in role_list or 890861951842942978 in role_list:
            await client.http.delete_message(react.message.channel.id, react.message.id)
    return

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
