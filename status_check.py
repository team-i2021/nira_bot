# coding: utf-8
import requests
 
# Steam Web APIを利用して、サーバーの有無を取得する。
# server_check.pyみてね

server_req_url = 'http://api.steampowered.com/ISteamApps/GetServersAtAddress/v1/?format=json&addr='
 
def server_status(ip, port):
    option = ip + ":" + str(port)
    url = server_req_url + option
    req = requests.get(url)
    server_list = req.json()
    print(server_list)
    if len(server_list["response"]["servers"]) >= 1:
        return True
    else:
        return False