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
        await message.channel.send('黙れよ(便乗)')
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
        embed.add_field(name="---その他---", value="------\n\n", inline=False)
        embed.add_field(name="`ぴの`", value="> ピノ\n", inline=False)
        embed.add_field(name="`てぃらみす`", value="> ティラミス\n", inline=False)
        embed.add_field(name="`りんご`", value="> スーパーエクストリームりんご\n", inline=False)
        embed.add_field(name="`いくもん`", value="> 村人のYouTube\n", inline=False)
        embed.add_field(name="`しゃけ`", value="> しゃけ\n\n", inline=False)
        embed.add_field(name="`リーパー`", value="> ろりーぱー\n\n", inline=False)
        embed.add_field(name="`tasuren`", value="> 凄い人\n", inline=False)
        embed.add_field(name="`なつ`", value="> このbotの製作者について\n", inline=False)
        await message.channel.send(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?", description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko", color=0xff0000)
            await message.channel.send(embed=embed)
            return
        return
    if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_zoku.mp4')
        return
    if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum)', message.content):
        if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
            if re.search(r'(?:水|みず|ミズ)', message.content):
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_water.jpg')
                return
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_sand.jpeg')
            return
        if re.search(r'(?:伊藤|いとう|イトウ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_itou.png')
            return
        if re.search(r'(?:枯|かれ|カレ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_kare.png')
            return
        if re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_fish.png')
            return
        if re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_dokusai.png')
            return
        if re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_seityou.jpeg')
            return
        if re.search(r'(?:なべ|鍋|ナベ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_nabe.jpg')
            await message.channel.send('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
            return
        if re.search(r'(?:かりばー|カリバー|剣)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_sword.png')
            return
        if re.search(r'(?:あんど|and|アンド)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_and.png')
            return
        rnd = random.randint(1, 4)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_b.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/nira_c.png')
            return
        elif rnd == 4:
            await message.channel.send('https://twitter.com/DR36Hl04ZUwnEnJ')
            return
    if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_a.png')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/tiramisu_b.png')
            return
    if re.search(r'(?:ぴの|ピノ|pino)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_nm.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_st.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/pino_cool.jpg')
            return
    if re.search(r'(?:きつね|キツネ|狐)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/kitune_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/kitune_b.png')
            return
    if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人|囚人)', message.content):
        await message.channel.send('https://www.youtube.com/IkumonTV')
        return
    if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e|アップル|あっぷる|林檎|maçã)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/apple.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://twitter.com/RINGOSANDAO')
            return
    if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|salmon|さーもん|サーモン)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_b.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/sarmon_c.jpg')
            return
        return
    if re.search(r'(?:なつ|なっちゃん|Nattyan|nattyan)', message.content):
        if re.search(r'(?:なつき)', message.content):
            await message.channel.send(':thinking:')
            return
        await message.channel.send('https://twitter.com/nattyan_tv')
        await message.channel.send('https://www.youtube.com/なっちゃんTV')
        return
    if re.search(r'(?:12pp|12PP)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/12pp.jpg')
        return
    if re.search(r'(?:名前|なまえ|ナマエ|name)', message.content):
        await message.channel.send('https://twitter.com/namae_1216')
        return
    if re.search(r'(?:みけ|ミケ|三毛)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/mike.mp4')
        return
    if re.search(r'(?:あう|アウ)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/au.png')
        return
    if re.search(r'(?:りーぱー|リーパー|犯|罪|はんざい|つみ|ろり|ロリ)', message.content):
        if re.search(r'(?:せろり|セロリ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/serori.jpg')
            return
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/images/ri_par.png')
        return
    if re.search(r'(?:tasuren|たすれん|タスレン)', message.content):
        rnd = random.randint(1, 2)
        if rnd == 1:
            await message.channel.send('毎晩10時が全盛期')
            return
        elif rnd == 2:
            await message.channel.send('すごいひと')
            return
    if re.search(r'(?:ｸﾜｧｸﾜｧｸﾜｧ|きよわらい)', message.content):
        await message.channel.send('ｸﾜｧｸﾜｧｸﾜｧｸﾜｧｸﾜｧｸﾜｧ!!!!')
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
