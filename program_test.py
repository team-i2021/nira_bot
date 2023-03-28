import nextcord
import os
import sys
import json
import traceback

from motor import motor_asyncio

from util import nira, database

SETTING = json.load(open(f"{sys.path[0]}/setting.json", "r"))


CLIENT = database.openClient()
_MONGO_CLIENT = motor_asyncio.AsyncIOMotorClient(SETTING["database_url"])

bot = nira.NIRA(
    help_command=None,
    client=CLIENT, # http_db
    mongo=_MONGO_CLIENT, # mongo_db
    database_name=SETTING["database_name"],
    shard_id=SETTING["shard_id"],
    shard_count=SETTING["shard_count"],
    settings=SETTING,
)

print("NIRA Test")
print(f"nextcord version: {nextcord.__version__}")
cogs = [cog for cog in os.listdir("cogs") if cog != "__pycache__"]
print(f"Cog(s) under test: {cogs}")

print("##### Starting test... #####")

success = 0

for cog in cogs:
    print(f"? {cog}", end="")
    if os.path.isdir(f"cogs/{cog}"):
        if os.path.exists(f"cogs/{cog}/__init__.py"):
            print(f"\rD {cog}")
            print(f"  ? {cog}/__init__.py", end="")
            try:
                bot.load_extension(f"cogs.{cog}")
                success += 1
                print(f"\r  O {cog}/__init__.py")
            except Exception as err:
                print(f"\r  ! {cog}/__init__.py\n{err}")
                traceback.print_exc()
        continue
    try:
        bot.load_extension(f"cogs.{'.'.join(cog.split('.')[:-1])}")
        success += 1
        print(f"\rO {cog}")
    except Exception as err:
        print(f"\r! {cog}\n{err}")
        traceback.print_exc()

print(f"##### Test finished. {success}/{len(cogs)} succeeded. #####")
