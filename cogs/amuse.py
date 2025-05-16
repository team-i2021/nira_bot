import random
import re
import urllib.parse
from enum import Enum, auto

import listre
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from util.nira import NIRA
from util.wordle_data import words

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
DICE_NORMAL_MIN_VALUE = -9_007_199_254_740_991  # Number.MIN_SAFE_INTEGER
DICE_NORMAL_MAX_VALUE = 9_007_199_254_740_991  # Number.MAX_SAFE_INTEGER
DICE_TRPG_MAX_DICE = 170
DICE_TRPG_MAX_VALUE = 9999

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
DIVINATION_PROBABILITIES = [5, 7, 10, 13, 15, 19, 13, 7, 6, 4, 1]
DIVINATION_MESSAGES = [
    "きっといいことあるよ...(`5%`)",
    "まぁ星0よりはマシだし...？(`7%`)",
    "まぁ、大抵の人はそんなもんじゃね？(`10%`)",
    "ほら、星みっつぅ～！w(`13%`)",
    "プロセカならいい方じゃん？(`15%`)",
    "ガルパならいい方だけど中途半端っすね。うん。(`19%`)",
    "おお、ええやん。(`13%`)",
    "ラッキーセブンやん！すごいなぁ！(`7%`)",
    "星8でも十分すごいやん！！(`6%`)",
    "いや、ここまで来たら星10出しなよwwwwwwwwwwwww(`4%`)",
    "星10は神の領域(当社調べ)だよ！！！！！凄い！！！(`1%`)",
]


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


def _get_dice_result(dice_id: DiceId, value_a: int, value_b: int) -> tuple[nextcord.Embed, _DiceRetryButtonView]:
    button = _DiceRetryButtonView(dice_id, value_a, value_b)

    match dice_id:
        case DiceId.NORMAL:
            min_value, max_value = value_a, value_b

            description = None
            if min_value < DICE_NORMAL_MIN_VALUE:
                description = f"最小値が小さすぎます。\n{DICE_NORMAL_MIN_VALUE:,} 以上である必要があります。"
            elif max_value > DICE_NORMAL_MAX_VALUE:
                description = f"最大値が大きすぎます。\n{DICE_NORMAL_MAX_VALUE:,} 以下である必要があります。"
            elif min_value > max_value:
                min_value, max_value = max_value, min_value
            if description:
                return nextcord.Embed(title="エラー", description=description, color=0xff0000), nextcord.utils.MISSING

            value = random.randint(min_value, max_value)
            return (
                nextcord.Embed(
                    title=f"サイコロ: {min_value:,}〜{max_value:,}",
                    description=f"# {value:,}",
                    color=0x00ff00,
                ),
                button,
            )

        case DiceId.TRPG:
            number_dice, max_value = value_a, value_b

            # 古い埋め込みのリトライボタンからだと範囲外の値が渡される可能性がある
            # (以前はどちらとも 1〜10000 まで入力を受け付けていた)
            if number_dice > DICE_TRPG_MAX_DICE or max_value < 2 or max_value > DICE_TRPG_MAX_VALUE:
                return (
                    nextcord.Embed(
                        title="エラー",
                        description="指定された値は範囲外です。\nお手数ですが、もう一度コマンドを実行してください。",
                        color=0xff0000,
                    ),
                    nextcord.utils.MISSING,
                )

            results = [random.randint(1, max_value) for _ in range(number_dice)]

            embed = nextcord.Embed(
                title=f"ダイスロール: `{number_dice}d{max_value}`",
                description=f"# {sum(results):,}",
                color=0x00ff00,
            )

            # 170d9999 の結果が全て 1000 以上になった場合ちょうど 1024 文字になる
            # len("1000") * 170 + len(", ") * 169 + len("```") * 2 = 1024
            # 埋め込みのフィールドに入れられる上限の文字数なので１文字も増やしてはいけない！
            if number_dice > 1:
                results_str = str(results)[1:-1]
                embed.add_field(name="詳細", value=f"```{results_str}```", inline=False)

            return embed, button

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
    message = random.choices(DIVINATION_MESSAGES, weights=DIVINATION_PROBABILITIES)[0]
    star_count = DIVINATION_MESSAGES.index(message)
    star = DIVINATION_STAR * star_count

    embed = nextcord.Embed(
        title="うらない",
        description=f"**{star}**",
        color=0x00ff00,
    )
    embed.add_field(
        name=f"あなたの運勢は**星10個中の{star_count}個**です！",
        value=f"> {message}",
    )
    return embed


class Amuse(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot

    @commands.command(name="dice", help=f"""\
指定した範囲のダイスを振るというか乱数を生成します。
需要は無いでしょうが一応 {DICE_NORMAL_MIN_VALUE:,} から {DICE_NORMAL_MAX_VALUE:,} まで振ることができます。
最大値が最小値より小さい場合は暗黙的に入れ替えられます。
例: `n!dice 10` (1〜10のダイス)
例: `n!dice 12 2` (2〜12のダイス)

引数1: int（省略可能）
ダイスの最大値。
デフォルト: 6

引数2: int（省略可能）
ダイスの最小値。
デフォルト: 1""")
    async def dice_ctx(self, ctx: commands.Context, max_value: int = 6, min_value: int = 1):
        embed, view = _get_dice_result(DiceId.NORMAL, min_value, max_value)
        await ctx.reply(embed=embed, view=view)

    @nextcord.slash_command(name="amuse", description="The command of amuse")
    async def amuse(self, interaction: Interaction):
        pass

    @amuse.subcommand(name="dice", description="dice subcommand group")
    async def dice(self, interaction: Interaction):
        pass

    @dice.subcommand(name="normal", description="普通のサイコロを振ります")
    async def normal(
        self,
        interaction: Interaction,
        max_value: int = SlashOption(
            description="ダイスの最大目の数です。省略時は6です。",
            required=False,
            default=6,
        ),
        min_value: int = SlashOption(
            description="ダイスの最小目の数です。省略時は1です。",
            required=False,
            default=1,
        ),
    ):
        embed, view = _get_dice_result(DiceId.NORMAL, min_value, max_value)
        await interaction.send(embed=embed, view=view)

    @dice.subcommand(name="trpg", description="TRPGのダイスロールができます")
    async def trpg(
        self,
        interaction: Interaction,
        number_dice: int = SlashOption(
            description=f"ダイスの数です。(1〜{DICE_TRPG_MAX_DICE})",
            required=True,
            min_value=1,
            max_value=DICE_TRPG_MAX_DICE,
        ),
        max_value: int = SlashOption(
            description=f"ダイスの最大目の数です。(2〜{DICE_TRPG_MAX_VALUE})",
            required=True,
            min_value=2,
            max_value=DICE_TRPG_MAX_VALUE,
        ),
    ):
        await interaction.response.defer()
        embed, view = _get_dice_result(DiceId.TRPG, number_dice, max_value)
        await interaction.send(embed=embed, view=view)

    @commands.command(name="janken", help=f"""\
じゃんけんで遊びます。
`n!janken [グー/チョキ/パー]`
グーかチョキかパー以外を出したりすると少し煽られます。
[ルール解説]({JANKEN_RULES_URL})

引数1: str
「グー」または「チョキ」または「パー」の手。""")
    async def janken_ctx(self, ctx: commands.Context, player_hand_str: str = ""):
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
        interaction: Interaction,
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

        embed, view = _get_dice_result(dice_id, value_a, value_b)
        if (user := interaction.user):
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        await interaction.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Amuse(bot))
