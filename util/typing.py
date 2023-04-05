from typing import Any, Literal, NoReturn, TypeAlias

import nextcord


class MissingType:
    def __eq__(self, _) -> Literal[False]:
        return False

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> Literal["Missing"]:
        return "Missing"


class IntersectionMeta(type):
    def __instancecheck__(self, instance: Any) -> bool:
        return all(isinstance(instance, c) for c in self.__bases__)


class MessageableGuildChannel(nextcord.abc.Messageable, nextcord.abc.GuildChannel, metaclass=IntersectionMeta):
    def __new__(cls) -> NoReturn:
        raise NotImplementedError


Missing = MissingType()

GeneralChannel: TypeAlias = nextcord.abc.GuildChannel | nextcord.Thread | nextcord.abc.PrivateChannel
GeneralUser: TypeAlias = nextcord.User | nextcord.Member

LoggerLevel: TypeAlias = Literal["CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", "NOTSET"]
