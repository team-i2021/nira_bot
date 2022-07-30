import json
import os
import sys
import HTTP_db


__version__ = "util"

# jsonFile = f"{sys.path[0]}/util/gapi.json"
# SPREADSHEET_KEY = str(json.load(open(f'{sys.path[0]}/setting.json', 'r'))["database"])


# def openSheet() -> gspread.Worksheet:
#     scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
#     credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonFile, scope)
#     gc = gspread.authorize(credentials)
#     worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
#     return worksheet


def readValue(data, cell) -> dict:
    return json.loads(data.acell(cell).value)


def writeValue(data, cell, value) -> None:
    data.update_acell(cell, json.dumps(value))
    return None


def openClient() -> HTTP_db.Client:
    url = str(json.load(open(f"{sys.path[0]}/setting.json", "r"))["database_data"]["address"])
    if os.path.isfile(f"{sys.path[0]}/password"):
        password = open(f"{sys.path[0]}/password", "r").read()
        return HTTP_db.Client(url=url, password=password)
    else:
        return HTTP_db.Client(url=url)

async def database_initialize(client: HTTP_db.Client, key, default):
    if await client.exists(key):
        return
    else:
        await client.post(key, default)
        return

# https://qiita.com/164kondo/items/eec4d1d8fd7648217935
# B2:テスト/B3:TTS/B4:Up通知/B5:Reminder/B6:Captcha/B7:InviteURLs
