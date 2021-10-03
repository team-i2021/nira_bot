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
    # 下のやつミスると「v0.9.2　～故に彼は猫だった～」の時みたいに猫爆弾が起爆するにゃ(botのメッセージは無視する)
    if message.author.bot:
        return
    if message.content == "n!help":
        embed = discord.Embed(title="ニラbot HELP",description="ニラちゃんの扱い方",color=0x00ff00)
        embed.set_author(name="製作者：なつ",url="https://twitter.com/nattyan_tv",icon_url="https://pbs.twimg.com/profile_images/1388437778292113411/pBiEOtHL_400x400.jpg")
        embed.set_image(url="https://nattyan-tv.github.io/tensei_disko/nira_a.jpg")
        embed.add_field(name="helpの見方",value="`単語A`・`単語B`> 単語Aと単語Bの両方が含まれるときの反応\n",inline=False)
        embed.add_field(name="---メイン---",value="（ひらがな・カタカナ・漢字は大体区別しません）\n\n",inline=False)
        embed.add_field(name="`ニラ`",value="> ニラの画像\n",inline=False)
        embed.add_field(name="`ニラ`・`栽培`",value="> 土の様子\n",inline=False)
        embed.add_field(name="`ニラ`・`栽培`・`水`",value="> 水栽培されているニラ\n",inline=False)
        embed.add_field(name="`ニラ`・`魚`",value="> 新種の魚「ニラ魚」\n",inline=False)
        embed.add_field(name="`ニラ`・`独裁`",value="> 独裁者ニラの肖像画\n",inline=False)
        embed.add_field(name="`ニラ`・`成長`",value="> 世にも珍しい、ニラの成長過程\n",inline=False)
        embed.add_field(name="`ニラ`・`鍋`",value="> ニラ鍋のレシピ\n",inline=False)
        embed.add_field(name="`ニラ`・`カリバー`",value="> 聖剣ニラカリバー！\n",inline=False)
        embed.add_field(name="`ニラ`・`アンド`",value="> 「nik〇 and...」のコラ画像\n",inline=False)
        embed.add_field(name="`煮裸族`",value="> nira_zoku.mp4\n\n",inline=False)
        embed.add_field(name="---その他---",value="------\n\n",inline=False)
        embed.add_field(name="`ぴの`",value="> ピノ\n",inline=False)
        embed.add_field(name="`てぃらみす`",value="> ティラミス\n",inline=False)
        embed.add_field(name="`りんご`",value="> スーパーエクストリームりんご\n",inline=False)
        embed.add_field(name="`いくもん`",value="> 村人のYouTube\n",inline=False)
        embed.add_field(name="`しゃけ`",value="> しゃけ\n",inline=False)
        await message.channel.send(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?",description="ってかお前俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko",color=0xff0000)
            await message.channel.send(embed=embed)
            return
        return
    if re.search(r'(?:煮裸族|にらぞく|ニラゾク)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_zoku.mp4')
        return
    if re.search(r'(?:にら|ニラ|nira|garlic|韮|Chinese chives|Allium tuberosum)', message.content):
        if re.search(r'(?:栽培|さいばい|サイバイ)', message.content):
            if re.search(r'(?:水|みず|ミズ)', message.content):
                await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_water.jpg')
                return
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_sand.jpeg')
            return
        if re.search(r'(?:魚|さかな|fish|サカナ|ざかな|ザカナ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_fish.png')
            return
        if re.search(r'(?:独裁|どくさい|ドクサイ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_dokusai.png')
            return
        if re.search(r'(?:成長|せいちょう|セイチョウ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_seityou.jpeg')
            return
        if re.search(r'(?:なべ|鍋|ナベ)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_nabe.jpg')
            await message.channel.send('https://cookpad.com/search/%E3%83%8B%E3%83%A9%E9%8D%8B')
            return
        if re.search(r'(?:かりばー|カリバー|剣)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_sword.png')
            return
        if re.search(r'(?:あんど|and|アンド)', message.content):
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_and.png')
            return
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_b.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/nira_c.png')
            return
    if re.search(r'(?:てぃらみす|ティラミス|tiramisu)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/tiramisu.jpg')
        return
    if re.search(r'(?:ぴの|ピノ|pino)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/pino_nm.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/pino_st.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/pino_cool.jpg')
            return
    if re.search(r'(?:きつね|キツネ|狐)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/kitune.jpg')
        return
    if re.search(r'(?:いくもん|イクモン|ikumon|Ikumon|村人)', message.content):
        await message.channel.send('https://www.youtube.com/IkumonTV')
        return
    if re.search(r'(?:りんご|リンゴ|apple|Apple|App1e|app1e)', message.content):
        await message.channel.send('https://nattyan-tv.github.io/tensei_disko/apple.jpg')
        return
    if re.search(r'(?:しゃけ|シャケ|さけ|サケ|鮭|syake|sarmon)', message.content):
        rnd = random.randint(1, 3)
        if rnd == 1:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/sarmon_a.jpg')
            return
        elif rnd == 2:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/sarmon_b.jpg')
            return
        elif rnd == 3:
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/sarmon_c.jpg')
            return
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
