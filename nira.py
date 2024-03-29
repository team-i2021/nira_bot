# 沢山のインポート
import json
import logging
import os
import sys
import traceback
from argparse import ArgumentParser

import nextcord
from motor import motor_asyncio

from util import n_fc
from util.nira import NIRA
from util.settings import BotSettings

sys.setrecursionlimit(10000)  # エラー回避
print("モジュールインポート完了")


# 引数解析
parser = ArgumentParser(add_help=False, allow_abbrev=False)
parser.add_argument("-d", "--debug", action="store_true")
args = parser.parse_args()


# 設定読み込み
if not os.path.isfile(f"{sys.path[0]}/setting.json"):
    print(
        """\
BOTの設定ファイルが見つかりませんでした。
「nira.py」があるフォルダに「setting.json」をおいてください。
「setting_temp.json」というテンプレートがありますのでそちらを参考にしてください。
""",
        file=sys.stderr,
    )
    os._exit(0)

HOME = os.path.dirname(os.path.abspath(__file__))

with open(f"{sys.path[0]}/setting.json", "r") as file:
    settings = BotSettings.model_validate(json.load(file))


n_fc.GUILD_IDS = settings.guild_ids
n_fc.py_admin = settings.py_admin
UNLOAD_COGS = settings.unload_cogs
LOAD_COGS = settings.load_cogs
DEBUG = False

if args.debug:
    DEBUG = True
    print(f"NIRA Bot Debug Mode\nThe following will be loaded... :{LOAD_COGS}")


# データベースの設定
_MONGO_CLIENT = motor_asyncio.AsyncIOMotorClient(str(settings.database_url))


# BOTの設定
intents = nextcord.Intents.all()  # 全部のインテントが有効になる
intents.typing = False  # 重くなる可能性があるのでTypingを無効化
intents.presences = False  # 未認証なのでPresence Intentは無効化
intents.members = True  # Members Intentを有効化
intents.message_content = True  # Message Content Intentを有効化

# TODO: BotSettings を直接渡せるようにする
bot = NIRA(
    mongo=_MONGO_CLIENT,  # mongo_db
    debug=DEBUG,
    token=settings.tokens.nira_bot.get_secret_value(),
    database_name=settings.database_name,
    shard_id=settings.shard_id,
    shard_count=settings.shard_count,
    settings=settings.model_dump(),
    command_prefix=settings.prefix,
    intents=intents,
    help_command=None,
    status=nextcord.Status.dnd,
    activity=nextcord.Game(name="Connecting...", type=1),
    rollout_delete_unknown=not DEBUG,
    default_guild_ids=list(settings.guild_ids) if settings.guild_ids else None
)

bot.load_extension("onami")

print("BOTの設定完了")


# loggingの設定

logging.basicConfig(
    format=settings.logging.format,
    filename=settings.logging.filepath,
    level=settings.logging.level,
)

print("Logging設定完了")


@bot.event
async def on_ready():
    if not bot.debug:
        await bot.change_presence(
            activity=nextcord.Game(name=f"{bot.command_prefix}help | にらゲー", type=1),
            status=nextcord.Status.online,
        )
    else:
        await bot.change_presence(
            activity=nextcord.Game(name=f"{bot.command_prefix} | にらゲー開発", type=1),
            status=nextcord.Status.dnd,
        )

    assert bot.user

    print("Welcome to nira-bot!")
    print(
        f"""\
USER: {bot.user.name}#{bot.user.discriminator}
ID: {bot.user.id}
COGS: {[dict(bot.cogs)[i].qualified_name for i in dict(bot.cogs).keys()]}
COMMANDS: {[i.name for i in list(bot.commands)]}
"""
    )


# 暫定: 元のエラーハンドラが反応して標準エラーにスタックトレースを出力してしまうので
#       bot.event で上書きして強制的に消えてもらう (nextcord が対応したら削除する)
async def on_application_command_error(interaction, exception):
    pass


# 非デバッグモードでのみイベント登録する
if not bot.debug:
    bot.event(on_application_command_error)


# load extensions
cogs_dir = HOME + "/cogs"
cogs_num = len(os.listdir(cogs_dir))
cogs_list = os.listdir(cogs_dir)
if bot.debug:
    cogs_num = len(LOAD_COGS)
    cogs_list = LOAD_COGS
for i in range(cogs_num):
    try:
        if not (
            cogs_list[i][-3:] != ".py"
            or cogs_list[i] == "__pycache__"
            or cogs_list[i] == "not_ready.py"
            or cogs_list[i] in UNLOAD_COGS
        ):
            bot.load_extension(f"cogs.{cogs_list[i][:-3]}")
    except Exception:
        print("Cog読み込み失敗:", cogs_list[i], file=sys.stderr)
        traceback.print_exc()
        logging.exception(f"Cog読み込み失敗: {cogs_list[i]}")

print("Cogの読み込み終了")


def main():
    # BOT起動
    print("BOT起動開始...")
    bot.run()
    print("BOT終了")


if __name__ == "__main__":
    main()
