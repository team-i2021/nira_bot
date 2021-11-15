import niconico_dl

url = "https://www.nicovideo.jp/watch/sm32672006?ref=search_key_video&playlist=eyJ0eXBlIjoic2VhcmNoIiwiY29udGV4dCI6eyJrZXl3b3JkIjoiI1x1MzBiM1x1MzBmM1x1MzBkMVx1MzBiOVx1MzBhZFx1MzBlM1x1MzBlOVx1MzBiZFx1MzBmM1x1MzBlYVx1MzBmM1x1MzBhZiIsInNvcnRLZXkiOiJsYXN0Q29tbWVudFRpbWUiLCJzb3J0T3JkZXIiOiJkZXNjIiwicGFnZSI6MSwicGFnZVNpemUiOjMyfX0&ss_pos=19&ss_id=a3ba7804-a3c5-409c-a68f-9072fe5d6863"

f = niconico_dl.NicoNicoVideo(url)
f.connect()
music_url = f.get_download_link()
music_info = f.get_info()
f.close()
print(music_url)