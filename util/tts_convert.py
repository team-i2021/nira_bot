import re, sys, os

def convert(message: str) -> str:
    """TTS用に文章を構成し直す"""
    if message == "" or type(message) != str:
        raise ValueError()
    message = message.replace("?","？").replace("&","あんど").replace("=","いこーる").replace("\n","。").replace("/", "すらっしゅ")
    message = re.sub("w{3,}", "わらわらわら", message)
    return message