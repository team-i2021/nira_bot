import asyncio
import json
import logging
import os
import re
import sys
import traceback

import deepl
import nextcord
import pycld2
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands


from util import admin_check, n_fc, eh

# Translate

SYSDIR = sys.path[0]
ICON_URL = "https://asset.watch.impress.co.jp/img/ktw/docs/1370/335/icon_l.png"

JA = ["ja", "jp", "日本語", "にほんご", "ぬほんご", "日本"]
EN = ["en", "eng", "英語", "えいご", "米", "英"]

TRANS_COMP = re.compile('[a-zA-Z0-9.,_;:()!?-]+')

def languageCheck(text: str) -> str:
    isReliable, textBytesFound, details = pycld2.detect(text)
    if "ja" == details[0][1]:
        return "JA"
    else:
        return "EN"

def contentCheck(message: nextcord.Message) -> bool:
    if message.content == "" or message.content is None:
        return False
    elif message.author.bot:
        return False
    else:
        return True

class TranslateModal(nextcord.ui.Modal):
    def __init__(self, translator: deepl.Translator, source_lang: str or None, target_lang: str):
        super().__init__(
            "翻訳",
            timeout=None,
        )
        self.translator = translator
        self.source_lang = source_lang
        self.target_lang = target_lang

        self.translate_text = nextcord.ui.TextInput(
            label="本文",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="なんで寺院に翻訳機があるんだよ！教えはどうなってるんだよ教えは！",
            required=True,
        )
        self.add_item(self.translate_text)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer()
        try:
            async with interaction.channel.typing():
                result = self.translator.translate_text(
                    self.translate_text.value,
                    source_lang=self.source_lang,
                    target_lang=self.target_lang)
                if self.source_lang is None:
                    self.source_lang = "..."
                embed = nextcord.Embed(
                    title="翻訳結果", description=result.text, color=0x00ff00)
                embed.set_footer(
                    text=f"DeepL Translate ([{self.source_lang}]->[{self.target_lang}])", icon_url=ICON_URL)
                await interaction.followup.send(embed=embed)
                return
        except deepl.DeepLException as err:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"DeepL APIエラー。\n```\n{err}```", color=0xFF0000))
        except Exception as err:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))
        return


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        SETTING = json.load(open(f'{SYSDIR}/setting.json'))
        if "translate" not in SETTING:
            self.TOKEN = None
        else:
            self.TOKEN = SETTING["translate"]
        self.translator = deepl.Translator(self.TOKEN)

    @nextcord.slash_command(name="translate", description="翻訳します", guild_ids=n_fc.GUILD_IDS)
    async def slash_genshin(
        self,
        interaction: Interaction,
        target_lang: str = SlashOption(
            description="翻訳先の言語",
            required=True,
            choices={
                "日本語": "JA",
                "英語（米国）": "EN-US",
                "英語（英国）": "EN-GB",
                "スペイン語": "ES",
                "フランス語": "FR",
                "ドイツ語": "DE",
                "イタリア語": "IT",
                "ロシア語": "RU",
                "オランダ語": "NL",
                "中国語": "ZH"
            }
        ),
        source_lang: str = SlashOption(
            description="翻訳元の言語",
            required=False,
            choices={
                "日本語": "JA",
                "英語": "EN",
                "スペイン語": "ES",
                "フランス語": "FR",
                "ドイツ語": "DE",
                "イタリア語": "IT",
                "ロシア語": "RU",
                "オランダ語": "NL",
                "中国語": "ZH"
            }
        )
    ):
        if self.TOKEN is None:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="エラー", description="管理者にお伝えください。\n`DeepL API Key doesn't exist.`\nDeepL APIのキーが存在しません。\n`setting.json`の`translate`欄にAPIキーを入力してから、`cogs/translate.py`をリロードしてください。", color=0xff0000)
            )
            return
        await interaction.response.send_modal(TranslateModal(self.translator, source_lang, target_lang))

    @nextcord.message_command(name="メッセージ翻訳", guild_ids=n_fc.GUILD_IDS)
    async def translation_message_command(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer()
        if self.TOKEN is None:
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="エラー", description="管理者にお伝えください。\n`DeepL API Key doesn't exist.`\nDeepL APIのキーが存在しません。\n`setting.json`の`translate`欄にAPIキーを入力してから、`cogs/translate.py`をリロードしてください。", color=0xff0000)
            )
            return
        if not contentCheck(message):
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="エラー",
                    description="指定されたメッセージには本文がありません。\nEmbedの場合は先に「Embedコンテンツの取得」から、メッセージを取得してください。",
                    color=0xff0000
                )
            )
            return

        sLang = languageCheck(message.content)
        if sLang == "EN": sLang, tLang = ("EN", "JA")
        else: sLang, tLang = ("JA", "EN-US")
        result = self.translator.translate_text(
            message.content, target_lang=tLang, source_lang=sLang)
        embed = nextcord.Embed(
            title="翻訳結果", description=result.text, color=0x00ff00)
        embed.set_footer(
            text="DeepL Translate", icon_url=ICON_URL)
        await interaction.followup.send(embed=embed)
        return

    @commands.command(name="translate", alias=["tr", "翻訳"], help="""\
翻訳
`n!translate [ja/en] [text]`

Powered by DeepL Translate API""")
    async def command_translate(self, ctx: commands.Context):
        if self.TOKEN is None:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー", description="管理者にお伝えください。\n`DeepL API Key doesn't exist.`\nDeepL APIのキーが存在しません。\n`setting.json`の`translate`欄にAPIキーを入力してから、`cogs/translate.py`をリロードしてください。", color=0xff0000)
            )
            return
        args = ctx.message.content.split(" ", 2)
        if len(args) == 1:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"翻訳先を指定してください\n`{self.bot.command_prefix}translate [ja/en] [text]`", color=0xFF0000))
        elif len(args) == 2:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"引数が足りません。\n`{self.bot.command_prefix}translate [ja/en] [text]`", color=0xFF0000))
        else:
            if args[1].lower() in JA:
                lang = "JA"
            elif args[1].lower() in EN:
                lang = "EN-US"
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"言語設定がおかしいです。\n英語:`en`/日本語:`jp`\n`{self.bot.command_prefix}translate [ja/en] [text]`", color=0xff0000))
                return
            try:
                async with ctx.message.channel.typing():
                    result = self.translator.translate_text(
                        args[2], target_lang=lang)
                    embed = nextcord.Embed(
                        title="翻訳結果", description=result.text, color=0x00ff00)
                    embed.set_footer(
                        text="DeepL Translate", icon_url=ICON_URL)
                    await ctx.reply(embed=embed)
                    return
            except deepl.DeepLException as err:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"DeepL APIエラー。\n```\n{err}```", color=0xFF0000))
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))
        return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not contentCheck(message):
            return
        if message.author.id == self.bot.user.id:
            return
        if message.channel.topic is None:
            return
        if re.search(u"nira-tl-(ja|en|auto)", message.channel.topic):
            CONTENT = message.content
            if CONTENT == "" or CONTENT is None:
                CONTENT = message.embeds[0].description
            if CONTENT == "" or CONTENT is None:
                return
            if re.search(u"nira-tl-(ja|en|auto)", message.channel.topic).group() == "nira-tl-ja":
                TARGET = "JA"
            elif re.search(u"nira-tl-(ja|en|auto)", message.channel.topic).group() == "nira-tl-en":
                TARGET = "EN-US"
            elif re.search(u"nira-tl-(ja|en|auto)", message.channel.topic).group() == "nira-tl-auto":
                sLang = languageCheck(message.content)
                TARGET = "JA"
                if sLang == "JA": TARGET = "EN-US"
            else:
                return
            async with message.channel.typing():
                result = self.translator.translate_text(
                    CONTENT,
                    target_lang=TARGET
                )
                embed = nextcord.Embed(
                    title="翻訳結果", description=result.text, color=0x00ff00)
                embed.set_footer(
                    text=f"DeepL Translate ([...]->[{TARGET}])", icon_url=ICON_URL)
                await message.reply(embed=embed)


def setup(bot):
    bot.add_cog(Translate(bot))
