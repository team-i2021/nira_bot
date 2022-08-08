import asyncio
import json
import logging
import os
import sys
import HTTP_db
import traceback

from util import dict_list


__version__ = "nira_bot/util"
GUILD_VALUE = 0 # {GUILD.id: value}
CHANNEL_VALUE = 1 # {GUILD.id: {CHANNEL.id: value}}
SAME_VALUE = 2 # 変換しない
OTHER_VALUE = 3


def openClient() -> HTTP_db.Client:
    url = str(json.load(open(f"{sys.path[0]}/setting.json", "r"))["database_url"])
    if os.path.isfile(f"{sys.path[0]}/password"):
        password = open(f"{sys.path[0]}/password", "r").read()
        return HTTP_db.Client(url=url, password=password)
    else:
        return HTTP_db.Client(url=url)


async def default_pull(client: HTTP_db.Client, obj: object) -> None:
    """Pull from database."""
    if obj.value_type == CHANNEL_VALUE:
        try:
            data = dict_list.listToDict(await client.get(obj.name))
            obj.value = data
        except HTTP_db.DatabaseKeyError:
            obj.value = obj.default
            asyncio.ensure_future(client.post(obj.name, dict_list.dictToList(obj.default)))
        except Exception:
            obj.value = obj.default
            logging.error(traceback.format_exc())
    elif obj.value_type == GUILD_VALUE:
        try:
            data = dict(await client.get(obj.name))
            obj.value = data
        except HTTP_db.DatabaseKeyError:
            obj.value = obj.default
            asyncio.ensure_future(client.post(obj.name, list(obj.default.items())))
        except Exception:
            obj.value = obj.default
            logging.error(traceback.format_exc())
    elif obj.value_type == SAME_VALUE:
        try:
            data = await client.get(obj.name)
            obj.value = data
        except HTTP_db.DatabaseKeyError:
            obj.value = obj.default
            asyncio.ensure_future(client.post(obj.name, obj.default))
        except Exception:
            obj.value = obj.default
            logging.error(traceback.format_exc())
    else:
        raise ValueError(f"value_type: {obj.value_type} is not defined.")
    return None


async def default_push(client: HTTP_db.Client, obj: object) -> None:
    """Push to database."""
    if obj.value_type == CHANNEL_VALUE:
        try:
            await client.post(obj.name, dict_list.dictToList(obj.value))
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e
    elif obj.value_type == GUILD_VALUE:
        try:
            await client.post(obj.name, list(obj.value.items()))
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e
    elif obj.value_type == SAME_VALUE:
        try:
            await client.post(obj.name, obj.value)
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e
    else:
        raise ValueError(f"value_type: {obj.value_type} is not defined.")
    return None
