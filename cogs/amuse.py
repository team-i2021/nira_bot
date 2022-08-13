import listre
import logging
import random
import re
import sys
import urllib.parse

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util.n_fc import GUILD_IDS
from util.slash_tool import messages
from util.wordle_data import words
from util.nira import NIRA

# 娯楽系

MESSAGE, SLASH = [0, 1]


class Amuse(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @commands.command(name="dice", help="""\
指定した最大目のダイスを振ります。
数値以外(マイナスとか文字とか)は無視されます。
例:`n!dice 10`(1-10のダイス)
例:`n!dice a12aaa 2`(2-12のダイス)
例:`n!dice -290 -13`(13-290のダイス)

引数1:int
ダイスの最大値。

引数2:int（省略可能）
ダイスの最小値
デフォルト:1""")
    async def dice_ctx(self, ctx: commands.context):
        if ctx.message.content == f"{self.bot.command_prefix}dice":
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"サイコロだよ！\n`{self.bot.command_prefix}dice [最大値] [最小値]`", color=0xff0000))
            return
        args = ctx.message.content.split(" ", 2)
        max_count, min_count = (0, 0)
        if len(args) == 3:
            if "".join(re.findall(r'[0-9]', args[2])) != "":
                min_count = int("".join(re.findall(r'[0-9]', args[2])))
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="数字を入力してね！", color=0xff0000))
                return
        else:
            min_count = 1
        if "".join(re.findall(r'[0-9]', args[1])) != "":
            max_count = int("".join(re.findall(r'[0-9]', args[1])))
        else:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="数字を入力してね！", color=0xff0000))
            return
        if max_count < min_count:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="最大値が最小値より小さいよ！", color=0xff0000))
            return
        rnd_ex = random.randint(min_count, max_count)
        await ctx.reply(embed=nextcord.Embed(title=f"サイコロ\n`{min_count}-{max_count}`", description=f"```{rnd_ex}```", color=0x00ff00))
        return

    @nextcord.slash_command(name="amuse", description="The command of amuse", guild_ids=GUILD_IDS)
    async def amuse(self, interaction: Interaction):
        pass

    @amuse.subcommand(name="dice", description="dice subcommand group")
    async def dice(self, interaction: Interaction):
        pass

    @dice.subcommand(name="normal", description="普通のサイコロを振ります")
    async def normal(
        self,
        interaction: Interaction,
        max_count: int = SlashOption(
            name="max_count",
            description="ダイスの最大目の数です",
            required=True
        ),
        min_count: int = SlashOption(
            name="min_count",
            description="ダイスの最小目の数です デフォルトは1です",
            required=False,
            default=1
        ),
    ):
        if max_count < min_count:
            await messages.mreply(interaction, "", embed=nextcord.Embed(title="エラー", description="最大値が最小値より小さいよ！", color=0xff0000))
            return
        rnd_ex = random.randint(min_count, max_count)
        await messages.mreply(interaction, "", embed=nextcord.Embed(title=f"サイコロ\n`{min_count}-{max_count}`", description=f"```{rnd_ex}```", color=0x00ff00))
        return

    @dice.subcommand(name="trpg", description="TRPG用のサイコロ「nDr」を振ります")
    async def trpg(
        self,
        interaction: Interaction,
        number_dice: int = SlashOption(
            name="number_dice",
            description="ダイスの数です。「n」の部分です。",
            required=True,
            min_value=1,
            max_value=10000
        ),
        dice_count: int = SlashOption(
            name="dice_count",
            description="ダイスの最大目の数です。「r」の部分です。",
            required=True,
            min_value=1,
            max_value=10000
        ),
    ):
        await interaction.response.defer()

        dices = []
        diceAllCount = 0
        for _ in range(number_dice):
            Num = random.randint(1, dice_count)
            dices.append(Num)
            diceAllCount += Num

        embed = nextcord.Embed(
            title=f"サイコロ\n`{number_dice}D{dice_count}`", description=f"```{diceAllCount}```", color=0x00ff00)

        dice_numbers = str(dices)
        if len(dice_numbers) > 1000:
            dice_numbers = dice_numbers[:1000] + "..."
        embed.add_field(name="ダイスの目の詳細",
                        value=f"```\n{dice_numbers}```", inline=False)
        await interaction.followup.send(embed=embed)

    def jankenEmbed(self, content, type):
        if type == MESSAGE and content == f"{self.bot.command_prefix}janken":
            return nextcord.Embed(title="Error", description=f"じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```{self.bot.command_prefix}janken [グー/チョキ/パー]```", color=0xff0000)
        mes_te = ""
        try:
            if type == MESSAGE:
                mes_te = content.split(" ", 1)[1]
            elif type == SLASH:
                mes_te = content
        except Exception as err:
            return nextcord.Embed(title="Error", description=f"な、なんかエラー出たけど！？\n```{self.bot.command_prefix}janken [グー/チョキ/パー]```\n{err}", color=0xff0000)
        if mes_te != "グー" and mes_te != "ぐー" and mes_te != "チョキ" and mes_te != "ちょき" and mes_te != "パー" and mes_te != "ぱー":
            return nextcord.Embed(title="Error", description=f"じゃんけんっていのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)\n```{self.bot.command_prefix}janken [グー/チョキ/パー]```", color=0xff0000)
        embed = nextcord.Embed(
            title="にらにらじゃんけん", description=f"```{self.bot.command_prefix}janken [グー/チョキ/パー]```", color=0x00ff00)
        if mes_te == "グー" or mes_te == "ぐー":
            mes_te = "```グー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_gu.png")
        elif mes_te == "チョキ" or mes_te == "ちょき":
            mes_te = "```チョキ```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_choki.png")
        elif mes_te == "パー" or mes_te == "ぱー":
            mes_te = "```パー```"
            embed.add_field(name="あなた", value=mes_te, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_pa.png")
        rnd_jyanken = random.randint(1, 3)
        if rnd_jyanken == 1:
            mes_te_e = "```グー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_gu.png")
            if mes_te == "```グー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```チョキ```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```パー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 2:
            mes_te_e = "```チョキ```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_choki.png")
            if mes_te == "```チョキ```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```パー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```グー```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        elif rnd_jyanken == 3:
            mes_te_e = "```パー```"
            embed.add_field(name="にら", value=mes_te_e, inline=False)
            embed.set_image(
                url="https://nattyan-tv.github.io/nira_bot/images/jyanken_pa.png")
            if mes_te == "```パー```":
                res_jyan = ":thinking: あいこですね..."
            elif mes_te == "```グー```":
                res_jyan = ":laughing: 私の勝ちです！！"
            elif mes_te == "```チョキ```":
                res_jyan = ":pensive: あなたの勝ちですね..."
        embed.add_field(name="\n```RESULT```\n", value=res_jyan, inline=False)
        return embed

    @commands.command(name="janken", help="""\
じゃんけんで遊びます。
`n!janekn [グー/チョキ/パー]`
グーかチョキかパー以外を出したりすると少し煽られます。
[ルール解説](https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#:~:text=%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93%E3%81%AF2%E4%BA%BA%E4%BB%A5%E4%B8%8A,%E3%81%A8%E6%95%97%E8%80%85%E3%82%92%E6%B1%BA%E5%AE%9A%E3%81%99%E3%82%8B%E3%80%82)

引数1:str
「グー」または「チョキ」または「パー」の手。""")
    async def janken_ctx(self, ctx: commands.context):
        await ctx.reply(embed=self.jankenEmbed(ctx.message.content, MESSAGE))
        return

    @amuse.subcommand(name="janken", description="じゃんけんをします！")
    async def janken(
            self,
            interaction=Interaction,
            hand: str = SlashOption(
                name="hand",
                description="じゃんけんの手です。",
                required=True,
                choices={"グー": "グー", "チョキ": "チョキ", "パー": "パー"},
            )):
        await messages.mreply(interaction, "じゃんけん！", embed=self.jankenEmbed(hand, SLASH))
        return

    def uranaiEmbed(self):
        rnd_uranai = random.randint(1, 100)
        if rnd_uranai >= 1 and rnd_uranai <= 5:
            ur_w = 0
            stars = ""
            ur_m = "きっといいことあるよ...(`5%`)"
        elif rnd_uranai >= 6 and rnd_uranai <= 12:
            ur_w = 1
            stars = "**★**"
            ur_m = "まぁ星0よりはマシだし...？(`7%`)"
        elif rnd_uranai >= 13 and rnd_uranai <= 22:
            ur_w = 2
            stars = "**★★**"
            ur_m = "まぁ、大抵の人はそんなもんじゃね？(`10%`)"
        elif rnd_uranai >= 23 and rnd_uranai <= 35:
            ur_w = 3
            stars = "**★★★**"
            ur_m = "ほら、星みっつぅ～！w(`13%`)"
        elif rnd_uranai >= 36 and rnd_uranai <= 50:
            ur_w = 4
            stars = "**★★★★**"
            ur_m = "ガルパとかプロセカとかならいい方じゃん？(`15%`)"
        elif rnd_uranai >= 51 and rnd_uranai <= 69:
            ur_w = 5
            stars = "**★★★★★**"
            ur_m = "中途半端っすね。うん。(`19%`)"
        elif rnd_uranai >= 70 and rnd_uranai <= 82:
            ur_w = 6
            stars = "**★★★★★★**"
            ur_m = "おお、ええやん。(`13%`)"
        elif rnd_uranai >= 83 and rnd_uranai <= 89:
            ur_w = 7
            stars = "**★★★★★★★**"
            ur_m = "ラッキーセブンやん！すごいなぁ！(`7%`)"
        elif rnd_uranai >= 90 and rnd_uranai <= 95:
            ur_w = 8
            stars = "**★★★★★★★★**"
            ur_m = "星8でも十分すごいやん！！(`6%`)"
        elif rnd_uranai >= 96 and rnd_uranai <= 99:
            ur_w = 9
            stars = "**★★★★★★★★★**"
            ur_m = "いや、ここまで来たら星10出しなよwwwwwwwwwwwww(`4%`)"
        elif rnd_uranai == 100:
            ur_w = 10
            stars = "**★★★★★★★★★★**"
            ur_m = "星10は神の領域(当社調べ)だよ！！！！！凄い！！！(`1%`)"
        embed = nextcord.Embed(
            title="うらない", description=f"{stars}", color=0x00ff00)
        embed.add_field(name=f"あなたの運勢は**星10個中の{ur_w}個**です！", value=f"> {ur_m}")
        return embed

    @commands.command(name="uranai", help="""\
占いで遊びます。いや、ちゃんと占います。
ただ、これであなたの運勢が決まるわけではありません。
あなたの行いが良くなれば、自然と運勢も上がっていきますし、行いが悪くなれば、自然と運勢が下がっていきます。
自分の運勢を上げたいと思うなら、人に優しくしたり、人のことを思った行動をしてみてください。""")
    async def uranai(self, ctx: commands.context):
        await ctx.reply(embed=self.uranaiEmbed())
        return

    @amuse.subcommand(name="uranai", description="占いをします")
    async def uranai_slash(
            self,
            interaction=Interaction):
        await messages.mreply(interaction, "占い", embed=self.uranaiEmbed())
        return

    @commands.command(name="wordle", help="""\
Wordleという、単語あてゲームです。
簡単なルールは[こちら](https://snsdays.com/game-app/wodle-play-strategy/)から。
本家と違うところは「1日何回でもプレイ可能」「辞書にない単語でも送れる」「バグが多い...」です。
とりあえずやってみてください。""")
    async def wordle(self, ctx: commands.Context):
        answer = words.splitlines()[random.randint(
            0, len(words.splitlines())-1)]
        check_out = 0
        answer_list = list(answer)
        answer_dic = {}
        share_block = []
        for i in range(5):
            if answer_list[i] not in answer_dic:
                answer_dic[answer_list[i]] = 1
            else:
                answer_dic[answer_list[i]] = answer_dic[answer_list[i]] + 1
        embed = nextcord.Embed(
            title="Wordle", description="6回以内に5文字の単語を当てろ！", color=0x00ff00)
        embed.add_field(
            name="・遊び方", value="5文字の英単語を送信していってください。\n詳しい遊び方は[こちら](https://snsdays.com/game-app/wodle-play-strategy/)から\n<:nira:915588411715358742>のリアクションがつかない場合はルールを間違えているのでやり直してください。")
        message = await ctx.send(embed=embed)
        for i in range(6):
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 5 and re.search("[a-z]", m.content)
            msg = await self.bot.wait_for('message', check=check)
            await msg.add_reaction("<:nira:915588411715358742>")
            if msg.content == answer:
                check_out = i
                share_block.extend(["🟩", "🟩", "🟩", "🟩", "🟩"])
                embed.add_field(
                    name=f"`Turn:{i+1}`", value=f"`{' '.join(list(msg.content.translate(str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)}))))}`\n:green_square::green_square::green_square::green_square::green_square:\n\n\n", inline=False)
                break
            text = list(msg.content.lower())
            check_list = [":black_large_square:", ":black_large_square:",
                          ":black_large_square:", ":black_large_square:", ":black_large_square:"]
            answer_copy = answer_dic.copy()
            for j in range(5):
                if text[j] == answer_list[j]:
                    check_list[j] = ":green_square:"
                    share_block.extend("🟩")
                    answer_copy[text[j]] = 0
                elif listre.search(answer_list, text[j]):
                    #listre.search(answer_list[j+1:], text[j]) != None
                    if answer_copy[text[j]] == 0:
                        share_block.extend("⬛")
                    elif answer_copy[text[j]] == 1:
                        check_result = None
                        for k in range(j+1, 5):
                            if answer_list[k] == text[k]:
                                if text[k] == text[j]:
                                    share_block.extend("⬛")
                                    check_result = None
                                    break
                            check_result = k
                        if check_result != None:
                            check_list[j] = ":yellow_square:"
                            share_block.extend("🟨")
                            answer_copy[text[j]] = answer_copy[text[j]] - 1
                    else:
                        check_result = (None, answer_copy[text[j]])
                        for k in range(j+1, 5):
                            if answer_list[k] == text[k]:
                                if text[k] == text[j]:
                                    check_result[1] = check_result[1] - 1
                            if check_result[1] == 0:
                                check_result[0] = None
                                break
                            check_result[0] = k
                        if check_result[0] != None:
                            check_list[j] = ":yellow_square:"
                            share_block.extend("🟨")
                            answer_copy[text[j]] = answer_copy[text[j]] - 1
                        else:
                            share_block.extend("⬛")
                else:
                    share_block.extend("⬛")
            embed.add_field(
                name=f"`Turn:{i+1}`", value=f"`{' '.join(list(msg.content.translate(str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)}))))}`\n{''.join(check_list)}\n\n\n", inline=False)
            share_block.extend("\n")
            if i != 5:
                await message.delete()
                message = await msg.channel.send(content=None, embed=embed)
        embed.add_field(name="GameOver",
                        value=f"答えは`{answer}`でした！", inline=False)
        share_text = ""
        if check_out != 0:
            embed.add_field(
                name="Great wordler!", value=f"流石です！あなたは`Turn{check_out+1}`でクリアしました！", inline=False)
            share_text = f""" #にらBOT #Wordle を{check_out+1}Turnでクリアしました！\n
{''.join(share_block)}\n
↓にらBOTと遊ぶ？
https://discord.gg/awfFpCYTcP"""
        else:
            embed.add_field(name="Study more!",
                            value=f"あなたの再度の挑戦をお待ちしています！", inline=False)
            share_text = f""" #にらBOT #Wordle で敗北しました！\n
{''.join(share_block)}\n
↓にらBOTと遊ぶ？
https://discord.gg/awfFpCYTcP"""
        embed.add_field(name="Twitterで共有する？",
                        value=f"Twitterであなたの雄姿を共有しましょう！\n[Twitterで共有](https://twitter.com/intent/tweet?text={urllib.parse.quote(f'{share_text}')}&url=)")
        await message.delete()
        await msg.channel.send(content=None, embed=embed)
        return


def setup(bot, **kwargs):
    bot.add_cog(Amuse(bot, **kwargs))
