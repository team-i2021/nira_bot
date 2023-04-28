import traceback

import nextcord

from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import n_fc
from util.nira import NIRA

# 定型文を指定したユーザーのDMに送る機能

class DefinedDMSET(nextcord.ui.Modal):
    def __init__(self, collection: motor_asyncio.AsyncIOMotorCollection):
        super().__init__(
            "DefinedDM Setting",
            timeout=None,
        )
        self.collection = collection

        self.dm_title = nextcord.ui.TextInput(
            label="定型文の名前",
            style=nextcord.TextInputStyle.short,
            placeholder="定型文A",
            max_length=30,
            required=True,
        )
        self.add_item(self.dm_title)

        self.dm_content = nextcord.ui.TextInput(
            label="本文",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="サーバーへ入ってくれてありがとう！\nけどめんどくさいから君後でBANしておくね！:D",
            required=True,
        )
        self.add_item(self.dm_content)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        result = await self.collection.find_one({"guild_id": interaction.guild.id, "type": "config"})
        if result is None:
            # サーバーに設定が一切なかった場合
            settings = []
            settings.append(self.dm_title.value)
        elif self.dm_title.value in result["settings"]:
            # サーバーに設定があり、かつ同名の設定があった場合
            settings = result["settings"]
        else:
            # サーバーに設定はあるが、同名の設定はなかった場合
            settings = result["settings"]
            settings.append(self.dm_title.value)
        await self.collection.update_one({"guild_id": interaction.guild.id, "type": "config"}, {"$set": {"settings": settings}}, upsert=True)
        await self.collection.update_one({"guild_id": interaction.guild.id, "title": self.dm_title.value}, {"$set":{"content": self.dm_content.value}}, upsert=True)
        await interaction.send(embed=nextcord.Embed(title="DefinedDM SET", description=f"設定しました。\n定型文名は`{self.dm_title.value}`です。\n(現在`{len(settings)}`個設定中)", color=0x00ff00))

class DefinedDM(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        self.collection = self.bot.database["defined_dm"]

    @application_checks.has_permissions(manage_guild=True)
    @nextcord.slash_command(name="defined", description="DefinedDM config")
    async def defined_slash(self, interaction: Interaction):
        pass

    @application_checks.has_permissions(manage_guild=True)
    @defined_slash.subcommand(name="set", description="Set 'DefinedDM''s message", description_localizations={nextcord.Locale.ja: "'DefinedDM'のメッセージ設定"})
    async def set_defined_slash(self, interaction: Interaction):
        await interaction.response.send_modal(modal=DefinedDMSET(self.collection))

    @application_checks.has_permissions(manage_guild=True)
    @defined_slash.subcommand(name="del", description="Delete 'DefinedDM''s message", description_localizations={nextcord.Locale.ja: "'DefinedDM'のメッセージを削除する"})
    async def del_defined_slash(
        self,
        interaction: Interaction,
        title: str = SlashOption(
            name="title",
            description="DefinedDM's config title",
            description_localizations={
                nextcord.Locale.ja: "定型文の名前"
            },
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        result = await self.collection.find_one({"guild_id": interaction.guild.id, "title": title})
        if result is None:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"指定された設定名`{title}`が見つかりませんでした。\n`/defined list`でご確認ください。", color=0xff0000))
        else:
            await self.collection.delete_one({"guild_id": interaction.guild.id, "title": title})
            config = await self.collection.find_one({"guild_id": interaction.guild.id, "type": "config"})
            config["settings"].remove(title)
            await self.collection.update_one({"guild_id": interaction.guild.id, "type": "config"}, {"$set": {"settings": config["settings"]}})
            await interaction.send(embed=nextcord.Embed(title="DefinedDM", description=f"指定された設定名`{title}`の設定を削除しました。", color=0x00ff00))

    @application_checks.has_permissions(manage_guild=True)
    @defined_slash.subcommand(name="check", description="Check 'DefinedDM''s messages", description_localizations={nextcord.Locale.ja: "'DefinedDM'のメッセージを確認する"})
    async def check_defined_slash(
        self,
        interaction: Interaction,
        title: str = SlashOption(
            name="title",
            description="DefinedDM's config title",
            description_localizations={
                nextcord.Locale.ja: "定型文の名前"
            },
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        result = await self.collection.find_one({"guild_id": interaction.guild.id, "title": title})
        if result is None:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"指定された設定名`{title}`が見つかりませんでした。\n`/defined list`でご確認ください。", color=0xff0000))
        else:
            embed = nextcord.Embed(title=interaction.guild.name, description=result["content"], color=0x00ff00)
            embed.set_footer(text=f"このメッセージは「{interaction.guild.name}」の「{interaction.user.name}#{interaction.user.discriminator}」さんによって送信されました。", icon_url=interaction.guild.icon.url)
            await interaction.send(f"定型文送信例:`{title}`", embed=embed)

    @application_checks.has_permissions(manage_guild=True)
    @defined_slash.subcommand(name="send", description="Send 'DefinedDM''s message", description_localizations={nextcord.Locale.ja: "'DefinedDM'のメッセージを送信する"})
    async def send_defined_slash(
        self,
        interaction: Interaction,
        title: str = SlashOption(
            name="title",
            description="DefinedDM's config title",
            description_localizations={
                nextcord.Locale.ja: "定型文の名前"
            },
            required=True
        ),
        member: nextcord.Member = SlashOption(
            name="member",
            description="Destination member",
            description_localizations={
                nextcord.Locale.ja: "送信したい相手"
            },
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        result = await self.collection.find_one({"guild_id": interaction.guild.id, "title": title})
        if result is None:
            await interaction.send(embed=nextcord.Embed(title="エラー", description=f"指定された設定名`{title}`が見つかりませんでした。\n`/defined list`でご確認ください。", color=0xff0000))
        else:
            try:
                embed = nextcord.Embed(title=interaction.guild.name, description=result["content"], color=0x00ff00)
                embed.set_footer(text=f"このメッセージは「{interaction.guild.name}」の「{interaction.user.name}#{interaction.user.discriminator}」さんによって送信されました。", icon_url=interaction.guild.icon.url)
                await member.send(embed=embed)
                await interaction.send(embed=nextcord.Embed(title="送信完了", description=f"{member.name}#{member.discriminator} さんに`{title}`の定型文を送信しました。", color=0x00ff00))
            except Exception as err:
                await interaction.send(embed=nextcord.Embed(title="送信失敗", description=f"{member.name}#{member.discriminator} さんへのメッセージ送信に失敗しました。\nERR: `{err}`\n```py\n{traceback.format_exc()}```", color=0xff0000))

    @send_defined_slash.on_autocomplete("title")
    @check_defined_slash.on_autocomplete("title")
    @del_defined_slash.on_autocomplete("title")
    async def title_near(self, interaction: Interaction, title: str):
        try:
            application_checks.has_permissions(manage_guild=True).predicate(interaction)
        except Exception as err:
            await interaction.response.send_autocomplete(["(サーバー管理権限がありません。)", f"{err}"])
            return
        result = await self.collection.find_one({"guild_id": interaction.guild.id, "type": "config"})
        if result is None:
            await interaction.response.send_autocomplete([])
            return
        if not title:
            await interaction.response.send_autocomplete(result["settings"])
        else:
            await interaction.response.send_autocomplete([setting for setting in result["settings"] if setting.lower().startswith(title.lower())])

def setup(bot, **kwargs):
    bot.add_cog(DefinedDM(bot, **kwargs))
