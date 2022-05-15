from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import nextcord
import pickle
import math

import sys,os

sys.path.append('../')
from util import admin_check, n_fc, eh, web_api

DIR = sys.path[0]

#通常反応や追加反応の反応系

class NotifyTokenSet(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "LINE Notify設定",
            timeout=None
        )

        self.token = nextcord.ui.TextInput(
            label="LINE Notify TOKEN",
            style=nextcord.TextInputStyle.short,
            placeholder="トークンを入力してください",
            required=True
        )
        self.add_item(self.token)
        #self.add_item(nextcord.ui.Button("トークンを設定する", style=nextcord.ButtonStyle.green, custom_id="token_set"))
        #self.add_item(nextcord.ui.Button("キャンセル", style=nextcord.ButtonStyle.red, custom_id="cancel"))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        if self.token.value == "" or self.token.value is None:
            await interaction.followup.send("トークンは必須です。", ephemeral=True)
            return
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.followup.send("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
        else:
            token_result = web_api.line_token_check(self.token.value)
            if token_result[0] == False:
                await interaction.followup.send(f"そのトークンは無効なようです。\n```{token_result[1]}```", ephemeral = True)
                return
            if interaction.guild.id not in n_fc.notify_token:
                n_fc.notify_token[interaction.guild.id] = {interaction.channel.id: self.token.value}
            else:
                n_fc.notify_token[interaction.guild.id][interaction.channel.id] = self.token.value
            with open(f'{DIR}/notify_token.nira', 'wb') as f:
                pickle.dump(n_fc.notify_token, f)
            await interaction.followup.send(f"{interaction.guild.name}/{interaction.channel.name}で`{self.token.value}`を保存します。\nトークンが他のユーザーに見られないようにしてください。", ephemeral = True)


class reaction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="line", help="""\
DiscordのメッセージをLINEに送信します。
LINE Notifyという機能を用いて、DiscordのメッセージをLINEに送信します。""")
    async def line(self, ctx: commands.Context):
        embed = nextcord.Embed(title="DiscordのメッセージをLINEに送信する機能", description="使い方", color=0x00ff00)
        embed.add_field(name="**このコマンドはスラッシュコマンドです**", value="`/line set`というスラッシュコマンドを送ると、TOKENを入力する画面が表示されるので、そこにTOKENを入力してください。\nちなみにTOKENの流出はとんでもないことにつながるので、気をつけてください。", inline=False)
        embed.add_field(name="**TOKENって何？**", value="TOKENとは簡単に言えばパスワードです。LINE Notifyのページから発行してきてください。\n[TOKENの発行方法](https://qiita.com/nattyan_tv/items/33ac7a7269fe12e49198)", inline=False)
        await ctx.reply(embed=embed)

    @commands.command(name="er", help="""\
追加で新しいにらの反応を作り出すことが出来ます。
オートリプライとかって呼ばれるんですかね？まぁ、トリガーとリターンを指定することで、トリガーが送信された際に指定したリターンを送信することが出来ます。
トリガーには正規表現を使うことが出来ます。が、スペースを含むことはできませんのでご了承ください。""")
    async def er(self, ctx: commands.Context):
        if ctx.message.content[:8] == "n!er add":
            if ctx.message.content == "n!er add":
                await ctx.message.reply("構文が異なります。\n```n!er add [トリガー] [返信文]```")
                return
            try:
                if ctx.message.guild.id not in n_fc.ex_reaction_list:
                    n_fc.ex_reaction_list[ctx.message.guild.id] = {"value":0}
                value = n_fc.ex_reaction_list[ctx.message.guild.id]["value"]
                ra = ctx.message.content[9:].split(" ", 1)
                react_triger = ra[0]
                react_return = ra[1]
                n_fc.ex_reaction_list[ctx.message.guild.id]["value"] = n_fc.ex_reaction_list[ctx.message.guild.id]["value"]+1
                n_fc.ex_reaction_list[ctx.message.guild.id][f'{value+1}_tr'] = str(react_triger)
                n_fc.ex_reaction_list[ctx.message.guild.id][f'{value+1}_re'] = str(react_return)
                await ctx.message.reply(f"トリガー：{ra[0]}\nリターン：{ra[1]}")
                with open(f'{DIR}/ex_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.ex_reaction_list, f)
                return
            except BaseException as err:
                await ctx.message.reply(embed=eh.eh(err))
        if ctx.message.content[:9] == "n!er list":
            if ctx.message.guild.id not in n_fc.ex_reaction_list or n_fc.ex_reaction_list[ctx.message.guild.id]["value"] == 0:
                await ctx.message.reply("追加返答は設定されていません。")
                return
            else:
                embed = nextcord.Embed(title="追加返答リスト", description="- にらBOT", color=0x00ff00)
                for i in range(int(n_fc.ex_reaction_list[ctx.message.guild.id]["value"])):
                    embed.add_field(name=f"トリガー：{n_fc.ex_reaction_list[ctx.message.guild.id][f'{i+1}_tr']}", value=f"リターン：{n_fc.ex_reaction_list[ctx.message.guild.id][f'{i+1}_re']}", inline=False)
                await ctx.message.reply(embed=embed)
                return
        if ctx.message.content.split(" ",1)[1][:4] == "edit":
            if ctx.message.content.split(" ",1)[1] == "edit":
                await ctx.message.reply("構文が異なります。\n```n!er edit [トリガー] [返信文]```")
                return
            if ctx.message.guild.id not in n_fc.ex_reaction_list:
                await ctx.message.reply("追加反応は登録されていません。")
                return
            if n_fc.ex_reaction_list[ctx.message.guild.id]["value"] == 0:
                await ctx.message.reply("追加反応は登録されていません。")
                return
            ssrt = ctx.message.content.split(" ", 3) # n!er,edit,triger,reply
            b_tr = ssrt[2]
            b_re = ssrt[3]
            try:
                rt_e = 0
                for i in range(math.floor((len(n_fc.ex_reaction_list[ctx.message.guild.id])-1)/2)):
                    if n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_tr"] == b_tr:
                        n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_re"] = b_re
                        rt_e = 1
                        break
                if rt_e == 1:
                    await ctx.message.reply(f"トリガー：{b_tr}\nリターン：{b_re}")
                    with open(f'{DIR}/ex_reaction_list.nira', 'wb') as f:
                        pickle.dump(n_fc.ex_reaction_list, f)
                    return
                elif rt_e == 0:
                    await ctx.message.reply("そのトリガーは登録されていません！")
                    return
            except BaseException as err:
                await ctx.message.reply(embed=eh.eh(err))
                return
        if ctx.message.content.split(" ",1)[1][:3] == "del":
            if ctx.message.guild.id not in n_fc.ex_reaction_list:
                await ctx.message.reply("追加返答は設定されていません。")
                return
            else:
                if ctx.message.content.split(" ",1) == "del all":
                    del_re = await ctx.message.reply("追加返答のリストを削除してもよろしいですか？リスト削除には管理者権限が必要です。\n\n:o:：削除\n:x:：キャンセル")
                    await del_re.add_reaction("\U00002B55")
                    await del_re.add_reaction("\U0000274C")
                    return
                elif ctx.message.content.split(" ",1) == "del":
                    await ctx.reply("コマンドの引数が足りません。\n全削除:`n!er del all`\n特定の返答を削除:`n!er del [トリガー]`")
                    return
                else:
                    result = None
                    triger = ctx.message.content.split(" ",2)[2]
                    for i in range(math.floor((len(n_fc.ex_reaction_list[ctx.message.guild.id])-1)/2)):
                        if n_fc.ex_reaction_list[ctx.message.guild.id][f"{i+1}_tr"] == triger:
                            result = i
                            break
                        continue
                    if result == None:
                        await ctx.reply(f"`{triger}`というトリガーが見つかりませんでした。\n不具合がある場合は全消しするか、サポートサーバーへご連絡ください。")
                        return
                    for i in range(math.floor((len(n_fc.ex_reaction_list[ctx.message.guild.id])-1)/2)-(result+1)):
                        n_fc.ex_reaction_list[ctx.message.guild.id][f"{result+i+1}_tr"] = n_fc.ex_reaction_list[ctx.message.guild.id][f"{result+i+2}_tr"]
                        n_fc.ex_reaction_list[ctx.message.guild.id][f"{result+i+1}_re"] = n_fc.ex_reaction_list[ctx.message.guild.id][f"{result+i+2}_re"]
                    await ctx.reply("Ok")
                    return
        return
    
    @commands.command(name="nr", help="""\
にらBOTの通常反応（にらとか）を無効にしたりすることが出来ます。
`n!nr`:今の状態を表示
`n!nr off`:通常反応を無効化
`n!nr on`:通常反応を有効化
`n!nr all off`:通常反応を**サーバーで**無効化
`n!nr all on`:通常反応を**サーバーで**有効化""")
    async def nr(self, ctx: commands.Context):
        try:
            if ctx.message.guild.id not in n_fc.reaction_bool_list: # 通常反応のブール値存在チェック
                n_fc.reaction_bool_list[ctx.message.guild.id] = {}
                n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 1
                with open(f'{DIR}/reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.reaction_bool_list, f)
            if ctx.message.channel.id not in n_fc.reaction_bool_list[ctx.message.guild.id]:
                n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                with open(f'{DIR}/reaction_bool_list.nira', 'wb') as f:
                    pickle.dump(n_fc.reaction_bool_list, f)
            if ctx.message.content == "n!nr":
                if n_fc.reaction_bool_list[ctx.message.guild.id]["all"] == 0:
                    setting = "サーバーで無効になっている為、チャンネルごとの設定は無効です。\n(`n!help nr`でご確認ください。)"
                elif n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] == 1:
                    setting = "有効"
                elif n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description=f"通常反応の設定:{setting}\n\n`n!nr [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                nr_setting = str((ctx.message.content).split(" ", 1)[1])
                if nr_setting in n_fc.on_ali:
                    n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                    await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を有効にしました。", color=0x00ff00))
                elif nr_setting in n_fc.off_ali:
                    n_fc.reaction_bool_list[ctx.message.guild.id][ctx.message.channel.id] = 0
                    await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="チャンネルでの通常反応を無効にしました。", color=0x00ff00))
                elif nr_setting[:3] == "all":
                    if nr_setting in n_fc.on_ali:
                        n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 1
                        await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を有効にしました。", color=0x00ff00))
                    elif nr_setting in n_fc.off_ali:
                        n_fc.reaction_bool_list[ctx.message.guild.id]["all"] = 0
                        await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="サーバーでの通常反応を無効にしました。", color=0x00ff00))
                    else:
                        await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
                else:
                    await ctx.message.reply(embed=nextcord.Embed(title="Normal Reaction Setting", description="コマンド使用方法:`n!nr [all] [on/off]`", color=0xff0000))
                return
            else:
                await ctx.message.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return
    
    @commands.command(name="ar",help="""\
にらBOTの通常反応及び追加反応(Bump通知および`n!`コマンド以外のすべて)を無効にしたりすることが出来ます。
`n!ar`:今の状態を表示
`n!ar off`:全反応を無効化
`n!ar on`:全反応を有効化

チャンネルトピックに`nira-off`と入れておくと、そのチャンネルでは反応を無効化します。""")
    async def ar(self, ctx: commands.Context):
        try:
            if ctx.message.guild.id not in n_fc.all_reaction_list:
                print(n_fc.all_reaction_list)
                n_fc.all_reaction_list[ctx.message.guild.id] = {}
                with open(f'{DIR}/all_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.all_reaction_list, f)
            if ctx.message.channel.id not in n_fc.all_reaction_list[ctx.message.guild.id]:
                n_fc.all_reaction_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                with open(f'{DIR}/all_reaction_list.nira', 'wb') as f:
                    pickle.dump(n_fc.all_reaction_list, f)
            if ctx.message.content == "n!ar":
                if n_fc.all_reaction_list[ctx.message.guild.id][ctx.message.channel.id] == 1:
                    setting = "有効"
                elif n_fc.all_reaction_list[ctx.message.guild.id][ctx.message.channel.id] == 0:
                    setting = "無効"
                else:
                    setting = "読み込めませんでした。"
                await ctx.message.reply(embed=nextcord.Embed(title="All Reaction Setting", description=f"「通常反応」及び「追加反応」（Bump通知および各種コマンドは除く）の設定:{setting}\n\n`n!ar [on/off]`で変更できます。", color=0x00ff00))
                return
            if admin_check.admin_check(ctx.message.guild, ctx.message.author) or ctx.message.author.id in n_fc.py_admin:
                ar_setting = str((ctx.message.content).split(" ", 1)[1])
                if ar_setting in n_fc.on_ali:
                    n_fc.all_reaction_list[ctx.message.guild.id][ctx.message.channel.id] = 1
                    await ctx.message.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を有効にしました。", color=0x00ff00))
                elif ar_setting in n_fc.off_ali:
                    n_fc.all_reaction_list[ctx.message.guild.id][ctx.message.channel.id] = 0
                    await ctx.message.reply(embed=nextcord.Embed(title="All Reaction Setting", description="チャンネルでの全反応を無効にしました。", color=0x00ff00))
                else:
                    await ctx.message.reply(embed=nextcord.Embed(title="All Reaction Setting", description="コマンド使用方法:`n!ar [all] [on/off]`", color=0xff0000))
                return
            else:
                await ctx.message.reply(embed=nextcord.Embed(title="Error", description=f"管理者権限がありません。", color=0xff0000))
                return
        except BaseException as err:
            await ctx.message.reply(embed=eh.eh(err))
            return
    
    @nextcord.slash_command(name="line", description="LINE Notifyの設定")
    async def line_slash(self, interaction: Interaction):
        pass

    @line_slash.subcommand(name="set", description="LINE Notifyのトークンを設定します。")
    async def line_set_slash(self, interaction: Interaction):
        modal = NotifyTokenSet()
        await interaction.response.send_modal(modal=modal)

    @line_slash.subcommand(name="del", description="LINE Notifyのトークンを削除します。")
    async def line_del_slash(self, interaction: Interaction):
        if admin_check.admin_check(interaction.guild, interaction.user) == False:
            await interaction.response.send_message("あなたにはサーバーの管理権限がないため実行できません。", ephemeral = True)
        else:
            if interaction.guild.id not in n_fc.notify_token:
                await interaction.response.send_message(f"{interaction.guild.name}では、LINEトークンが設定されていません。", ephemeral = True)
                return
            if interaction.channel.id not in n_fc.notify_token[interaction.guild.id]:
                await interaction.response.send_message(f"{interaction.channel.name}では、LINEトークンが設定されていません。", ephemeral = True)
                return
            del n_fc.notify_token[interaction.guild.id][interaction.channel.id]
            with open(f'{DIR}/notify_token.nira', 'wb') as f:
                pickle.dump(n_fc.notify_token, f)
            await interaction.response.send_message(f"{interaction.channel.name}でのLINEトークンを削除しました。", ephemeral = True)

def setup(bot):
    bot.add_cog(reaction(bot))
