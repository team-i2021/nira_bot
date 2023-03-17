import asyncio
import dataclasses
import logging
from collections.abc import Callable, Coroutine
from enum import Enum, auto
from typing import Any, AsyncGenerator, TypeGuard
from typing_extensions import Self

import nextcord
from nextcord import Interaction
from nextcord.ext import application_checks, commands

from util import admin_check, n_fc
from util.nira import NIRA

# ボトムアップ的な機能

COLLECTION_NAME = 'bottom_up'

FIRST_SLEEP = 3
SECOND_SLEEP = 2
SLEEP_COUNT = 2

MAX_LENGTH = 2000

AsyncIOMotorCollection = Any

glock = asyncio.Lock()


# typing には交差型が無いなんて...
class MessageableGuildChannel(nextcord.abc.Messageable, nextcord.abc.GuildChannel):
    @classmethod
    def isinstance(cls, instance: Any) -> TypeGuard[Self]:
        return all(isinstance(instance, c) for c in cls.__bases__)


class Mode(Enum):
    ON = auto()
    OFF = auto()


@dataclasses.dataclass
class _StoredPinDocument:
    _id: int  # to store channel id; it is unique
    text: str
    last_message_id: int | None = None

    @classmethod
    def bind(cls, document: dict | None) -> Self | None:
        if document is None:
            return None
        # TODO: 型チェック…？ 自前で実装したくはないから Pydantic あたりを使いたいが…
        # データベース周りだから念の為にもやっておきたいなぁ…
        return cls(**document)


class StoredPin:
    def __init__(
            self,
            collection: AsyncIOMotorCollection,
            channel: MessageableGuildChannel,
            text: str,
            last_message: nextcord.Message | None = None,
    ) -> None:
        self._collection = collection
        self._channel = channel
        self._text = text
        self._last_message = last_message

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self._collection

    @property
    def channel(self) -> MessageableGuildChannel:
        return self._channel

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text_setter(self, text: str) -> None:
        self.set_text(text)

    @property
    def last_message(self) -> nextcord.Message | None:
        return self._last_message

    @last_message.setter
    def last_message_setter(self, message: nextcord.Message | None) -> None:
        self.set_last_message(message)

    def set_text(self, text: str) -> Self:
        self._text = text
        return self

    def set_last_message(self, message: nextcord.Message | None) -> Self:
        self._last_message = message
        return self

    async def update(self) -> Self:
        doc = _StoredPinDocument(
            _id=self._channel.id,
            text=self._text,
            last_message_id=getattr(self._last_message, 'id', None),
        )

        await self._collection.replace_one({'_id': doc._id}, dataclasses.asdict(doc), upsert=True)
        return self

    async def clear(self) -> Self:
        self._last_message = None
        if self._channel is not None:
            await self._collection.delete_one({'_id': self._channel.id})

        return self


class StoredPinCollection:
    def __init__(self, bot: NIRA) -> None:
        self._bot = bot
        self._collection: AsyncIOMotorCollection = bot.database[COLLECTION_NAME]

    def new(self, channel: MessageableGuildChannel, text: str) -> StoredPin:
        return StoredPin(self._collection, channel, text, None)

    async def get(self, channel: MessageableGuildChannel) -> StoredPin | None:
        doc = _StoredPinDocument.bind(
            await self._collection.find_one({'_id': channel.id}),
        )
        if doc is None:
            return None

        return await self._doc_to_storedpin(channel, doc)

    async def get_all(self) -> AsyncGenerator[StoredPin | Exception, None]:
        async for doc_raw in self._collection.find({'_id': {'$type': ['int', 'long']}}):
            doc = _StoredPinDocument.bind(doc_raw)
            assert doc is not None

            channel = self._bot.get_channel(doc._id)
            if channel is None or isinstance(channel, nextcord.PartialMessageable):
                try:
                    channel = await self._bot.fetch_channel(doc._id)
                except (nextcord.NotFound, nextcord.Forbidden):
                    continue
                except Exception as e:
                    yield e
                    continue

            if not MessageableGuildChannel.isinstance(channel):
                continue

            yield await self._doc_to_storedpin(channel, doc)

    async def _doc_to_storedpin(
            self,
            channel: MessageableGuildChannel,
            doc: _StoredPinDocument,
    ) -> StoredPin:
        text = doc.text
        last_message: nextcord.Message | None = None
        if doc.last_message_id is not None:
            try:
                msg = await channel.fetch_message(doc.last_message_id)
            except (nextcord.NotFound, nextcord.Forbidden):
                pass
            else:
                last_message = msg

        return StoredPin(self._collection, channel, text, last_message)


class PinLock:
    def __init__(self):
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


def err_embed(description: str) -> nextcord.Embed:
    return nextcord.Embed(title="エラー", description=description, color=0xff0000)


class BottomUp(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self.collection = StoredPinCollection(bot)
        self._locks: dict[int, PinLock] = {}

    async def _pin(
            self,
            mode: Mode,
            channel: MessageableGuildChannel,
            message: str | None = None,
    ) -> tuple[str | None, nextcord.Embed | None]:
        async with glock:
            pass

        guild = channel.guild

        match mode:
            case Mode.ON:
                if not message:
                    return (None, err_embed("メッセージ本文がありません。"))
                elif len(message) > MAX_LENGTH:
                    return (None, err_embed(f"文字数は{MAX_LENGTH}文字以下である必要があります。"))

                async with self._get_lock(channel.id).save:
                    await self.collection.new(channel, message).update()

                return (
                    "メッセージを設定しました。",
                    nextcord.Embed(title="ピン留め", description=message),
                )

            case Mode.OFF:
                lock = self._get_lock(channel.id)
                async with lock.save:
                    store = await self.collection.get(channel)
                    if store is None:
                        return (None, err_embed("このチャンネルにはメッセージが設定されていません。"))

                    last_msg = store.last_message
                    failed = False
                    if last_msg is not None:
                        try:
                            await last_msg.delete()
                        except nextcord.NotFound:
                            pass
                        except nextcord.Forbidden:
                            failed = True
                    await store.clear()
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
        aliases=("Pin", "bottomup", "ピン留め", "ピン"),
        help="""\
特定のメッセージを一番下に持ってくることで、いつでも見られるようにする、ピン留めの改良版。

`n!pin on [メッセージ内容...(複数行可)]`

他の誰かがメッセージを送った場合、どんどんどんどんその特定のメッセージを送ると言うような感じの機能です。
Webhookは使いたくない精神なので、にらBOTが直々に送ってあげます。感謝しなさい。

offにするには、`n!pin off`と送信してください。

前に送ったピンメッセージが削除されずに送信されて、残っている場合は、にらBOTに適切な権限が与えられているか確認してみてください。
もしくは、周期内にめちゃくちゃメッセージを送信された場合はメッセージが削除されないかもしれません。仕様です。許してヒヤシンス。""",
        invoke_without_command=True,
    )
    @admin_check.admin_only_cmd()
    @commands.guild_only()
    async def pin_c(self, ctx: commands.Context, *args) -> None:
        await ctx.reply(embed=err_embed(
            ("不明なサブコマンドです。" if args else "サブコマンドがありません。")
            + f"\n`{ctx.prefix}help pin`で使い方を確認してください。",
        ))

    @pin_c.command(name="on")
    @admin_check.admin_only_cmd()
    @commands.guild_only()
    async def pin_on_c(self, ctx: commands.Context, *, message: str) -> None:
        res = await self._pin(Mode.ON, ctx.channel, message)
        if res[0] is not None:
            res = (res[0], None)
        await ctx.reply(res[0], embed=res[1])

    @pin_c.command(name="off")
    @admin_check.admin_only_cmd()
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

        if not MessageableGuildChannel.isinstance(channel):
            await ctx.reply("Not messageable guild channel")
            return
        elif await self.collection.get(channel) is None:
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

    @nextcord.message_command(
        name="Set BottomPin",
        name_localizations={nextcord.Locale.ja: "下部ピン留めする"},
        guild_ids=n_fc.GUILD_IDS,
    )
    @admin_check.admin_only_app()
    @application_checks.guild_only()
    async def pin_m(self, interaction: Interaction, message: nextcord.Message) -> None:
        await interaction.response.defer(ephemeral=True)
        res = await self._pin(Mode.ON, interaction.channel, message.content)
        await interaction.send(res[0], embed=res[1], ephemeral=True)
        if res[0] is not None:
            await self._refresh_channel(interaction.channel)

    @nextcord.slash_command(name="pin", description="BottomUp command", guild_ids=n_fc.GUILD_IDS)
    @admin_check.admin_only_app()
    @application_checks.guild_only()
    async def pin_s(self, interaction: Interaction) -> None:
        pass

    @pin_s.subcommand(
        name="on",
        description="Turn ON the bottom pin message",
        description_localizations={nextcord.Locale.ja: "下部ピン留めをONにする"},
    )
    @admin_check.admin_only_app()
    @application_checks.guild_only()
    async def pin_on_s(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(BottomModal(self))

    @pin_s.subcommand(
        name="off",
        description="Turn OFF the bottom pin message",
        description_localizations={nextcord.Locale.ja: "下部ピン留めをOFFにする"},
    )
    @admin_check.admin_only_app()
    @application_checks.guild_only()
    async def pin_off_s(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        res = await self._pin(Mode.OFF, interaction.channel)
        await interaction.send(res[0], embed=res[1], ephemeral=True)

    def _get_lock(self, ch_id: int) -> PinLock:
        if ch_id not in self._locks:
            self._locks[ch_id] = PinLock()
        return self._locks[ch_id]

    async def _send_msg(self, store: StoredPin) -> bool:
        try:
            msg = await store.channel.send(store.text)
        except Exception as e:
            if isinstance(e, nextcord.Forbidden):
                logging.exception("Error while sending message")
            return False

        try:
            await store.set_last_message(msg).update()
        except Exception:
            logging.exception("Error while updating database")

        return True

    async def _del_msg(self, store: StoredPin) -> bool:
        if store.last_message is None:
            return True

        try:
            await store.last_message.delete()
        except (nextcord.NotFound, nextcord.Forbidden):
            pass
        except Exception:
            logging.exception("Error while deleting message")
            return False

        try:
            await store.set_last_message(None).update()
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

            store = await self.collection.get(ch)
            if store is None:
                return
            elif (last_message is None
                  or last_message != store.last_message and await self._del_msg(store)):
                await self._send_msg(store)
                await lock.sleep_lock(FIRST_SLEEP, SECOND_SLEEP)

    async def _refresh_messages(self) -> None:
        async with glock:
            async for store in self.collection.get_all():
                if isinstance(store, StoredPin):
                    await self._refresh_channel(store.channel)
                else:
                    logging.exception("Error while fetching channel", exc_info=store)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._refresh_messages()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message) -> None:
        async with glock:
            pass

        channel = message.channel
        if message.flags.ephemeral or not MessageableGuildChannel.isinstance(channel):
            return

        lock = self._get_lock(channel.id)
        async with lock.save:
            store = await self.collection.get(channel)
            if store is None:
                return

            last_message = store.last_message
            if message == last_message:
                return

            lock.count += 1
            if lock.sleep.locked():
                if not lock.callback:
                    lock.set_callback(self._refresh_channel, channel)
                return

            if await self._del_msg(store):
                await self._send_msg(store)
                await lock.sleep_lock(FIRST_SLEEP, SECOND_SLEEP)


class BottomModal(nextcord.ui.Modal):
    def __init__(self, cog: BottomUp):
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
        res = await self.cog._pin(Mode.ON, interaction.channel, self.mes.value)
        await interaction.send(res[0], embed=res[1], ephemeral=True)
        if res[0] is not None:
            await self.cog._refresh_channel(interaction.channel)


def setup(bot) -> None:
    bot.add_cog(BottomUp(bot))


def teardown(bot) -> None:
    print("Pin: teardown!")
