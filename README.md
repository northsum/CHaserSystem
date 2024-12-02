# CHaserSystem
CHaserのシステムと、HTTPサーバを作成

# 使用方法について

## 初期設定
必要なライブラリをインストールする
```sh
python3 -m pip install requests fastapi
```

## 実行方法
実行時はfastapiのコマンドを利用する

fastapiコマンドは初期設定のインストールで入っている
```sh
fastapi run server.py
```

ゲームシステムのみを検証する場合は`gameSystem.py`を実行する
```sh
python3 gameSystem.py
```

# プログラムについて

## gameSystem.py

ゲーム対戦機能をまとめたプログラム群

クライアントプログラムを並列で実行して、対戦を行う。


### class Game
CHaserの盤面や行動、勝敗判定を行うクラス

### class ChildManager
複数の子プロセスから順番に通信を行って行動文字列を受け取るクラス

### function play_game
Game, ChildManagerクラスから対戦を実施する関数


## server.py
httpサーバとして外部からの対戦リクエストを処理するプログラム

リクエスト・レスポンスのフォーマットはソースコードから参照する。

## client

通信クライアントをまとめたプログラム群

windowsアプリでの通信クライアントライブラリの機能を標準入出力でこなせるようにした

（このためデバッグ時にprintを使用すると、通信エラーが発生してしまう）

現在は、通信クライアントライブラリ以外でprintが使えないように対処

```python
# 何もしないように上書きすることでprintを無効化
print(*args, **argv):
    pass
```

別案として,「printを使わないように呼びかけ」,「"wu", "sd"などの適切な命令とそれ以外を分けて扱う(やるならこれ？)」が考えられる