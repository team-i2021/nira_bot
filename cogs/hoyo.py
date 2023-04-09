import asyncio
import base64
import datetime
import logging
import math

import genshin
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, tasks

from util import n_fc, pagination
from util.nira import NIRA

# Genshin...

GenshinClients: dict[int, genshin.Client] = {}

MAP_ELEMENT = {
    1: "Anemo", # モンド
    2: "Geo", # 璃月
    3: "Cryo", # ドラゴンスパイン
    4: "Electro", # 稲妻
    5: "Electro", # 淵下宮
    6: "Geo", # 層岩巨淵
    7: "Geo", # 層岩巨淵・地下鉱区
    8: "Dendro", # スメール
}

# 元素に対応した色表
COLOR_PAD = {
    None: 0x000000, # 未指定
    "Pyro": 0xef7a35, # 火
    "Hydro": 0x4bc3f1, # 水
    "Electro": 0xb08fc2, # 雷
    "Cryo": 0xa0d7e4, # 氷
    "Dendro": 0xa6c938, # 草
    "Anemo": 0x75c3a9, # 風
    "Geo": 0xfab72e, # 岩
}

# サーバーリスト
SERVER = {
    "cn_gf01": "天空岛",  # 中国本土版公式サーバー
    "cn_qd01": "世界树",  # 中国本土版提携サーバー
    "os_usa": "America",
    "os_euro": "Europe",
    "os_asia": "Asia",
    "os_cht": "TW, HK, MO",
}

STAT, CHARA = range(2) # マジックナンバー対策
REPU = "Reputation"

# 日本時間設定
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

class ModalButton(nextcord.ui.View):
    def __init__(self, collection):
        super().__init__(timeout=None)
        self.collection = collection
        self.add_item(nextcord.ui.Button(label="HoYoLAB", url="https://www.hoyolab.com"))

    @nextcord.ui.button(label="同意して接続", style=nextcord.ButtonStyle.red)
    async def connect(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(modal=TokenSend(self.collection))
        self.stop()


class TokenSend(nextcord.ui.Modal):
    def __init__(self, collection):
        super().__init__(
            "Connect Genshin Account",
            timeout=None
        )
        self.collection = collection

        self.connect_code = nextcord.ui.TextInput(
            label="アカウント接続コード",
            style=nextcord.TextInputStyle.short,
            placeholder="ODAwMDAwMDAwL+OBk+OCjOOBr+ODhuOCueODiOOBoOOBi+OCieOAgg==",
            required=True
        )
        self.add_item(self.connect_code)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, with_message=True)
        try:
            decoded = base64.b64decode(self.connect_code.value.strip()).decode()
        except Exception:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"入力された接続コードは無効です。\nこの形式は接続コードではありません。", color=0xff0000), ephemeral=True)
            return
        if len(code := decoded.split("/", 1)) != 2:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"入力された接続コードは無効です。\nこの形式は接続コードではありません。", color=0xff0000), ephemeral=True)
            return
        GenshinClients[interaction.user.id] = genshin.Client({"ltuid": code[0], "ltoken": code[1]}, game=genshin.Game.GENSHIN, lang="ja-jp")
        try:
            UID = await get_uid(GenshinClients[interaction.user.id])
        except genshin.errors.InvalidCookies as err:
            del GenshinClients[interaction.user.id]
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"入力された接続コードは無効です。\nCookieの形が不正です。\n`{err}`", color=0xff0000), ephemeral=True)
            logging.error(err, exc_info=True)
        except Exception as err:
            del GenshinClients[interaction.user.id]
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"アカウントに接続できませんでした。\n`{err}`", color=0xff0000), ephemeral=True)
            logging.error(err, exc_info=True)
        else:
            # 本当に気持ち程度としてbase64でエンコードする
            ltoken = base64.b64encode(code[1].encode()).decode()
            await self.collection.update_one({"user_id": interaction.user.id}, update={"$set": {"ltuid": code[0], "ltoken": ltoken, "auto_daily": False}}, upsert=True)
            await interaction.send(embed=nextcord.Embed(title="接続できました！", description=f"これで原神のコマンドが利用できます！\nUID:`{UID}`", color=0x00ff00))

async def get_uid(client: genshin.Client) -> int:
    if genshin.Game.GENSHIN not in client.uids:
        await client._update_cached_uids()
    return client.uids[genshin.Game.GENSHIN]

def create_paginator(
        content_type: int,
        uid: int,
        user: genshin.models.FullGenshinUserStats,
) -> pagination.Paginator:
    pages: list[pagination.Page] = []

    if content_type == STAT:
        info_embed = nextcord.Embed(
            title=f"戦績",
            description=f"{SERVER.get(user.info.server, 'Unknown')} Server Lv.{user.info.level}",
            color=0x00ff00,
        )
        info_embed.add_field(
            name="活動日数",
            value=f"`{user.stats.days_active}`日",
        )
        info_embed.add_field(
            name="アチーブメント",
            value=f"`{user.stats.achievements}`個",
        )
        info_embed.add_field(
            name="所持キャラクター",
            value=f"`{user.stats.characters}`人",
        )
        info_embed.add_field(
            name="開放済みワープポイント",
            value=f"`{user.stats.unlocked_waypoints}`個",
        )
        info_embed.add_field(
            name="深境螺旋",
            value=f"`{user.stats.spiral_abyss}`",
        )
        info_embed.add_field(
            name="宝箱",
            value="```\n" + "\n".join([
                f"普通: {user.stats.common_chests}個",
                f"精巧: {user.stats.exquisite_chests}個",
                f"貴重: {user.stats.precious_chests}個",
                f"豪華: {user.stats.luxurious_chests}個",
                f"珍奇: {user.stats.remarkable_chests}個",
            ]) + "```",
        )
        pages.append(pagination.Page("基本情報", embeds=[info_embed]))

        expl_embeds: dict[int, nextcord.Embed] = {}
        description_idx: dict[int, int] = {}
        for expl in reversed(user.explorations):
            if expl.raw_explored:
                explored = expl.explored
                description = f"""\
{expl.name} 探索度: {explored:.1f}% ([テイワットマップ]({expl.map_url}))
`[{'#' * math.floor(explored / 10)}{'_' * (10 - math.floor(explored / 10))}]`

"""
                description_idx[expl.id] = len(description)

                if expl.parent_id:
                    old_description = expl_embeds[expl.parent_id].description
                    idx = description_idx[expl.parent_id]

                    description = f"{old_description[:idx]}{description}"
                    description_idx[expl.parent_id] = len(description) - 2

                    expl_embeds[expl.parent_id].description = f"{description}{old_description[idx:]}"
                    continue

                for offer in expl.offerings:
                    if offer.name == REPU:
                        description += f"評判レベル: Lv.{offer.level}\n"
                    elif offer.level:
                        description += f"{offer.name}: Lv.{offer.level}\n"
            else:
                description = f"未探索 ([テイワットマップ]({expl.map_url}))"

            embed = nextcord.Embed(
                title=expl.name,
                description=description.rstrip(),
                color=COLOR_PAD[MAP_ELEMENT.get(expl.id, None)],
            )
            embed.set_thumbnail(expl.inner_icon)
            expl_embeds[expl.id] = embed

        pages.extend(pagination.Page(e.title, embeds=[e]) for e in reversed(expl_embeds.values()))

    elif content_type == CHARA:
        info_embed = nextcord.Embed(
            title="キャラクター",
            color=0x00ff00,
        )
        info_embed.add_field(
            name="所持キャラクター",
            value=f"`{user.stats.characters}`人",
        )
        pages.append(pagination.Page("概要", embeds=[info_embed]))

        chara_embeds: list[tuple[str, nextcord.Embed]] = []
        per_page = 6 if len(user.characters) > 96 else 4
        for chara in user.characters:
            embed = nextcord.Embed(
                title=f"{'★' * chara.rarity} {chara.name} ({chara.constellation})",
                description=f"キャラクターLv: {chara.level}\n好感度Lv: {chara.friendship}",
                color=COLOR_PAD[chara.element],
            )
            embed.add_field(
                name=f"武器: {'★' * chara.weapon.rarity} {chara.weapon.name}"
                     f" (Lv.{chara.weapon.level} / 精錬ランク{chara.weapon.refinement})",
                value=chara.weapon.description,
                inline=False,
            )
            artifact_value = "\n".join(
                f"{artifact.pos_name}: {'★' * artifact.rarity} {artifact.name} (+{artifact.level})"
                for artifact in chara.artifacts
            )
            if artifact_value:
                embed.add_field(name="聖遺物", value=artifact_value)
            embed.set_thumbnail(url=chara.icon)

            chara_embeds.append((chara.name, embed))
            if len(chara_embeds) >= per_page or chara.id == user.characters[-1].id:
                pages.append(pagination.Page(
                    f"ページ{len(pages)}",
                    description="、".join(embed[0] for embed in chara_embeds),
                    embeds=[embed[1] for embed in chara_embeds],
                ))
                chara_embeds = []

    pages[0].embeds[0].set_author(
        name=f"{user.info.nickname} ({uid})",
        icon_url=user.info.icon or None,
    )

    return pagination.Paginator(
        pages,
        show_menu=True,
        menu_placeholder="ページを選択...",
        author_check=False,
        loop_pages=True,
    )

class Genshin(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection = self.bot.database["genshin"]
        asyncio.ensure_future(self._init_clients())
        self.claim_daily_loop.start()

    def cog_unload(self):
        self.claim_daily_loop.cancel()

    async def _init_clients(self):
        cookie = {"ltuid": self.bot.settings["ltuid"], "ltoken": self.bot.settings["ltoken"].get_secret_value()}
        self.base_client = genshin.Client(cookie, game=genshin.Game.GENSHIN, lang="ja-jp") # TODO: ベースクライアントを設定しない/設定されていなかった場合...
        async for doc in self.collection.find():
            GenshinClients[doc["user_id"]] = genshin.Client({"ltuid": doc["ltuid"], "ltoken": base64.b64decode(doc["ltoken"]).decode()}, game=genshin.Game.GENSHIN, lang="ja-jp")


    @nextcord.slash_command(name="genshin", description="Genshin slash command", guild_ids=n_fc.GUILD_IDS)
    async def slash_genshin(self, interaction: Interaction):
        pass


    @slash_genshin.subcommand(name="account", description="Manage your genshin account")
    async def slash_genshin_account(self, interaction: Interaction):
        pass

    @slash_genshin_account.subcommand(name="connect", description="Connect your Genshin account")
    async def connect_account_slash(self, interaction: Interaction):
        # TODO: util/genshin_token.jsを実行すれば情報は取れるから、そのことを明記したdocs/noteを作る...
        await interaction.response.defer(ephemeral=True)
        view = ModalButton(self.collection)
        await interaction.send(embed=nextcord.Embed(
            title="原神アカウントの接続の注意点",
            description="BOTにアカウントを接続する場合は、必ず注意事項をお読みください。\n原神アカウントの接続方法及び注意事項については[こちら](https://nattyan-tv.github.io/nira-note/bot/notes/genshin)をご確認ください。\n接続コードを取得できましたら下のボタンを押してください。",
            color=self.bot.color.ATTENTION
        ), view=view)

    @slash_genshin_account.subcommand(name="disconnect", description="Disconnect your Genshin account")
    async def disconnect_account_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。", color=self.bot.color.ERROR), ephemeral=True)
            return
        await self.collection.delete_one({"user_id": interaction.user.id})
        del GenshinClients[interaction.user.id]
        await interaction.send(embed=nextcord.Embed(title="成功", description=f"{interaction.user.mention}の原神アカウントとの接続を解除しました。", color=self.bot.color.NORMAL), ephemeral=True)

    @slash_genshin.subcommand(name="daily", description="Daily reward")
    async def slash_genshin_daily(self, interaction: Interaction):
        pass

    @slash_genshin_daily.subcommand(name="check", description="Check daily rewards status")
    async def check_daily_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。", color=self.bot.color.ERROR), ephemeral=True)
            return
        signed_in, claimed = await GenshinClients[interaction.user.id].get_reward_info()
        embed=nextcord.Embed(
            title="デイリー報酬",
            description=f"本日のデイリー報酬は受け取られていま{'す！' if signed_in else 'せん！'}\n{'' if signed_in else '`/genshin daily claim`で獲得しましょう！'}",
            color=self.bot.color.NORMAL if signed_in else self.bot.color.ATTENTION
        ).set_footer(
            text="デイリー報酬は毎日5時(JST)にリセットされます。"
        )
        await interaction.send(embed=embed)

    @slash_genshin_daily.subcommand(name="claim", description="Claim daily rewards")
    async def claim_daily_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。", color=self.bot.color.ERROR), ephemeral=True)
        else:
            description = ""
            try:
                reward = await GenshinClients[interaction.user.id].claim_daily_reward()
            except genshin.AlreadyClaimed:
                description = "今日のデイリーは既に獲得されています！"
            else:
                description = f"デイリー報酬を獲得しました！\n\n・今日の報酬\n{reward.name} `x{reward.amount}`"
            await interaction.send(embed=nextcord.Embed(title="デイリー報酬", description=description, color=self.bot.color.NORMAL))

    @slash_genshin_daily.subcommand(name="enable", description="Enable auto claim daily rewards")
    async def auto_daily_on_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。", color=self.bot.color.ERROR), ephemeral=True)
        else:
            await self.collection.update_one({"user_id": interaction.user.id}, {"$set": {"auto_daily": True}}, upsert=True)
            await interaction.send(embed=nextcord.Embed(title="自動デイリー報酬", description="自動ログインボーナスを有効にしました。\n毎日、日本時間の午前1時に報酬を受け取ります。（午前2時にも確認のため実行されます。）", color=self.bot.color.NORMAL))

    @slash_genshin_daily.subcommand(name="disable", description="Disable auto claim daily rewards")
    async def auto_daily_off_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。", color=self.bot.color.ERROR), ephemeral=True)
        else:
            await self.collection.update_one({"user_id": interaction.user.id}, {"$set": {"auto_daily": False}}, upsert=True)
            await interaction.send(embed=nextcord.Embed(title="自動デイリー報酬", description="自動ログインボーナスを無効にしました。", color=self.bot.color.NORMAL))

    @slash_genshin.subcommand(name="stats", description="Show genshin user info")
    async def slash_genshin_stats(
            self,
            interaction: Interaction,
            uid: int = SlashOption(
                name="uid",
                description="UID that you want to show",
                required=False,
            )
        ):
        if uid is None:
            if interaction.user.id not in GenshinClients:
                await interaction.send(embed=nextcord.Embed(title="エラー", description="ユーザー情報の取得で、UIDを指定しない場合は先に原神アカウントをBOTと接続する必要があります。", color=self.bot.color.ERROR), ephemeral=True)
            else:
                await interaction.response.defer(ephemeral=False)
                UID = await get_uid(GenshinClients[interaction.user.id])
                user = await GenshinClients[interaction.user.id].get_full_genshin_user(UID)
                await create_paginator(STAT, UID, user).respond(interaction)
        else:
            try:
                if interaction.user.id not in GenshinClients:
                    await interaction.response.defer(ephemeral=False)
                    user = await self.base_client.get_full_genshin_user(uid)
                    await create_paginator(STAT, uid, user).respond(interaction)
                else:
                    await interaction.response.defer(ephemeral=False)
                    user = await GenshinClients[interaction.user.id].get_full_genshin_user(uid)
                    await create_paginator(STAT, uid, user).respond(interaction)
            except genshin.errors.AccountNotFound:
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントが見つかりませんでした。", color=self.bot.color.ERROR), ephemeral=True)
            except genshin.errors.DataNotPublic:
                # TODO: Statsのパブリック条件がわからないけど取れる情報は取りたい
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントはデータがパブリックになっていません。", color=self.bot.color.ERROR))

    @slash_genshin.subcommand(name="chara", description="Show genshin characters")
    async def slash_genshin_chara(
            self,
            interaction: Interaction,
            uid: int = SlashOption(
                name="uid",
                description="UID that you want to show",
                required=False,
            )
        ):
        if uid is None:
            if interaction.user.id not in GenshinClients:
                await interaction.send(embed=nextcord.Embed(title="エラー", description="ユーザー情報の取得で、UIDを指定しない場合は先に原神アカウントをBOTと接続する必要があります。", color=self.bot.color.ERROR), ephemeral=True)
            else:
                await interaction.response.defer()
                UID = await get_uid(GenshinClients[interaction.user.id])
                user = await GenshinClients[interaction.user.id].get_full_genshin_user(UID)
                await create_paginator(CHARA, UID, user).respond(interaction)
        else:
            try:
                if interaction.user.id not in GenshinClients:
                    await interaction.response.defer()
                    user = await self.base_client.get_full_genshin_user(uid)
                    await create_paginator(CHARA, uid, user).respond(interaction)
                else:
                    await interaction.response.defer()
                    user = await GenshinClients[interaction.user.id].get_full_genshin_user(uid)
                    await create_paginator(CHARA, uid, user).respond(interaction)
            except genshin.errors.AccountNotFound:
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントが見つかりませんでした。", color=self.bot.color.ERROR))
            except genshin.errors.DataNotPublic:
                # TODO: 公開設定にしてるキャラクターの情報は見れるはずだからその処理を...(fullじゃなくてなんかぱーしゃるとかそっちのほう...)
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントはデータがパブリックになっていません。", color=self.bot.color.ERROR))

    @tasks.loop(time=[datetime.time(hour=1, tzinfo=JST), datetime.time(hour=2, tzinfo=JST)])
    async def claim_daily_loop(self):
        async for doc in self.collection.find({"auto_daily": True}):
            try:
                # ふぉあせーふ。
                # await GenshinClients[doc["user_id"]].claim_daily_reward()
                ...
            except genshin.AlreadyClaimed:
                pass
            except genshin.errors.AccountNotFound:
                ...
            except Exception as e:
                logging.error(e)


def setup(bot: NIRA, **kwargs):
    if bot.debug:
        bot.add_cog(Genshin(bot, **kwargs))

# await GenshinClients[interaction.user.id].genshin_accounts()
# [GenshinAccount(game_biz=????(str), uid=UID, level=冒険者ランク, nickname=ユーザー名, server="os_asia", server_name="Asia Server")]
