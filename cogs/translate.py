import re
import sys

import deepl
import nextcord
import pycld2
from googletrans import Translator
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.ext import commands


from util import admin_check, n_fc, eh
from util.nira import NIRA

# Translate

SYSDIR = sys.path[0]

JA = ["ja", "jp", "日本語", "にほんご", "ぬほんご", "日本"]
EN = ["en", "eng", "英語", "えいご", "米", "英"]

PROVIDER = {
    "DEEPL": {
        "NAME": "DeepL Translate",
        "ICON": "https://nira.f5.si/images/deepl_translate.png",
        "ACTIVE": True,
        "COLOR": 0x0f2b46,
        "ID": 0
    },
    "GOOGLE": {
        "NAME": "Google Translate",
        "ICON": "https://nira.f5.si/images/google_translate.png",
        "ACTIVE": True,
        "COLOR": 0x5390f5,
        "ID": 1
    }
}


def deepl_translate(deepl_tr: deepl.Translator, content, source_lang, target_lang):
    if PROVIDER["DEEPL"]["ACTIVE"]:
        if source_lang is None:
            return deepl_tr.translate_text(content, target_lang=target_lang)
        else:
            return deepl_tr.translate_text(content, source_lang=source_lang, target_lang=target_lang)
    else:
        raise Exception("DeepL Translatie isn't active.")


def google_translate(google_tr: Translator, content, source_lang, target_lang):
    if PROVIDER["GOOGLE"]["ACTIVE"]:
        if source_lang is None:
            return google_tr.translate(content, dest=target_lang)
        else:
            return google_tr.translate(content, src=source_lang, dest=target_lang)
    else:
        raise Exception("Google Translate isn't active.")


def make_embed(provider: int, translated_content: str, source: str, target: str) -> nextcord.Embed:
    if provider == PROVIDER["DEEPL"]["ID"]:
        color = PROVIDER["DEEPL"]["COLOR"]
        text = PROVIDER["DEEPL"]["NAME"]
        url = PROVIDER["DEEPL"]["ICON"]
    elif provider == PROVIDER["GOOGLE"]["ID"]:
        color = PROVIDER["GOOGLE"]["COLOR"]
        text = PROVIDER["DEEPL"]["NAME"]
        url = PROVIDER["GOOGLE"]["ICON"]
    else:
        raise ValueError(f"Unknown provider id: {provider}")
    return nextcord.Embed(title="翻訳結果", description=translated_content, color=color).set_footer(text=f"{text} ([{source}]->[{target}])", icon_url=url)


async def translation(bot: commands.Bot, deepl_tr: deepl.Translator, google_tr: Translator, content: str, source_lang: str, target_lang: str) -> tuple:
    translate = PROVIDER["DEEPL"]["ID"]
    try:
        if deepl_tr is not None:
            result = await bot.loop.run_in_executor(
                None,
                deepl_translate,
                deepl_tr,
                content,
                source_lang,
                target_lang
            )
        else:
            raise Exception("DeepL API Key doesn't exist.")
    except Exception:
        translate = PROVIDER["GOOGLE"]["ID"]
        if target_lang in ["EN-US", "EN-GB"]:
            target_lang = "en"
        if source_lang is not None:
            result = await bot.loop.run_in_executor(
                None,
                google_translate,
                google_tr,
                content,
                source_lang,
                target_lang
            )
        else:
            result = await bot.loop.run_in_executor(
                None,
                google_translate,
                google_tr,
                content,
                None,
                target_lang,
            )
    return (result.text, translate)


def languageCheck(text: str) -> str:
    isReliable, textBytesFound, details = pycld2.detect(text)
    if "ja" == details[0][1]:
        return "JA"
    else:
        return "EN"


def contentCheck(message: nextcord.Message) -> bool:
    if message.content == "" or message.content is None or message.is_system():
        return False
    else:
        return True


class ProviderSwitch(nextcord.ui.View):
    def __init__(self, message: nextcord.Message):
        super().__init__(timeout=None)
        self.add_item(ProviderSwitchDeepL(message))
        self.add_item(ProviderSwitchGoogle(message))


class ProviderSwitchDeepL(nextcord.ui.Button):
    def __init__(self, message: nextcord.Message):
        super().__init__(label="DeepL Translate", style=nextcord.ButtonStyle.grey)
        self.message = message

    async def callback(self, interaction: Interaction):
        if interaction.user.id in n_fc.py_admin:
            PROVIDER["DEEPL"]["ACTIVE"] = not PROVIDER["DEEPL"]["ACTIVE"]
            await interaction.response.send_message(f"DeepL Translate is now `{(lambda x: 'enabled' if x else 'disabled')(PROVIDER['DEEPL']['ACTIVE'])}`.", ephemeral=True)
            await self.message.delete()
            return
        else:
            await interaction.response.send_message("You can't switch providers.(`Foribidden`)", ephemeral=True)


class ProviderSwitchGoogle(nextcord.ui.Button):
    def __init__(self, message: nextcord.Message):
        super().__init__(label="Google Translate", style=nextcord.ButtonStyle.grey)
        self.message = message

    async def callback(self, interaction: Interaction):
        if interaction.user.id in n_fc.py_admin:
            PROVIDER['GOOGLE']['ACTIVE'] = not PROVIDER['GOOGLE']['ACTIVE']
            await interaction.response.send_message(f"Google Translate is now `{(lambda x: 'enabled' if x else 'disabled')(PROVIDER['GOOGLE']['ACTIVE'])}`.", ephemeral=True)
            await self.message.delete()
            return
        else:
            await interaction.response.send_message("You can't switch providers.(`Foribidden`)", ephemeral=True)


class TranslateModal(nextcord.ui.Modal):
    def __init__(self, bot: commands.Bot, deepl_tr: deepl.Translator, google_tr: Translator, source_lang: str or None, target_lang: str):
        super().__init__(
            "翻訳",
            timeout=None,
        )
        self._bot = bot
        self._deepl_tr = deepl_tr
        self._google_tr = google_tr
        self._source_lang = source_lang
        self._target_lang = target_lang

        self._translate_text = nextcord.ui.TextInput(
            label="本文",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="なんで寺院に翻訳機があるんだよ！教えはどうなってるんだよ教えは！",
            required=True,
        )
        self.add_item(self._translate_text)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer()
        try:
            async with interaction.channel.typing():
                result = await translation(self._bot, self._deepl_tr, self._google_tr, self._translate_text.value, self._source_lang, self._target_lang)
                if self._source_lang is None:
                    self._source_lang = "..."
                await interaction.followup.send(embed=make_embed(result[1], result[0], self._source_lang, self._target_lang))
        except Exception as err:
            await interaction.followup.send(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))


class Translate(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot
        if "translate" not in self.bot.settings or self.bot.settings["translate"] == "":
            self.deepl_tr = None
            PROVIDER['DEEPL']['ACTIVE'] = False
            print(
                "[Extension: Translate]\nDeepL API Key doesn't exist.\nWe use google Tranlate.")
        else:
            self.deepl_tr = deepl.Translator(self.bot.settings["translate"])
        self.google_tr = Translator()
        self.mscommand = self.translation_message_command

    @nextcord.slash_command(name="translate", description="Translate.", description_localizations={nextcord.Locale.ja: "翻訳します"}, guild_ids=n_fc.GUILD_IDS)
    async def slash_translate(
        self,
        interaction: Interaction,
        target_lang: str = SlashOption(
            description="Language of Target.",
            description_localizations={nextcord.Locale.ja: "翻訳先の言語"},
            required=True,
            choices={
                "Japanese": "JA",
                "English (US)": "EN-US",
                "English (UK)": "EN-GB",
                "Spanish": "ES",
                "French": "FR",
                "German": "DE",
                "Italy": "IT",
                "Russian": "RU",
                "Dutch": "NL",
                "Chinese": "ZH"
            },
            choice_localizations={
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
                "Japanese": "JA",
                "English": "EN",
                "Spanish": "ES",
                "French": "FR",
                "German": "DE",
                "Italy": "IT",
                "Russian": "RU",
                "Dutch": "NL",
                "Chinese": "ZH"
            },
            choice_localizations={
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
        await interaction.response.send_modal(TranslateModal(self.bot, self.deepl_tr, self.google_tr, source_lang, target_lang))

    #@nextcord.message_command(name="メッセージ翻訳", guild_ids=n_fc.GUILD_IDS)
    async def translation_message_command(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer()
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
        if sLang == "EN":
            sLang, tLang = ("EN", "JA")
        else:
            sLang, tLang = ("JA", "EN-US")
        result = await translation(self.bot, self.deepl_tr, self.google_tr, message.content, sLang, tLang)
        await interaction.followup.send(embed=make_embed(result[1], result[0], sLang, tLang))
        return

    @commands.command(name="translate", alias=["tr", "翻訳", "ほんやくこんにゃく", "ほんやく"], help="""\
翻訳
メッセージを翻訳します。

コンテキストコマンド:`n!translate [ja/en] [text]`
スラッシュコマンド:`/translate`

・チャンネルトピックについて
`nira-tl-en`: チャンネルに来たメッセージを英語に翻訳します。
`nira-tl-ja`: チャンネルに来たメッセージを日本語に翻訳します。
`nira-tl-auto`: チャンネルに来たメッセージが、日本語であれば英語に、英語であれば日本語に翻訳します。

・翻訳提供
`n!translate`と送信すると、メッセージの下部で使用できる翻訳プロバイダが表示されます。

Powered by DeepL Translate/Google Translate.""")
    async def command_translate(self, ctx: commands.Context):
        args = ctx.message.content.split(" ", 2)
        if len(args) == 1:
            await ctx.reply(
                embed=nextcord.Embed(
                    title="エラー",
                    description=f"翻訳先を指定してください\n`{self.bot.command_prefix}translate [ja/en] [text]`",
                    color=0xFF0000
                ).set_footer(
                    text=f"{(lambda x, y: 'No Provider!' if x and y else '')(not PROVIDER['DEEPL']['ACTIVE'], not PROVIDER['GOOGLE']['ACTIVE'])}{(lambda x: 'DeepL Translate' if x else '')(PROVIDER['DEEPL']['ACTIVE'])}{(lambda x, y: '/' if x and y else '')(PROVIDER['DEEPL']['ACTIVE'], PROVIDER['GOOGLE']['ACTIVE'])}{(lambda x: 'Google Translate' if x else '')(PROVIDER['GOOGLE']['ACTIVE'])}"
                )
            )
        elif len(args) == 2:
            if args[1] == "provider":
                if not await self.bot.is_owner(ctx.author):
                    raise NIRA.ForbiddenExpand()
                message = await ctx.send("Please wait...")
                await message.edit(content="", embed=nextcord.Embed(title="Provider Switch", description=f"DeepL Translate: `{(lambda x: 'Enable' if x else 'Disable')(PROVIDER['DEEPL']['ACTIVE'])}`\nGoogle Translate: `{(lambda x: 'Enable' if x else 'Disable')(PROVIDER['GOOGLE']['ACTIVE'])}`", color=0x00ff00), view=ProviderSwitch(message=message))
                return
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
                async with ctx.channel.typing():
                    result = await translation(self.bot, self.deepl_tr, self.google_tr, args[2], None, lang)
                    await ctx.reply(embed=make_embed(result[1], result[0], "...", lang))
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="エラー", description=f"エラー。\n```\n{err}```", color=0xFF0000))
        return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel):
            return
        if not contentCheck(message):
            return
        if message.author.id == self.bot.user.id:
            return
        if message.channel.topic is None:
            return

        if re.search(u"nira-tl-(ja|en|auto)", message.channel.topic):
            if message.author.bot:
                return
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
                if sLang == "JA":
                    TARGET = "EN-US"
            else:
                return
            async with message.channel.typing():
                result = await translation(self.bot, self.deepl_tr, self.google_tr, CONTENT, None, TARGET)
                await message.reply(embed=make_embed(result[1], result[0], "...", TARGET))

        elif re.search(u"nira-tlb-(ja|en|auto)", message.channel.topic):
            if message.author.id == self.bot.user.id:
                return
            CONTENT = message.content
            if CONTENT == "" or CONTENT is None:
                CONTENT = message.embeds[0].description
            if CONTENT == "" or CONTENT is None:
                return
            if re.search(u"nira-tlb-(ja|en|auto)", message.channel.topic).group() == "nira-tlb-ja":
                TARGET = "JA"
            elif re.search(u"nira-tlb-(ja|en|auto)", message.channel.topic).group() == "nira-tlb-en":
                TARGET = "EN-US"
            elif re.search(u"nira-tlb-(ja|en|auto)", message.channel.topic).group() == "nira-tlb-auto":
                sLang = languageCheck(message.content)
                TARGET = "JA"
                if sLang == "JA":
                    TARGET = "EN-US"
            else:
                return
            async with message.channel.typing():
                result = await translation(self.bot, self.deepl_tr, self.google_tr, CONTENT, None, TARGET)
                await message.reply(embed=make_embed(result[1], result[0], "...", TARGET))


def setup(bot, **kwargs):
    bot.add_cog(Translate(bot, **kwargs))
