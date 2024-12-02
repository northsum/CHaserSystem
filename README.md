# CHaserSystem
CHaserのシステムと、HTTPサーバを作成

# 使用方法について

## 初期設定
必要なライブラリを入れる
```sh
python3 -m pip install requests fastapi
```

## 実行方法
実行時はfastapiのコマンドを利用する
```sh
fastapi run server.py
```

ゲームシステムのみを検証する場合は`gameSystem.py`を実行する
```sh
python3 gameSystem.py
```

# プログラムについて

## gameSystem.py

### class Game
CHaserの盤面や行動、勝敗判定を行うクラス

### class ChildManager
複数の子プロセスから順番に入出力通信を行うクラス

### function play_game
Game, ChildManagerクラスから対戦を実施する関数


## server.py
httpサーバとして外部からの対戦リクエストを処理するプログラム

リクエスト・レスポンスのフォーマットはソースコードから参照してほしい