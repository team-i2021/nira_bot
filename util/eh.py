import discord
import os
import sys

#エラー発生時に簡単にembedを送信できる

def eh(err):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    return discord.Embed(title="Error", description=f"大変申し訳ございません。エラーが発生しました。\n```{err}```\n```sh\n{sys.exc_info()}```\nfile:`{fname}`\nline:{exc_tb.tb_lineno}\n\n[サポートサーバー](https://discord.gg/awfFpCYTcP)", color=0xff0000)
