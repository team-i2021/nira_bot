import discord
from os import getenv
import re
import random

TOKEN = getenv('DISCORD_BOT_TOKEN')
client = discord.Client()


# 起動時に動作する処理
@client.event
async def on_ready():
    print('正常に起動しました')
    print('ニラbot v0.9.2')
    print('～故に彼女は猫だった～')
    await client.change_presence(activity=discord.Game(name="ニラの栽培ゲーム", type=1))

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
        embed.add_field(name="helpの見方", value="`単語A`・`単語B`\n> 単語Aと単語Bの両方が含まれるときの反応\n", inline=False)
        embed.add_field(name="---メイン---", value="（ひらがな・カタカナ・漢字は大体区別しません）\n\n", inline=False)
        embed.add_field(name="`ニラ`", value="> ニラの画像\n", inline=False)
        embed.add_field(name="`ニラ`・`栽培`", value="> 土の様子\n", inline=False)
        embed.add_field(name="`ニラ`・`栽培`・`水`", value="> 水栽培されているニラ\n", inline=False)
        embed.add_field(name="`ニラ`・`魚`", value="> 新種の魚「ニラ魚」\n", inline=False)
        embed.add_field(name="`ニラ`・`独裁`", value="> 独裁者ニラの肖像画\n", inline=False)
        embed.add_field(name="`ニラ`・`成長`", value="> 世にも珍しい、ニラの成長過程\n", inline=False)
        embed.add_field(name="`ニラ`・`鍋`", value="> ニラ鍋のレシピ\n", inline=False)
        embed.add_field(name="`ニラ`・`カリバー`", value="> 聖剣ニラカリバー！\n", inline=False)
        embed.add_field(name="`ニラ`・`アンド`", value="> 「nik〇 and...」のコラ画像\n", inline=False)
        embed.add_field(name="`煮裸族`", value="> nira_zoku.mp4\n\n", inline=False)
        embed.add_field(name="---その他---", value="ARKサーバーの人物名にも反応したり？", inline=False)
        await message.channel.send(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?", description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko", color=0xff0000)
            await message.channel.send(embed=embed)
            return
        return
    if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_zoku.mp4')
    if re.search(r'(?:コイキング|イトコイ|いとこい|コイキング|itokoi)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/koikingu.jpg')
    if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum|てりじの|テリジノ)', message.content):
        if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
            if re.search(r'(?:水|みず|ミズ)', message.content):
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_water.jpg')
            else:
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_sand.jpeg')
        elif re.search(r'(?:伊藤|いとう|イトウ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_itou.png')
        elif re.search(r'(?:枯|かれ|カレ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_kare.png')
        elif re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_fish.png')
        elif re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_dokusai.png')
        elif re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_seityou.jpeg')
        elif re.search(r'(?:なべ|鍋|ナベ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_nabe.jpg')
            await message.channel.send('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
        elif re.search(r'(?:かりばー|カリバー|剣)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_sword.png')
        elif re.search(r'(?:あんど|and|アンド)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_and.png')
        else:
            rnd = random.randint(1, 4)
            if rnd == 1:
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg')
            elif rnd == 2:
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_b.jpg')
            elif rnd == 3:
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_c.png')
            elif rnd == 4:
                await message.channel.send('https://twitter.com/DR36Hl04ZUwnEnJ')
    if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_a.png')
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_b.png')
    if re.search(r'(?:ぴの|ピノ|pino)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_nm.jpg')
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_st.jpg')
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_cool.jpg')
    if re.search(r'(?:きつね|キツネ|狐)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
        elif rnd == 3:
            await message.channel.send('https://twitter.com/rougitune')
    if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人|囚人)', message.content):
        await message.channel.send('https://www.youtube.com/IkumonTV')
    if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
        elif rnd == 2:
            await message.channel.send('https://twitter.com/RINGOSANDAO')
    if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
    if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
        if message.content == "なつき":
            channel = message.channel.id
            del_mes_id = message.id
            await client.http.delete_message(channel, del_mes_id)
            await message.channel.send('なつ....き...? :thinking:')
        elif re.search(r'(?:なつき)'):
            await message.channel.send('なつ....き...? :thinking:')
        else:
            await message.channel.send('https://twitter.com/nattyan_tv')
            await message.channel.send('https://www.youtube.com/なっちゃんTV')
    if re.search(r'(?:12pp|12PP)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
    if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://twitter.com/namae_1216')
        elif rnd == 2:
            await message.channel.send('ｳﾋｮﾋｮﾋｮﾋﾋﾋｸﾞﾍｯﾍﾍ‪‪ :heart:')
    if re.search(r'(?:みけ|ミケ|三毛)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
    if re.search(r'(?:あう|アウ)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/au.png')
    if re.search(r'(?:りーぱー|リーパー|犯|罪|はんざい|つみ|ろり|ロリ)', message.content):
        if re.search(r'(?:せろり|セロリ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
        else:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
    if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('毎晩10時が全盛期')
        elif rnd == 2:
            await message.channel.send('すごいひと')
    if re.search(r'(?:ｸｧ|きよわらい|きよ笑い|くあっ|クアッ|クァ|くぁ|くわぁ|クワァ)', message.content):
        await message.channel.send('ﾜｰｽｹﾞｪｽｯｹﾞｸｧｯｸｧｯｸｧwwwww')
    if re.search(r'(?:ふぇにっくす|フェニックス|不死鳥|ふしちょう|phoenix|焼き鳥|やきとり)', message.content):
        await message.reply("https://www.google.com/search?q=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B&oq=%E3%81%93%E3%81%AE%E8%BF%91%E3%81%8F%E3%81%AE%E7%84%BC%E3%81%8D%E9%B3%A5%E5%B1%8B")
    if re.search(r'(?:ark|ARK|あーく|アーク|Ark)', message.content):
        embed = discord.Embed(title="ARK: Survival Evolved", description="[Launch ARK(Steam)](https://nattyan-tv.github.io/tensei_disko/html/launch_ark_steam.html)", color=0x555555)
        await message.channel.send(embed=embed)


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
