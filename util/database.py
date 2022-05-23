import os, sys
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

jsonFile = f"{sys.path[0]}/util/gapi.json"
SPREADSHEET_KEY = str(json.load(open(f'{sys.path[0]}/setting.json', 'r'))["database"])

def openSheet() -> gspread.Worksheet:
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonFile, scope)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
    return worksheet


def readValue(data, cell) -> dict:
    return json.loads(data.acell(cell).value)


def writeValue(data, cell, value) -> None:
    data.update_acell(cell, json.dumps(value))
    return None


# https://qiita.com/164kondo/items/eec4d1d8fd7648217935
# B2:テスト/B3:TTS/B4:Up通知/B5:Reminder/B6:Captcha

