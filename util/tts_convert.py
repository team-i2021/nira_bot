import alkana
import os
import re
import sys
from urlextract import URLExtract


extractor = URLExtract()

SUBER = {
    ""
    "?":"？",
    "&":"あんど",
    "=":"いこーる",
    "\n":"。",
    "/":"すらっしゅ",
    "(´・ω・｀)":"しょぼん",
    "改8号機":"かいはちごうき",
    "禍津御建鳴神命":"まがつみたけなるかみのみこと",
    "NREV":"ねるふ",
    "WILLE":"ヴィレ",
    "EURO":"ゆーろ",
    "広有射怪鳥事":"ひろありけちょうをいること",
    "Ура":"うらあ",
    "EVANGELION":"エヴァンゲリオン",
}

def convertE2K(text: str) -> str:
    temp_text = text
    output = ""
    while word := re.search(r'[a-zA-Z]{3,}', temp_text):
        output += temp_text[:word.start()]
        if kana := alkana.get_kana(word.group().lower()):
            output += kana
        else:
            output += word.group()
        temp_text = temp_text[word.end():]
    output += temp_text
    return output


def convert(message: str) -> str:
    """TTS用に文章を構成し直す"""
    if message == "" or type(message) != str:
        raise ValueError()
    urls = extractor.find_urls(message)
    for url in urls:
        message = message.replace(url, "、ゆーあーるえる、")
    for word, read in SUBER.items():
        message = message.replace(word, read)
    message = convertE2K(message)
    message = message.replace("?","？").replace("&","あんど").replace("=","いこーる").replace("\n","。").replace("/", "すらっしゅ").replace(" ", "、").replace(" ", "、")
    message = re.sub(r"<[\da-z_:]+>", "えもじ", re.sub(r"</[\da-z_ ]+:[\d]>", "こまんど", re.sub(r"<#[\d]+>", "ちゃんねる", re.sub(r"<@[\d]+>", "ゆーざー", re.sub(r"<@&[\d]+>", "ろーる", message)))))
    message = re.sub("w{3,}", "わらわらわら", message)
    return message
