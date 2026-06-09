# 沢山のインポート
import json
import logging
import logging.config
import os
import sys
from argparse import ArgumentParser

import nextcord
from motor import motor_asyncio

from util import n_fc
from util.nira import NIRA
from util.settings import BotSettings, Logging

sys.setrecursionlimit(10000)  # エラー回避


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


# loggingの設定
if isinstance(settings.logging, Logging):
    logging.basicConfig(
        format=settings.logging.format,
        filename=settings.logging.filepath,
        level=settings.logging.level,
    )
else:
    logging.config.dictConfig(settings.logging.model_dump())

_logger = logging.getLogger("main")
_logger.info("Starting NIRA Bot...")


n_fc.GUILD_IDS = settings.guild_ids
n_fc.py_admin = settings.py_admin
UNLOAD_COGS = settings.unload_cogs
LOAD_COGS = settings.load_cogs
DEBUG: bool = args.debug

if DEBUG:
    _logger.info(f"[Debug Mode] The following will be loaded... :{LOAD_COGS}")


# データベースの設定
_MONGO_CLIENT = motor_asyncio.AsyncIOMotorClient(str(settings.database_url))


# BOTの設定
intents = nextcord.Intents.all()  # 全部のインテントが有効になる
intents.typing = False  # 重くなる可能性があるのでTypingを無効化
intents.presences = False  # 未認証なのでPresence Intentは無効化
intents.members = True  # Members Intentを有効化
intents.message_content = True  # Message Content Intentを有効化

bot = NIRA(
    mongo=_MONGO_CLIENT,  # mongo_db
    debug=DEBUG,
    token=settings.tokens.nira_bot.get_secret_value(),
    database_name=settings.database_name,
    shard_id=settings.shard_id,
    shard_count=settings.shard_count,
    settings=settings,
    command_prefix=settings.prefix,
    intents=intents,
    help_command=None,
    status=nextcord.Status.dnd,
    activity=nextcord.Game(name="Connecting...", type=1),
    rollout_delete_unknown=not DEBUG,
    default_guild_ids=list(settings.guild_ids) if DEBUG else None
)

_logger.debug("Loading jishaku...")
bot.load_extension("ncjishaku")


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

    _logger.info(f"""Welcome to nira-bot!
USER: {bot.user.name}{bot.user.discriminator and f"#{bot.user.discriminator}"}
ID: {bot.user.id}
COGS: {[cog.qualified_name for cog in bot.cogs.values()]}
COMMANDS: {sorted(cmd.name for cmd in bot.commands)}
"""[:-1])


# 暫定: 元のエラーハンドラが反応して標準エラーにスタックトレースを出力してしまうので
#       bot.event で上書きして強制的に消えてもらう (nextcord が対応したら削除する)
async def on_application_command_error(interaction, exception):
    pass


# 非デバッグモードでのみイベント登録する
if not bot.debug:
    bot.event(on_application_command_error)


# load extensions
cogs_dir = HOME + "/cogs"
if bot.debug:
    cogs_list = LOAD_COGS
else:
    cogs_list = os.listdir(cogs_dir)
cogs_list = [
    f"cogs.{f.removesuffix('.py')}"
    for f in cogs_list
    if f.endswith(".py") and f != "not_ready.py" and f not in UNLOAD_COGS
]
_logger.info(f"Loading {len(cogs_list)} cogs...")
cogs_num_loaded = 0
for cog in cogs_list:
    try:
        _logger.debug(f"Loading cog {cog}...")
        bot.load_extension(cog)
    except Exception:
        logging.exception(f"Failed to load cog {cog}")
    else:
        cogs_num_loaded += 1
_logger.info(f"{cogs_num_loaded} cogs are loaded")


def main():
    # BOT起動
    _logger.info("Running bot...")
    bot.run()
    _logger.info("Exiting bot")


if __name__ == "__main__":
    main()
