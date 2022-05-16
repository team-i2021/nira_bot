import re, sys, os
from urlextract import URLExtract
from util import tts_dict

extractor = URLExtract()

def convert(message: str) -> str:
    """TTS用に文章を構成し直す"""
    if message == "" or type(message) != str:
        raise ValueError()
    urls = extractor.find_urls(message)
    for url in urls:
        message = message.replace(url, "、ゆーあーるえる、")
    for word, read in tts_dict.main.items():
        message = message.replace(word, read)
    message = message.replace("?","？").replace("&","あんど").replace("=","いこーる").replace("\n","。").replace("/", "すらっしゅ").replace(" ", "、").replace(" ", "、")
    message = re.sub("w{3,}", "わらわらわら", message)
    return message
