from discord.ext import commands
import discord
import os
import pickle
import shutil
import subprocess
from subprocess import PIPE
import re

import sys
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh

#管理者向けdebug

class debug(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def create(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            if ctx.message.content == "n!create":
                await ctx.message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
                return
            c_file_d = str((ctx.message.content).split(" ", 1)[1])
            try:
                with open(c_file_d, 'w'):
                    pass
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
                return
        else:
            await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))

    @commands.command()
    async def py_exec(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            if ctx.message.content == "n!py_exec":
                await ctx.message.reply(embed=discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000))
                return
            e_file = str((ctx.message.content).split(" ", 1)[1])
            try:
                exec(open(e_file).read())
                return
            except BaseException as err:
                await ctx.message.reply(embed=discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000))
                return
        else:
            await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))

    @commands.command()
    async def read(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            await ctx.message.reply(embed=discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000))
            return
        try:
            shutil.copyfile("nira.py", "nira_copy.txt")
            await ctx.message.reply('`nira.py（コピー）`', file=discord.File('nira_copy.txt'))
            os.remove('nira_copy.txt')
            return
        except BaseException as err:
            embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def restart(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            await self.bot.change_presence(activity=discord.Game(name="再起動中...", type=1), status=discord.Status.dnd)
            restart_code = await ctx.message.reply("再起動準備中...")
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(n_fc.steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(n_fc.welcome_id_list, f)
                with open('ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.ex_reaction_list, f)
                with open('srtr_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.srtr_bool_list, f)
                await restart_code.edit(content="RESTART:`nira.py`\n再起動します")
                print("-----[n!restart]コマンドが実行されたため、再起動します。-----")
                os.execl(sys.executable, 'python3.7', "nira.py")
                return
            except BaseException as err:
                await ctx.message.reply(err)
                await self.bot.change_presence(activity=discord.Game(name="n!help", type=1), status=discord.Status.idle)
                return
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def exit(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            await self.bot.change_presence(activity=discord.Game(name="終了中...", type=1), status=discord.Status.dnd)
            exit_code = await ctx.message.reply("終了準備中...")
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(n_fc.steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(n_fc.welcome_id_list, f)
                with open('ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.ex_reaction_list, f)
                with open('srtr_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.srtr_bool_list, f)
                await exit_code.edit(content="STOP:`nira.py`\n終了します")
                print("-----[n!exit]コマンドが実行されたため、終了します。-----")
                await self.bot.logout()
                exit()
                return
            except BaseException as err:
                await ctx.message.reply(err)
                await self.bot.change_presence(activity=discord.Game(name="n!help", type=1), status=discord.Status.idle)
                return
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def py(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content == "n!py":
            embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        if ctx.message.content[:10] == "n!py await":
            if ctx.message.author.id not in n_fc.py_admin:
                embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
                await ctx.message.repcly(embed=embed)
                await ctx.message.add_reaction("\U0000274C")
                return
            if ctx.message.content == "n!py await":
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
                    embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
            else:
                try:
                    exec(mes[i])
                    cmd_rt.append("")
                except BaseException as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = discord.Embed(title="Error", description=f"Python error has occurred!\n```{err}```\n```sh\n{sys.exc_info()}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
        await ctx.message.add_reaction("\U0001F197")
        return

    @commands.command()
    async def sh(self, ctx: commands.Context):
        if ctx.message.author.id not in n_fc.py_admin:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            await ctx.message.add_reaction("\U0000274C")
            return
        else:
            if ctx.message.content == "n!sh":
                embed = discord.Embed(title="Error", description="The command has no enough arguments!", color=0xff0000)
                await ctx.message.reply(embed=embed)
                await ctx.message.add_reaction("\U0000274C")
                return
            mes_sh = ctx.message.content[5:].splitlines()
            sh_nm = len(mes_sh)
            sh_rt = []
            print(mes_sh)
            for i in range(sh_nm):
                try:
                    export = subprocess.run(f'{mes_sh[i]}', stdout=PIPE, stderr=PIPE, shell=True, text=True)
                    sh_rt.append(export.stdout)
                except BaseException as err:
                    await ctx.message.add_reaction("\U0000274C")
                    embed = discord.Embed(title="Error", description=f"Shell error has occurred!\n・Pythonエラー```{err}```\n・スクリプトエラー```{export.stdout}```", color=0xff0000)
                    await ctx.message.reply(embed=embed)
                    return
            await ctx.message.add_reaction("\U0001F197")
            for i in range(len(sh_rt)):
                rt_sh = "\n".join(sh_rt)
            await ctx.message.reply(f"```{rt_sh}```")
            return

    @commands.command()
    async def save(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            try:
                with open('steam_server_list.nira', 'wb') as f:
                    pickle.dump(n_fc.steam_server_list, f)
                with open('reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.reaction_bool_list, f)
                with open('welcome_id_list.nira', 'wb') as f:
                    pickle.dump(n_fc.welcome_id_list, f)
                with open('ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.ex_reaction_list, f)
                with open('srtr_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.srtr_bool_list, f)
                await ctx.message.reply("Saved.")
                print("[save]")
            except BaseException as err:
                await ctx.message.reply(f"Error happend.\n{err}")
            return
        else:
            embed = discord.Embed(title="Error", description="You don't have the required permission!", color=0xff0000)
            await ctx.message.reply(embed=embed)
            return

    @commands.command()
    async def cog(self, ctx: commands.Context):
        if ctx.message.author.id in n_fc.py_admin:
            if ctx.message.content == "n!cog":
                embed = discord.Embed(title="cogs", description="`extension`", color=0x00ff00)
                embed.add_field(name="Cog Names", value="表示されている名前は、`cog.[Cog name]`のcog nameです。", inline=False)
                embed.add_field(name="amuse", value="娯楽系のコマンド。\n`janken`/`uranai`")
                embed.add_field(name="check", value="管理者チェックをするコマンド。\n`check`")
                embed.add_field(name="debug", value="管理者用コマンド。\n`create`/`py_exec`/`read`/`restart`/`exit`/`py`/`sh`/`save`/`cog`")
                embed.add_field(name="embed", value="Embed送信用コマンド。\n`embed`")
                embed.add_field(name="get_reaction", value="リアクションを受け取った際のイベント。")
                embed.add_field(name="info", value="にらBOTの情報系コマンド。\n`info`/`help`")
                embed.add_field(name="music", value="音楽再生(VC)に関するコマンド。\n`join`/`play`/`pause`/`resume`/`stop`/`leave`")
                embed.add_field(name="normal_reaction", value="送信されたメッセージに反応するイベント。")
                embed.add_field(name="ping", value="pingコマンド。\n`ping`")
                embed.add_field(name="reaction", value="反応系コマンド。\n`nr`/`er`")
                embed.add_field(name="siritori", value="しりとり系コマンド。\n`srtr`")
                embed.add_field(name="user_join", value="ユーザーがguildに入った際のイベント。")
                embed.add_field(name="user", value="ユーザー情報表示系コマンド。\n`d`/`ui`")
                embed.add_field(name="Cog function", value="cog系のコマンドです。`[Cog name]`には「`cog.`」を抜いたCogの名前だけを入力してください。", inline=False)
                embed.add_field(name="`n!cog`", value="cogの情報を表示します。")
                embed.add_field(name="`n!cog reload [Cog name]`", value="指定したCogをリロードします。")
                embed.add_field(name="`n!cog load [Cog name]`", value="指定したCogをロードします。")
                embed.add_field(name="`n!cog unload [Cog name]`", value="指定したCogをアンロードします。")
                await ctx.message.reply(embed=embed)
                return
            elif ctx.message.content[:12] == "n!cog reload":
                try:
                    self.bot.reload_extension(f"cogs.{ctx.message.content[13:]}")
                    await ctx.message.add_reaction("\U0001F197")
                except BaseException as err:
                    await ctx.reply(f"リロードできませんでした。\n```{err}```")
                    await ctx.message.add_reaction("\U0000274C")
            elif ctx.message.content[:10] == "n!cog load":
                try:
                    self.bot.load_extension(f"cogs.{ctx.message.content[11:]}")
                    await ctx.message.add_reaction("\U0001F197")
                except BaseException as err:
                    await ctx.reply(f"ロードできませんでした。\n```{err}```")
                    await ctx.message.add_reaction("\U0000274C")
            elif ctx.message.content[:12] == "n!cog unload":
                try:
                    self.bot.unload_extension(f"cogs.{ctx.message.content[13:]}")
                    await ctx.message.add_reaction("\U0001F197")
                except BaseException as err:
                    await ctx.reply(f"アンロードできませんでした。\n```{err}```")
                    await ctx.message.add_reaction("\U0000274C")

def setup(bot):
    bot.add_cog(debug(bot))