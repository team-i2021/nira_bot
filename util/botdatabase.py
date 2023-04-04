"""MongoDB ドキュメントとコレクションを操作するラッパークラス ライブラリ"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Hashable, Mapping
from typing import Any, ClassVar, Final, Generic, TypeVar, cast

import nextcord
from cachetools import Cache
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import Extra
from pydantic.generics import GenericModel
from typing_extensions import Self

from util.nira import NIRA
from util.typing import GeneralChannel, GeneralUser, Missing, MissingType

ID_KEY_NAME: Final = "_id"

PrimaryKeyT = TypeVar("PrimaryKeyT")
IDValueT = TypeVar("IDValueT", bound=Hashable)
ChannelT = TypeVar("ChannelT", bound=GeneralChannel)

# FIXME: ところどころ苦し紛れに書いたのでカオスコードになっている (ほぼ型周り)
# FIXME: docstring もかなり苦し紛れに書いたのでもっと良い書き方あれば変更してほしい


class DocumentBase(GenericModel, ABC):
    """基本的な MongoDB ドキュメントを表す ABC です。

    ドキュメントのそれぞれのフィールドは Pydantic によって解析・検証されます。
    """

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid
        underscore_attrs_are_private = True
        use_enum_values = True

    @abstractmethod
    async def encode(self) -> dict[str, Any]:
        """この関数はコルーチンです。

        ドキュメントから辞書を生成します。

        Motor によって型変換が可能な形式である必要があります。

        Returns
        -------
        ドキュメントから生成された辞書。
        """
        ...

    @classmethod
    @abstractmethod
    async def decode(cls, bot: NIRA, raw: Mapping[str, Any]) -> Self:
        """この関数はコルーチンです。

        マッピングからドキュメントを生成します。

        Parameters
        ----------
        bot
            NIRA Bot のインスタンス。
        raw
            生成元となるマッピングオブジェクト。

        Returns
        -------
        マッピングから生成されたドキュメント。

        Raises
        ------
        :class:`pydantic.ValidationError`
            型の不一致など、マッピングの検証に失敗した。
        """
        ...

    @classmethod
    def get_field_type(cls, name: str) -> type:
        """指定した名前を持つフィールドの型を返します。

        Parameters
        ----------
        name
            フィールドの名前。

        Returns
        -------
        フィールドの型。

        Raises
        ------
        :class:`KeyError`
            指定した名前のフィールドが見つからなかった。
        """
        return cls.__fields__[name].type_


class UniqueDocument(DocumentBase, Generic[PrimaryKeyT, IDValueT]):
    """コレクション内でキーが一意であるドキュメントを表す ABC です。

    Attributes
    ----------
    _key_name: ClassVar[:class:`str`]
        ドキュメントの主キーの名前。
    """

    _key_name: ClassVar[str]

    @classmethod
    @abstractmethod
    async def resolve_primary(cls, bot: NIRA, raw: Mapping[str, Any]) -> tuple[PrimaryKeyT, dict[str, Any]]:
        """この関数はコルーチンです。

        マッピングから主キーを解決して辞書を生成します。

        主キーが既に解決済みの場合はそのまま辞書を生成します。

        Parameters
        ----------
        bot
            NIRA Bot のインスタンス。
        raw
            生成元となるマッピング オブジェクト。

        Returns
        -------
        主キーの解決結果と生成された辞書のタプル。
        """
        ...

    @classmethod
    async def decode(cls, bot: NIRA, raw: Mapping[str, Any]) -> Self:
        primary, doc = await cls.resolve_primary(bot, raw)
        doc.pop(ID_KEY_NAME)
        doc[cls._key_name] = primary
        return cls(**doc)


class ChannelDocument(DocumentBase, Generic[ChannelT]):
    """Discord チャンネルと対応するドキュメントを表す ABC です。"""

    channel: ChannelT


class UniqueChannelDocument(UniqueDocument[ChannelT, int], ChannelDocument[ChannelT], Generic[ChannelT]):
    """コレクション内で一意の Discord チャンネルと対応するドキュメントです。"""

    _key_name = "channel"

    async def encode(self) -> dict[str, Any]:
        doc = self.dict(exclude_unset=True)
        doc.pop(self._key_name)
        doc[ID_KEY_NAME] = self.channel.id
        return doc

    @classmethod
    async def resolve_primary(cls, bot: NIRA, raw: Mapping[str, Any]) -> tuple[ChannelT, dict[str, Any]]:
        doc = dict(raw)
        if isinstance(doc.get(ID_KEY_NAME), cls.get_field_type(cls._key_name)):
            channel = cast(ChannelT, doc[ID_KEY_NAME])
            return channel, doc

        channel_id = int(doc.pop(ID_KEY_NAME))
        channel = await bot.resolve_channel(channel_id)
        if not isinstance(channel, cls.get_field_type(cls._key_name)):
            raise TypeError
        channel = cast(ChannelT, channel)
        doc[ID_KEY_NAME] = channel
        return channel, doc


class UserDocument(DocumentBase):
    """Discord ユーザーと対応するドキュメントを表す ABC です。"""

    user: GeneralUser


class UniqueUserDocument(UniqueDocument[GeneralUser, int], UserDocument):
    """コレクション内で一意の Discord ユーザーと対応するドキュメントです。"""

    _key_name = "user"

    async def encode(self) -> dict[str, Any]:
        doc = self.dict(exclude_unset=True)
        doc.pop(self._key_name)
        doc[ID_KEY_NAME] = self.user.id
        return doc

    @classmethod
    async def resolve_primary(cls, bot: NIRA, raw: Mapping[str, Any]) -> tuple[GeneralUser, dict[str, Any]]:
        doc = dict(raw)
        if isinstance(doc[ID_KEY_NAME], GeneralUser):
            return doc[ID_KEY_NAME], doc

        user_id = int(doc.pop(ID_KEY_NAME))
        user = await bot.resolve_user(user_id)
        doc[ID_KEY_NAME] = user
        return user, doc


DocumentBaseT = TypeVar("DocumentBaseT", bound=DocumentBase)
UniqueDocumentT = TypeVar("UniqueDocumentT", bound=UniqueDocument)
ChannelDocumentT = TypeVar("ChannelDocumentT", bound=ChannelDocument)
UniqueChannelDocumentT = TypeVar("UniqueChannelDocumentT", bound=UniqueChannelDocument)
UserDocumentT = TypeVar("UserDocumentT", bound=UserDocument)
UniqueUserDocumentT = TypeVar("UniqueUserDocumentT", bound=UniqueUserDocument)


class CollectionBase(ABC, Generic[DocumentBaseT]):
    """基本的な MongoDB コレクションを表す ABC です。"""

    def __init__(self, bot: NIRA, collection: AsyncIOMotorCollection, document: type[DocumentBaseT]) -> None:
        """基本的な MongoDB コレクションを表す ABC です。

        Parameters
        ----------
        bot
            NIRA Bot のインスタンス。
        collection
            操作対象とする Motor のコレクション クラス インスタンス。
        document
            このコレクションに保持するドキュメント クラス。
        """
        self.__bot = bot
        self.__collection = collection
        self.__document = document

    @property
    def bot(self) -> NIRA:
        """NIRA Bot のインスタンスです。"""
        return self.__bot

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """操作対象となっている Motor のコレクション クラス インスタンスです。"""
        return self.__collection

    @property
    def document(self) -> type[DocumentBaseT]:
        """このコレクションのドキュメント クラスです。"""
        return self.__document

    @abstractmethod
    def new(self, **kwargs: Any) -> DocumentBaseT:
        """新しいドキュメントを生成します。

        Parameters
        ----------
        **kwargs
            ドキュメント クラスのコンストラクタに渡される引数。

        Returns
        -------
        生成されたドキュメント。

        Raises
        ------
        :class:`pydantic.ValidationError`
            型の不一致など、引数の検証に失敗した。
        """
        ...

    @abstractmethod
    async def get(self, **kwargs: Any) -> DocumentBaseT | None:
        """この関数はコルーチンです。

        コレクションからドキュメントを取得します。
        引数に一致するドキュメントが見つからない場合は `None` が返されます。

        Parameters
        ----------
        **kwargs
            検索するパラメータ。

        Returns
        -------
        見つかったドキュメント、または見つからない場合 `None`。
        """
        ...

    @abstractmethod
    async def get_all(self) -> AsyncGenerator[DocumentBaseT | Exception, None]:
        """この関数はコルーチンです。

        コレクション内の全てのドキュメントを取得する非同期ジェネレータです。

        検証中にエラーが発生した場合は例外オブジェクトが列挙されます。

        Yields
        ------
        ドキュメントまたは例外オブジェクト。
        """
        ...

    @abstractmethod
    async def update(self, document: DocumentBaseT) -> DocumentBaseT:
        """この関数はコルーチンです。

        コレクション内のドキュメントを更新します。
        ドキュメントがコレクションに存在しない場合は新たに作成されます。

        Parameters
        ----------
        document
            追加・更新するドキュメント。

        Returns
        -------
        追加・更新されたドキュメント。
        """
        ...

    @abstractmethod
    async def delete(self, document: DocumentBaseT) -> DocumentBaseT:
        """この関数はコルーチンです。

        コレクションからドキュメントを削除します。

        Parameters
        ----------
        document
            削除するドキュメント。

        Returns
        -------
        削除されたドキュメント。
        """
        ...


class UniqueCollection(CollectionBase[UniqueDocumentT], Generic[UniqueDocumentT, PrimaryKeyT, IDValueT]):
    """それぞれのドキュメントが一意であるコレクションを表す ABC です。"""

    def __init__(
        self,
        bot: NIRA,
        collection: AsyncIOMotorCollection,
        document: type[UniqueDocumentT],
        cache: Cache[IDValueT, UniqueDocumentT | None] | None = None,
    ) -> None:
        """それぞれのドキュメントが一意であるコレクションを表す ABC です。

        Parameters
        ----------
        bot
            NIRA Bot のインスタンス。
        collection
            操作対象とする Motor のコレクション クラス インスタンス。
        document
            このコレクションに保持するドキュメント クラス。
        cache, default `None`
            キャッシュを保持するクラス インスタンス。既定ではキャッシュは無効です。
        """
        super().__init__(bot, collection, document)
        self._cache = cache

    @property
    def cache(self) -> Cache[IDValueT, UniqueDocumentT | None] | None:
        return self._cache

    @abstractmethod
    def new(self, primary: PrimaryKeyT, /, **kwargs: Any) -> UniqueDocumentT:
        """新しいドキュメントを生成します。

        Parameters
        ----------
        primary
            主キーとなるオブジェクト。
        **kwargs
            ドキュメント クラスのコンストラクタに渡される引数。

        Returns
        -------
        生成されたドキュメント。

        Raises
        ------
        :class:`pydantic.ValidationError`
            型の不一致など、引数の検証に失敗した。
        """
        ...

    async def get(self, key: IDValueT, /) -> UniqueDocumentT | None:
        """この関数はコルーチンです。

        コレクションからドキュメントを取得します。
        指定された主キーと一致するドキュメントが見つからない場合は `None` が返されます。

        Parameters
        ----------
        key
            検索する主キー。

        Returns
        -------
        見つかったドキュメント、または見つからない場合 `None`。
        """
        if not isinstance(cache := self._get_cache(key), MissingType):
            return cache
        elif (doc := await self.collection.find_one({ID_KEY_NAME: key})) is None:
            return None
        return await self.document.decode(self.bot, doc)

    async def update(self, document: UniqueDocumentT) -> UniqueDocumentT:
        doc = await document.encode()
        await self.collection.replace_one({ID_KEY_NAME: doc[ID_KEY_NAME]}, doc, upsert=True)
        self._set_cache(doc[ID_KEY_NAME], document)
        return document

    async def delete(self, document: UniqueDocumentT) -> UniqueDocumentT:
        key = self._get_primary_key(document)
        await self.collection.delete_one({ID_KEY_NAME: key})
        self._set_cache(key, None)
        return document

    def uncache(self, key: IDValueT | None = None, /) -> None:
        """指定された主キーを持つ、または全てのドキュメントをキャッシュから消去します。

        Parameters
        ----------
        key, default `None`
            消去対象のドキュメントの主キー。既定では、全てのドキュメントが対象になります。
        """
        if self.cache is None:
            return
        elif key is None:
            self.cache.clear()
        elif key in self.cache:
            self.cache.pop(key)

    def _get_cache(self, key: IDValueT, /) -> UniqueDocumentT | None | MissingType:
        if self.cache is None or key not in self.cache:
            return Missing
        return self.cache[key]

    def _set_cache(self, key: IDValueT, /, document: UniqueDocumentT | None) -> None:
        if self.cache is not None:
            self.cache[key] = document

    @abstractmethod
    def _get_primary_key(self, document: UniqueDocumentT) -> IDValueT:
        """指定されたドキュメントから主キーを取得する内部関数です。"""
        ...


class ChannelCollection(CollectionBase[ChannelDocumentT]):
    """Discord チャンネルと対応するドキュメントを持つコレクションの ABC です。"""

    pass


class UniqueChannelCollection(
    UniqueCollection[UniqueChannelDocumentT, ChannelT, int],
    ChannelCollection[UniqueChannelDocumentT],
):
    """それぞれの Discord チャンネルと対応するドキュメントが一意であるコレクションです。"""

    def new(self, primary: ChannelT, /, **kwargs: Any) -> UniqueChannelDocumentT:
        doc = self.document(channel=primary, **kwargs)
        self._set_cache(primary.id, doc)
        return doc

    async def get_all(self) -> AsyncGenerator[UniqueChannelDocumentT | Exception, None]:
        async for doc in self.collection.find({ID_KEY_NAME: {"$type": ["int", "long"]}}):
            try:
                document = await self.document.decode(self.bot, doc)
            except (nextcord.NotFound, nextcord.Forbidden):
                pass
            except Exception as e:
                yield e
            else:
                self._set_cache(self._get_primary_key(document), document)
                yield document

    def _get_primary_key(self, document: UniqueChannelDocumentT) -> int:
        return document.channel.id


class UserCollection(CollectionBase[UserDocumentT]):
    """Discord ユーザーと対応するドキュメントを持つコレクションの ABC です。"""

    pass


class UniqueUserCollection(
    UniqueCollection[UniqueUserDocumentT, GeneralUser, int],
    UserCollection[UniqueUserDocumentT],
):
    """それぞれの Discord ユーザーと対応するドキュメントが一意であるコレクションです。"""

    def new(self, primary: GeneralUser, /, **kwargs: Any) -> UniqueUserDocumentT:
        doc = self.document(user=primary, **kwargs)
        self._set_cache(primary.id, doc)
        return doc

    async def get_all(self) -> AsyncGenerator[UniqueUserDocumentT | Exception, None]:
        async for doc in self.collection.find({ID_KEY_NAME: {"$type": ["int", "long"]}}):
            try:
                document = await self.document.decode(self.bot, doc)
            except nextcord.NotFound:
                pass
            except Exception as e:
                yield e
            else:
                self._set_cache(self._get_primary_key(document), document)
                yield document

    def _get_primary_key(self, document: UniqueUserDocumentT) -> int:
        return document.user.id
