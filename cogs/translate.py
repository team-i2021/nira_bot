import asyncio
import json
import logging
import os
import subprocess
import sys
import traceback
from subprocess import PIPE

import deepl
import nextcord
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands

from util import admin_check, n_fc, eh

# Translate

dir = sys.path[0]

JA = ["ja", "jp", "日本語", "にほんご", "ぬほんご", "日本"]
EN = ["en", "eng", "英語", "えいご", "米", "英"]


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
            result = self.translator.translate_text(
                self.translate_text.value,
                source_lang=self.source_lang,
                target_lang=self.target_lang)
            if self.source_lang is None:
                self.source_lang = "..."
            embed = nextcord.Embed(
                title="翻訳結果", description=result.text, color=0x00ff00)
            embed.set_footer(
                text=f"DeepL API ({self.source_lang} -> {self.target_lang})", icon_url="https://static.deepl.com/img/logo/deepl-logo-blue.svg")
            await interaction.followup.send(embed=embed)
        except deepl.DeepLException as err:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"DeepL APIエラー。\n```\n{err}```", color=0xFF0000))
        except Exception as err:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        SETTING = json.load(open(f'{dir}/setting.json'))
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

    @commands.command(name="translate", alias=["tr", "翻訳"], help="""\
翻訳
`n!translate [ja/en] [text]`""")
    async def command_translate(self, ctx: commands.Context):
        if self.TOKEN is None:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー", description="管理者にお伝えください。\n`DeepL API Key doesn't exist.`\nDeepL APIのキーが存在しません。\n`setting.json`の`translate`欄にAPIキーを入力してから、`cogs/translate.py`をリロードしてください。", color=0xff0000)
            )
            return
        args = ctx.message.content.split(" ", 2)
        if len(args) == 1:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="翻訳先を指定してください\n`n!translate [ja/en] [text]`", color=0xFF0000))
        elif len(args) == 2:
            await ctx.reply(embed=nextcord.Embed(title="エラー", description="引数が足りません。\n`n!translate [ja/en] [text]`", color=0xFF0000))
        else:
            if args[1].lower() in JA:
                lang = "JA"
            elif args[1].lower() in EN:
                lang = "EN-US"
            else:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description="言語設定がおかしいです。\n英語:`en`/日本語:`jp`\n`n!translate [ja/en] [text]`", color=0xFF0000))
                return
            try:
                result = self.translator.translate_text(
                    args[2], target_lang=lang)
                embed = nextcord.Embed(
                    title="翻訳結果", description=result.text, color=0x00ff00)
                embed.set_footer(
                    text="DeepL APi", icon_url="https://static.deepl.com/img/logo/deepl-logo-blue.svg")
                await ctx.reply(embed=embed)
            except deepl.DeepLException as err:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"DeepL APIエラー。\n```\n{err}```", color=0xFF0000))
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))
        return


def setup(bot):
    bot.add_cog(Translate(bot))
