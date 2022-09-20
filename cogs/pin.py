import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import Enum, auto
from typing import Any

import HTTP_db
import nextcord
from nextcord import Interaction
from nextcord.ext import application_checks, commands

from util import admin_check, n_fc, database
from util.nira import NIRA

# ボトムアップ的な機能

FIRST_SLEEP = 3
SECOND_SLEEP = 2
SLEEP_COUNT = 2
MAX_LENGTH = 2000

glock = asyncio.Lock()


# typing には交差型が無いなんて...
class MessageableGuildChannel(nextcord.abc.Messageable, nextcord.abc.GuildChannel):
    pass


class Mode(Enum):
    ON = auto()
    OFF = auto()


class PinData:
    name = "bottom_up"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE


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
        finally:
            if self.count < SLEEP_COUNT:
                self.sleep.release()
                self.count = 0
                if self.callback:
                    await self.callback[0](*self.callback[1])
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


async def update(
        client: HTTP_db.Client,
        channel: MessageableGuildChannel,
        data: list[str, int | None] | None,
) -> None:
    guild = channel.guild

    if data is None:
        try:
            del PinData.value[guild.id][channel.id]
            if not PinData.value[guild.id]:
                del PinData.value[guild.id]
        except KeyError:
            pass
    else:
        PinData.value.update({guild.id: {channel.id: data}})

    await database.default_push(client, PinData)


async def pull_data(client: HTTP_db.Client) -> None:
    async with glock:
        await database.default_pull(client, PinData)


async def update_database(bot: NIRA) -> None:
    await glock.acquire()
    await database.default_pull(bot.client, PinData)

    await bot.wait_until_ready()
    logging.info("Updating database format")

    count = 0
    new_data: dict[int, dict[int, list[str, int | None]]] = {}
    for guild_id, _g in PinData.value.items():
        new_data[guild_id] = {}
        for ch_id, data in _g.items():
            if type(data) is list:
                new_data[guild_id][ch_id] = data
                continue
            elif type(data) is not str:
                logging.info(f"Incorrect data found on channel {ch_id}")
                continue

            logging.debug(f"Updating data for channel: {ch_id}")

            failed = True
            ch = bot.get_channel(ch_id)
            if ch is None:
                try:
                    ch = await bot.fetch_channel(ch_id)
                except (nextcord.NotFound, nextcord.Forbidden):
                    pass
                except Exception:
                    logging.exception("Error while searching for a channel")
                else:
                    failed = False
            else:
                failed = False

            last_id: int | None = None
            if not failed:
                failed = True
                try:
                    async for msg in ch.history(limit=10):
                        if msg.author.id == bot.user.id and msg.content == data:
                            last_id = msg.id
                            break
                except nextcord.Forbidden:
                    pass
                except Exception:
                    logging.exception("Error while fetching message history")
                else:
                    failed = False

            new_data[guild_id][ch_id] = [data, None if failed else last_id]
            count += 1

        if not new_data[guild_id]:
            del new_data[guild_id]

    PinData.value = new_data
    try:
        await database.default_push(bot.client, PinData)
    finally:
        glock.release()

    if count:
        logging.info(f"Updated data for {count} channel(s)")
    logging.info("Update successfully")


def err_embed(description: str) -> nextcord.Embed:
    return nextcord.Embed(title="エラー", description=description, color=0xff0000)


class BottomUp(commands.Cog):
    def __init__(self, bot: NIRA):
        self.bot = bot
        self._locks: dict[int, PinLock] = {}
        asyncio.ensure_future(update_database(bot))
        # asyncio.ensure_future(pull_data(bot.client))

    async def _pin(
            self,
            mode: Mode,
            author: nextcord.Member | nextcord.User,
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
                    await update(self.bot.client, channel, [message, None])

                return (
                    "メッセージを設定しました。",
                    nextcord.Embed(title="ピン留め", description=message),
                )

            case Mode.OFF:
                if guild.id not in PinData.value or channel.id not in PinData.value[guild.id]:
                    return (None, err_embed("このチャンネルにはメッセージが設定されていません。"))

                async with self._get_lock(channel.id).save:
                    last_id = PinData.value[guild.id][channel.id][1]
                    failed = False
                    await update(self.bot.client, channel, None)
                    if last_id is not None:
                        try:
                            await (await channel.fetch_message(last_id)).delete()
                        except nextcord.NotFound:
                            pass
                        except nextcord.Forbidden:
                            failed = True
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
        res = await self._pin(Mode.ON, ctx.author, ctx.channel, message)
        if res[0] is not None:
            res = (res[0], None)
        await ctx.reply(res[0], embed=res[1])

    @pin_c.command(name="off")
    @admin_check.admin_only_cmd()
    @commands.guild_only()
    async def pin_off_c(self, ctx: commands.Context) -> None:
        res = await self._pin(Mode.OFF, ctx.author, ctx.channel)
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
            ch: nextcord.abc.GuildChannel | None = None,
    ) -> None:
        if isinstance(ch, nextcord.abc.Messageable):
            if ch.guild.id in PinData.value and ch.id in PinData.value[ch.guild.id]:
                msg = await ctx.reply(f"Refreshing {ch.id}...")
                await self._refresh_channel(ch)
                await msg.edit("Refresh finished.")
            else:
                await ctx.reply(f"{ch.id}: Not configured")
        elif ch:
            await ctx.reply(f"{ch.id}: Not messageable")
        else:
            msg = await ctx.reply("Refreshing...")
            await self._refresh_messages()
            await msg.edit("Refresh finished.")

    @pin_debug_c.command(name="lock")
    @commands.is_owner()
    async def pin_debug_lock_c(
            self,
            ctx: commands.Context,
            ch: nextcord.abc.GuildChannel | None = None,
            force_unlock: bool = False,
    ) -> None:
        if isinstance(ch, nextcord.abc.Messageable):
            if ch.id in self._locks:
                lock = self._locks[ch.id]
                await ctx.reply(
                    f"ID {ch.id}\n"
                    f"Save: {lock.save.locked()}\n"
                    f"Sleep: {lock.sleep.locked()}\n"
                    f"Count: {lock.count}\n"
                    f"Callback: {'Set' if lock.callback else 'None'}",
                )
                if force_unlock:
                    lock.sleep_unlock()
            else:
                await ctx.reply(f"{ch.id}: Not set")
        elif ch:
            await ctx.reply(f"{ch.id}: Not messageable")
        else:
            await ctx.reply(f"glock: {glock.locked()}")
            if force_unlock and glock.locked():
                glock.release()

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
        res = await self._pin(Mode.ON, interaction.user, interaction.channel, message.content)
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
        res = await self._pin(Mode.OFF, interaction.user, interaction.channel)
        await interaction.send(res[0], embed=res[1], ephemeral=True)

    def _get_lock(self, ch_id: int) -> PinLock:
        if ch_id not in self._locks:
            self._locks[ch_id] = PinLock()
        return self._locks[ch_id]

    async def _send_msg(self, ch: MessageableGuildChannel) -> bool:
        msg = PinData.value[ch.guild.id][ch.id][0]
        msg_id = None
        try:
            msg_id = (await ch.send(msg)).id
        except nextcord.Forbidden:
            return False
        except Exception:
            logging.exception("Error while sending message")
            return False

        try:
            await update(self.bot.client, ch, [msg, msg_id])
        except Exception:
            logging.exception("Error while updating database")

        return True

    async def _del_msg(self, ch: MessageableGuildChannel) -> bool:
        data = PinData.value[ch.guild.id][ch.id]
        if data[1] is None:
            return True

        try:
            await (await ch.fetch_message(data[1])).delete()
        except (nextcord.NotFound, nextcord.Forbidden):
            pass
        except Exception:
            logging.exception("Error while deleting message")
            return False

        data[1] = None
        try:
            await update(self.bot.client, ch, data)
        except Exception:
            logging.exception("Error while updating database")

        return True

    async def _refresh_channel(self, ch: MessageableGuildChannel) -> None:
        lock = self._get_lock(ch.id)
        async with lock.save:
            last_msg = None
            try:
                last_msg = (await ch.history(limit=1).flatten())[0]
            except IndexError:
                pass
            except nextcord.Forbidden:
                return
            except Exception:
                logging.exception("Error while fetching message history")
                return

            if lock.sleep.locked():
                return

            last_id = PinData.value[ch.guild.id][ch.id][1]
            if last_msg is None or last_msg.id != last_id and await self._del_msg(ch):
                await self._send_msg(ch)
                await lock.sleep_lock(FIRST_SLEEP, SECOND_SLEEP)

    async def _refresh_messages(self) -> None:
        async with glock:
            for _g in PinData.value.values():
                for ch_id, data in _g.items():
                    ch = self.bot.get_channel(ch_id)
                    if ch is None:
                        try:
                            ch = await self.bot.fetch_channel(ch_id)
                        except (nextcord.NotFound, nextcord.Forbidden):
                            continue
                        except Exception:
                            logging.exception("Error while searching for a channel")
                            continue

                    await self._refresh_channel(ch)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._refresh_messages()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message) -> None:
        async with glock:
            pass

        ch = message.channel
        if (message.flags.ephemeral
                or not hasattr(ch, "guild")
                or message.guild.id not in PinData.value
                or ch.id not in PinData.value[message.guild.id]):
            return

        lock = self._get_lock(ch.id)
        async with lock.save:
            last_id = PinData.value[ch.guild.id][ch.id][1]
            if message.id == last_id:
                return

            lock.count += 1
            if lock.sleep.locked():
                if not lock.callback:
                    lock.set_callback(self._refresh_channel, ch)
                return

            if await self._del_msg(ch):
                await self._send_msg(ch)
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
        res = await self.cog._pin(Mode.ON, interaction.user, interaction.channel, self.mes.value)
        await interaction.send(res[0], embed=res[1], ephemeral=True)
        if res[0] is not None:
            await self.cog._refresh_channel(interaction.channel)


def setup(bot) -> None:
    bot.add_cog(BottomUp(bot))


def teardown(bot) -> None:
    print("Pin: teardown!")
