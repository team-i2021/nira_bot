import asyncio
import logging
from collections.abc import Callable, Coroutine, Mapping
from enum import Enum, auto
from typing import Any, Final

import nextcord
from cachetools import TTLCache
from nextcord import Embed, Interaction, Message, Locale
from nextcord.ext import application_checks, commands
from typing_extensions import Self

from util import n_fc
from util.botdatabase import UniqueChannelCollection, UniqueChannelDocument
from util.nira import NIRA
from util.typing import MessageableGuildChannel

# 下部ピン留め

COLLECTION_NAME: Final = "bottom_pin"
CACHE_MAX_SIZE: Final = 1024
CACHE_TTL: Final = 43200  # 12 hours

FIRST_SLEEP: Final = 3
SECOND_SLEEP: Final = 2
SLEEP_COUNT: Final = 2

MAX_LENGTH: Final = 2000

glock = asyncio.Lock()


class Mode(Enum):
    ON = auto()
    OFF = auto()


class PinDocument(UniqueChannelDocument[MessageableGuildChannel]):
    text: str
    last_message: nextcord.Message | None = None

    async def encode(self) -> dict[str, Any]:
        doc = await super().encode()
        doc["last_message"] = self.last_message.id if self.last_message else None
        return doc

    @classmethod
    async def decode(cls, bot: NIRA, raw: Mapping[str, Any]) -> Self:
        if (message_id := raw.get("last_message")) is not None:
            channel, doc = await cls.resolve_primary(bot, raw)

            message_id = int(message_id)
            try:
                message = await channel.fetch_message(message_id)
            except (nextcord.NotFound, nextcord.Forbidden):
                message = None

            doc["last_message"] = message
        else:
            doc = raw
        return await super().decode(bot, doc)


class PinLock:
    def __init__(self) -> None:
        self.save = asyncio.Lock()
        self.sleep = asyncio.Lock()
        self.count = 0
        self.callback: tuple[Callable[..., Coroutine[Any, Any, Any]], tuple] | None = None
        self._task: asyncio.Task | None = None

    async def _run(self, delay: int, next_delay: int) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            self.callback = None
        finally:
            if self.count < SLEEP_COUNT:
                self.sleep.release()
                self.count = 0
                if self.callback:
                    try:
                        await self.callback[0](*self.callback[1])
                    finally:
                        self.callback = None
            else:
                self.count = SLEEP_COUNT - 1
                self._task = asyncio.create_task(self._run(next_delay, next_delay))

    async def sleep_lock(self, delay: int, next_delay: int) -> None:
        if not self.sleep.locked():
            await self.sleep.acquire()
            self._task = asyncio.create_task(self._run(delay, next_delay))

    def sleep_unlock(self) -> None:
        self.count = 0
        if self._task is not None and not self._task.cancelled():
            self._task.cancel()

    def set_callback(self, func: Callable[..., Coroutine[Any, Any, Any]], *args) -> None:
        self.callback = (func, args)


def err_embed(description: str) -> Embed:
    return Embed(title="エラー", description=description, color=0xff0000)


class BottomPin(commands.Cog):
    def __init__(self, bot: NIRA) -> None:
        self.bot = bot
        self.collection = UniqueChannelCollection(
            bot,
            bot.database[COLLECTION_NAME],
            PinDocument,
            TTLCache(CACHE_MAX_SIZE, CACHE_TTL),
        )
        self._locks: dict[int, PinLock] = {}

    async def _pin(
            self,
            mode: Mode,
            channel: nextcord.abc.GuildChannel
            | nextcord.PartialMessageable
            | nextcord.abc.Messageable,
            message: str | None = None,
    ) -> tuple[str, Embed | Any] | tuple[None, Embed]:
        async with glock:
            pass

        if not isinstance(channel, MessageableGuildChannel):
            return (None, err_embed("下部ピン留めはスレッドでは使用できません。"))

        match mode:
            case Mode.ON:
                if not message:
                    return (None, err_embed("メッセージ本文がありません。"))
                elif len(message) > MAX_LENGTH:
                    return (None, err_embed(f"文字数は{MAX_LENGTH}文字以下である必要があります。"))

                async with self._get_lock(channel.id).save:
                    document = self.collection.new(channel, text=message)
                    await self.collection.update(document)

                return ("メッセージを設定しました。", Embed(title="ピン留め", description=message))

            case Mode.OFF:
                lock = self._get_lock(channel.id)
                async with lock.save:
                    document = await self.collection.get(channel.id)
                    if document is None:
                        return (None, err_embed("このチャンネルにはメッセージが設定されていません。"))

                    last_msg = document.last_message
                    failed = False
                    if last_msg is not None:
                        try:
                            await last_msg.delete()
                        except nextcord.NotFound:
                            pass
                        except nextcord.Forbidden:
                            failed = True
                    await self.collection.delete(document)
                    self.collection.uncache(channel.id)
                    lock.sleep_unlock()
                    del self._locks[channel.id]

                return (
                    "登録を解除しました。" if not failed else
                    "登録は解除しましたが、送信したメッセージを削除できませんでした。\n"
                    "お手数ですが手動で削除してください。",
                    None,
                )

    @commands.group(
        name="pin",
        aliases=("Pin", "bottomup", "bottompin", "ピン留め", "ピン"),
        help="""\
特定のメッセージを一番下に持ってくることで、いつでも見られるようにする、ピン留めの改良版。

```n!pin on [メッセージ内容...(複数行可)]```

他の誰かがメッセージを送った場合、どんどんどんどんその特定のメッセージを送ると言うような感じの機能です。
Webhookは使いたくない精神なので、にらBOTが直々に送ってあげます。感謝しなさい。

設定を解除するには、`n!pin off`と送信してください。
この直後に、ピンメッセージを送信してすぐに消すという動作をすることがあります。仕様です。許してヒヤシンス。

メッセージを送信した時に前のピンメッセージが削除されない場合は、にらBOTに適切な権限が付与されていない可能性があります。
メッセージ履歴の閲覧が許可されているか確認してください。""",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def pin_c(self, ctx: commands.Context, *args) -> None:
        await ctx.reply(embed=err_embed(
            ("不明なサブコマンドです。" if args else "サブコマンドがありません。")
            + f"\n`{ctx.prefix}help pin`で使い方を確認してください。",
        ))

    @pin_c.command(name="on")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def pin_on_c(self, ctx: commands.Context, *, message: str) -> None:
        res = await self._pin(Mode.ON, ctx.channel, message)
        if res[0] is not None:
            res = (res[0], None)
        await ctx.reply(res[0], embed=res[1])

    @pin_c.command(name="off")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def pin_off_c(self, ctx: commands.Context) -> None:
        res = await self._pin(Mode.OFF, ctx.channel)
        await ctx.reply(res[0], embed=res[1])

    @pin_c.group(name="debug", invoke_without_command=True)
    @commands.is_owner()
    async def pin_debug_c(self, ctx: commands.Context, *args) -> None:
        await ctx.reply("Unknown operation" if args else "Operation not specified")

    @pin_debug_c.command(name="refresh")
    @commands.is_owner()
    async def pin_debug_refresh_c(
            self,
            ctx: commands.Context,
            ch_id: int | None = None,
    ) -> None:
        if ch_id is None:
            msg = await ctx.reply("Refreshing...")
            await self._refresh_messages()
            await msg.edit(content="Refresh finished.")
            return

        channel = self.bot.get_channel(ch_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(ch_id)
            except nextcord.NotFound:
                await ctx.reply("Channel not found")
                return
            except nextcord.Forbidden:
                await ctx.reply("Permission denied")
                return

        if not isinstance(channel, MessageableGuildChannel):
            await ctx.reply("Not messageable guild channel")
            return
        elif await self.collection.get(channel.id) is None:
            await ctx.reply("Not configured")
            return

        msg = await ctx.reply(f"Refreshing {ch_id}...")
        await self._refresh_channel(channel)
        await msg.edit(content="Refresh finished.")

    @pin_debug_c.command(name="lock")
    @commands.is_owner()
    async def pin_debug_lock_c(
            self,
            ctx: commands.Context,
            ch_id: int | None = None,
            force_unlock: bool = False,
    ) -> None:
        if ch_id is None:
            await ctx.reply(f"glock: {glock.locked()}")
            if force_unlock and glock.locked():
                glock.release()
        elif ch_id in self._locks:
            lock = self._locks[ch_id]
            await ctx.reply(
                f"Save: {lock.save.locked()}\n"
                f"Sleep: {lock.sleep.locked()}\n"
                f"Count: {lock.count}\n"
                f"Callback: {'Set' if lock.callback else 'None'}",
            )
            if force_unlock:
                lock.sleep_unlock()
        else:
            await ctx.reply("Not set")

        if force_unlock:
            await ctx.reply("Unlocked.")

    @pin_debug_c.group(name="cache", invoke_without_command=True)
    @commands.is_owner()
    async def pin_debug_cache_c(self, ctx: commands.Context, *args) -> None:
        await ctx.reply("Unknown operation" if args else "Operation not specified")

    @pin_debug_cache_c.command(name="info")
    @commands.is_owner()
    async def pin_debug_cache_info_c(
            self,
            ctx: commands.Context,
            channel_id: int | None = None,
    ) -> None:
        cache = self.collection.cache
        assert isinstance(cache, TTLCache)
        if channel_id is None:
            msg = (
                f"Channels: {cache.currsize}\n"
                f"Max: {cache.maxsize}\n"
                f"TTL: {cache.ttl}s"
            )
        else:
            msg = "Cached" if channel_id in cache else "Uncached"
        await ctx.reply(msg)

    @pin_debug_cache_c.command(name="clear")
    @commands.is_owner()
    async def pin_debug_cache_clear_c(
            self,
            ctx: commands.Context,
            channel_id: int | None = None,
    ) -> None:
        msg = await ctx.reply(
            f"Clearing cache{'' if channel_id is None else f' in {channel_id}'}...",
        )
        self.collection.uncache(channel_id)
        await msg.edit(content="Cache cleared.")

    @nextcord.message_command(
        name="Set BottomPin",
        name_localizations={Locale.ja: "下部ピン留めする"},
    )
    @application_checks.has_permissions(manage_messages=True)
    @application_checks.guild_only()
    async def pin_m(self, interaction: Interaction, message: Message) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.channel is not None
        res = await self._pin(Mode.ON, interaction.channel, message.content)
        await interaction.send(res[0], embed=res[1], ephemeral=True)
        if res[0] is not None:
            assert isinstance(interaction.channel, MessageableGuildChannel)
            await self._refresh_channel(interaction.channel)

    @nextcord.slash_command(name="pin", description="BottomPin command")
    @application_checks.has_permissions(manage_messages=True)
    @application_checks.guild_only()
    async def pin_s(self, _) -> None:
        pass

    @pin_s.subcommand(
        name="on",
        description="Turn ON the bottom pin message",
        description_localizations={Locale.ja: "下部ピン留めをONにする"},
    )
    @application_checks.has_permissions(manage_messages=True)
    @application_checks.guild_only()
    async def pin_on_s(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(BottomPinModal(self))

    @pin_s.subcommand(
        name="off",
        description="Turn OFF the bottom pin message",
        description_localizations={Locale.ja: "下部ピン留めをOFFにする"},
    )
    @application_checks.has_permissions(manage_messages=True)
    @application_checks.guild_only()
    async def pin_off_s(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.channel is not None
        res = await self._pin(Mode.OFF, interaction.channel)
        await interaction.send(res[0], embed=res[1], ephemeral=True)

    def _get_lock(self, ch_id: int) -> PinLock:
        if ch_id not in self._locks:
            self._locks[ch_id] = PinLock()
        return self._locks[ch_id]

    async def _send_msg(self, document: PinDocument) -> bool:
        try:
            msg = await document.channel.send(document.text)
        except Exception as e:
            if isinstance(e, nextcord.Forbidden):
                logging.exception("Error while sending message")
            return False

        try:
            document.last_message = msg
            await self.collection.update(document)
        except Exception:
            logging.exception("Error while updating database")

        return True

    async def _del_msg(self, document: PinDocument) -> bool:
        if document.last_message is None:
            return True

        try:
            await document.last_message.delete()
        except (nextcord.NotFound, nextcord.Forbidden):
            pass
        except Exception:
            logging.exception("Error while deleting message")
            return False

        try:
            document.last_message = None
            await self.collection.update(document)
        except Exception:
            logging.exception("Error while updating database")

        return True

    async def _refresh_channel(self, ch: MessageableGuildChannel) -> None:
        lock = self._get_lock(ch.id)
        async with lock.save:
            last_message = None
            try:
                last_message = (await ch.history(limit=1).flatten())[0]
            except IndexError:
                pass
            except nextcord.Forbidden:
                return
            except Exception:
                logging.exception("Error while fetching message history")
                return

            if lock.sleep.locked():
                return

            document = await self.collection.get(ch.id)
            if document is None:
                return
            elif (last_message is None
                  or last_message != document.last_message and await self._del_msg(document)):
                await self._send_msg(document)
                await lock.sleep_lock(FIRST_SLEEP, SECOND_SLEEP)

    async def _refresh_messages(self) -> None:
        async with glock:
            async for document in self.collection.get_all():
                if isinstance(document, PinDocument):
                    await self._refresh_channel(document.channel)
                else:
                    logging.exception("Error while fetching channel", exc_info=document)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._refresh_messages()

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        async with glock:
            pass

        channel = message.channel
        if message.flags.ephemeral or not isinstance(channel, MessageableGuildChannel):
            return

        lock = self._get_lock(channel.id)
        async with lock.save:
            document = await self.collection.get(channel.id)
            if document is None:
                return

            last_message = document.last_message
            if message == last_message:
                return

            lock.count += 1
            if lock.sleep.locked():
                if not lock.callback:
                    lock.set_callback(self._refresh_channel, channel)
                return

            if await self._del_msg(document):
                await self._send_msg(document)
                await lock.sleep_lock(FIRST_SLEEP, SECOND_SLEEP)


class BottomPinModal(nextcord.ui.Modal):
    def __init__(self, cog: BottomPin) -> None:
        super().__init__("下部ピン留め", timeout=None)

        self.cog = cog

        self.mes = nextcord.ui.TextInput(
            label="ピン留めしたい文章",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="このチャンネルでたくさん話したらずんだ餅にするよ！",
            min_length=1,
            max_length=MAX_LENGTH,
            required=True,
        )
        self.add_item(self.mes)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.channel is not None
        res = await self.cog._pin(Mode.ON, interaction.channel, self.mes.value)
        await interaction.send(res[0], embed=res[1], ephemeral=True)
        if res[0] is not None:
            assert isinstance(interaction.channel, MessageableGuildChannel)
            await self.cog._refresh_channel(interaction.channel)


def setup(bot: NIRA) -> None:
    bot.add_cog(BottomPin(bot))


def teardown(_) -> None:
    logging.info("Tearing down bottom pin")
