import asyncio
import datetime
import importlib
import logging
import random
import sys
import traceback

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks

from motor import motor_asyncio

from util import n_fc, tts_convert, semiembed
from util.nira import NIRA

# Text To Speech

class Text2Speech(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.VOICEVOX_VERSION = "0.14.4"
        self.collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["tts_database"]
        self.dict_collection: motor_asyncio.AsyncIOMotorCollection = self.bot.database["tts_dictionary"]
        self.keys: list[str] | None = self.bot.settings["voicevox"]
        self.Effective = True
        self.Reason = ""
        if self.keys is None or len(self.keys) == 0:
            self.Effective = False
            self.Reason = "VOICEVOX API Key doesn't exist."
        self.SPEAKER_AUTHOR = {}
        self.TTS_CHANNEL = {}
        self.mscommand = self.speak_message

        self.custom_dictionary: dict[int, dict[str, str]] = {}

        self.voicevox_embed = nextcord.Embed(
            title="声の種類選択",
            description="VOICEVOXには多種多様なキャラクターがいます！",
            color=0xa5d4ad
        ).add_field(
            name="7期生",
            value="†聖騎士紅桜†、雀松朱司、麒ヶ島宗麟、春歌ナナ、猫使アル、猫使ビィ、中国うさぎ",
            inline=False
        ).add_field(
            name="6期生",
            value="ちび式じい、櫻歌ミコ、小夜/SAYO、ナースロボ＿タイプＴ",
            inline=False
        ).add_field(
            name="5期生",
            value="WhiteCUL、後鬼、No.7",
            inline=False
        ).add_field(
            name="4期生",
            value="もち子さん、剣崎雌雄",
            inline=False
        ).add_field(
            name="3期生",
            value="玄野武宏、白上虎太郎、青山龍星、冥鳴ひまり、九州そら",
            inline=False
        ).add_field(
            name="2期生",
            value="春日部つむぎ、雨晴はう、波音リツ",
            inline=False
        ).add_field(
            name="1期生",
            value="四国めたん、ずんだもん",
            inline=False
        )

        self.VOICEVOX_SPEAKER_LIST = []

        self.api_url = "https://deprecatedapis.tts.quest/v2/voicevox"

        asyncio.ensure_future(self.__recover_channel())
        asyncio.ensure_future(self.__recover_speaker())
        asyncio.ensure_future(self.__fetch_speakers())


    class VOICEVOXGenerationSelect(nextcord.ui.Select):
        def __init__(self, parent: 'Text2Speech', author: nextcord.Member | nextcord.User, generation: str | None = None):
            self.parent = parent
            self.author = author
            options = [
                nextcord.SelectOption(label="7期生", value="7"),
                nextcord.SelectOption(label="6期生", value="6"),
                nextcord.SelectOption(label="5期生", value="5"),
                nextcord.SelectOption(label="4期生", value="4"),
                nextcord.SelectOption(label="3期生", value="3"),
                nextcord.SelectOption(label="2期生", value="2"),
                nextcord.SelectOption(label="1期生", value="1"),
            ]
            super().__init__(
                placeholder=f"世代: {generation}期生" if generation else 'キャラクターの世代を選択してください。',
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, interaction: nextcord.Interaction):
            assert interaction.user is not None, "このメニューを操作したユーザーを特定できませんでした。"
            assert interaction.message is not None, "このメニューを表示しているメッセージを特定できませんでした。"

            if self.author.id != interaction.user.id:
                await interaction.send("あなたが送信した声選択メニューではありません。\n`/tts voice`と送信して、声選択メニューを表示してください。", ephemeral=True)
                return
            try:
                view = self.parent.VoiceSelectView(self.parent, self.author, generation=self.values[0])
                await interaction.message.edit(content=interaction.message.content, embed=interaction.message.embeds[0], view=view)
            except Exception as err:
                logging.error(err)


    class VOICEVOXSpeakerSelect(nextcord.ui.Select):
        def __init__(self, parent: 'Text2Speech', author: nextcord.Member | nextcord.User, generation: str, speaker: str | None = None):
            self.parent = parent
            self.author = author
            self.generation = generation

            match generation:
                case "7":
                    options = [
                        nextcord.SelectOption(label="†聖騎士紅桜†", value="19"),
                        nextcord.SelectOption(label="雀松朱司", value="20"),
                        nextcord.SelectOption(label="麒ヶ島宗麟", value="21"),
                        nextcord.SelectOption(label="春歌ナナ", value="22"),
                        nextcord.SelectOption(label="猫使アル", value="23"),
                        nextcord.SelectOption(label="猫使ビィ", value="24"),
                        nextcord.SelectOption(label="中国うさぎ", value="25"),
                    ]
                case "6":
                    options = [
                        nextcord.SelectOption(label="ちび式じい", value="15"),
                        nextcord.SelectOption(label="櫻歌ミコ", value="16"),
                        nextcord.SelectOption(label="小夜/SAYO", value="17"),
                        nextcord.SelectOption(label="ナースロボ＿タイプＴ", value="18"),
                    ]
                case "5":
                    options = [
                        nextcord.SelectOption(label="WhiteCUL", value="12"),
                        nextcord.SelectOption(label="後鬼", value="13"),
                        nextcord.SelectOption(label="No.7", value="14"),
                    ]
                case "4":
                    options = [
                        nextcord.SelectOption(label="もち子さん", value="10"),
                        nextcord.SelectOption(label="剣崎雌雄", value="11"),
                    ]
                case "3":
                    options = [
                        nextcord.SelectOption(label="玄野武宏", value="5"),
                        nextcord.SelectOption(label="白上虎太郎", value="6"),
                        nextcord.SelectOption(label="青山龍星", value="7"),
                        nextcord.SelectOption(label="冥鳴ひまり", value="8"),
                        nextcord.SelectOption(label="九州そら", value="9"),
                    ]
                case "2":
                    options = [
                        nextcord.SelectOption(label="春日部つむぎ", value="2"),
                        nextcord.SelectOption(label="雨晴はう", value="3"),
                        nextcord.SelectOption(label="波音リツ", value="4"),
                    ]
                case "1":
                    options = [
                        nextcord.SelectOption(label="四国めたん", value="0"),
                        nextcord.SelectOption(label="ずんだもん", value="1"),
                    ]
                case _:
                    options = []

            if speaker:
                chara = self.parent.VOICEVOX_SPEAKER_LIST[int(speaker)]
                placeholder = f"キャラクター: {chara['name']}"
            else:
                chara = None
                placeholder = f'{self.generation}期生のキャラクターを選択してください。'
            super().__init__(
                placeholder=placeholder,
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, interaction: nextcord.Interaction):
            assert interaction.user is not None, "このメニューを操作したユーザーを特定できませんでした。"
            assert interaction.message is not None, "このメニューを表示しているメッセージを特定できませんでした。"

            if self.author.id != interaction.user.id:
                await interaction.send("あなたが送信した声選択メニューではありません。\n`/tts voice`と送信して、声選択メニューを表示してください。", ephemeral=True)
                return
            try:
                view = self.parent.VoiceSelectView(self.parent, self.author, generation=self.generation, speaker=self.values[0])
                await interaction.message.edit(content=interaction.message.content, embed=interaction.message.embeds[0], view=view)
            except Exception as err:
                logging.error(err)

    class VOICEVOXVoiceTypeSelect(nextcord.ui.Select):
        def __init__(self, parent: 'Text2Speech', author: nextcord.Member | nextcord.User, generation: str, speaker: str):
            self.parent = parent
            self.author = author
            self.generation = generation
            self.speaker = speaker

            self.chara = self.parent.VOICEVOX_SPEAKER_LIST[int(self.speaker)]
            options = []

            for i in range(len(self.chara["styles"])):
                options.append(nextcord.SelectOption(label=self.chara["styles"][i]["name"], value=f'{self.chara["styles"][i]["name"]}:{self.chara["styles"][i]["id"]}'))

            super().__init__(
                placeholder=f"{self.chara['name']}の声の種類を選んでください。",
                min_values=1,
                max_values=1,
                options=options
            )

        async def callback(self, interaction: nextcord.Interaction):
            assert interaction.user is not None, "このメニューを操作したユーザーを特定できませんでした。"
            assert interaction.message is not None, "このメニューを表示しているメッセージを特定できませんでした。"

            if self.author.id != interaction.user.id:
                await interaction.send("あなたが送信した声選択メニューではありません。\n`/tts voice`と送信して、声選択メニューを表示してください。", ephemeral=True)
                return
            try:
                style_name, style_id = self.values[0].split(":")
                self.parent.SPEAKER_AUTHOR[interaction.user.id] = style_id
                await self.parent.collection.update_one({"user_id": interaction.user.id, "type": "speaker"}, {"$set": {"speaker": style_id}}, upsert=True)
                await interaction.message.edit(content=f"{self.chara['name']}の{style_name}に声の種類を変更しました。", embed=None, view=None)
            except Exception as err:
                logging.error(err)


    class VoiceSelectView(nextcord.ui.View):
        def __init__(
                self,
                parent: 'Text2Speech',
                author: nextcord.Member | nextcord.User,
                generation: str | None = None,
                speaker: str | None = None,
            ):
            self.parent = parent
            self.author = author
            super().__init__(timeout=None)
            self.add_item(self.parent.VOICEVOXGenerationSelect(self.parent, author, generation))
            if generation:
                self.add_item(self.parent.VOICEVOXSpeakerSelect(self.parent, author, generation, speaker))
                if speaker:
                    self.add_item(self.parent.VOICEVOXVoiceTypeSelect(self.parent, author, generation, speaker))


    @property
    def key(self):
        return self.keys[random.randint(0, len(self.keys) - 1)]

    def get_custom_dictionary(self, guild_id: int | None = None) -> dict[str, str]:
        if guild_id is not None and guild_id in self.custom_dictionary:
            return self.custom_dictionary[guild_id]
        else:
            return {}

    async def pull_dictionary(self, guild_id: int) -> None:
        self.custom_dictionary[guild_id] = {}
        dictionary = await self.dict_collection.find({"guild_id": guild_id}).to_list(length=None)
        if dictionary is None:
            return
        for dic in dictionary:
            self.custom_dictionary[guild_id][dic["word"]] = dic["read"]

    async def push_dictionary(self, guild_id: int, word: str, read: str) -> None:
        # pushとか言ってるけど正確にはaddとcommitとpush全部やってる
        self.custom_dictionary[guild_id][word] = read
        await self.dict_collection.update_one({"guild_id": guild_id, "word": word}, {"$set": {"read": read}}, upsert=True)

    def get_speak_url(self, message: str, speaker: str = "2", guild_id: int | None = None) -> str:
        return f"{self.api_url}/audio/?text={tts_convert.convert(message, self.get_custom_dictionary(guild_id))}&key={self.key}&speaker={speaker}"

    async def __recover_channel(self):
        channels = await self.collection.find({"type":"channel"}).to_list(length=None)
        for channel in channels:
            self.TTS_CHANNEL[channel['guild_id']] = channel['channel_id']

    async def __recover_speaker(self):
        speaker = await self.collection.find({"type": "speaker"}).to_list(length=None)
        for sp in speaker:
            self.SPEAKER_AUTHOR[sp['user_id']] = sp['speaker']

    async def __fetch_speakers(self, retry: int = 3):
        for _ in range(retry):
            async with self.bot.session.post(f"{self.api_url}/speakers/", data={"key": self.key}) as resp:
                if resp.status == 200:
                    self.VOICEVOX_SPEAKER_LIST = await resp.json()
                    return
                else:
                    self.Reason = f"Failed to fetch speakers. (VOICEVOX API) {resp.status}"
                    await asyncio.sleep(1)
        logging.error("Failed to fetch speakers.")
        self.Effective = False

    @nextcord.slash_command(name="tts", description="Text-To-Speech")
    async def tts_slash(self, interaction: Interaction):
        pass

    @tts_slash.subcommand(name="join", description="Join VC (for TTS)", description_localizations={nextcord.Locale.ja: "BOTを読み上げ用にVCに参加させます"})
    async def join_slash(self, interaction: Interaction):
        if not self.Effective:
            await interaction.response.send_message(embed=nextcord.Embed(title="現在読み上げ機能は利用できません。", description=f"BOT管理者からの情報をご確認ください。\n`{self.Reason}`", color=0xff0000))
            return
        if interaction.user.voice is None:
            await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="先にVCに接続してください。", color=0xff0000), ephemeral=True)
        else:
            if interaction.guild.voice_client is not None:
                if interaction.guild.voice_client.channel.id == interaction.user.voice.channel.id:
                    await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description=f"既にVCに入っています。\n音楽再生から切り替える場合は、`{self.bot.command_prefix}leave`->`{self.bot.command_prefix}tts join`の順に入力してください。", color=0xff0000), ephemeral=True)
                    return
                else:
                    await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description=f"BOTが別のVCに参加しています。\nBOTが参加しているVCに参加して、切断コマンドを実行してください。", color=0xff0000), ephemeral=True)
                    return
            await self.pull_dictionary(interaction.guild.id)
            await interaction.user.voice.channel.connect()
            self.TTS_CHANNEL[interaction.guild.id] = interaction.channel.id
            asyncio.ensure_future(self.collection.update_one({"guild_id": interaction.guild.id, "type": "channel"}, {"$set": {"channel_id": interaction.channel.id}}, upsert=True))
            await interaction.response.send_message("接続しました", embed=nextcord.Embed(title="TTS", description="""\
TTSの読み上げ音声には、VOICEVOXが使われています。
ご利用の際は、[VOICEVOXホームページ](https://voicevox.hiroshiba.jp/)から、VOICEVOX利用規約及びキャラクターや音声ライブラリなどの利用規約などをご確認ください。
[青空龍星の利用許諾](https://virvoxproject.wixsite.com/official/voicevox%E3%81%AE%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84)・[もち子の利用規約](https://vtubermochio.wixsite.com/mochizora/%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84)

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。

本サービスはVOICEVOX公式より承諾されたものではなく、非公式で提供しているものです。""", color=0x00ff00))
            interaction.guild.voice_client.play(
                nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(
                    self.get_speak_url("接続しました。", "2")
                ),
                    volume=0.5)
            )


    @tts_slash.subcommand(name="leave", description="Leave from VC", description_localizations={nextcord.Locale.ja: "BOTからVCを離脱させます"})
    async def leave_slash(self, interaction: Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000), ephemeral=True)
        else:
            if interaction.guild.voice_client is None:
                await interaction.response.send_message(embed=nextcord.Embed(title="TTSエラー", description="そもそも入ってないっす...(´・ω・｀)", color=0xff0000), ephemeral=True)
                return
            await interaction.guild.voice_client.disconnect()
            del self.TTS_CHANNEL[interaction.guild.id]
            await self.collection.delete_one({"guild_id": interaction.guild.id, "type": "channel"})
            await interaction.response.send_message(embed=nextcord.Embed(title="TTS", description="あっ...ばいばーい...", color=0x00ff00))


    @tts_slash.subcommand(name="voice", description="Change TTS Voice", description_localizations={nextcord.Locale.ja: "読み上げの声の種類を変更します"})
    async def voice_slash(self, interaction: Interaction):
        if interaction.user.voice is None:
            await interaction.send("先にボイスチャンネルに接続してください。", ephemeral=True)
        else:
            view = self.VoiceSelectView(self, interaction.user)
            await interaction.send(f"下のプルダウンから声を選択してください。\n選択可能声種類: `v{self.VOICEVOX_VERSION}`基準", embed=self.voicevox_embed, view=view, ephemeral=False)


    @tts_slash.subcommand(name="reload", description="Reload Modules for TTS")
    async def reload_slash(self, interaction: Interaction):
        if await self.bot.is_owner(interaction.user):
            importlib.reload(tts_convert)
            await interaction.response.send_message(nextcord.Embed(title="Reloaded.", description="TTS modules were reloaded.", color=0x00ff00), ephemeral=True)
        else:
            raise NIRA.ForbiddenExpand()


    @tts_slash.subcommand(name="dictionary", description="Custom Dictionary")
    async def dictionary_slash(self, interaction: Interaction):
        pass


    @application_checks.has_permissions(speak=True, connect=True)
    @dictionary_slash.subcommand(name="add", description="Add word to custom dictionary", description_localizations={nextcord.Locale.ja: "カスタム辞書に単語を追加します"})
    async def dictionary_add_slash(
            self,
            interaction: Interaction,
            word: str = SlashOption(
                name="word",
                description="Substitute word",
                description_localizations={nextcord.Locale.ja: "置き換える単語"},
                required=True
            ),
            read: str = SlashOption(
                name="read",
                description="Reading",
                description_localizations={nextcord.Locale.ja: "読み方"},
                required=True
            )
        ):
        await self.push_dictionary(interaction.guild.id, word, read)
        await interaction.response.send_message(embed=nextcord.Embed(title="Server Custom Dictionary", description=f"単語 `{word}` を `{read}` として登録しました。", color=0x00ff00))
        await self.pull_dictionary(interaction.guild.id)


    @application_checks.has_permissions(speak=True, connect=True)
    @dictionary_slash.subcommand(name="remove", description="Remove word from custom dictionary", description_localizations={nextcord.Locale.ja: "カスタム辞書から単語を削除します"})
    async def dictionary_remove_slash(self, interaction: Interaction, word: str):
        await self.pull_dictionary(interaction.guild.id)
        if word in self.get_custom_dictionary(interaction.guild.id):
            await self.dict_collection.delete_one({"guild_id": interaction.guild.id, "word": word})
            await interaction.response.send_message(embed=nextcord.Embed(title="Server Custom Dictionary", description=f"単語 `{word}` を削除しました。", color=0x00ff00))
            await self.pull_dictionary(interaction.guild.id)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(title="Server Custom Dictionary", description=f"単語 `{word}` は登録されていません。", color=0xff0000))


    @dictionary_slash.subcommand(name="list", description="Show custom dictionary", description_localizations={nextcord.Locale.ja: "カスタム辞書を表示します"})
    async def dictionary_list_slash(self, interaction: Interaction):
        await self.pull_dictionary(interaction.guild.id)
        if len(self.get_custom_dictionary(interaction.guild.id)) == 0:
            await interaction.response.send_message(embed=nextcord.Embed(title="Server Custom Dictionary", description="カスタム辞書は空です。", color=0xff0000))
        else:
            embed = semiembed.SemiEmbed(title="Server Custom Dictionary", description="カスタム辞書", color=0x00ff00)
            for word, read in self.get_custom_dictionary(interaction.guild.id).items():
                embed.add_field(name=word, value=read, inline=False)
            await interaction.response.send_message(embeds=embed.get_embeds())


    @commands.command(name='tts', aliases=("読み上げ", "よみあげ"), help="""\
VCに乱入して、代わりに読み上げてくれる機能。

`n!tts join`で、今あなたが入っているVCチャンネルににらが乱入します。
あとは、コマンドを打ったチャンネルでテキストを入力すれば、それを読み上げます。
`n!tts leave`で、乱入しているVCチャンネルから出ます。

なお、既に音楽再生機能としてにらBOTがVCに入っている場合は、どっちかしか使えないので、どっちかにしてください。はい。

声の種類を選ぶには`n!tts voice`と入力してください。

TTSは、(暫定的だけど)[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。
API制限などが来た場合はご了承ください。許せ。""")
    async def tts(self, ctx: commands.Context, action: str = None):
        # assert isinstance(ctx.channel, nextcord.TextChannel), "このコマンドはテキストチャンネルでのみ実行できます。"
        assert isinstance(ctx.author, nextcord.Member), "このコマンドはサーバー内でのみ実行できます。"
        assert isinstance(ctx.guild, nextcord.Guild), "このコマンドはサーバー内でのみ実行できます。"

        if not self.Effective:
            await ctx.reply(embed=nextcord.Embed(title="現在読み上げ機能は利用できません。", description=f"BOT管理者からの情報をご確認ください。\n`{self.Reason}`", color=0xff0000))
            return

        if action is None:
            await ctx.reply(f"・読み上げ機能 `VOICEVOX: v{self.VOICEVOX_VERSION}`\nエラー：書き方が間違っています。\n\n`{ctx.prefix}tts join`: 参加\n`{ctx.prefix}tts leave`: 退出\n`{ctx.prefix}tts voice`: 声選択")
            return

        if action == "join":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is not None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"既にVCに入っています。\n音楽再生から読み上げに切り替える場合は、`{ctx.prefix}leave`->`{ctx.prefix}tts join`の順に入力してください。", color=0xff0000))
                        return
                    await ctx.author.voice.channel.connect()
                    self.TTS_CHANNEL[ctx.guild.id] = ctx.channel.id
                    await self.collection.update_one({"guild_id": ctx.guild.id, "type": "channel"}, {"$set": {"tts_channel": ctx.channel.id}}, upsert=True)
                    await ctx.reply("接続しました", embed=nextcord.Embed(title="TTS", description="""\
TTSの読み上げ音声には、VOICEVOXが使われています。
ご利用の際は、[VOICEVOXホームページ](https://voicevox.hiroshiba.jp/)から、VOICEVOX利用規約及びキャラクターや音声ライブラリなどの利用規約などをご確認ください。
[青空龍星の利用許諾](https://virvoxproject.wixsite.com/official/voicevox%E3%81%AE%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84)・[もち子の利用規約](https://vtubermochio.wixsite.com/mochizora/%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84)

また、音声生成には[WEB版VOICEVOX](https://voicevox.su-shiki.com/)のAPIを使用させていただいております。

本サービスはVOICEVOX公式より承諾されたものではなく、非公式で提供しているものです。""", color=0x00ff00))
                    ctx.guild.voice_client.play(
                        nextcord.PCMVolumeTransformer(
                            nextcord.FFmpegPCMAudio(
                                self.get_speak_url("接続しました。", "2")
                            ),
                            volume=0.5
                        )
                    )
                    logging.info(f"Connect TTS at {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
                logging.error(traceback.format_exc())
                return

        elif action == "leave":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="そもそも入ってないっす...(´・ω・｀)", color=0xff0000))
                        return
                    await ctx.guild.voice_client.disconnect()
                    del self.TTS_CHANNEL[ctx.guild.id]
                    await self.collection.delete_one({"guild_id": ctx.guild.id, "type": "channel"})
                    await ctx.reply(embed=nextcord.Embed(title="TTS", description="あっ...ばいばーい...", color=0x00ff00))
                    logging.info(f"Leave TTS from {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTS切断時エラー", description=f"```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000))
                logging.error(
                    f"[TTS切断時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}"
                )
                return

        elif action == "voice":
            try:
                if ctx.author.voice is None:
                    await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                    return
                else:
                    if ctx.guild.voice_client is None:
                        await ctx.reply(embed=nextcord.Embed(title="TTSエラー", description="僕...入ってないっす...(´・ω・｀)", color=0xff0000))
                        return
                    else:
                        view = self.VoiceSelectView(self, ctx.author)
                        await ctx.reply(f"下のプルダウンから声を選択してください。\n選択可能声種類: `v{self.VOICEVOX_VERSION}`基準", embed=self.voicevox_embed, view=view)
                    logging.info(f"Change TTS {ctx.author.name}'s Voice at {ctx.guild.name}")
                    return
            except Exception as err:
                await ctx.reply(embed=nextcord.Embed(title="TTS声変更時のエラー", description=f"```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000))
                logging.error(
                    f"[TTS voice change時のエラー - {datetime.datetime.now()}]\n\n{err}\n\n{sys.exc_info()}"
                )
                return

        elif action == "reload" and await self.bot.is_owner(ctx.author):
            importlib.reload(tts_convert)
            await ctx.reply("Reloaded.")

        else:
            await ctx.reply(f"・読み上げ機能\nエラー：書き方が間違っています。\n\n`{ctx.prefix}tts join`: 参加\n`{ctx.prefix}tts leave`: 退出\n`{ctx.prefix}tts voice`: 声選択")


    #@nextcord.message_command(name="メッセージを読み上げる")
    async def speak_message(self, interaction: Interaction, message: nextcord.Message):
        await interaction.response.defer(ephemeral=True)
        try:
            if interaction.user.voice is None:
                await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="先にボイスチャンネルに接続してください。", color=0xff0000))
                return
            else:
                if interaction.guild.voice_client is None:
                    await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="にらBOTがボイスチャンネルに接続されていません。", color=0xff0000))
                    return

                if message.content == "" or message.content is None:
                    await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description="メッセージが空です。", color=0xff0000))
                    return
                if interaction.user.id not in self.SPEAKER_AUTHOR:
                    self.SPEAKER_AUTHOR[interaction.user.id] = "2"
                    asyncio.ensure_future(self.collection.update_one({"user_id": interaction.user.id, "type": "speaker"}, {"$set": {"speaker": "2"}}, upsert=True))
                if interaction.guild.voice_client.is_playing():
                    while True:
                        if interaction.guild.voice_client.is_playing():
                            await asyncio.sleep(0.1)
                        else:
                            break
                await interaction.followup.send(embed=nextcord.Embed(title="TTS", description=f"```\n{message.content}```\nを読み上げます...", color=0x00ff00))
                interaction.guild.voice_client.play(
                    nextcord.PCMVolumeTransformer(
                        nextcord.FFmpegPCMAudio(
                            self.get_speak_url(message.content, self.SPEAKER_AUTHOR[interaction.user.id], interaction.guild.id)
                        ),
                        volume=0.5
                    )
                )
                return
        except Exception as err:
            await interaction.followup.send(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
            logging.error(traceback.format_exc())
            return

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if (
            message.guild is None or
            message.author.bot or
            message.content is None or
            message.content == "" or
            message.guild.id not in self.TTS_CHANNEL or
            message.channel.id != self.TTS_CHANNEL[message.guild.id] or
            getattr(message.guild, 'voice_client', None) is None or
            isinstance(self.bot.command_prefix, str) and message.content.startswith(self.bot.command_prefix) or
            isinstance(self.bot.command_prefix, list) and any([message.content.startswith(prefix) for prefix in self.bot.command_prefix])
        ):
            return

        try:
            if message.author.id not in self.SPEAKER_AUTHOR:
                self.SPEAKER_AUTHOR[message.author.id] = 2
                asyncio.ensure_future(self.collection.update_one({"user_id": message.author.id, "type": "speaker"}, {"$set": {"speaker": 2}}, upsert=True))
            if not isinstance(message.guild.voice_client, nextcord.VoiceClient):
                return
            if message.guild.voice_client.is_playing():
                while True:
                    if message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.1)
                    else:
                        break
            message.guild.voice_client.play(
                nextcord.PCMVolumeTransformer(
                    nextcord.FFmpegPCMAudio(
                        self.get_speak_url(message.content, self.SPEAKER_AUTHOR[message.author.id], message.guild.id)
                    ),
                    volume=0.5
                )
            )
        except Exception as err:
            await message.channel.send(embed=nextcord.Embed(title="TTSエラー", description=f"```{err}```\n```sh\n{traceback.format_exc()}```", color=0xff0000))
            logging.error(traceback.format_exc())
            return


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
        if member == self.bot.user:
            # にらBOTに関するイベント
            assert isinstance(after, nextcord.VoiceState)
            if after.channel is None:
                # ユーザー切断時
                return
            if self.bot.user in after.channel.members and after.mute:
                # ミュートにされているため、ミュートを解除する
                try:
                    await member.edit(mute=False)
                    if member.guild.id in self.TTS_CHANNEL:
                        channel = await self.bot.resolve_channel(self.TTS_CHANNEL[member.guild.id])
                        await channel.send(embed=nextcord.Embed(title="なんでそんなことするの！", description="呼吸できなくて死ぬかと思ったわ！！！\nお願いやからサーバーミュートとかしないでくれたまえ！！！", color=self.bot.color.YELLOW))
                except (nextcord.Forbidden, nextcord.HTTPException):
                    # サーバーミュートを外す権限がない場合
                    if member.guild.id in self.TTS_CHANNEL:
                        channel = await self.bot.resolve_channel(self.TTS_CHANNEL[member.guild.id])
                        await channel.send(embed=nextcord.Embed(title="...", description="（どうやら喋れないらしい。\nサーバーミュートになっていないかご確認ください。）", color=self.bot.color.YELLOW))
                except AttributeError:
                    # メッセージを送信できないタイプのチャンネルだった場合
                    pass
        else:
            # にらBOT以外のイベント
            if member.guild.voice_client is None:
                # そもそもBOTがVCに接続していない場合
                return
            assert isinstance(member.guild.voice_client, nextcord.VoiceClient)

            if before.channel is None:
                # ユーザー接続時
                return

            assert isinstance(member.guild.voice_client.channel, (nextcord.VoiceChannel, nextcord.StageChannel))
            if len(member.guild.voice_client.channel.members) == 1:
                await member.guild.voice_client.disconnect()
                if member.guild.id in self.TTS_CHANNEL:
                    channel_id = self.TTS_CHANNEL[member.guild.id]
                    del self.TTS_CHANNEL[member.guild.id]
                    await self.collection.delete_one({"guild_id": member.guild.id, "type": "channel"})
                    message_channel = await self.bot.resolve_channel(channel_id)
                    assert isinstance(message_channel, nextcord.TextChannel)
                    await message_channel.send(embed=nextcord.Embed(title="TTS", description="誰もいなくなったため切断しました。", color=0x00ff00))
                    return



def setup(bot, **kwargs):
    bot.add_cog(Text2Speech(bot, **kwargs))
