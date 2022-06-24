import importlib
import json
import os
import pip
import traceback


def main():
    print("モジュールのインストールを始めます...")
    try:
        pip.main(['install', '-r', f'{os.path.dirname(__file__)}/requirements.txt'])
    except BaseException as err:
        print(f"モジュールのインストール中にエラーが発生しました。\n\n・エラー内容\n{err}\n\n・トレースバック\n{traceback.format_exc()}")
        return
    print("モジュールのインストールが完了しました。")
    print("BOTの設定ファイルを作成します。")
    print("DiscordBOTのTOKENを入力してください。\nトークンの取得/確認は[https://discord.com/developers/applications]から行えます。")
    setting = {
        "tokens":{
            "nira_bot":str
        },
        "main_channel":str,
        "py_admin":int
    }
    setting["tokens"]["nira_bot"] = input("TOKEN>")
    print("管理者用コマンドを使用することが出来るユーザーのIDを入力してください。\nユーザーIDの取得方法は[https://support.discord.com/hc/ja/articles/206346498-%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC-%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC-%E3%83%A1%E3%83%83%E3%82%BB%E3%83%BC%E3%82%B8ID%E3%81%AF%E3%81%A9%E3%81%93%E3%81%A7%E8%A6%8B%E3%81%A4%E3%81%91%E3%82%89%E3%82%8C%E3%82%8B-]からご確認ください。")
    setting["py_admin"] = [int(input("ID>"))]
    print("ファイル生成中...")
    try:
        with open(f'{os.path.dirname(__file__)}/setting.json', 'w') as f:
            json.dump(setting, f, indent=4)
    except BaseException as err:
        print(f"設定ファイル生成中にエラーが発生しました。\n\n・エラー内容\n{err}\n\n・トレースバック\n{traceback.format_exc()}")
        return
    print("設定ファイルを生成しました!")
    input("[nira.py]を実行することでBOTを起動できます！\nEnterキーで終了します...")
    return


if __name__ == "__main__":
    main()
