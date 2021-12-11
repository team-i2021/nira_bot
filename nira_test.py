import discord
from discord.ext import commands

import bot_token
import os
import sys

bot = discord.Bot(command_prefix="n#")

@bot.event
async def on_ready():
    bot.add_application_command(hello)
    bot.add_application_command(restart)
    bot.add_application_command(hi)
    print(bot.application_commands)
    print(bot.pending_application_commands)
    print(bot.get_application_command(hello))
    print(bot.get_application_command(restart))

@bot.slash_command()
async def hello(ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"Hello {name}!")

@bot.slash_command()
async def restart(ctx, text: str = None):
    await ctx.respond("再起動します。")
    os.execl(sys.executable, 'python', "nira_test.py")

@bot.user_command(name="Say Hello")
async def hi(ctx, user):
    await ctx.respond(f"{ctx.author.mention} says hello to {user.name}!")


bot.run(bot_token.nira_dev)