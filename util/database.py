import json
import logging
import os
import sys
import HTTP_db
import traceback

from util import dict_list


__version__ = "util"
GUILD_VALUE = 0 # {GUILD.id: value}
CHANNEL_VALUE = 1 # {GUILD.id: {CHANNEL.id: value}}
OTHER_VALUE = 2


def openClient() -> HTTP_db.Client:
    url = str(json.load(open(f"{sys.path[0]}/setting.json", "r"))["database_data"]["address"])
    if os.path.isfile(f"{sys.path[0]}/password"):
        password = open(f"{sys.path[0]}/password", "r").read()
        return HTTP_db.Client(url=url, password=password)
    else:
        return HTTP_db.Client(url=url)


async def default_pull(client: HTTP_db.Client, obj: object) -> dict:
    if obj.value_type == CHANNEL_VALUE:
        if not await client.exists(obj.name):
            await client.post(obj.name, dict_list.dictToList(obj.default))
        try:
            data = dict_list.listToDict(await client.get(obj.name))
            obj.value = data
        except Exception:
            logging.error(traceback.format_exc())
            obj.value = obj.default
    elif obj.value_type == GUILD_VALUE:
        if not await client.exists(obj.name):
            await client.post(obj.name, list(obj.default.items()))
        try:
            data = dict(await client.get(obj.name))
            obj.value = data
        except Exception:
            logging.error(traceback.format_exc())
            obj.value = obj.default
    else:
        raise ValueError("value_type is not defined.")


async def default_push(client: HTTP_db.Client, obj: object) -> None:
    if obj.value_type == CHANNEL_VALUE:
        try:
            await client.post(obj.name, dict_list.dictToList(obj.value))
            return None
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e
    elif obj.value_type == GUILD_VALUE:
        try:
            await client.post(obj.name, list(obj.value.items()))
            return None
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e
    else:
        raise ValueError("value_type is not defined.")
