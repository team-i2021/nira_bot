from discord.ext import commands
import discord
import pickle

import sys
from cogs.embed import embed
sys.path.append('../')
from util import admin_check, n_fc, eh

class get_reaction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, react, mem):
        # SteamServerListのリスト
        try:
            if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "サーバーリストを削除しますか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
                if n_fc.admin_check(react.message.guild, mem) or react.message.author.id in n_fc.py_admin:
                    if str(react.emoji) == "\U00002B55":
                        del n_fc.steam_server_list[react.message.guild.id]
                        with open('steam_server_list.nira', 'wb') as f:
                            pickle.dump(n_fc.steam_server_list, f)
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                        if mem.id == 669178357371371522:
                            embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                        await react.message.channel.send(embed=embed)
                        await self.bot.http.delete_message(react.message.channel.id, react.message.id)
                        return
                    elif str(react.emoji) == "\U0000274C":
                        await self.bot.http.delete_message(react.message.channel.id, react.message.id)
                        return
                else:
                    user = await self.bot.fetch_user(mem.id)
                    await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーのカスタムサーバーリスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                    return
        except KeyError as err:
            await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
            return
        except BaseException as err:
            await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
            return
        # 追加返答のリスト
        try:
            if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and react.message.content == "追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル":
                if n_fc.admin_check(react.message.guild, mem) or react.message.author.id in n_fc.py_admin:
                    if str(react.emoji) == "\U00002B55":
                        del n_fc.ex_reaction_list[react.message.guild.id]
                        with open('ex_reaction_list.nira', 'wb') as f:
                            pickle.dump(n_fc.ex_reaction_list, f)
                        embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\nリストは正常に削除されました。", color=0xffffff)
                        if mem.id == 669178357371371522:
                            embed = discord.Embed(title="リスト削除", description=f"{mem.mention}\ndic deleted.", color=0xffffff)
                        await react.message.channel.send(embed=embed)
                        await self.bot.http.delete_message(react.message.channel.id, react.message.id)
                        return
                    elif str(react.emoji) == "\U0000274C":
                        await self.bot.http.delete_message(react.message.channel.id, react.message.id)
                        return
                else:
                    user = await self.bot.fetch_user(mem.id)
                    await user.send(embed=discord.Embed(title="リスト削除", description=f"{react.message.guild.name}のサーバーの追加返答リスト削除メッセージにインタラクトされましたが、あなたには権限がないため実行できませんでした。", color=0xff0000))
                    return
        except KeyError as err:
            await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\nこのサーバーにはリストが登録されていません。\n```{err}```", color=0xff0000))
            return
        except BaseException as err:
            await react.message.channel.send(embed=discord.Embed(title="エラー", description=f"{mem.mention}\n大変申し訳ございません。エラーが発生しました。\n```{err}```", color=0xff0000))
            return
        #メッセ削除
        if mem.id != 892759276152573953 and react.message.author.id == 892759276152573953 and str(react.emoji) == '<:trash:908565976407236608>':
            await self.bot.http.delete_message(react.message.channel.id, react.message.id)
            return

def setup(bot):
    bot.add_cog(get_reaction(bot))