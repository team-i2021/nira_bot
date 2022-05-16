import re, sys, os
from urlextract import URLExtract
from util import tts_dict
import alkana

extractor = URLExtract()

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
    for word, read in tts_dict.main.items():
        message = message.replace(word, read)
    message = convertE2K(message)
    message = message.replace("?","？").replace("&","あんど").replace("=","いこーる").replace("\n","。").replace("/", "すらっしゅ").replace(" ", "、").replace(" ", "、")
    message = re.sub("w{3,}", "わらわらわら", message)
    return message
