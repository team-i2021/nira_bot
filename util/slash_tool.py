import nextcord
import sys
import logging


class messages:
    def mreply(message: nextcord.ext.commands.Context or nextcord.Message or nextcord.Interaction, reply_message: str, **kwargs):
        """
第1引数: 返信元のメッセージやコンテキストやインタラクション
第2引数: 返信するメッセージ
*第3引数: EmbedやEphemeralなどの設定"""
        if kwargs == {}:
            kwargs["embed"] = None
            kwargs["ephemeral"] = False
        elif "embed" not in kwargs:
            kwargs["embed"] = None
        elif "ephemeral" not in kwargs:
            kwargs["ephemeral"] = False
        if type(message) == nextcord.Message:
            return message.reply(reply_message, embed=kwargs["embed"])
        elif type(message) == nextcord.Interaction:
            # InteractionResponse.send_message は embed=None すると例外を吐く
            if kwargs["embed"] is None:
                return message.response.send_message(reply_message, ephemeral=kwargs["ephemeral"])
            else:
                return message.response.send_message(reply_message, embed=kwargs["embed"], ephemeral=kwargs["ephemeral"])
        elif type(message) == nextcord.ext.commands.Context:
            return message.reply(reply_message, embed=kwargs["embed"])
        else:
            raise TypeError
            return

    def content_check(message):
        if type(message) == nextcord.Message:
            return message.content
        elif type(message) == nextcord.Interaction:
            return message.message.content
        else:
            raise TypeError
            return
