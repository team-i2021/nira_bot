from types import BuiltinMethodType
import discord
from discord import message
from discord.ext import commands
from discord.ext.commands.bot import Bot
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
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
from subprocess import PIPE
import web_api
from discord.embeds import Embed
sys.setrecursionlimit(10000)#エラー回避
import pickle
from discord.flags import MessageFlags
py_admin = [669178357371371522]
from discord_buttons_plugin import *

# NIRA BOT for DEV
# バージョン及び権利は全て、にらBOTと同じです。

intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.members = True


bot = commands.Bot(command_prefix="n#", intents=intents)
buttons = ButtonsClient(bot)

def bot_reboot(event):
    messagebox.showinfo("操作", "にらBOTを再起動します。")
    os.execl(sys.executable, 'python3.7', "test.py")

def bot_func_read(event):
    try:
        with open("steam_server_list.nira", "rb") as f:
            messagebox.showinfo("steam_server_list", pickle.load(f))
    except BaseException as err:
        messagebox.showinfo("steam_server_list", f"エラーが発生しました。\n{err}")
    try:
        with open("reaction_bool_list.nira", "rb") as f:
            messagebox.showinfo("reaction_bool_list", pickle.load(f))
    except BaseException as err:
        messagebox.showinfo("reaction_bool_list", f"エラーが発生しました。\n{err}")
    try:
        with open("srtr_bool_list.nira", "rb") as f:
            messagebox.showinfo("srtr_bool_list", pickle.load(f))
    except BaseException as err:
        messagebox.showinfo("srtr_bool_list", f"エラーが発生しました。\n{err}")
    try:
        with open("ex_reaction_list.nira", "rb") as f:
            messagebox.showinfo("ex_reaction_list", pickle.load(f))
    except BaseException as err:
        messagebox.showinfo("ex_reaction_list", f"エラーが発生しました。\n{err}")
    try:
        with open("welcome_id_list.nira", "rb") as f:
            messagebox.showinfo("welcome_id_list", pickle.load(f))
    except BaseException as err:
        messagebox.showinfo("welcome_id_list", f"エラーが発生しました。\n{err}")

def bot_send_mes(event):
    url = tk_channel.get()
    body = {"content": tk_message.get()}
    requests.post(url, body)

main_window = tk.Tk()
main_window.title("にらBOT - Main window")
main_window.geometry("1600x900")


# メインフレームの作成と設置
frame = tk.Frame(main_window)
frame.pack(padx=20,pady=10)

ttk.Label(text="=====再起動ボタン=====").pack()
bt_reboot = ttk.Button(text="再起動", width=100)
bt_reboot.bind("<Button-1>",bot_reboot)
bt_reboot.pack()
ttk.Label(text="\n\n=====Webhookでメッセージ送信=====").pack()
ttk.Label(text="・WebhookURL").pack()
tk_channel = ttk.Entry(width=100)
tk_channel.pack()
ttk.Label(text="・Message").pack()
tk_message = ttk.Entry(width=100)
tk_message.pack()
bt_reboot = ttk.Button(text="メッセージ送信", width=100)
bt_reboot.bind("<Button-1>",bot_send_mes)
bt_reboot.pack()
ttk.Label(text="\n\n=====変数=====").pack()
bt_func = ttk.Button(text="変数表示", width=100)
bt_func.bind("<Button-1>",bot_func_read)
bt_func.pack()

def on_config(event):
    event.widget.config(width=main_window.winfo_width())


@bot.event
async def on_ready():
    print("Ready!")
    bot.loop.run_in_executor(None, main_window.mainloop)


@buttons.click
async def button_ephemeral(ctx):
    print(ctx.message)
    await ctx.reply("お前にしか見えないメッセージだぜ...(ｲｹｳﾞｫ)", flags = MessageFlags().EPHEMERAL)


@bot.command(name="del")
async def delet(ctx):
    if ctx.message.author.id in py_admin:
        await buttons.send(
            content = "追加反応リストの削除", 
            channel = ctx.channel.id,
            components = [ 
                ActionRow([
                    Button(
                        label="削除する",
                        style=ButtonType().Danger,
                        custom_id="button_ephemeral"
                    )
                ])
            ]
        )
    else:
        await ctx.message.reply(embed=discord.Embed(title="エラー", description="あなたの権限では使えません。", color=0xff0000))
    return


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
        if ctx.message.guild.id not in web_api.tokens:
            web_api.tokens[ctx.message.guild.id] = {ctx.message.channel.id:add_token}
        elif ctx.message.guild.id in web_api.tokens:
            if ctx.message.channel.id in web_api.tokens[ctx.message.guild.id]:
                await ctx.message.reply("上書きしますで...？")
                web_api.tokens[ctx.message.guild.id][ctx.message.channel.id] = add_token
            else:
                web_api.tokens[ctx.message.guild.id][ctx.message.channel.id] = add_token
        await ctx.message.reply("多分終わったよっ")
        return
    except BaseException as err:
        await ctx.message.reply(embed=discord.Embed(title="エラー",description=f"```{err}```\n```sh\n{sys.exc_info()}```",color=0xff0000))

bot.run(bot_token.nira_dev)

