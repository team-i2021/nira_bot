import importlib
import logging
import traceback
from difflib import get_close_matches
from http import HTTPStatus as Codes

import nextcord
from nextcord.ext import application_checks, commands

import nira_commands
from util.nira import NIRA


# エラー時のイベント！
class error(commands.Cog):
    def __init__(self, bot: NIRA, **kwargs):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        code, description = None, None
        add_trace, add_help, add_support = False, False, False

        # 継承を考慮した判定
        if isinstance(error, commands.UserInputError):
            code = Codes.BAD_REQUEST
            description = "コマンド文字列の解析に失敗しました。構文が誤っていないか確認してください。"
            add_help = True
            # 解析に失敗した原因を特定できなかった場合のみサポートリンクを表示する
            add_support = not issubclass(type(error), commands.UserInputError)
        elif isinstance(error, commands.CheckFailure):
            code = Codes.FORBIDDEN
            description = "コマンド実行時チェックに失敗しました。適切なロールや権限が無い可能性があります。"
            # どのチェックが失敗したか特定できなかった場合のみヘルプ・サポートリンクを表示する
            add_help = not issubclass(type(error), commands.CheckFailure)
            add_support = add_help

        # よくありそうなエラー
        if isinstance(error, commands.CommandNotFound):
            # 仮
            suggestion = ''
            try:
                command_list = [i.name for i in list(self.bot.commands)]
                close_command = get_close_matches(word=error.command_name, possibilities=command_list, n=1, cutoff=0)[0]
                close_description = [i.help for i in list(self.bot.commands) if i.name == close_command][0]
                close_oneline = ("(ヘルプがないコマンド)" if close_description is None else close_description.splitlines()[0])
                suggestion = f"\n\nもしかして：\n`{ctx.prefix}{close_command}`: {close_oneline}"
            except Exception:
                logging.exception("コマンド検索中のエラー")

            code = Codes.NOT_FOUND
            description = f"`{ctx.prefix}{error.command_name}`というコマンドはありません。\n`{ctx.prefix}help`でコマンドを確認してください。{suggestion}"
        elif isinstance(error, commands.CommandOnCooldown):
            code = Codes.TOO_MANY_REQUESTS
            description = f"このコマンドは現在クールタイム中です。\n残り：**{error.retry_after:.2f}**秒"
        elif isinstance(error, commands.MaxConcurrencyReached):
            code = Codes.TOO_MANY_REQUESTS
            description = "このコマンドの同時実行数制限に達しました。時間を置いてやり直してください。"
        elif isinstance(error, commands.DisabledCommand):
            code = Codes.FORBIDDEN
            description = "このコマンドは無効化されています。"
            add_support = True

        # UserInputError -> BadArgument
        elif isinstance(error, commands.BadBoolArgument):
            # TODO: 許可される真偽値についてのヘルプ (n!help) を追加してここから誘導する
            # https://docs.nextcord.dev/en/stable/ext/commands/commands.html#bool
            description = f"`{error.argument}`は不正な真偽値です。"
        elif isinstance(error, commands.MemberNotFound | commands.UserNotFound):
            description = f"`{error.argument}`というユーザーはいません。"
        elif isinstance(error, commands.RoleNotFound):
            description = f"`{error.argument}`というロールはありません。"
        elif isinstance(error, commands.GuildStickerNotFound):
            description = f"`{error.argument}`というスタンプはありません。"
        elif isinstance(error, commands.ChannelNotFound):
            description = f"`{error.argument}`というチャンネルはありません。"
        elif isinstance(error, commands.ThreadNotFound):
            description = f"`{error.argument}`というスレッドはありません。"
        elif isinstance(error, commands.ChannelNotReadable):
            code = Codes.FORBIDDEN
            description = f"{error.argument.mention} のメッセージを読み込むことができません。\nBotに適切な権限が付与されているか確認してください。"
            add_help = False
        elif isinstance(error, commands.BadInviteArgument):
            description = "招待が無効か、期限切れです。"

        # UserInputError -> ArgumentParsingError
        elif isinstance(error, commands.UnexpectedQuoteError):
            description = "予期しない引用符です。"
        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            description = "引数の区切りにスペースが必要ですが、つながっています。"
        elif isinstance(error, commands.ExpectedClosingQuoteError):
            description = "対応する引用符が見つかりません。"

        # UserInputError
        elif isinstance(error, commands.MissingRequiredArgument):
            description = f"引数`{error.param.name}`が足りません。"
        elif isinstance(error, commands.TooManyArguments):
            description = "引数が多すぎます。"
        elif isinstance(error, commands.BadUnionArgument | commands.BadLiteralArgument):
            description = f"引数`{error.param.name}`の値が不正です。"
        elif isinstance(error, commands.BadArgument):
            description = "引数の値が不正です。"
        elif isinstance(error, commands.ArgumentParsingError):
            description = "引数を解析できません。"

        # CheckFailure
        elif isinstance(error, commands.PrivateMessageOnly):
            description = "このコマンドはダイレクトメッセージでのみ実行できます。"
            add_help = True
        elif isinstance(error, commands.NoPrivateMessage):
            description = "このコマンドはダイレクトメッセージからは実行できません。"
            add_help = True
        elif isinstance(error, commands.NotOwner | NIRA.ForbiddenExpand):
            description = "このコマンドはBot管理者専用です。"
        elif isinstance(error, commands.MissingPermissions | NIRA.Forbidden):
            description = "このコマンドの実行に必要な権限がありません。"
        elif isinstance(error, commands.BotMissingPermissions):
            perms = "`, `".join(error.missing_permissions)
            description = f"このコマンドの実行に必要な権限がBotにありません。\n実行にはこれらの権限が必要です：\n`{perms}`"
        elif isinstance(error, commands.MissingRole | commands.MissingAnyRole):
            description = "このコマンドの実行に必要なロールを持っていません。"
        elif isinstance(error, commands.BotMissingRole):
            # ロールIDの場合、名前の取得を試みる
            if type(role := error.missing_role) is int:
                role = r.name if (r := ctx.guild.get_role(role)) else f"(ID) {role}"
            description = f"このコマンドの実行に必要なロールをBotが持っていません。\n実行には`{role}`が必要です。"
        elif isinstance(error, commands.BotMissingAnyRole):
            roles = "`, `".join(
                (r.name if (r := ctx.guild.get_role(role)) else f"(ID) {role}") if type(role) is int else role
                for role in error.missing_roles
            )
            description = f"このコマンドの実行に必要なロールをBotが持っていません。\n実行にはこれらのロールが必要です：\n`{roles}`"

        # 内部エラー
        elif isinstance(error, commands.ConversionError):
            error = error.original
            logging.error("コンバーターエラー", exc_info=error)

            code = Codes.INTERNAL_SERVER_ERROR
            description = "コマンド呼び出しに失敗しました。"
            add_trace = True
            add_support = True
        elif isinstance(error, commands.CommandInvokeError):
            error = error.original
            logging.error("コマンド内部エラー", exc_info=error)

            code = Codes.INTERNAL_SERVER_ERROR
            description = "コマンド内部でエラーが発生しました。"
            add_trace = True
            add_support = True
        elif code is None or description is None:
            logging.error("不明なエラー", exc_info=error)

            code = Codes.INTERNAL_SERVER_ERROR
            description = "予期しない不明なエラーが発生しました。"
            add_trace = True
            add_support = True

        if add_trace:
            trace = "".join(traceback.TracebackException.from_exception(error).format())
            description += f"\n```py\n{trace.replace(self.bot.settings["database_url"], '[URL]')}```"
        # Context.command は Optional[Command]
        if add_help and ctx.command:
            name = ctx.invoked_parents[0]
            description += f"\n`{ctx.prefix}help {name}`でヘルプを表示できます。"
        if add_support:
            description += "\n[サポートサーバー](https://discord.gg/awfFpCYTcP)"

        embed = nextcord.Embed(
            title=f"{code.value} - {code.phrase}",
            description=description,
            color=0xff0000,
        )

        try:
            for method in (ctx.reply, ctx.send):
                try:
                    await method(embed=embed)
                except nextcord.Forbidden:
                    continue
                else:
                    break
            else:
                await ctx.author.send(embed=embed)
        except (nextcord.Forbidden, nextcord.HTTPException):
            logging.exception("エラーメッセージを送信できませんでした")

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, error: nextcord.ApplicationError):
        code, description = None, None
        add_trace, add_help, add_support = False, False, False

        # 継承を考慮した判定
        if isinstance(error, nextcord.ApplicationCheckFailure):
            code = Codes.FORBIDDEN
            description = "コマンド実行時チェックに失敗しました。適切なロールや権限が無い可能性があります。"
            # どのチェックが失敗したか特定できなかった場合のみヘルプ・サポートリンクを表示する
            add_help = not issubclass(type(error), nextcord.ApplicationCheckFailure)
            add_support = add_help

        # ApplicationCheckFailure
        if isinstance(error, application_checks.ApplicationPrivateMessageOnly):
            description = "このコマンドはダイレクトメッセージでのみ実行できます。"
            add_help = True
        elif isinstance(error, application_checks.ApplicationNoPrivateMessage):
            description = "このコマンドはダイレクトメッセージからは実行できません。"
            add_help = True
        elif isinstance(error, application_checks.ApplicationNotOwner | NIRA.ForbiddenExpand):
            description = "このコマンドはBot管理者専用です。"
        elif isinstance(error, application_checks.ApplicationMissingPermissions | NIRA.Forbidden):
            description = "このコマンドの実行に必要な権限がありません。"
        elif isinstance(error, application_checks.ApplicationBotMissingPermissions):
            perms = "`, `".join(error.missing_permissions)
            description = f"このコマンドの実行に必要な権限がBotにありません。\n実行にはこれらの権限が必要です：\n`{perms}`"
        elif isinstance(error, application_checks.ApplicationMissingRole | application_checks.ApplicationMissingAnyRole):
            description = "このコマンドの実行に必要なロールを持っていません。"
        elif isinstance(error, application_checks.ApplicationBotMissingRole):
            if type(role := error.missing_role) is int:
                role = f"(ID) {role}" if (role_ := interaction.guild.get_role(role)) is None else role_.name
            description = f"このコマンドの実行に必要なロールをBotが持っていません。\n実行には`{role}`が必要です。"
        elif isinstance(error, application_checks.ApplicationBotMissingAnyRole):
            roles = "`, `".join(
                (f"(ID) {role}" if (r := interaction.guild.get_role(role)) is None else r.name) if type(role) is int else role
                for role in error.missing_roles
            )
            description = f"このコマンドの実行に必要なロールをBotが持っていません。\n実行にはこれらのロールが必要です：\n`{roles}`"

        # 内部エラー
        elif isinstance(error, nextcord.ApplicationInvokeError):
            error = error.original
            if isinstance(error, nextcord.ApplicationError):
                return await self.on_application_command_error(interaction, error)

            logging.error("コマンド内部エラー", exc_info=error)

            code = Codes.INTERNAL_SERVER_ERROR
            description = "コマンド内部でエラーが発生しました。"
            add_trace = True
            add_support = True
        elif code is None or description is None:
            logging.error("不明なエラー", exc_info=error)

            code = Codes.INTERNAL_SERVER_ERROR
            description = "予期しない不明なエラーが発生しました。"
            add_trace = True
            add_support = True

        if add_trace:
            trace = "".join(traceback.TracebackException.from_exception(error).format())
            description += f"\n```py\n{trace.replace(self.bot.settings["database_url"], '[URL]')}```"
        # Interaction.application_command は Optional[ApplicationCommand]
        if add_help and (command := interaction.application_command):
            while getattr(command, "parent_cmd", None) is not None:
                command = command.parent_cmd
            description += f"\n`/help {command.name}`でヘルプを表示できます。"
        if add_support:
            description += "\n[サポートサーバー](https://discord.gg/awfFpCYTcP)"

        embed = nextcord.Embed(
            title=f"{code.value} - {code.phrase}",
            description=description,
            color=0xff0000,
        )

        try:
            try:
                await interaction.send(embed=embed, ephemeral=True)
            except (nextcord.NotFound, nextcord.Forbidden):
                if interaction.user:
                    await interaction.user.send(embed=embed)
                else:
                    raise
        except (nextcord.HTTPException, nextcord.NotFound, nextcord.Forbidden):
            logging.exception("エラーメッセージを送信できませんでした")


def setup(bot, **kwargs):
    bot.add_cog(error(bot, **kwargs))
    importlib.reload(nira_commands)
