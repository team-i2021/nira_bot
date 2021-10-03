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
        embed.add_field(title="helpの見方",value="`単語A`・`単語B`\n> 単語Aと単語Bの両方が含まれるときの反応")
        embed.add_field(name="---メイン---",value="（ひらがな・カタカナ・漢字は大体区別しません）")
        embed.add_field(value="`ニラ`\n> ニラの画像")
        embed.add_field(value="`ニラ`・`栽培`\n> 土の様子")
        embed.add_field(value="`ニラ`・`栽培`・`水`\n> 水栽培されているニラ")
        embed.add_field(value="`ニラ`・`魚`\n> 新種の魚「ニラ魚」")
        embed.add_field(value="`ニラ`・`独裁`\n> 独裁者ニラの肖像画")
        embed.add_field(value="`ニラ`・`成長`\n> 世にも珍しい、ニラの成長過程")
        embed.add_field(value="`ニラ`・`鍋`\n> ニラ鍋のレシピ")
        embed.add_field(value="`ニラ`・`カリバー`\n> 聖剣ニラカリバー！")
        embed.add_field(value="`ニラ`・`アンド`\n> 「nik〇 and...」のコラ画像")
        embed.add_field(value="`煮裸族`\n> nira_zoku.mp4")
        embed.add_field(name="---その他---",value="------")
        embed.add_field(value="`ぴの`\n> ピノ")
        embed.add_field(value="`てぃらみす`\n> ティラミス")
        embed.add_field(value="`りんご`\n> スーパーエクストリームりんご")
        embed.add_field(value="`いくもん`\n> 村人のYouTube")
        await message.channel.send(embed=embed)
        if message.author.id == 669178357371371522:
            embed = discord.Embed(title="Error?",description="ってかてめぇ俺の開発者だろ\n自分でコード見るなりして考えろ\nhttps://github.com/nattyan-tv/tensei_disko",color=0xff0000)
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
            await message.channel.send('https://nattyan-tv.github.io/tensei_disko/pino_cool.png')
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




# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
