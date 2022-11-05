import listre
import logging
import random
import re
import sys
import urllib.parse
from enum import Enum, auto
from typing import Literal

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util.n_fc import GUILD_IDS
from util.slash_tool import messages
from util.wordle_data import words
from util.nira import NIRA

# 娯楽系


class DiceId(Enum):
    NORMAL = "normal"
    TRPG = "diceroll"


class JankenHand(Enum):
    ROCK = 1
    SCISSORS = 2
    PAPER = 3


class JankenResult(Enum):
    DRAW = auto()
    LOSE = auto()
    WIN = auto()


DICE_ID_PREFIX = "cogs.amuse.dice"

JANKEN_RULES_URL = r"https://ja.wikipedia.org/wiki/%E3%81%98%E3%82%83%E3%82%93%E3%81%91%E3%82%93#%E3%83%AB%E3%83%BC%E3%83%AB"
JANKEN_HAND_NAMES = {
    JankenHand.ROCK: ":fist: グー",
    JankenHand.SCISSORS: ":v: チョキ",
    JankenHand.PAPER: ":hand_splayed: パー",
}
JANKEN_REGEXES = {
    JankenHand.ROCK: re.compile(r"(ぐ|グ|ｸﾞ)[うウｳぅゥｩーｰ―−-〜~]+|rock", re.I),
    JankenHand.SCISSORS: re.compile(r"[ちチﾁ][ょョｮ][きキｷ]|scissors?", re.I),
    JankenHand.PAPER: re.compile(r"(ぱ|パ|ﾊﾟ)[あアｱぁァｧーｰ―−-〜~]+|paper", re.I),
}
JANKEN_RESULTS = {
    JankenResult.DRAW: ":thinking: あいこですね...",
    JankenResult.LOSE: ":pensive: あなたの勝ちですね...",
    JankenResult.WIN: ":laughing: 私の勝ちです！！",
}

DIVINATION_STAR = "★"
DIVINATION_MESSAGES = [
    "きっといいことあるよ...(`5%`)",
    "まぁ星0よりはマシだし...？(`7%`)",
    "まぁ、大抵の人はそんなもんじゃね？(`10%`)",
    "ほら、星みっつぅ～！w(`13%`)",
    "ガルパとかプロセカとかならいい方じゃん？(`15%`)",
    "中途半端っすね。うん。(`19%`)",
    "おお、ええやん。(`13%`)",
    "ラッキーセブンやん！すごいなぁ！(`7%`)",
    "星8でも十分すごいやん！！(`6%`)",
    "いや、ここまで来たら星10出しなよwwwwwwwwwwwww(`4%`)",
    "星10は神の領域(当社調べ)だよ！！！！！凄い！！！(`1%`)",
]


def _get_dice_result(dice_id: DiceId, value_a: int, value_b: int) -> nextcord.Embed:
    match dice_id:
        case DiceId.NORMAL:
            min_value, max_value = value_a, value_b

            if max_value < min_value:
                return nextcord.Embed(
                    title="エラー",
                    description="最大値が最小値より小さいよ！",
                    color=0xff0000,
                )

            value = random.randint(min_value, max_value)
            return nextcord.Embed(
                title=f"サイコロ\n`{min_value}-{max_value}`",
                description=f"```{value}```",
                color=0x00ff00,
            )

        case DiceId.TRPG:
            number_dice, max_value = value_a, value_b

            results = [random.randint(1, max_value) for _ in range(number_dice)]

            embed = nextcord.Embed(
                title=f"サイコロ\n`{number_dice}D{max_value}`",
                description=f"```{sum(results)}```",
                color=0x00ff00,
            )

            results_str = str(results)
            if len(results_str) > 1000:
                results_str = f"{results_str[:1000]}..."
            embed.add_field(name="ダイスの目の詳細", value=f"```{results_str}```", inline=False)

            return embed

    raise ValueError(f"Unknown dice id: {dice_id}")


def _get_janken_result(player_hand: JankenHand) -> nextcord.Embed:
    nira_hand = JankenHand(random.randint(1, 3))
    result = JankenResult.DRAW

    match player_hand:
        case _ if player_hand is nira_hand:
            pass
        case JankenHand.ROCK:
            result = JankenResult.LOSE if nira_hand is JankenHand.SCISSORS else JankenResult.WIN
        case JankenHand.SCISSORS:
            result = JankenResult.LOSE if nira_hand is JankenHand.PAPER else JankenResult.WIN
        case JankenHand.PAPER:
            result = JankenResult.LOSE if nira_hand is JankenHand.ROCK else JankenResult.WIN

    embed = nextcord.Embed(title="にらにらじゃんけん", color=0x00ff00)
    embed.add_field(name="あなた", value=JANKEN_HAND_NAMES[player_hand], inline=False)
    embed.add_field(name="にら", value=JANKEN_HAND_NAMES[nira_hand], inline=False)
    embed.add_field(name="RESULT", value=JANKEN_RESULTS[result], inline=False)
    return embed


def _get_divination_result() -> nextcord.Embed:
    value = random.randint(1, 100)
    star_num = 1

    # TODO: もう少しスマートにしたい
    if 1 <= value <= 5:
        star_num = 0
    elif 5 < value <= 12:
        star_num = 1
    elif 12 < value <= 22:
        star_num = 2
    elif 22 < value <= 35:
        star_num = 3
    elif 35 < value <= 50:
        star_num = 4
    elif 50 < value <= 69:
        star_num = 5
    elif 69 < value <= 82:
        star_num = 6
    elif 82 < value <= 89:
        star_num = 7
    elif 89 < value <= 95:
        star_num = 8
    elif 95 < value <= 99:
        star_num = 9
    else:
        star_num = 10

    embed = nextcord.Embed(
        title="うらない",
        description=f"**{DIVINATION_STAR * star_num}**",
        color=0x00ff00,
    )
    embed.add_field(
        name=f"あなたの運勢は**星10個中の{star_num}個**です！",
        value=f"> {DIVINATION_MESSAGES[star_num]}",
    )
    return embed


class _DiceRetryButtonView(nextcord.ui.View):
    def __init__(self, dice_id: DiceId, value_a: int, value_b: int):
        super().__init__(timeout=None)

        self.add_item(nextcord.ui.Button(
            style=nextcord.ButtonStyle.green,
            label="もう一度",
            emoji="\N{Rightwards Arrow with Hook}",
            custom_id=f"{DICE_ID_PREFIX}:{dice_id.value}:{value_a},{value_b}",
        ))

        self.stop()


def _get_retry_button(dice_id: DiceId, value_a: int, value_b: int) -> _DiceRetryButtonView | None:
    return (
        _DiceRetryButtonView(dice_id, value_a, value_b)
        if dice_id is not DiceId.NORMAL or value_a < value_b
        else nextcord.utils.MISSING
    )


class Amuse(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @commands.command(name="dice", help="""\
指定した最大目のダイスを振ります。
例: `n!dice 10` (1-10のダイス)
例: `n!dice 12 2` (2-12のダイス)

引数1: int
ダイスの最大値。

引数2: int（省略可能）
ダイスの最小値
デフォルト: 1""")
    async def dice_ctx(self, ctx: commands.Context, max_count: int, min_count: int = 1):
        await ctx.reply(
            embed=_get_dice_result(DiceId.NORMAL, min_count, max_count),
            view=_get_retry_button(DiceId.NORMAL, min_count, max_count),
        )

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
        await interaction.send(
            embed=_get_dice_result(DiceId.NORMAL, min_count, max_count),
            view=_get_retry_button(DiceId.NORMAL, min_count, max_count),
        )

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
        await interaction.send(
            embed=_get_dice_result(DiceId.TRPG, number_dice, dice_count),
            view=_get_retry_button(DiceId.TRPG, number_dice, dice_count),
        )

    @commands.command(name="janken", help=f"""\
じゃんけんで遊びます。
`n!janken [グー/チョキ/パー]`
グーかチョキかパー以外を出したりすると少し煽られます。
[ルール解説]({JANKEN_RULES_URL})

引数1: str
「グー」または「チョキ」または「パー」の手。""")
    async def janken_ctx(self, ctx: commands.Context, player_hand_str: str):
        player_hand: JankenHand | None = None
        for hand, regex in JANKEN_REGEXES.items():
            if regex.fullmatch(player_hand_str):
                player_hand = hand
                break

        await ctx.reply(embed=(
            nextcord.Embed(
                title="Error",
                description=f"じゃんけんっていうのは、「グー」「チョキ」「パー」のどれかを出して遊ぶゲームだよ。\n"
                            f"[ルール解説]({JANKEN_RULES_URL})\n"
                            f"```{ctx.prefix}janken [グー/チョキ/パー]```",
                color=0xff0000,
            )
            if player_hand is None
            else _get_janken_result(player_hand)
        ))

    @amuse.subcommand(name="janken", description="じゃんけんをします！")
    async def janken(
        self,
        interaction=Interaction,
        player_hand_id: int = SlashOption(
            name="hand",
            description="じゃんけんの手です",
            required=True,
            choices={
                "グー": JankenHand.ROCK.value,
                "チョキ": JankenHand.SCISSORS.value,
                "パー": JankenHand.PAPER.value,
            },
        ),
    ):
        await interaction.send(
            "じゃんけん！",
            embed=_get_janken_result(JankenHand(player_hand_id)),
        )

    @commands.command(name="divination", aliases=("uranai",), help="""\
占いで遊びます。いや、ちゃんと占います。
ただ、これであなたの運勢が決まるわけではありません。
あなたの行いが良くなれば、自然と運勢も上がっていきますし、行いが悪くなれば、自然と運勢が下がっていきます。
自分の運勢を上げたいと思うなら、人に優しくしたり、人のことを思った行動をしてみてください。""")
    async def divination_ctx(self, ctx: commands.Context):
        await ctx.reply(embed=_get_divination_result())

    @amuse.subcommand(name="divination", description="占いをします")
    async def divination(self, interaction: Interaction):
        await interaction.send("占い", embed=_get_divination_result())

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

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction) -> None:
        if interaction.type is not nextcord.InteractionType.component:
            return

        button_id = interaction.data.get("custom_id")
        if button_id is None or not button_id.startswith(f"{DICE_ID_PREFIX}:"):
            return

        dice_id, value_a, value_b = None, None, None
        try:
            _, dice_id, values = button_id.split(":", 2)
            dice_id = DiceId(dice_id)
            a, b = values.split(",", 1)
            value_a, value_b = int(a), int(b)
        except ValueError:
            return

        await interaction.response.defer()

        embed = _get_dice_result(dice_id, value_a, value_b)
        if (user := interaction.user):
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        await interaction.send(embed=embed, view=_get_retry_button(dice_id, value_a, value_b))


def setup(bot, **kwargs):
    bot.add_cog(Amuse(bot, **kwargs))
