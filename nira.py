# coding: utf-8

#沢山のインポート
try:
    import os
    import nextcord
    from nextcord.ext import commands
    import sys
    from nextcord import Interaction
    from util import n_fc, admin_check, web_api
    import json
    from cogs import debug as cogs_debug
    from cogs import server_status
    sys.setrecursionlimit(10000)#エラー回避
    import pickle
    import traceback
    import datetime
    import asyncio
    from cogs import rolepanel
    from cogs import pollpanel
    print("モジュールインポート完了")
except BaseException as err:
    print(f"""モジュールインポート時のエラー:{err}\n
    「pip install -r requirements.txt」でモジュールをインストールするか、「setup.py」を実行してモジュールをインストールしてください。
    """)
    os._exit(1)



HOME = os.path.dirname(os.path.abspath(__file__))
SETTING = json.load(open(f'{sys.path[0]}/setting.json', 'r'))
TOKEN = SETTING["tokens"]["nira_bot"]
PREFIX = SETTING["prefix"]
n_fc.GUILD_IDS = SETTING["guild_ids"]
n_fc.py_admin = SETTING["py_admin"]
UNLOAD_COGS = SETTING["unload_cogs"]
LOAD_COGS = SETTING["load_cogs"]
DEBUG = False
if sys.argv[1] == "-d":
    DEBUG = True

##### BOTの設定 #####
intents = nextcord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False # typingを受け取らないように
intents.presences = True # Presence Intentだよ
intents.members = True # メンバーに関する情報を受け取る
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
bot.remove_command("help") #意味あるのかしらんけどjishakuのヘルプコマンド削除
bot.load_extension("jishaku")

# オーナー設定
async def is_owner(author):
    return author.id in n_fc.py_admin
bot.is_owner = is_owner
print("BOTの設定完了")


#設定読み込み
if os.path.isfile(f'{sys.path[0]}/setting.json') == False:
    print("""[事前停止]
BOTの設定ファイルが見つかりませんでした。
「nira.py」があるフォルダに「setting.json」をおいてください。
「setting_temp.json」というテンプレートがありますのでそちらを参考にしてください。

または、「setup.py」を実行して、画面の指示通りにしてください。""")
    os._exit(2)



#loggingの設定
import logging

class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message



logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{HOME}/nira.log', level=logging.INFO)
print("外部設定完了")



@bot.event
async def on_ready():
    print("起動後処理を開始...")
    if os.path.exists(f'{sys.path[0]}/PersistentViews.nira'):
        with open(f'{sys.path[0]}/PersistentViews.nira', 'rb') as f:
            rolepanel.PersistentViews = pickle.load(f)
        for i in rolepanel.PersistentViews:
            bot.add_view(rolepanel.RolePanelView(i))

    if os.path.exists(f'{sys.path[0]}/PollViews.nira'):
        with open(f'{sys.path[0]}/PollViews.nira', 'rb') as f:
            pollpanel.PollViews = pickle.load(f)
        for i in pollpanel.PollViews:
            bot.add_view(pollpanel.PollPanelView(i))
    
    # asyncio.new_event_loop().run_in_executor(None, bottomup.MessagePin, bot)
    # asyncio.ensure_future(bottomup.MessagePin(bot))

    await bot.change_presence(activity=nextcord.Game(name="起動中...(1/2)", type=1), status=nextcord.Status.idle)
    print("ユーザー情報読み込み中")
    for i in bot.guilds:
        if i.id not in n_fc.role_keeper:
            n_fc.role_keeper[i.id] = {"rk": 0}
        for j in i.members:
            n_fc.role_keeper[i.id][j.id] = [k.id for k in j.roles if k.name != "@everyone"]
    print(n_fc.role_keeper)
    cogs_debug.save()
    
    print("ユーザー情報読み込み完了")
    await bot.change_presence(activity=nextcord.Game(name="起動中...(2/2)", type=1), status=nextcord.Status.idle)

    print(list(n_fc.force_ss_list.keys()))
    for i in range(len(list(n_fc.force_ss_list.keys()))):
        print(list(n_fc.force_ss_list.keys())[i])
        try:
            print(f"復元対象チャンネルID:{n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][0]}")
            ch_obj = await bot.fetch_channel(n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][0])
            print(f"復元対象チャンネル名:{ch_obj.name}/復元対象メッセージID:{n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][1]}")
            messs = await ch_obj.fetch_message(n_fc.force_ss_list[list(n_fc.force_ss_list.keys())[i]][1])
            print(messs.author.id)
            await messs.edit(content=f"reloading now...\nPlease wait...\n```{datetime.datetime.now()}```", embed=None)
            print(f"復元対象メッセージコンテンツ:```{messs.content}```")
            n_fc.pid_ss[list(n_fc.force_ss_list.keys())[i]] = (asyncio.ensure_future(server_status.ss_force(bot.loop, messs)),messs)
            print(f"復元完了")
        except BaseException as err:
            print(err, traceback.format_exc())
    print("AutoSSのタスク復元完了")
    await bot.change_presence(activity=nextcord.Game(name="n!info | にらゲー", type=1), status=nextcord.Status.online)
    print("Welcome to nira-bot!")

#機能しなかったときの保険↓
#loop = asyncio.get_event_loop()
#loop.run_in_executor(None, server_status.ss_force, bot, messs)

# @bot.slash_command(name="ping", description="サーバーとのレスポンスを表示します。")
# async def ping(interaction: Interaction, address: str = None):
#     await cogs_ping.base_ping(bot, interaction, address)
#     return

@bot.slash_command(description="AutoSSを更新します。")
async def reload(interaction: Interaction):
    if interaction.guild.id not in n_fc.pid_ss:
        await interaction.response.send_message(f"{interaction.guild.name}では、AutoSSは実行されていません。", ephemeral = True)
        return
    else:
        status_message = n_fc.pid_ss[interaction.guild.id][1]
        n_fc.pid_ss[interaction.guild.id] = (asyncio.ensure_future(server_status.ss_force(bot.loop, status_message)),status_message)
        await interaction.response.send_message("リロードしました。", ephemeral = True)
        return

@bot.slash_command(description="LINE Notifyのトークンを設定します。")
async def line(interaction: Interaction, token: str):
    if token == "":
        await interaction.response.send_message("トークンは必須です。", ephemeral=True)
        return
    if admin_check.admin_check(interaction.guild, interaction.user) == False:
        await interaction.response.send_message("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
    else:
        token_result = web_api.line_token_check(token)
        if token_result[0] == False:
            await interaction.response.send_message(f"そのトークンは無効なようです。\n```{token_result[1]}```", ephemeral = True)
            return
        if interaction.guild.id not in n_fc.notify_token:
            n_fc.notify_token[interaction.guild.id] = {interaction.channel.id: token}
        else:
            n_fc.notify_token[interaction.guild.id][interaction.channel.id] = token
        with open(f'{HOME}/notify_token.nira', 'wb') as f:
            pickle.dump(n_fc.notify_token, f)
        await interaction.response.send_message(f"{interaction.guild.name}/{interaction.channel.name}で`{token}`を保存します。\nトークンが他のユーザーに見られないようにしてください。", ephemeral = True)

@bot.slash_command(description="LINE Notifyのトークンを削除します。")
async def line_del(interaction: Interaction):
    if admin_check.admin_check(interaction.guild, interaction.user) == False:
        await interaction.response.send_message("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
    else:
        if interaction.guild.id not in n_fc.notify_token:
            await interaction.response.send_message(f"{interaction.guild.name}では、LINEトークンが設定されていません。", ephemeral = True)
            return
        if interaction.channel.id not in n_fc.notify_token[interaction.guild.id]:
            await interaction.response.send_message(f"{interaction.channel.name}では、LINEトークンが設定されていません。", ephemeral = True)
            return
        del n_fc.notify_token[interaction.guild.id][interaction.channel.id]
        with open(f'{HOME}/notify_token.nira', 'wb') as f:
            pickle.dump(n_fc.notify_token, f)
        await interaction.response.send_message(f"{interaction.channel.name}でのLINEトークンを削除しました。", ephemeral = True)


func_error_count = 0
for i in range(len(n_fc.save_list)):
    logging.info(f"Start:{n_fc.save_list[i]}")
    try:
        if os.path.isfile(f"{HOME}/{n_fc.save_list[i]}.nira"):
            with open(f'{HOME}/{n_fc.save_list[i]}.nira', 'rb') as f:
                exec(f"n_fc.{n_fc.save_list[i]} = pickle.load(f)")
            logging.info(f"変数[{n_fc.save_list[i]}]のファイル読み込みに成功しました。")
            if n_fc.save_list[i] == "notify_token.nira":
                logging.info("LINE NotifyのTOKENのため、表示はされません。")
            else:
                exec(f"logging.info(n_fc.{n_fc.save_list[i]})")
        else:
            logging.info("ファイルが存在しません。")
            with open(f"{HOME}/{n_fc.save_list[i]}.nira", "wb") as f:
                pickle.dump({},f)
    except BaseException as err:
        logging.info(f"変数[{n_fc.save_list[i]}]のファイル読み込みに失敗しました。\n{err}\n{traceback.format_exc()}")
        print("変数の読み込み時にエラーが発生しました。ログを確認して、再度やり直してください。")
        os._exit(4)
print("変数の読み込み完了")


try:
    cogs_dir = HOME + "/cogs"
    cogs_num = len(os.listdir(cogs_dir))
    cogs_list = os.listdir(cogs_dir)
    if DEBUG:
        cogs_num = len(LOAD_COGS)
        cogs_list = LOAD_COGS
    for i in range(cogs_num):
        if cogs_list[i][-3:] != ".py" or cogs_list[i] == "__pycache__" or cogs_list[i] == "not_ready.py" or cogs_list[i] in LOAD_COGS:
            continue
        bot.load_extension(f"cogs.{cogs_list[i][:-3]}")
except BaseException as err:
    print(err, traceback.format_exc())
    os._exit(8)
print("Cogの読み込み完了")


def main():
    # BOT起動
    print("BOT起動開始...")
    bot.run(TOKEN)
    print("BOT終了")

if __name__ == "__main__":
    main()
