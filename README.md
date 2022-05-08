# NIRA Bot
痒い所に手が届きそうで届かないDiscord用BOT

# Installation
## 必要なもの
- Python3.8以上

## セットアップ
### 方法1
1. 同梱の`setup.py`を実行します。(にらBOTを動かすPython/ユーザーで実行してください。)
2. 画面の指示の通りにします。

### 方法2
1. `pip install -r requirements.txt`でモジュールをインストールします。
2. `setting_temp.json`を参考にして、`setting.json`にTOKENなどの必要な設定を書き込みます。

### `setting.json`の設定項目について
キー|内容|例|変数型
---|---|---|---
`tokens`-`nira_bot`|Botのトークン入れ|`"abcdefniofwpajrjr92.f3h208hfi0iffhifhihi"`|str
`py_admin`|再起動やJishakuなどの管理者コマンドを使用できるユーザーのDiscordID|`[1234567989,987654321]`|list(int)
`voicevox`|VOICEVOX WebAPIのAPIキー|`["abcdefg1234","1234abcdef"]`|list(str)
`prefix`|コマンドのプレフィックス|`"n!"`|str
`guild_ids`|スラッシュコマンドを登録するGuildID。未指定で全サーバーに登録する。|`[1234567989,987654321]`|list(int)
`unload_cogs`|cogsフォルダにあるPythonファイルで、Cogとして読み込まないファイルを指定する。|`["yabai.py","tondemonai.py"]`|list(str)
`load_cogs`|Debugモードで起動した際に読み込むCogを指定する。|`["debug.py"]`|list(str)


## 起動
`nira.py`を実行します。  
Debugモードで起動する場合は、引数として`-d`を指定します。

# enhance-fix
もし、プログラムに不具合があったり、機能改善をしてほしい場合は、[にらBOT Discordサーバー](https://discord.gg/awfFpCYTcP)の`#enhance-fix`でスレッドを立てるか、本レポジトリにissueやPRを立ててください。  

# Contribute
issueやPRを立てる場合は、初心者プログラマー(私)にやさしくしてくれるとうれしいです。  
特にテンプレとかは書かないですし、**大半の人がみて分かりやすいような書き方**であれば何でもいいです。

# 機能
[こちら](https://nira.f5.si/help.html)をご確認ください。

# Extra Licenses
- Words list for Wordle  
『CEFR-J Wordlist Version 1.6』 東京外国語大学投野由紀夫研究室. （URL: http://www.cefr-j.org/download.html より2022年02月ダウンロード）

- TTS Character Voice
TTSの読み上げ音声には、VOICEVOXが使われています。  
[各キャラクターについて](https://voicevox.hiroshiba.jp/)  
キャラクターボイス: `VOICEVOX: 四国めたん`/`VOICEVOX: ずんだもん`/`VOICEVOX: 春日部つむぎ`/`雨晴はう`/`VOICEVOX: 波音リツ`/`VOICEVOX: 玄野武宏`/`VOICEVOX: 白上虎太郎`/`VOICEVOX: 青山龍星`/`VOICEVOX: 冥鳴ひまり`/`VOICEVOX: 九州そら`  
**公序良俗に反する読み上げは一部のキャラクターでは、利用規約違反となります。**


# 最後に
優しく見守ってくださいませ
