from math import modf
import discord
from os import getenv
import re
import random
import a2s
from discord.colour import Color

# | N     N  IIIII  RRRR     A     BBBB   OOOOO  TTTTT  
# | NN    N    I    R  R    A A    B   B  O   O    T    
# | N N   N    I    R  R   A   A   B   B  O   O    T    
# | N  N  N    I    RRRR   AAAAA   BBBB   O   O    T    
# | N   N N    I    RR     A   A   B   B  O   O    T    
# | N    NN    I    R R    A   A   B   B  O   O    T    
# | N     N  IIIII  R  R   A   A   BBBB   OOOOO    T    v.永遠にβバージョン

ark_1 = ("60.114.86.249", 27015)
ark_2 = ("60.114.86.249", 27016)
TOKEN = getenv('DISCORD_BOT_TOKEN')
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    print('Launched! NIRABOT v.永遠にβバージョン')
    await client.change_presence(activity=discord.Game(name="n!help | にらゲー", type=1))

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    if message.content == "そうだよ(便乗)":
        await message.reply('黙れよ(便乗)')
        return
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    if message.content == "n!help":
        embed = discord.Embed(title="ニラbot HELP", description="ニラちゃんの扱い方", color=0x00ff00)
        embed.set_author(name="製作者：なつ", url="https://twitter.com/nattyan_tv", icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg")
        embed.add_field(name="```にら系の単語```", value="なんかしらの反応を示します。", inline=False)
        embed.add_field(name="```ここの鯖の住民の3割の人(一部例外あり)の名前```", value="何かしら反応したり、Twitterが送られたりします。", inline=False)
        embed.add_field(name="```n!help```", value="このヘルプを表示します。", inline=False)
        embed.add_field(name="```n!ark```", value="dinosaur鯖(ここでのメインARK鯖)に接続できるか表示します。", inline=False)
        embed.add_field(name="```n!jyanken [グー/チョキ/パー]]```", value="じゃんけんで遊びます。確率操作はしてません。", inline=False)
        embed.add_field(name="```n!uranai```", value="あなたの運勢が占われます。同上。", inline=False)
        await message.reply(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?", description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko", color=0xff0000)
            await message.reply(embed=embed)
            return
        return
    if re.search(r'(?:n!jyanken)', message.content):
        if message.content == "n!jyanken":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!jyanken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        mes = message.content
        try:
            mes_te = mes.split(" ", 2)[1]
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```n!jyanken [グー/チョキ/パー]```\n{err}", color=0xff0000)
            await message.reply(embed=embed)
            return
        if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "チョキ" and mes_te != "パー" and mes_te != "ぱー":
            embed = discord.Embed(title="Error", description="じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```n!jyanken [グー/チョキ/パー]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        embed = discord.Embed(title="にらにらじゃんけん", description="```n!jyanken [グー/チョキ/パー]```", color=0x00ff00)
        if mes_te == "グー" or mes_te == "ぐー":
            mes_te = "グー"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
        elif mes_te == "チョキ" or mes_te == "ちょき":
            mes_te = "チョキ"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
        elif mes_te == "パー" or mes_te == "ぱー":
            mes_te = "パー"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
        rnd_jyanken = random.randint(1, 3)
        if rnd_jyanken == 1:
            mes_te_e = "グー"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_gu.png")
            if mes_te == "グー":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "チョキ":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "パー":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 2:
            mes_te_e = "チョキ"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_choki.png")
            if mes_te == "チョキ":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "パー":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "グー":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 3:
            mes_te_e = "パー"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/images/jyanken_pa.png")
            if mes_te == "パー":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "グー":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "チョキ":
                res_jyan = ":pensive: あなたの勝ちですね..."
        print(mes_te,mes_te_e,rnd_jyanken)
        embed.add_field(name="RESULT", value=res_jyan, inline=False)
        await message.reply(embed=embed)
        return
    if message.content == "n!uranai":
        rnd_uranai = random.randint(0, 10)
        not_star = 10 - rnd_uranai
        stars = ""
        for i in range(rnd_uranai):
            stars = stars + ':star:'
        for i in range(not_star):
            stars = stars + ':eight_pointed_black_star:'
        await message.reply(f"{stars}\nあなたの運勢は星10個中の{rnd_uranai}個です！")
        return
    if re.search(r'(?:n!html)', message.content):
        if message.content == "n!html":
            embed = discord.Embed(title="Error", description="構文が間違っています。\n```n!html\n[Your HTML code here]```", color=0xff0000)
            await message.reply(embed=embed)
            return
        try:
        	mes_ch = message.content
        	mes_code = mes_ch.split("\n", 2)[1]
        	html_link = f"data:text/html,{mes_code}"
        	embed = discord.Embed(title="HTML", description=f"[link](https://nattyan-tv.github.io/tensei_disko/html/data_uri.html#{html_link})", color=0x333333)
        	await message.reply(embed=embed)
        	return
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"エラーが発生しました。\n```{err}```", color=0xff0000)
            await message.reply(embed=embed)
            return
    if message.content == "n!ark":
        embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=":arrows_counterclockwise:Connecting...\nPlease wait...", color=0x333333)
        ark = await message.reply(embed=embed)
        embed = discord.Embed(title="ARK: Survival Evolved\ndinosaur Server", description=f"{message.author.mention}\n:globe_with_meridians:Status", color=0x333333)
        try:
            a2s.info(ark_1)
            embed.add_field(name="RAGNALOK(Server1)", value=":white_check_mark:Success!", inline=False)
            ark_1_users = a2s.players(ark_1)
            user_1 = ""
            ark_1_users = ""
            for i in range(len(a2s.players(ark_1))):
                user_1 = user_1 + "\n" + ark_1_users[-1].split(", ", 4)[1]
                ark_1_users.pop()
            embed.add_field(name="Online User", value=f"ユーザー数:{len(a2s.players(ark_1))}人{ark_1_users}", inline=False)
        except BaseException:
            embed.add_field(name="RAGNALOK(Server1)", value=":x:Failure", inline=False)
        try:
            a2s.info(ark_2)
            embed.add_field(name="THE ISLAND(Server2)", value=":white_check_mark:Success!", inline=False)
            ark_2_users = a2s.players(ark_2)
            user_2 = ""
            ark_2_users = ""
            for i in range(len(a2s.players(ark_2))):
                user_2 = user_2 + "\n" + ark_2_users[-1].split(", ", 4)[1]
                ark_2_users.pop()
            embed.add_field(name="Online User", value=f"ユーザー数:{len(a2s.players(ark_1))}人{ark_1_users}", inline=False)
        except BaseException:
            embed.add_field(name="THE ISLAND(Server2)", value=":x:Failure", inline=False)
        await ark.edit(embed=embed)
        return
    if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
        await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_zoku.mp4')
    if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
        await message.reply('https://nattyan-tv.github.io/tensei_disko/images/koikingu.jpg')
    if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
        if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
            if re.search(r'(?:水|みず|ミズ)', message.content):
                await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_water.jpg')
            else:
                await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sand.jpeg')
        elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_itou.png')
        elif re.search(r'(?:枯|かれ|カレ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_kare.png')
        elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_fish.png')
        elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_dokusai.png')
        elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_seityou.jpeg')
        elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_nabe.jpg')
            await message.reply('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
        elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_sword.png')
        elif re.search(r'(?:あんど|and|アンド)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_and.png')
        else:
            rnd = random.randint(1, 4)
            if rnd == 1:
                await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg')
            elif rnd == 2:
                await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_b.jpg')
            elif rnd == 3:
                await message.reply('https://nattyan-tv.github.io/tensei_disko/images/nira_c.png')
            elif rnd == 4:
                await message.reply('https://twitter.com/DR36Hl04ZUwnEnJ')
    if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_a.png')
        elif rnd == 2:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_b.png')
    if re.search(r'(?:ぴの|ピノ|pino)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_nm.jpg')
        elif rnd == 2:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_st.jpg')
        elif rnd == 3:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/pino_cool.jpg')
    if re.search(r'(?:きつね|キツネ|狐)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
        elif rnd == 2:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
        elif rnd == 3:
            await message.reply('https://twitter.com/rougitune')
    if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人|囚人)', message.content):
        await message.reply('https://www.youtube.com/IkumonTV')
    if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
        elif rnd == 2:
            await message.reply('https://twitter.com/RINGOSANDAO')
    if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
        elif rnd == 2:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
        elif rnd == 3:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
    if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
        if message.content == "なつき":
            channel = message.channel.id
            del_mes_id = message.id
            await client.http.delete_message(channel, del_mes_id)
            await message.reply('なつ....き...? :thinking:')
        elif re.search(r'(?:なつき)', message.content):
            await message.reply('なつ....き...? :thinking:')
        else:
            await message.reply('https://twitter.com/nattyan_tv')
            await message.reply('https://www.youtube.com/なっちゃんTV')
    if re.search(r'(?:12pp|12PP)', message.content):
        await message.reply('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
    if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.reply('https://twitter.com/namae_1216')
        elif rnd == 2:
            await message.reply('ｳﾋｮﾋｮﾋｮﾋﾋﾋｸﾞﾍｯﾍﾍ‪‪ :heart:')
    if re.search(r'(?:みけ|ミケ|三毛)', message.content):
        await message.reply('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
    if re.search(r'(?:あう|アウ)', message.content):
        await message.reply('https://nattyan-tv.github.io/tensei_disko/images/au.png')
    if re.search(r'(?:りーぱー|リーパー|犯|罪|はんざい|つみ|ろり|ロリ)', message.content):
        if re.search(r'(?:せろり|セロリ)', message.content):
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
        else:
            await message.reply('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
    if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.reply('毎晩10時が全盛期')
        elif rnd == 2:
            await message.reply('すごいひと')
    if re.search(r'(?:ｸｧ|きよわらい|きよ笑い|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)', message.content):
        await message.reply('ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww')
    if re.search(r'(?:ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり)', message.content):
        await message.reply("https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B&oq=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B")
    if re.search(r'(?:ark|ARK|あーく|アーク|Ark)', message.content):
        embed = discord.Embed(title="ARK: Survival Evolved", description="[Launch ARK(Steam)](https://nattyan-tv.github.io/tensei_disko/html/launch_ark_steam.html)", color=0x555555)
        await message.reply(embed=embed)


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
