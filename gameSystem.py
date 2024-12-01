import subprocess
import select
import json
import time
import resource

H, W = 17, 15
acts, ds, dx, dy = 'wlsp', 'lurd', [0,-1,0,1], [-1,0,1,0]
NOTHING, COOL, HOT, WALL, ITEM = 0, 1, 1, 2, 3

WAIT_TIME = 0.5
MAX_MEMORY = 500 * 1024 * 1024

class Game:
    """CHaserのゲームを管理するクラス"""

    def __init__(self, field: list[str], turn: int):
        self.logs: list[str] = []
        self.end_turn: int = turn
        self.now_turn: int = 0
        self.field: list[list[int]] = [[0]*W for _ in range(H)]
        self.hot_point: int = 0
        self.cool_point: int = 0

        self.is_hot: bool = False

        for i in range(H):
            for j in range(W):
                if field[i][j]=='H':
                    self.hot = [i, j]
                elif field[i][j]=='C':
                    self.cool = [i, j]
                else:
                    self.field[i][j] = int(field[i][j])
    
    def is_done(self) -> bool:
        """ゲームが終了しているかどうかを判定する"""
        [hi, hj], [ci, cj] = self.hot, self.cool
        if self.lose(*self.cool) or self.lose(*self.hot):
            return True
        is_mounted = self.hot == self.cool
        is_puted   = self.field[hi][hj]==WALL or self.field[ci][cj]==WALL
        is_finish = self.now_turn >= self.end_turn
        return is_mounted or is_puted or is_finish
    
    def lose(self, x: int, y: int) -> bool:
        """(x, y)に存在する対象が負けているかどうかを判定する"""
        if not(0<=x<H and 0<=y<W):
            return True
        if self.field[x][y] == WALL:
            return True
        for i in range(4):
            if self.field[x+dx[i]][y+dy[i]] != WALL:
                return False
        return True
    
    def return_winner(self) -> str:
        """現時点での勝者を返す"""
        hot_lose = self.lose(*self.hot)
        cool_lose = self.lose(*self.cool)
        if hot_lose == cool_lose:
            if self.hot_point > self.cool_point:
                return "HOT"
            elif self.hot_point < self.cool_point:
                return "COOL"
            else:
                return "DRAW"
        elif hot_lose:
            return "COOL"
        elif cool_lose:
            return "HOT"
        else:
            return "DRAW"
    
    def step(self, order: str) -> str:
        """プレイヤーの行動を受け取り、次の状態に遷移し、周辺情報を返す"""
        if self.is_hot:
            self.cool, self.hot = self.hot, self.cool
            self.hot_point, self.cool_point = self.cool_point, self.hot_point

        act, direct = order
        d = ds.index(direct)
        result= self.walk(d) if act=='w' else \
                self.look(d) if act=='l' else \
                self.search(d) if act=='s' else \
                self.put(d)
        
        self.logs.append(order)

        if self.is_hot:
            self.cool, self.hot = self.hot, self.cool
            self.hot_point, self.cool_point = self.cool_point, self.hot_point
        self.now_turn += 1
        self.is_hot = not self.is_hot
        return result
    
    def check_operation(order: str) -> bool:
        """プレイヤーの行動を示す文字列が正しいかどうかを判定する"""
        act, direct = order
        return act in acts and direct in ds

    def _search(self) -> str:
        x, y = self.cool
        res = ''
        for i in range(-1,2):
            for j in range(-1,2):
                nx, ny = x+i, y+j
                e = str(HOT if [nx, ny] == self.hot else \
                        WALL if not(0<=nx<H and 0<=ny<W) else \
                        self.field[nx][ny])
                res += e
        return res
    
    def look(self, d: int) -> str:
        self.cool[0] += 2*dx[d]
        self.cool[1] += 2*dy[d]
        res = self._search()
        self.cool[0] -= 2*dx[d]
        self.cool[1] -= 2*dy[d]
        return res
    
    def neibor(self) -> str:
        if self.is_hot:
            self.hot, self.cool = self.cool, self.hot
        res = self._search()
        if self.is_hot:
            self.hot, self.cool = self.cool, self.hot
        return res
    
    def search(self, d: int) -> str:
        res = ''
        for i in range(1, 10):
            nx, ny = self.cool[0]+dx[d]*i, self.cool[1]+dy[d]*i
            res += str(WALL if not(0<=nx<H and 0<=ny<W) else \
                       HOT if [nx, ny] == self.hot else \
                       self.field[nx][ny])
        return res

    def put(self, d: int) -> str:
        self.field[dx[d]+self.cool[0]][dy[d]+self.cool[1]] = WALL
        return self.neibor(is_hot=False)

    def walk(self, d: int) -> str:
        [x, y] = self.cool
        nx, ny = x+dx[d], y+dy[d]
        if 0<=nx<H and 0<=ny<W and self.field[nx][ny] == ITEM:
            self.field[x][y] = WALL
            self.field[nx][ny] = NOTHING
            self.cool_point += 1
        self.cool = [nx, ny]
        
        return self.neibor(is_hot=False)
    
    def print_field(self):
        for i in range(H):
            for j in range(W):                
                print('H' if [i, j] == self.hot else \
                      'C' if [i, j] == self.cool else \
                      self.field[i][j], end='')
            print()

class ChildManager:
    """プレイヤーごとのプログラムを管理するクラス"""
    def __init__(self):
        self.players = []
        self.whose_turn = 0
        self.player_labels = []
    
    def set_player_labels(self, labels: list[str]):
        self.player_labels = labels
    
    def add_player(self, player_program: list[str]):
        self.players.append(subprocess.Popen(player_program, 
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY)),
            text=True))
    
    def send_to_player(self, message: str):
        self.players[self.whose_turn].stdin.write(message+'\n')
        self.players[self.whose_turn].stdin.flush()
    
    def receive_from_player(self, wait_time: float) -> tuple[bool, str]:
        """プレイヤーからの出力を受け取る"""
        ready, _,_ = select.select([self.players[self.whose_turn].stdout], [], [], wait_time)
        eready, _,_ = select.select([self.players[self.whose_turn].stderr], [], [], 0)

        if len(eready):
            output = self.players[self.whose_turn].stderr.readline().strip()
            self.whose_turn = (self.whose_turn + 1) % len(self.players)
            return False, self.player_labels[self.whose_turn] if self.whose_turn < len(self.player_labels) else "", output
        elif ready:
            output = self.players[self.whose_turn].stdout.readline().strip()
            self.whose_turn = (self.whose_turn + 1) % len(self.players)
            return True, self.player_labels[self.whose_turn] if self.whose_turn < len(self.player_labels) else "", output
        else:
            self.whose_turn = (self.whose_turn + 1) % len(self.players)
            return False, self.player_labels[self.whose_turn] if self.whose_turn < len(self.player_labels) else "", "時間切れ。無限ループが発生している可能性があります."
        

    
    def stop_players(self):
        for player in self.players:
            player.kill()
            player.wait()

# return log
def play_game(player1, player2, field, turn):
    manager = ChildManager()
    manager.set_player_labels(["COOL", "HOT"])
    manager.add_player(player1)
    manager.add_player(player2)
    game = Game(field, turn)

    winner = "DRAW"
    cool_error = ""
    hot_error = ""

    while not game.is_done():
        neib = game.neibor()
        manager.send_to_player(neib)
        ok, player, result = manager.receive_from_player(WAIT_TIME)
        if not ok:
            if player == "COOL":
                cool_error = result
                winner = "HOT"
            else:
                hot_error = result
                winner = "COOL"
            break
        if not Game.check_operation(result):
            if player == "COOL":
                cool_error = "不正な操作が行われました。"
                winner = "HOT"
            else:
                hot_error = "不正な操作が行われました。"
                winner = "COOL"
            break
        manager.send_to_player(game.step(result))

        # game.print_field()
        # print('player act: ', result)
        # time.sleep(0.5)
    
    if winner == "DRAW":
        winner = game.return_winner()

    manager.stop_players()
    return {
        "log": game.logs,
        "winner": winner,
        "player1_error": cool_error,
        "player2_error": hot_error
    }

def api(event, context):
    body = json.loads(event['body'])
    player1 = body['player1']
    player2 = body['player2']
    field = body['field']
    turn = body['turn']
    result = play_game(player1, player2, field, turn)
    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }

if __name__ == '__main__':
    now = time.time()
    field = [
        '000300000300000',
        "0C0000000000000",
        "000300030000300",
        '022200000000003',
        '000003000300030',
        '003000003000000',
        '000000000000220',
        '000300030000000',
        '023000030000032',
        '300000000003000',
        '020200000000000',
        '000000003000300',
        '000300030000300',
        '300000000002220',
        '000003000003000',
        '0000000000000H0',
        '000003000003000'
    ]
    turn = 100

    player1 = ['python3', './samples/randomchoice.py']
    player2 = ['python3', './samples/randomchoice.py']
    result = play_game(player1, player2, field, turn)

    print('past time: ', time.time()-now)
    print(result)
