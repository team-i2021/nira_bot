# にらBOT Contribute

適当ドキュメント。

多分もう使い物にならない。

## NIRAオブジェクトについて
NIRAオブジェクトは、`commands.Bot`を継承したクラスです。  
基本的に`commands.Bot`と同じ動作をします。  
ですが、一部関数やメソッドにおいて異なる動作をします。

### Method
- `NIRA.debug`  
    type: bool  
    description: BOTのデバッグモードが有効かどうかを示します。

- `NIRA._token`  
    type: str  
    description: BOTのトークンです。渡すときはキーワード引数`token`に渡してください。  
    BOTの起動もこのトークンで行います。

- `NIRA.client`  
    type: HTTP_db.client  
    description: HTTP_db用のクライアントです。Cogの中で、`self.bot.client`みたいに引き出せたり、`onami`でも使えるので便利です。

### Function
- `NIRA.run`  
    args: ()  
    return: None  
    description: BOTを起動します。トークンは、`token`で指定されたものを使用します。

- `NIRA.is_owner`  
    args: (user: discord.User)  
    return: bool  
    description: 指定されたユーザーがBOTの管理者かどうか（py_adminに含まれるか・BOTの所有者か）を示します。

## データベースについて
データベースは`HTTP_db`のPythonラッパーにさらにラッピングしたようなものを使用しています。  
データは最初にクラスで宣言しておいて、`util.database`内の各関数で取得/書き込みを行います。  

### クラスの宣言

```python
from util import database

class ClassName:
    name = "database_key"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE
```

このようなclassが必要です。  
- `name`  
    type: str  
    description: データベース側のキーです。

- `value`  
    type: dict  
    description: データの本体です。ここに書き込み/ここから読み込みを行います。

- `default`  
    type: dict  
    description: サーバー側にキーが存在しなかった場合などに`value`に書き込まれるデフォルト値です。

- `value_type`  
    type: int  
    description: データのタイプです。中身は`util.database`で宣言されてるただの変数です。  
    - `database.GUILD_VALUE`  
        サーバー側が`list`で、クライアント側が`dict`で、これらが相互変換されます。その際、1階層分しか変更されません。  
        `{guild1:[values], guild2:[values]}`と`[[guild1,[values]],[guild2,[values]]]`です。  
    - `database.CHANNEL_VALUE`  
        サーバー側が`list`で、クライアント側が`dict`で、これらが相互変換されます。その際、2階層分変更されます。  
        `{guild1:{channel1:[values],channel2:[values]}, guild2:{channel1:[values]}}`と`[[guild1,[[channel1,[values]],[channel2,[values]]]],[guild2,[[channel1,[values]]]]]`です。  
    - `database.SAME_VALUE`  
        サーバー側とクライアント側で、相互変換を行わず、生のデータを渡します。  
        ちなみにJSONにはintのキーはないので注意してください。  

そしたら、データの呼び出し「pull」と書き込み「push」を行う準備ができました。

```python
from util import database

class Test:
    name = "test"
    value = {}
    default = {}
    value_type = database.CHANNEL_VALUE

---中略---

await database.default_pull(self.bot.client, Test)
Test.value[interaction.guild.id][interaction.channel.id] = 1
await database.default_push(self.bot.client, Test)
```

これで、`test`の値が編集できました。

pullを行うことで、データベースからデータを取得します。  
（基本的にコグのインスタンス化時にデータを読み込むようにしています。）  

pushを行うことで、データベースにデータを書き込みます。
