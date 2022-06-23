import asyncio
import traceback
from nextcord.ext import commands
import nextcord
import os
import sys
import logging
from nextcord import Interaction, SlashOption, ChannelType
from cogs.debug import save

sys.path.append('../')
from util import admin_check, n_fc, eh

# join message system
# Copilotでちょっとだけ楽をした。


class welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="welcome", aliases=("youkoso","goodbye","ようこそ","Welcome"), help="""\
ユーザーが加入/離脱したときに、特定のメッセージをこのチャンネルに送信するようにします。
書き方: `n!welcome [join/leave]` `[メッセージ]`
(メッセージは複数行可能です。)

メッセージ内には`%name%`/`%count%`/`%ment%`と入れることで、それぞれ`ユーザー名`/`ユーザー数`/`メンション`に置き換わります。

・例
```
n!welcome join %name%さんこんちゃ！！！！！
```

```
n!welcome leave %name%さんばいばい！！！
```

メッセージの部分に`off`と入力すると、設定を削除します。

・例
```
n!welcome join off
```

```
n!welcome leave off
```
""")
    async def welcome(self, ctx: commands.Context):
        if not admin_check.admin_check(ctx.guild, ctx.author):
            await ctx.reply("・Welcomeメッセージコマンド\nエラー：権限がありません。")
            return  
        args = ctx.message.content.split(" ", 3)
        if len(args) != 3:
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー：書き方が間違っています。")
            return
        if args[1] != "join" and args[1] != "leave":
            await ctx.reply(f"・Welcomeメッセージコマンド\nエラー：書き方が間違っています。")
            return
        if args[2] == "off":
            if ctx.guild.id in n_fc.welcome_message_list:
                if args[1] in n_fc.welcome_message_list[ctx.guild.id]:
                    del n_fc.welcome_message_list[ctx.guid.id][args[1]]
                else:
                    await ctx.reply(f"・Welcomeメッセージコマンド\n{args[1]}用メッセージは設定されていません。")
            else:
                await ctx.reply(f"・Welcomeメッセージコマンド\n`{ctx.guild.name}`には設定されていません。")
            return
        if ctx.guild.id not in n_fc.welcome_message_list:
            n_fc.welcome_message_list[ctx.guild.id] = {args[1]: (args[2], ctx.channel.id)}
        else:
            n_fc.welcome_message_list[ctx.guild.id][args[1]] = (args[2], ctx.channel.id)
        await ctx.reply(f"・Welcomeメッセージコマンド\n・成功\n```\n{args[2]}```\n`{ctx.channel.name}`にメッセージを設定しました。")
        save()
        return

    @nextcord.slash_command(name="welcome",description="誰かがサーバー加入/離脱した時にメッセージを送信します。", guild_ids=n_fc.GUILD_IDS)
    async def welcome_slash(self, interaction: Interaction):
        pass

    @welcome_slash.subcommand(name="set",description="サーバー加入/離脱時のメッセージを指定します")
    async def set_slash(
            self,
            interaction: Interaction,
            MessageType: int = SlashOption(
                name="message_type",
                description="サーバー参加時か離脱時かを選択してください",
                required=True,
                choices={"参加時": 1, "離脱時": 2}
            ),
            message: str = SlashOption(
                name="message",
                description="送信するメッセージ内容",
                required=True
            )
        ):
        await interaction.response.defer()
        try:
            if MessageType == 1:
                if interaction.guild.id not in n_fc.welcome_message_list:
                    n_fc.welcome_message_list[interaction.guild.id] = {'join': (message, interaction.channel.id)}
                else:
                    n_fc.welcome_message_list[interaction.guild.id]['join'] = (message, interaction.channel.id)
                await interaction.followup.send(embed=nextcord.Embed(title=f"参加時のメッセージ表示", description=f"・成功\n```\n{message}```\n`{interaction.channel.name}`にメッセージを設定しました。", color=0x00ff00), ephemeral=True)
            elif MessageType == 2:
                if interaction.guild.id not in n_fc.welcome_message_list:
                    n_fc.welcome_message_list[interaction.guild.id] = {'leave': (message, interaction.channel.id)}
                else:
                    n_fc.welcome_message_list[interaction.guild.id]['leave'] = (message, interaction.channel.id)
                await interaction.followup.send(embed=nextcord.Embed(title=f"離脱時のメッセージ表示", description=f"・成功\n```\n{message}```\n`{interaction.channel.name}`にメッセージを設定しました。", color=0x00ff00), ephemeral=True)
            save()
            return
        except BaseException as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome set [**kwargs]`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return

    @welcome_slash.subcommand(name="del",description="サーバー加入/離脱時のメッセージ設定を削除します")
    async def del_slash(
            self,
            interaction: Interaction,
            MessageType: int = SlashOption(
                name="message_type",
                description="サーバー参加時か離脱時かを選択してください",
                required=True,
                choices={"参加時": 1, "離脱時": 2}
            )
        ):
        await interaction.response.defer()
        try:
            if MessageType == 1:
                if interaction.guild.id in n_fc.welcome_message_list:
                    del n_fc.welcome_message_list[interaction.guild.id]["join"]
                    await interaction.followup.send(embed=nextcord.Embed(title=f"参加時のメッセージ表示", description=f"・成功\n設定を削除しました。", color=0x00ff00), ephemeral=True)
                    save()
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"参加時のメッセージ表示", description=f"このサーバーには参加時のメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            elif MessageType == 2:
                if interaction.guild.id in n_fc.welcome_message_list:
                    del n_fc.welcome_message_list[interaction.guild.id]["leave"]
                    await interaction.followup.send(embed=nextcord.Embed(title=f"離脱時のメッセージ表示", description=f"・成功\n設定を削除しました。", color=0x00ff00), ephemeral=True)
                    save()
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"離脱時のメッセージ表示", description=f"このサーバーには離脱時のメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            return
        except BaseException as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome del [**kwargs]`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return

    @welcome_slash.subcommand(name="status",description="サーバー加入/離脱時のメッセージ設定を表示します")
    async def status_slash(
            self,
            interaction: Interaction,
            MessageType: int = SlashOption(
                name="message_type",
                description="サーバー参加時か離脱時かを選択してください",
                required=True,
                choices={"参加時": 1, "離脱時": 2}
            )
        ):
        await interaction.response.defer()
        try:
            if MessageType == 1:
                if interaction.guild.id in n_fc.welcome_message_list:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"参加時のメッセージ表示", description=n_fc.welcome_message_list[interaction.guild.id]["join"][0], color=0x00ff00), ephemeral=True)
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"参加時のメッセージ表示", description=f"このサーバーには参加時のメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            elif MessageType == 2:
                if interaction.guild.id in n_fc.welcome_message_list:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"離脱時のメッセージ表示", description=n_fc.welcome_message_list[interaction.guild.id]["leave"][0], color=0x00ff00), ephemeral=True)
                else:
                    await interaction.followup.send(embed=nextcord.Embed(title=f"離脱時のメッセージ表示", description=f"このサーバーには離脱時のメッセージ表示が設定されていません。", color=0xff0000), ephemeral=True)
            return
        except BaseException as err:
            await interaction.followup.send("コマンド実行時にエラーが発生しました。", embed=nextcord.Embed(title=f"An error has occurred during `/welcome status`", description=f"```py\n{err}```\n```py\n{traceback.format_exc()}```", color=0xff0000), ephemeral=True)
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id not in n_fc.welcome_message_list:
            return
        if "join" not in n_fc.welcome_message_list[member.guild.id]:
            return
        message = n_fc.welcome_message_list[member.guild.id]["join"][0]
        message = message.replace("%name%", member.name)
        message = message.replace("%count%", str(len(member.guild.members)))
        message = message.replace("%ment%", member.mention)
        CHANNEL = member.guild.get_channel(n_fc.welcome_message_list[member.guild.id]["join"][1])
        await CHANNEL.send(message)
        return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id not in n_fc.welcome_message_list:
            return
        if "leave" not in n_fc.welcome_message_list[member.guild.id]:
            return
        message = n_fc.welcome_message_list[member.guild.id]["leave"][0]
        message = message.replace("%name%", member.name)
        message = message.replace("%count%", str(len(member.guild.members)))
        message = message.replace("%ment%", member.mention)
        CHANNEL = member.guild.get_channel(n_fc.welcome_message_list[member.guild.id]["leave"][1])
        await CHANNEL.send(message)
        return

def setup(bot):
    bot.add_cog(welcome(bot))
