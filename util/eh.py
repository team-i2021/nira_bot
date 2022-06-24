import os
import sys
import traceback

import nextcord

#エラー発生時に簡単にembedを送信できる


def eh(err):
    exc_type, exc_obj, exc_tb = sys.exc_info() 
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return nextcord.Embed(title="Error",description=f"大変申し訳ございません。ニラがエラーが発生させました。\n```{err}```\n```sh\n{traceback.format_exc()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000)


def PermisionError():
    pass
