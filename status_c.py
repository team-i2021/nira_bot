# coding: utf-8
import discord
import asyncio

async def change(client):
    while True:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"n!help | {len(client.guilds)}サーバー"), status=discord.Status.online)
        await asyncio.sleep(4)
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"n!help | {len(client.users)}ユーザー"), status=discord.Status.online)
        await asyncio.sleep(4)
        await client.change_presence(activity=discord.Game(name=f"n!help | ニラゲーム", type=1), status=discord.Status.online)
        await asyncio.sleep(4)