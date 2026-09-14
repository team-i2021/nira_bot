"""Components v2用のモーダルとそのコンポーネントの定義"""

import functools
import time
from collections.abc import Iterator
from typing import Self, override

import nextcord
import nextcord.state
import nextcord.types.components as cp_payloads
import nextcord.types.interactions as intr_payloads
import nextcord.ui.select.base
from nextcord import ui
from nextcord.utils import MISSING

__all__ = (
    "Modal",
    "ModalLabel",
    "ModalTextInput",
    "ModalStringSelect",
    "ModalUserSelect",
    "ModalRoleSelect",
    "ModalMentionableSelect",
    "ModalChannelSelect",
)


# ModalLabel の子を送信できるようにした nextcord.ui.Modal
class Modal(ui.Modal):
    # Modal.to_dict() から呼び出される、nextcord.components をペイロード辞書データに変換する処理
    @override
    def to_components(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> list[cp_payloads.Component]:
        children = sorted(self.children, key=lambda item: item._rendered_row or 0)
        # 基底は何でもかんでも Action Row に詰め込んでしまうので、Text Input 以外はそのまま追加するようにする
        components: list[cp_payloads.Component] = []
        for item in children:
            component = item.to_component_dict()
            if isinstance(item, ui.TextInput):
                # Text Input を Action Row に入れるのはDiscord側で非推奨となっている
                components.append({"type": 1, "components": [component]})
            else:
                components.append(component)

        return components

    # インタラクションを受信して各Modalにdispatchされたら呼び出される、Modalのメイン処理
    @override
    async def _scheduled_task(self, interaction: nextcord.Interaction):
        # ui.modal._walk_component_interaction_data() を代替する
        # オリジナルは "components" (複数形) しか見ないため、
        # Label の "component" (単数形) にあるコンポーネントを処理することができない
        def walk_data(
            components: list[intr_payloads.ModalSubmitComponentInteractionData],
        ) -> Iterator[intr_payloads.ComponentInteractionData]:
            for item in components:
                if "components" in item:
                    yield from item["components"]
                elif "component" in item:
                    yield item["component"]
                else:
                    yield item

        # 以下はほぼ基底からのコピペ (念のため全部をtryブロックで囲む)
        data: intr_payloads.ModalSubmitInteractionData = interaction.data  # type: ignore
        try:
            for child in self.children:
                for component_data in walk_data(data["components"]):
                    if component_data["custom_id"] == getattr(child, "custom_id", None):
                        # ui.UserSelect や ui.RoleSelect 等はペイロードの "resolved" にあるデータを必要とする
                        # しかし MESSAGE_COMPONENT インタラクションと MODAL_SUBMIT インタラクションでは
                        # データ構造が異なるため、そのままでは "resolved" を参照することができない
                        # (前者の "values" は "resolved" と同じ階層だが、後者の "values" は "components" の下にある)
                        # https://docs.discord.com/developers/interactions/receiving-and-responding#interaction-object-message-component-data-structure
                        if "resolved" in interaction.data:  # type: ignore
                            component_data["resolved"] = interaction.data["resolved"]  # type: ignore
                        child.refresh_state(component_data, interaction._state, interaction.guild)
                        break

            if self.timeout:
                # ゴリ押し↓ (他にアクセスする手段が無かったので仕方がない)
                self._Modal__timeout_expiry = time.monotonic() + self.timeout

            await self.callback(interaction)
            if (
                not interaction.response.is_done()
                and not interaction.is_expired()
                and self.auto_defer
            ):
                await interaction.response.defer()
        except Exception as e:
            return await self.on_error(e, interaction)


class ModalLabel[I: ui.Item[ui.View]](ui.Item[ui.View]):
    """モーダル内のUIラベルを表します。

    これは :class:`Modal` でのみ使用可能な、最上位のレイアウトコンポーネントです。

    Parameters
    ----------
    text: :class:`str`
        入力フィールドの上に表示するテキスト。最大45文字までです。
    description: :class:`str`
        ラベルテキストのすぐ下に表示する説明文。最大100文字までです。
    component: :class:`nextcord.ui.Item`
        ラベルの下に表示するコンポーネント。
    """

    # パラメータ・属性は discord.py に準拠

    __item_repr_attributes__: tuple[str, ...] = (
        "text",
        "description",
        "component",
    )

    @override
    def __init__(self, text: str, component: I, *, description: str | None = None) -> None:
        super().__init__()

        self.text = text
        self.description = MISSING if description is None else description
        self.component = component

        if isinstance(self.component, ui.TextInput):
            self.component.label = self.text

    @property
    @override
    def row(self) -> int | None:
        return self.component.row

    @row.setter
    @override
    def row(self, value: int | None) -> None:
        self.component.row = value

    @property
    @override
    def width(self) -> int:
        return self.component.width

    @property
    @override
    def view(self) -> ui.View | None:
        return self.component.view

    # nextcord内部で見ている模様。子のcustom_idをそのまま返す
    @property
    def custom_id(self) -> str:
        return self.component.custom_id  # type: ignore

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        self.component.custom_id = value  # type: ignore

    @property
    @override
    def type(self) -> nextcord.ComponentType:
        return nextcord.ComponentType.label

    # ui.View でメッセージからコンポーネントを生成するために使用されるが、
    # Label はメッセージに載せられないので恐らく呼び出されることは無い
    @classmethod
    @override
    def from_component(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        component: nextcord.components.Label,
    ) -> Self:
        if isinstance(component.component, nextcord.components.TextInput):
            component.component.label = component.label
        child_component = ui.view._component_to_item(component.component)
        return cls(
            text=component.label,
            description=component.description,
            component=child_component,  # type: ignore
        )

    @override
    def to_component_dict(self) -> cp_payloads.Label:
        child_component = self.component.to_component_dict()
        # 子が Text Input の場合、"label" を持っていると重複してしまうので削除する
        if child_component["type"] == nextcord.ComponentType.text_input:
            child_component.pop("label", None)
        component = nextcord.components.Label(
            label=self.text,
            description=self.description,
            component=nextcord.Component(component_type=nextcord.ComponentType.label),  # ダミー
        )
        payload = component.to_dict()
        payload["component"] = child_component
        return payload

    @override
    def is_dispatchable(self) -> bool:
        return self.component.is_dispatchable()

    @override
    def refresh_component(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        component: nextcord.components.Label,
    ) -> None:
        self.text = component.label
        self.description = component.description
        return self.component.refresh_component(component.component)

    @override
    def refresh_state(
        self,
        data: intr_payloads.ComponentInteractionData,
        state: nextcord.state.ConnectionState,
        guild: nextcord.Guild | None,
    ) -> None:
        return self.component.refresh_state(data, state, guild)


# 以下はモーダルで使う場合に便利な代替コンポーネントたち
# 標準のコンポーネント (ui.TextInput, ui.StringSelect, ui.UserSelect, etc.) も一応使えないことは無い
# (が、label に適当な文字列を入れておかないといけなかったり、required をFalseにできないなどの制限がある)


class ModalTextInput[V: ui.View](ui.TextInput[V]):
    @override
    def __init__(
        self,
        *,
        style: nextcord.TextInputStyle = nextcord.TextInputStyle.short,
        custom_id: str = MISSING,
        row: int | None = None,
        min_length: int | None = 0,
        max_length: int | None = 4000,
        required: bool | None = None,
        default_value: str | None = None,
        placeholder: str | None = None,
    ) -> None:
        super().__init__(
            "",  # ModalLabelによって上書きされる
            style=style,
            custom_id=custom_id,
            row=row,
            min_length=min_length,
            max_length=max_length,
            required=required,
            default_value=default_value,
            placeholder=placeholder,
        )


def _modal_select[S: nextcord.ui.select.base.SelectBase](cls: type[S]) -> type[S]:
    """コンポーネントに ``required`` フィールドを追加するためのデコレータ"""

    orig_to_component_dict = cls.to_component_dict

    @functools.wraps(orig_to_component_dict)
    def to_component_dict(self: S):
        component = orig_to_component_dict(self)
        if (required := getattr(self, "required", MISSING)) is not MISSING:
            component["required"] = required  # type: ignore
        return component

    cls.__item_repr_attributes__ += ("required",)
    cls.to_component_dict = to_component_dict
    return cls


@_modal_select
class ModalStringSelect[V: ui.View](ui.StringSelect[V]):
    @override
    def __init__(
        self,
        *,
        custom_id: str | None = None,  # https://github.com/nextcord/nextcord/pull/1289
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = MISSING,
        options: list[nextcord.SelectOption] = MISSING,
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,  # type: ignore
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            row=row,
        )
        self.required = required


@_modal_select
class ModalUserSelect[V: ui.View](ui.UserSelect[V]):
    @override
    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = MISSING,
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        self.required = required


@_modal_select
class ModalRoleSelect[V: ui.View](ui.RoleSelect[V]):
    @override
    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = MISSING,
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        self.required = required


@_modal_select
class ModalMentionableSelect[V: ui.View](ui.MentionableSelect[V]):
    @override
    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = MISSING,
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        self.required = required


@_modal_select
class ModalChannelSelect[V: ui.View](ui.ChannelSelect[V]):
    @override
    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = MISSING,
        disabled: bool = False,
        row: int | None = None,
        channel_types: list[nextcord.ChannelType] = MISSING,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            channel_types=channel_types,
        )
        self.required = required
