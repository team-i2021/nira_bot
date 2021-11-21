import discord
from discord.ext import commands
import bot_token
from os import getenv
import sys
import os
import re
import random
import a2s
import asyncio
import datetime
from discord.utils import get
import srtr
import status_check
import subprocess
from subprocess import PIPE
import line
import n_cmd
from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
from discord.flags import MessageFlags
py_admin = [669178357371371522]

# NIRA BOT for DEV
# バージョン及び権利は全て、にらBOTと同じです。

intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.members = True

bot = commands.Bot(command_prefix="n#", intents=intents)

@bot.event
async def on_ready():
    print("Ready!")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.command()
async def sh(ctx):
    if ctx.message.author.id not in py_admin:
        ctx.message.reply("管理者が行ってください。")
        return
    if ctx.message.content == "n#sh":
        embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        await ctx.message.add_reaction("\U0000274C")
        return
    mes = ctx.message.content[5:].splitlines()
    cmd_nm = len(mes)
    cmd_rt = []
    print(mes)
    for i in range(cmd_nm):
        try:
            export = subprocess.run(f'{mes[i]}', stdout=PIPE, stderr=PIPE, shell=True, text=True)
            cmd_rt.append(export.stdout[:-1])
        except BaseException as err:
            await ctx.message.add_reaction("\U0000274C")
            embed = discord.Embed(title="Error", description=f"Shell error has occurred!\n・Pythonエラー```{err}```\n・スクリプトエラー```{export.stdout}```", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return
    await ctx.message.add_reaction("\U0001F197")
    for i in range(len(cmd_rt)):
        rt_cmd = "\n".join(cmd_rt)
    await ctx.message.reply(rt_cmd)
    return

@bot.command()
async def py(ctx):
    if ctx.message.author.id not in py_admin:
        ctx.message.reply("管理者が行ってください。")
        return
    if ctx.message.content == "n#py":
        embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
        await ctx.message.reply(embed=embed)
        await ctx.message.add_reaction("\U0000274C")
        return
    if ctx.message.content[:10] == "n#py await":
        if ctx.message.content == "n#py await":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
    mes = ctx.message.content[5:].splitlines()
    cmd_nm = len(mes)
    cmd_rt = []
    print(mes)
    for i in range(cmd_nm):
        if re.search(r'(?:await)', mes[i]):
            try:
                mes_py = mes[i].split(" ", 1)[1]
                cmd_rt.append(await eval(mes_py))
            except BaseException as err:
                await ctx.message.add_reaction("\U0000274C")
                embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
                await ctx.message.reply(embed=embed)
                return
        else:
            try:
                exec(mes[i])
                cmd_rt.append("")
            except BaseException as err:
                await ctx.message.add_reaction("\U0000274C")
                embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
                await ctx.message.reply(embed=embed)
                return
    await ctx.message.add_reaction("\U0001F197")
    return

@bot.command()
async def line_send(ctx):
    try:
        if len(ctx.message.content) <= 12:
            await ctx.message.reply(embed = discord.Embed(title="エラー", description="なんか...足りなくね？", color=0xff0000))
            return
        add_token = ctx.message.content[10:]
        if ctx.message.guild.id not in line.tokens:
            line.tokens[ctx.message.guild.id] = {ctx.message.channel.id:add_token}
        elif ctx.message.guild.id in line.tokens:
            if ctx.message.channel.id in line.tokens[ctx.message.guild.id]:
                await ctx.message.reply("上書きしますで...？")
                line.tokens[ctx.message.guild.id][ctx.message.channel.id] = add_token
            else:
                line.tokens[ctx.message.guild.id][ctx.message.channel.id] = add_token
        await ctx.message.reply("多分終わったよっ")
        return
    except BaseException as err:
        await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))

bot.run(bot_token.nira_dev)