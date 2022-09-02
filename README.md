# NIRA Bot

痒い所に手が届きそうで届かない Discord 用 BOT

# Installation

## 必要なもの

- Python3.10 以上
- つよい（小並感）パソコン（Windows/Linux/macOSどれでも可）

## セットアップ

1. `pip3 install -r requirements.txt`などの方法で、`requirements.txt`のモジュールをインストールします。
2. `setting_temp.json`及び下の表を参考にして、`setting.json`に TOKEN などの必要な設定を書き込みます。
3. `HTTP_db`のデータベースのパスワードを、`password`ファイルに書き込んで保存します。

- 追加したファイルのツリー図
  ```sh
  N:.
  \--nira_bot
     +--setting.json
     \--password
  ```

### `setting.json`の設定項目について

| キー                | 内容                                                                              | 例                                           | 変数型        |
| ------------------- | --------------------------------------------------------------------------------- | -------------------------------------------- | ------------- |
| `tokens`-`nira_bot` | Bot のトークン入れ                                                                | `"abcdefniofwpajrjr92.f3h208hfi0iffhifhihi"` | str           |
| `py_admin`          | 再起動や Jishaku などの管理者コマンドを使用できるユーザーの DiscordID             | `[1234567989,987654321]`                     | list[int]     |
| `voicevox`          | VOICEVOX WebAPI の API キー                                                       | `["abcdefg1234","1234abcdef"]`               | list[str]     |
| `prefix`            | コマンドのプレフィックス                                                          | `"n!"`                                       | str           |
| `guild_ids`         | スラッシュコマンドを登録する GuildID。未指定で全サーバーに登録する。              | `[1234567989,987654321]`                     | list[int]    |
| `unload_cogs`       | cogs フォルダにある Python ファイルで、Cog として読み込まないファイルを指定する。 | `["yabai.py","tondemonai.py"]`               | list[str]     |
| `load_cogs`         | Debug モードで起動した際に読み込む Cog を指定する。                               | `["debug.py"]`                               | list[str]     |
| `translate`         | DeepL API のキー（必須ではない）                                                  | `abcd1234-ab12-ab12-ab12-ab12ab12ab12`       | str           |
| `database_url`     | HTTP_dbのデータベースのURL                                                  | `http://127.0.0.1:9090`       | str |

## 起動

`nira.py`を実行します。

Debug モードで起動する場合は、引数として`-d`を指定します。  
Debug モードで起動すると、下記の状態になります。

- `setting.json`の`load_cogs`で指定された Cog のみが読み込まれます。
- 起動時に通常より少し多くのコンソール表示が行われます。
- BOT のステータス表示が少し変わります。

# enhance-fix

もし、プログラムに不具合があったり、機能改善をしてほしい場合は、[にら BOT Discord サーバー](https://discord.gg/awfFpCYTcP)の`#enhance-fix`でスレッドを立てるか、本レポジトリに issue や PR を立ててください。

# Contribute

issue や PR を立てる場合は、初心者プログラマー(私)にやさしくしてくれるとうれしいです。  
特にテンプレとかは書かないですし、**大半の人がみて分かりやすいような書き方**であれば何でもいいです。  
なお、Contribute用のガイドは[こちら](https://github.com/team-i2021/nira_bot/contribute.md)にあります。

# 機能

[こちら](https://nira.f5.si/help.html)をご確認ください。

# Extra Licenses

- Words list for Wordle  
  『CEFR-J Wordlist Version 1.6』 東京外国語大学投野由紀夫研究室. （URL: http://www.cefr-j.org/download.html より 2022 年 02 月ダウンロード）

- TTS Character Voice
  TTS の読み上げ音声には、VOICEVOX が使われています。  
  [各キャラクターについて](https://voicevox.hiroshiba.jp/)  
  キャラクターボイス: `VOICEVOX: 四国めたん`/`VOICEVOX: ずんだもん`/`VOICEVOX: 春日部つむぎ`/`雨晴はう`/`VOICEVOX: 波音リツ`/`VOICEVOX: 玄野武宏`/`VOICEVOX: 白上虎太郎`/`VOICEVOX: 青山龍星`/`VOICEVOX: 冥鳴ひまり`/`VOICEVOX: 九州そら`  
  **公序良俗に反する読み上げは一部のキャラクターでは、利用規約違反となります。**

# 最後に

優しく見守ってくださいませ
