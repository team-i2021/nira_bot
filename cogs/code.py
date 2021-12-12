from discord import file
from discord.ext import commands
import discord
import os
import linecache

import sys
sys.path.append('../')
from util import admin_check, n_fc, eh
#pingを送信するだけ
global open_file
open_file = {}

# コード編集用
#
# code open [filename]
# 指定したファイルを開きます。
# code show [line]
# 指定した行を表示します。
# code edit [line] [text]
# 指定した行を[text]に置き換えます。
# code write [line] [text]
# 指定した行に[text]を挿入します。
# code close
# 開いているファイルを閉じます。

class code(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def code(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            await ctx.reply(embed=discord.Embed(title="エラー",description="このコマンドを実行する権限がありません。", color=0xff0000))
            return
        if ctx.message.content[:11] == "n!code open":
            file_name = ctx.message.content[12:]
            if os.path.isfile(file_name) == False:
                await ctx.reply(embed=discord.Embed(title="エラー",description=f"そのファイルは存在しません。[NoSuchFile]\n```ファイル名：{file_name}```", color=0xff0000))
                return
            open_file[ctx.message.author.id] = file_name
            await ctx.reply(embed=discord.Embed(title="指定完了",description=f"ファイル「`{file_name}`」を開きます。", color=0x00ff00))
            return
        if ctx.message.content == "n!code close":
            del open_file[ctx.message.author.id]
            await ctx.reply(embed=discord.Embed(title="指定完了",description=f"ファイルを閉じました。", color=0x00ff00))
            return
        if ctx.message.content[:11] == "n!code show":
            file_line = ctx.message.content[12:]
            if ctx.message.author.id not in open_file:
                await ctx.reply(embed=discord.Embed(title="エラー",description=f"先にファイルを指定してください。\n```n!code open [filename]```", color=0xff0000))
                return
            with open(open_file[ctx.message.author.id]) as f:
                line_data = f.readlines()
            await ctx.reply(f"```{file_line} {line_data[int(file_line ) - 1]}```")
            return
        if ctx.message.content[:11] == "n!code edit":
            try:
                edit_file = ctx.message.content[12:].split(" ", 1)
                code_line = edit_file[0]
                code_text = edit_file[1]
                if ctx.message.author.id not in open_file:
                    await ctx.reply(embed=discord.Embed(title="エラー",description=f"先にファイルを指定してください。\n```n!code open [filename]```", color=0xff0000))
                    return
                with open(open_file[ctx.message.author.id]) as f:
                    line_list = f.readlines()
                bak_lile = line_list[int(code_line) - 1]
                line_list[int(code_line) - 1] = code_text
                with open(open_file[ctx.message.author.id], mode='w') as f:
                    f.write('\n'.join(line_list))
                await ctx.reply(f"・置き換え前\n```{code_line} {bak_lile}```\n・置き換え後\n```{code_line} {code_text}```")
                return
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        if ctx.message.content[:12] == "n!code write":
            try:
                add_file = ctx.message.content[13:].split(" ", 1)
                code_line = add_file[0]
                code_text = add_file[1]
                if ctx.message.author.id not in open_file:
                    await ctx.reply(embed=discord.Embed(title="エラー",description=f"先にファイルを指定してください。\n```n!code open [filename]```", color=0xff0000))
                    return
                with open(open_file[ctx.message.author.id]) as f:
                    l = f.readlines()
                l.insert((int(code_line) - 1), f'{code_text}\n')
                with open(open_file[ctx.message.author.id], mode='w') as f:
                    f.writelines(l)
                await ctx.reply(f"```{code_line} {code_text}```")
                return
            except BaseException as err:
                await ctx.reply(embed=eh.eh(err))
                return
        else:
            await ctx.reply(embed=discord.Embed(title="使い方", description="`n!code open [file name]`：ファイルを開きます。\n`n!code close`：ファイルを閉じます。\n`n!code show [line num]`：開かれているファイルの特定行を表示します。\n`n!code edit [line num] [text]`：開かれているファイルの特定業を編集します。\n`n!code write [line num] [text]`：開かれているファイルの特定行に挿入します。"))
            return

def setup(bot):
    bot.add_cog(code(bot))