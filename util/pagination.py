"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from enum import Enum, auto

import nextcord
from nextcord import Interaction
from nextcord.ext import commands


class PaginatorButtonType(Enum):
    FIRST = auto()
    PREV = auto()
    INDICATOR = auto()
    NEXT = auto()
    LAST = auto()


class PaginatorButton(nextcord.ui.Button):
    def __init__(
            self,
            button_type: PaginatorButtonType,
            *,
            label: str | None = None,
            emoji: str | nextcord.Emoji | nextcord.PartialEmoji | None = None,
            style: nextcord.ButtonStyle = nextcord.ButtonStyle.green,
            disabled: bool = False,
            row: int | None = None,
    ):
        label_: str = button_type.name.title() if label is None else label

        super().__init__(
            label=label_,
            emoji=emoji,
            style=style,
            disabled=disabled,
            row=row,
        )

        self.button_type = button_type
        self.label = label_
        self.emoji = emoji
        self.style = style
        self.disabled = disabled
        self.paginator = None

    async def callback(self, interaction: Interaction) -> None:
        if self.button_type == PaginatorButtonType.FIRST:
            self.paginator.current_page = 0
        elif self.button_type == PaginatorButtonType.PREV:
            if self.paginator.loop_pages and self.paginator.current_page == 0:
                self.paginator.current_page = self.paginator.page_count
            else:
                self.paginator.current_page -= 1
        elif self.button_type == PaginatorButtonType.NEXT:
            if self.paginator.loop_pages and self.paginator.current_page == self.paginator.page_count:
                self.paginator.current_page = 0
            else:
                self.paginator.current_page += 1
        elif self.button_type == PaginatorButtonType.LAST:
            self.paginator.current_page = self.paginator.page_count

        await self.paginator.goto_page(self.paginator.current_page, interaction)


class Page:
    def __init__(
            self,
            title: str | tuple[nextcord.Emoji, str] | None = None,
            *,
            content: str | None = None,
            description: str | None = None,
            embeds: list[nextcord.Embed] | None = None,
            files: list[nextcord.File] | None = None,
            custom_view: nextcord.ui.View | None = None,
    ):
        if content is None and embeds is None:
            raise nextcord.InvalidArgument("A page cannot have both content and embeds equal to None")

        self.content = content
        self.title = title
        self.description = description
        self.embeds = embeds or []
        self.files = files or []
        self.custom_view = custom_view

    async def callback(self, interaction: Interaction | None = None):
        pass

    def update_files(self) -> list[nextcord.File] | None:
        for file in self.files:
            with open(file.fp.name, "rb") as fp:
                self._files[self.files.index(file)] = nextcord.File(
                    fp,
                    filename=file.filename,
                    description=file.description,
                    spoiler=file.spoiler,
                )
        return self.files


class Paginator(nextcord.ui.View):
    def __init__(
            self,
            pages: list[Page],
            *,
            show_disabled: bool = True,
            show_indicator: bool = True,
            show_menu: bool = False,
            menu_placeholder: str = "Select Page...",
            timeout: float | None = 600.0,
            disable_on_timeout: bool = True,
            use_default_buttons: bool = True,
            default_button_row: int = 0,
            custom_buttons: list[PaginatorButton] | None = None,
            custom_view: nextcord.ui.View | None = None,
            author_check: bool = True,
            loop_pages: bool = False,
            trigger_on_display: bool = False,
    ):
        if not all(isinstance(p, Page) for p in pages):
            raise TypeError("pages must be a list of Page objects")

        super().__init__(timeout=timeout)

        self.pages = pages
        self.show_disabled = show_disabled
        self.show_indicator = show_indicator
        self.show_menu = show_menu
        self.menu_placeholder = menu_placeholder
        self.disable_on_timeout = disable_on_timeout
        self.use_default_buttons = use_default_buttons
        self.default_button_row = default_button_row
        self.custom_buttons = custom_buttons
        self.custom_view = custom_view
        self.author_check = author_check
        self.loop_pages = loop_pages
        self.trigger_on_display = trigger_on_display

        self.message: nextcord.Message | nextcord.InteractionMessage | nextcord.WebhookMessage | None = None
        self.menu: PaginatorMenu | None = None
        self.buttons: dict[PaginatorButtonType, dict[str, PaginatorButton | bool]] = {}
        self.page_count = max(len(pages) - 1, 0)
        self.current_page = 0
        self.user: nextcord.User | nextcord.Member | None = None

        if self.use_default_buttons:
            self.add_default_buttons()
        elif self.custom_buttons:
            for button in custom_buttons:
                self.add_button(button)

        if self.show_menu:
            self.add_menu()

    async def update(
            self,
            interaction: Interaction,
            pages: list[Page] | None = None,
            *,
            trigger_on_display: bool | None = None,
    ) -> None:
        self.pages = self.pages if pages is None else pages
        self.trigger_on_display = \
            self.trigger_on_display if trigger_on_display is None else trigger_on_display
        self.page_count = max(len(self.pages) - 1, 0)
        self.current_page = 0

        await self.goto_page(self.current_page, interaction)

    async def on_timeout(self) -> None:
        if not self.disable_on_timeout or self.message is None:
            return

        for item in self.children:
            item.disabled = True

        page = self.pages[self.current_page]
        page = self.get_page_content(page)
        files = page.update_files()

        try:
            await self.message.edit(view=self, files=files or [], attachments=[])
        except nextcord.HTTPException:
            pass

    async def disable(
            self,
            include_custom: bool = False,
            page: Page | None = None,
    ) -> None:
        page = self.get_page_content(page)

        for item in self.children:
            if include_custom or not self.custom_view or item not in self.custom_view.children:
                item.disabled = True

        if page:
            await self.message.edit(content=page.content, embeds=page.embeds, view=self)
        else:
            await self.message.edit(view=self)

    async def cancel(
            self,
            include_custom: bool = False,
            page: Page | None = None,
    ) -> None:
        items = self.children.copy()
        page = self.get_page_content(page)

        for item in items:
            if include_custom or not self.custom_view or item not in self.custom_view.children:
                self.remove_item(item)

        if page:
            await self.message.edit(content=page.content, embeds=page.embeds, view=self)
        else:
            await self.message.edit(view=self)

    async def goto_page(
            self,
            page_number: int = 0,
            interaction: nextcord.Interaction | None = None,
    ) -> None:
        self.update_buttons()
        self.current_page = page_number
        if self.show_indicator:
            self.buttons[PaginatorButtonType.INDICATOR]["object"].label = \
                    f"{self.current_page + 1}/{self.page_count + 1}"

        page = self.pages[page_number]
        page = self.get_page_content(page)

        if page.custom_view:
            self.update_custom_view(page.custom_view)

        files = page.update_files()

        if interaction:
            await interaction.edit(
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )
        else:
            await self.message.edit(
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )

        if self.trigger_on_display:
            await self.page_action(interaction)

    async def interaction_check(self, interaction: Interaction) -> bool:
        return self.author_check or self.user == interaction.user

    def add_menu(self) -> None:
        self.menu = PaginatorMenu(self.pages, self.menu_placeholder)
        self.menu.paginator = self
        self.add_item(self.menu)

    def add_default_buttons(self) -> None:
        default_buttons = [
            PaginatorButton(
                PaginatorButtonType.FIRST,
                label="<<",
                style=nextcord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
            PaginatorButton(
                PaginatorButtonType.PREV,
                label="<",
                style=nextcord.ButtonStyle.red,
                row=self.default_button_row,
            ),
            PaginatorButton(
                PaginatorButtonType.INDICATOR,
                style=nextcord.ButtonStyle.gray,
                disabled=True,
                row=self.default_button_row,
            ),
            PaginatorButton(
                PaginatorButtonType.NEXT,
                label=">",
                style=nextcord.ButtonStyle.green,
                row=self.default_button_row,
            ),
            PaginatorButton(
                PaginatorButtonType.LAST,
                label=">>",
                style=nextcord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
        ]

        for button in default_buttons:
            self.add_button(button)

    def add_button(self, button: PaginatorButton) -> None:
        self.buttons[button.button_type] = {
            "object": nextcord.ui.Button(
                label=button.label
                      if button.label or button.emoji
                      else button.button_type.capitalize()
                           if button.button_type != PaginatorButtonType.INDICATOR
                           else f"{self.current_page + 1}/{self.page_count + 1}",
                emoji=button.emoji,
                style=button.style,
                disabled=button.disabled,
                row=button.row,
            ),
            "hidden": button.disabled
                      if button.button_type != PaginatorButtonType.INDICATOR
                      else not self.show_indicator,
        }
        self.buttons[button.button_type]["object"].callback = button.callback
        button.paginator = self

    def remove_button(self, button_type: PaginatorButtonType) -> None:
        if button_type not in self.buttons.keys():
            raise ValueError(f"no button_type {button_type} was found in this paginator")
        self.buttons.pop(button_type)

    def update_buttons(self) -> dict[PaginatorButtonType, dict[str, PaginatorButton | bool]]:
        for key, button in self.buttons.items():
            if key == PaginatorButtonType.FIRST:
                if self.current_page <= 1:
                    button["hidden"] = True
                elif self.current_page >= 1:
                    button["hidden"] = False
            elif key == PaginatorButtonType.LAST:
                button["hidden"] = self.current_page >= self.page_count - 1
            elif key == PaginatorButtonType.NEXT:
                if self.current_page == self.page_count:
                    button["hidden"] = not self.loop_pages
                elif self.current_page < self.page_count:
                    button["hidden"] = False
            elif key == PaginatorButtonType.PREV:
                if self.current_page <= 0:
                    button["hidden"] = not self.loop_pages
                else:
                    button["hidden"] = False

        self.clear_items()

        if self.show_indicator:
            self.buttons[PaginatorButtonType.INDICATOR]["object"].label = \
                    f"{self.current_page + 1}/{self.page_count + 1}"

        for key, button in self.buttons.items():
            if key != PaginatorButtonType.INDICATOR:
                if button["hidden"]:
                    button["object"].disabled = True
                    if self.show_disabled:
                        self.add_item(button["object"])
                else:
                    button["object"].disabled = False
                    self.add_item(button["object"])
            elif self.show_indicator:
                self.add_item(button["object"])

        if self.show_menu:
            self.add_menu()

        if self.custom_view:
            self.update_custom_view(self.custom_view)

        return self.buttons

    def update_custom_view(self, custom_view: nextcord.ui.View):
        if isinstance(self.custom_view, nextcord.ui.View):
            for item in self.custom_view.children:
                self.remove_item(item)
        for item in custom_view.children:
            self.add_item(item)

    @staticmethod
    def get_page_content(page: Page) -> Page:
        if not isinstance(page, Page):
            raise TypeError("Page content must be a Page object")

        return page

    async def page_action(self, interaction: Interaction | None = None) -> None:
        if self.get_page_content(self.pages[self.current_page]).callback:
            await self.get_page_content(self.pages[self.current_page]).callback(interaction)

    async def send(
            self,
            ctx: commands.Context,
            target: nextcord.abc.Messageable | None = None,
            target_message: str | None = None,
            reference: nextcord.Message | nextcord.MessageReference | nextcord.PartialMessage | None = None,
            allowed_mentions: nextcord.AllowedMentions | None = None,
            mention_author: bool = True,
            delete_after: float | None = None,
    ) -> nextcord.Message:
        if not isinstance(ctx, commands.Context):
            raise TypeError(f"expected Context, not {ctx.__class__!r}")

        if target is not None and not isinstance(target, nextcord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable, not {target.__class__!r}")

        if reference is not None and not isinstance(
            reference, nextcord.Message | nextcord.MessageReference | nextcord.PartialMessage,
        ):
            raise TypeError(f"expected Message, MessageReference, or PartialMessage, not {reference.__class__!r}")

        if allowed_mentions is not None and not isinstance(allowed_mentions, nextcord.AllowedMentions):
            raise TypeError(f"expected AllowedMentions, not {allowed_mentions.__class__!r}")

        if not isinstance(mention_author, bool):
            raise TypeError(f"expected bool, not {mention_author.__class__!r}")

        self.update_buttons()
        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = ctx.author

        if target:
            if target_message:
                await ctx.send(
                    target_message,
                    reference=reference,
                    allowed_mentions=allowed_mentions,
                    mention_author=mention_author,
                )
            ctx = target

        self.message = await ctx.send(
            content=page_content.content,
            embeds=page_content.embeds,
            files=page_content.files,
            view=self,
            reference=reference,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            delete_after=delete_after,
        )

        return self.message

    async def edit(
            self,
            message: nextcord.Message,
            suppress: bool = False,
            allowed_mentions: nextcord.AllowedMentions | None = None,
            delete_after: float | None = None,
    ) -> nextcord.Message | None:
        if not isinstance(message, nextcord.Message):
            raise TypeError(f"expected Message, not {message.__class__!r}")

        self.update_buttons()

        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = message.author

        try:
            self.message = await message.edit(
                content=page_content.content,
                embeds=page_content.embeds,
                files=page_content.files,
                attachments=[],
                view=self,
                suppress=suppress,
                allowed_mentions=allowed_mentions,
                delete_after=delete_after,
            )
        except (nextcord.NotFound, nextcord.Forbidden):
            pass

        return self.message

    async def respond(
            self,
            interaction: commands.Context | Interaction,
            ephemeral: bool = False,
            target: nextcord.abc.Messageable | None = None,
            target_message: str = "Paginator sent!",
    ) -> nextcord.Message | nextcord.InteractionMessage | nextcord.WebhookMessage | None:
        if not isinstance(interaction, commands.Context | nextcord.Interaction):
            raise TypeError(f"expected commands.Context, or Interaction, not {interaction.__class__!r}")

        if target is not None and not isinstance(target, nextcord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable, not {target.__class__!r}")

        if ephemeral and (self.timeout > 855 or self.timeout is None):
            raise ValueError(
                "paginator responses cannot be ephemeral if the paginator timeout is 15 minutes or greater"
            )

        self.update_buttons()

        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        if isinstance(interaction, nextcord.Interaction):
            self.user = interaction.user

            if target:
                msg = await target.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
                await interaction.send(target_message, ephemeral=ephemeral)
            else:
                done = interaction.response.is_done()

                msg = await interaction.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                    ephemeral=ephemeral,
                )

                if done and not ephemeral:
                    msg = await msg.channel.fetch_message(msg.id)

        else:
            ctx = interaction
            self.user = ctx.author
            if target:
                msg = await target.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
                await ctx.reply(target_message)
            else:
                msg = await ctx.reply(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )

        if isinstance(msg, nextcord.PartialInteractionMessage):
            try:
                self.message = await msg.fetch()
            except nextcord.HTTPException:
                pass
        else:
            self.message = msg

        return self.message


class PaginatorMenu(nextcord.ui.Select):
    def __init__(
            self,
            pages: list[Page],
            placeholder: str | None = None,
    ):
        self.pages = pages
        self.paginator: Paginator | None = None

        opts: list[nextcord.SelectOption] = []
        for index, page in enumerate(pages):
            emoji, label = None, None
            if page.title is None:
                label = f"Page {index + 1}"
            elif isinstance(page.title, tuple):
                emoji = page.title[0]
                label = page.title[1]
            else:
                label = page.title

            opts.append(nextcord.SelectOption(
                label=label,
                description=page.description,
                value=f"{index}",
                emoji=emoji,
            ))

        super().__init__(
            placeholder=placeholder,
            options=opts,
            max_values=1,
            min_values=1,
        )

    async def callback(self, interaction: Interaction) -> None:
        page_number = int(self.values[0])
        self.paginator.current_page = page_number
        await self.paginator.goto_page(page_number, interaction)
