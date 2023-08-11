import alkana
import os
import re
import sys

from re import compile, IGNORECASE


emoji_pattern = compile(r"<[\da-z_:]+>")
command_pattern = compile(r"</[\da-z_ ]+:[\d]>")
channel_pattern = compile(r"<#[\d]+>")
user_pattern = compile(r"<@[\d]+>")
role_pattern = compile(r"<@&[\d]+>")
url_pattern = compile(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+")
lol_pattern = compile(r"w{3,}")


PreDictionary: dict[re.Pattern, str] = {
    compile(r"youtube", IGNORECASE): "ゆーちゅーぶ",
    compile(r"twitter", IGNORECASE): "ついったー",
    compile(r"discord", IGNORECASE): "でぃすこーど",
    compile(r"twitch", IGNORECASE): "ついっち",
    compile(r"tiktok", IGNORECASE): "てぃっくとっく",
    compile(r"instagram", IGNORECASE): "いんすたぐらむ",
    compile(r"facebook", IGNORECASE): "ふぇいすぶっく",
    compile(r"reddit", IGNORECASE): "れでぃっと",
    compile(r"pixiv", IGNORECASE): "ぴくしぶ",
    compile(r"niconico", IGNORECASE): "にこにこ",
    compile(r"github", IGNORECASE): "ぎっとはぶ",
    compile(r"steam", IGNORECASE): "すてぃーむ",
    compile(r"minecraft", IGNORECASE): "まいんくらふと",
    compile(r"nintendo", IGNORECASE): "にんてんどー",
    compile(r"playstation", IGNORECASE): "ぷれいすてーしょん",
    compile(r"xbox", IGNORECASE): "えっくすぼっくす",
    compile(r"switch", IGNORECASE): "すいっち",
    compile(r"pc", IGNORECASE): "ぴーしー",
    compile(r"ps4", IGNORECASE): "ぴーえすふぉー",
    compile(r"ps5", IGNORECASE): "ぴーえすふぁいぶ",
    compile(r"line", IGNORECASE): "らいん",
    compile(r"wiki", IGNORECASE): "うぃき",
    compile(r"amazon", IGNORECASE): "あまぞん",
    compile(r"mod", IGNORECASE): "もっど",
    compile(r"bot", IGNORECASE): "ぼっと",
    compile(r"windows", IGNORECASE): "うぃんどうず",
    compile(r"mac", IGNORECASE): "まっく",
    compile(r"macos", IGNORECASE): "まっくおーえす",
    compile(r"linux", IGNORECASE): "りなっくす",
    compile(r"android", IGNORECASE): "あんどろいど",
    compile(r"ios", IGNORECASE): "あいおーえす",
    compile(r"google", IGNORECASE): "ぐーぐる",
    compile(r"apple", IGNORECASE): "あっぷる",
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


def convert(message: str, custom_dicationary: dict[str, str] = {}) -> str:
    """TTS用に文章を構成し直す"""
    if not isinstance(message, str) or message == "":
        return ""
    message = url_pattern.sub("、ゆーあーるえる、", message)
    for pattern, read in PreDictionary.items():
        message = pattern.sub(read, message)
    message = convertE2K(message)
    message = emoji_pattern.sub("、えもじ、", message)
    message = command_pattern.sub("、こまんど、", message)
    message = channel_pattern.sub("、ちゃんねる、", message)
    message = user_pattern.sub("、ゆーざー、", message)
    message = role_pattern.sub("、ろーる、", message)
    for word, read in custom_dicationary.items():
        message = message.replace(word, read)
    message = message.replace(
        "?","？"
    ).replace(
        "&","あんど"
    ).replace(
        "=","いこーる"
    ).replace(
        "\n","。"
    ).replace(
        "/", "すらっしゅ"
    ).replace(
        " ", "、"
    ).replace(
        " ", "、"
    )
    message = lol_pattern.sub("わら", message)
    return message
