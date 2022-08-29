import asyncio
import logging
import math
import os
import sys
import traceback
import json

import HTTP_db
import genshin
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands


from util import admin_check, n_fc, eh, database
from util.nira import NIRA

# Genshin...

GenshinClients: dict[int, genshin.Client] = {}

MAP_ELEMENT = {
    1: "Anemo",
    2: "Geo",
    3: "Cryo",
    4: "Electro",
    5: None,
    6: None,
    7: None,
    8: "Dendro",
}
COLOR_PAD = {
    "Pyro":0xef7a35, #火
    "Hydro":0x4bc3f1, #水
    "Electro":0xb08fc2, #雷
    "Cryo":0xa0d7e4, #氷
    "Dendro":0xa6c938, #草
    "Anemo":0x75c3a9, #風
    "Geo":0xfab72e #岩
} # 元素に対応した色表
ARTIFACT_POS = {
    1:"花",
    2:"羽",
    3:"砂時計", # TODO: 「砂時計」じゃない別の1文字ぐらいの表記があれば楽だなって
    4:"杯",
    5:"冠"
} # 場所に対応した聖遺物表
STAT, CHARA = range(2) # マジックナンバー対策
AMERICA, EUROPE, ASIA, TAIWAN = "os_usa", "os_euro", "os_asia", "os_cht" # America/Europe/Asia/TW,HK,MO
REPU = "Reputation"

class ClientData:
    name = "genshin_client"
    value = {}
    default = {}
    value_type = database.GUILD_VALUE

class ModalButton(nextcord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(nextcord.ui.Button(label="HoYoLAB", url="https://www.hoyolab.com"))

    @nextcord.ui.button(label="Connect", style=nextcord.ButtonStyle.red)
    async def connect(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(modal=TokenSend(self.bot))
        self.stop()



class TokenSend(nextcord.ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            "Connect Genshin Account",
            timeout=None
        )
        self.bot = bot

        self.connect_code = nextcord.ui.TextInput(
            label="アカウント接続コード",
            style=nextcord.TextInputStyle.short,
            placeholder="123456789/Ab1Cd2Ef3Gh4Ij5Kl6Mn7",
            required=True
        )
        self.add_item(self.connect_code)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, with_message=True)
        if len(code := self.connect_code.value.strip().split("/", 1)) != 2:
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
            ClientData.value[interaction.user.id] = code
            asyncio.ensure_future(database.default_push(self.bot.client, ClientData))
            await interaction.send(embed=nextcord.Embed(title="コードを保存しました。", description=f"以降、原神コマンドの各機能がご利用いただけます。\nUID:`{UID}`", color=0x00ff00))

async def get_uid(client: genshin.Client) -> int:
    if genshin.Game.GENSHIN not in client.uids:
        await client._update_cached_uids()
    return client.uids[genshin.Game.GENSHIN]

def getEmbed(content_type: int, uid: int, user: genshin.models.FullGenshinUserStats) -> list[nextcord.Embed]:
    if content_type == STAT:
        embeds = []
        main_embed = nextcord.Embed(
            title=f"戦績",
            description=f"UID:`{uid}`",
            color=0x00ff00
        )
        main_embed.add_field(
            name="活動日数",
            value=f"`{user.stats.days_active}`日"
        )
        main_embed.add_field(
            name="アチーブメント",
            value=f"`{user.stats.achievements}`個"
        )
        main_embed.add_field(
            name="総キャラクター数",
            value=f"`{user.stats.characters}`人"
        )
        main_embed.add_field(
            name="解放済みワープポイント",
            value=f"`{user.stats.unlocked_waypoints}`個"
        )
        main_embed.add_field(
            name="深境螺旋",
            value=f"`{user.abyss.current.max_floor}`"
        )
        main_embed.add_field(
            name="宝箱",
            value="```\n" + "\n".join([
                f"普通:{user.stats.common_chests}個",
                f"精巧:{user.stats.exquisite_chests}個",
                f"貴重:{user.stats.precious_chests}個",
                f"豪華:{user.stats.luxurious_chests}個",
                f"珍奇:{user.stats.remarkable_chests}個"
            ]) + "```"
        )
        embeds.append(main_embed)
        for exploration in user.explorations:
            embed = nextcord.Embed(
                title=exploration.name,
                description=f"""\
探索レベル:{(explore := exploration.raw_explored / 10 if exploration.raw_explored != 0 else 0.0)}%
`[{'#' * math.floor(explore/10)}{'_' * (10 - math.floor(explore/10))}]`

{f'評判レベル:{[i for i in exploration.offerings if i.name == REPU][0].level}' if exploration.type == REPU else ''}
{(f"{offer[0].name}:Lv{offer[0].level}" if len(offer := [i for i in exploration.offerings if i.name != REPU]) > 0 else '')}
""",
                color=COLOR_PAD[MAP_ELEMENT[exploration.id]]
            )
            # embed.set_image(exploration.background_image)
            embed.set_thumbnail(exploration.inner_icon)
            embed.set_author(name=f"MAPはこちら ({exploration.name})", url=exploration.map_url)
            embeds.append(embed)
        return embeds
    elif content_type == CHARA:
        embeds = []
        main_embed = nextcord.Embed(
            title="キャラクター",
            description=f"UID:`{uid}`",
            color=0x00ff00
        )
        main_embed.add_field(
            name=f"総キャラクター数",
            value=f"`{user.stats.characters}`人"
        )
        embeds.append(main_embed)
        for chara in user.characters:
            embed = nextcord.Embed(
                title=f"{'★' * chara.rarity} {chara.name} ({chara.constellation})",
                description=f"レベル: {chara.level}\n好感度: {chara.friendship}",
                color=COLOR_PAD[chara.element]
            )
            embed.add_field(
                name=f"武器: {'★' * chara.weapon.rarity} {chara.weapon.name} (Lv.{chara.weapon.level})",
                value=chara.weapon.description,
                inline=False
            )
            for artifact in chara.artifacts:
                embed.add_field(
                    name=f"{ARTIFACT_POS[artifact.pos]}聖遺物",
                    value=f"{'★' * artifact.rarity} {artifact.name} (+{artifact.level})"
                )
            embed.set_thumbnail(url=chara.icon)
            embeds.append(embed)
        return embeds


async def GetClient(client: HTTP_db.Client):
    global GenshinClients
    await database.default_pull(client, ClientData)
    for key, value in ClientData.value.items():
        GenshinClients[key] = genshin.Client({"ltuid": value[0], "ltoken": value[1]}, game=genshin.Game.GENSHIN, lang="ja-jp")


class Genshin(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        SETTING = json.load(open(f"{sys.path[0]}/setting.json", "r"))
        cookie = {"ltuid": SETTING["ltuid"], "ltoken": SETTING["ltoken"]}
        self.base_client = genshin.Client(cookie, game=genshin.Game.GENSHIN, lang="ja-jp") # TODO: ベースクライアントを設定しない/設定されていなかった場合...
        asyncio.ensure_future(GetClient(self.bot.client))


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
        view = ModalButton(self.bot)
        await interaction.send(embed=nextcord.Embed(title="原神アカウントの接続の注意点", description="If you want to connect your Genshin account to NIRA Bot, please watch important notice.\nCheck how to connect your genshin account at [here](https://127.0.0.1/note/genshin).\nAfter get tokens, press below button.", color=0xff0000), view=view)


    @slash_genshin.subcommand(name="daily", description="Daily reward")
    async def slash_genshin_daily(self, interaction: Interaction):
        pass

    @slash_genshin_daily.subcommand(name="check", description="Check daily rewards status")
    async def check_daily_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。(コマンドは開発中です)", color=0xff0000), ephemeral=True)
            return
        signed_in, claimed = await GenshinClients[interaction.user.id].get_reward_info()
        embed=nextcord.Embed(title="デイリー報酬", description=f"本日のデイリー報酬は受け取られていま{'す！' if signed_in else 'せん！'}\n{'' if signed_in else '`/genshin daily claim`で獲得しましょう！'}\nあなたはデイリーを{claimed}日間受け取っています！", color=0x00ff00)
        await interaction.send(embed=embed)

    @slash_genshin_daily.subcommand(name="claim", description="Claim daily rewards")
    async def claim_daily_slash(self, interaction: Interaction):
        if interaction.user.id not in GenshinClients:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"{interaction.user.mention}の原神アカウントは接続されていません。\n`/genshin account`からご確認ください。(コマンドは開発中です)", color=0xff0000), ephemeral=True)
        else:
            description = ""
            try:
                reward = await GenshinClients[interaction.user.id].claim_daily_reward()
            except genshin.AlreadyClaimed:
                description = "今日のデイリーは既に獲得されています！"
            else:
                description = f"デイリー報酬を獲得しました！\n\n・今日の報酬\n{reward.name} `x{reward.amount}`"
            await interaction.send(embed=nextcord.Embed(title="デイリー報酬", description=description, color=0x00ff00))


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
                await interaction.send(embed=nextcord.Embed(title="エラー", description="ユーザー情報の取得で、UIDを指定しない場合は先に原神アカウントをBOTと接続する必要があります。"), ephemeral=True)
            else:
                await interaction.response.defer(ephemeral=False)
                UID = await get_uid(GenshinClients[interaction.user.id])
                user = await GenshinClients[interaction.user.id].get_full_genshin_user(UID)
                await interaction.send(embeds=getEmbed(STAT, UID, user), ephemeral=False)
        else:
            try:
                if interaction.user.id not in GenshinClients:
                    await interaction.response.defer(ephemeral=False)
                    user = await self.base_client.get_full_genshin_user(uid)
                    await interaction.send(embeds=getEmbed(STAT, uid, user), ephemeral=False)
                else:
                    await interaction.response.defer(ephemeral=False)
                    user = await GenshinClients[interaction.user.id].get_full_genshin_user(uid)
                    await interaction.send(embeds=getEmbed(STAT, uid, user), ephemeral=False)
            except genshin.errors.AccountNotFound:
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントが見つかりませんでした。", color=0xff0000), ephemeral=True)
            except genshin.errors.DataNotPublic:
                # TODO: Statsのパブリック条件がわからないけど取れる情報は取りたい
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントはデータがパブリックになっていません。", color=0xff0000))

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
                await interaction.send(embed=nextcord.Embed(title="エラー", description="ユーザー情報の取得で、UIDを指定しない場合は先に原神アカウントをBOTと接続する必要があります。"), ephemeral=True)
            else:
                await interaction.response.defer()
                UID = await get_uid(GenshinClients[interaction.user.id])
                user = await GenshinClients[interaction.user.id].get_full_genshin_user(UID)
                if len(embeds := getEmbed(CHARA, UID, user)) > 10:
                    for i in range(math.ceil(len(embeds)/10)):
                        await interaction.send(embeds=embeds[i*10:(i+1)*10], ephemeral=False)
                else:
                    await interaction.send(embeds=embeds, ephemeral=True)
        else:
            try:
                if interaction.user.id not in GenshinClients:
                    await interaction.response.defer()
                    user = await self.base_client.get_full_genshin_user(uid)
                    if len(embeds := getEmbed(CHARA, uid, user)) > 10:
                        for i in range(math.ceil(len(embeds)/10)):
                            await interaction.send(embeds=embeds[i*10:(i+1)*10], ephemeral=False)
                    else:
                        await interaction.send(embeds=embeds, ephemeral=True)
                else:
                    await interaction.response.defer()
                    user = await GenshinClients[interaction.user.id].get_full_genshin_user(uid)
                    if len(embeds := getEmbed(CHARA, uid, user)) > 10:
                        for i in range(math.ceil(len(embeds)/10)):
                            await interaction.send(embeds=embeds[i*10:(i+1)*10], ephemeral=False)
                    else:
                        await interaction.send(embeds=embeds, ephemeral=True)
            except genshin.errors.AccountNotFound:
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントが見つかりませんでした。", color=0xff0000))
            except genshin.errors.DataNotPublic:
                # TODO: 公開設定にしてるキャラクターの情報は見れるはずだからその処理を...
                await interaction.send(embed=nextcord.Embed(title="エラー", description=f"UID:`{uid}`の原神アカウントはデータがパブリックになっていません。", color=0xff0000))


#    @nextcord.slash_command(name="genshin", description="Show genshin info", guild_ids=n_fc.GUILD_IDS)
#    async def slash_genshin(self, interaction: Interaction):
#        pass
#
#    @slash_genshin.subcommand(name="stats", description="原神のユーザーの戦績を表示します")
#    async def slash_genshin_stats(self, interaction: Interaction, authkey: str = SlashOption(required=True, description="原神のAuthKey")):
#        await interaction.response.defer()
#        client = genshin.Client(
#            lang="ja-jp", game=genshin.Game.GENSHIN, authkey=authkey)
#        user = await client.get_full_genshin_user(client.uid)
#        # user.stats.
#        embed = nextcord.Embed(
#            title=f"{client.get_banner_names}の戦績", description=f"UID:`{client.uid}`", color=0x00ff00)
#        embed.add_field(name="活動日数", value=f"`{user.stats.days_active}`日")
#        embed.add_field(name="アチーブメント", value=f"`{user.stats.achievements}`個")
#        embed.add_field(name="キャラクター数", value=f"`{user.stats.characters}`人")
#        embed.add_field(name="解放済みワープポイント",
#                        value=f"`{user.stats.unlocked_waypoints}`")
#        embed.add_field(name="宝箱(普通,精巧,貴重,豪華,珍奇)",
#                        value=f"`{[user.stats.common_chests, user.stats.exquisite_chests, user.stats.precious_chests, user.stats.luxurious_chests, user.stats.remarkable_chests]}`")
#        await interaction.followup.send(embed=embed)

    @commands.command(name="genshin", help="""\
原神の情報表示
`n!genshin ...` : 原神の戦績を表示します""")
    async def command_genshin(self, ctx: commands.Context):
        return


def setup(bot: NIRA, **kwargs):
    if bot.debug:
        bot.add_cog(Genshin(bot, **kwargs))

# await GenshinClients[interaction.user.id].genshin_accounts()
# [GenshinAccount(game_biz=????(str), uid=UID, level=冒険者ランク, nickname=ユーザー名, server="os_asia", server_name="Asia Server")]
