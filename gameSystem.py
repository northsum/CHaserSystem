import subprocess
import select
import json
import time

H, W = 17, 15
acts, ds, dx, dy = 'wlsp', 'lurd', [0,-1,0,1], [-1,0,1,0]
WALL, ITEM, COOL, HOT, NOTHING = 2,3,1,1,0

WAIT_TIME = 0.5

class Game:
    logs = []

    def __init__(self, field, turn):
        self.turn = turn
        self.field = [[0]*W for _ in range(H)]
        self.hot_point = 0
        self.cool_point = 0
        for i in range(H):
            for j in range(W):
                if field[i][j]=='H':
                    self.hot = [i, j]
                elif field[i][j]=='C':
                    self.cool = [i, j]
                else:
                    self.field[i][j] = int(field[i][j])
    
    def is_done(self):
        [hi, hj], [ci, cj] = self.hot, self.cool
        outof   = not(0<=hi<H and 0<=hj<W) or not(0<=ci<H and 0<=cj<W)
        if outof:
            return True
        mounted = self.hot == self.cool
        puted   = self.field[hi][hj]==WALL or self.field[ci][cj]==WALL
        finish  = self.turn <= 0
        return mounted or puted or finish
    
    def lose(self, x, y):
        for i in range(4):
            if self.field[x+dx[i]][y+dy[i]] != WALL:
                return False
        if self.field[x][y] == WALL:
            return True
        return False
    
    def return_winner(self):
        hot_lose = self.lose(*self.hot)
        cool_lose = self.lose(*self.cool)
        if hot_lose == cool_lose:
            if self.hot_point > self.cool_point:
                return "HOT"
            elif self.hot_point < self.cool_point:
                return "COOL"
            else:
                return "Draw"
        elif hot_lose:
            return "COOL"
        elif cool_lose:
            return "HOT"
    
    def step(self, order, is_hot=True):
        if is_hot:
            self.cool, self.hot = self.hot, self.cool
            self.hot_point, self.cool_point = self.cool_point, self.hot_point

        act, direct = order
        d = ds.index(direct)
        result= self.walk(d) if act=='w' else \
                self.look(d) if act=='l' else \
                self.search(d) if act=='s' else \
                self.put(d)
        
        self.logs.append(order)
        self.turn -= 1

        if is_hot:
            self.cool, self.hot = self.hot, self.cool
            self.hot_point, self.cool_point = self.cool_point, self.hot_point
        
        return result
    
    def check_operation(order):
        act, direct = order
        return act in acts and direct in ds

    def _search(self):
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
    
    def search(self, d):
        self.cool[0] += 2*dx[d]
        self.cool[1] += 2*dy[d]
        res = self._search(*self.cool)
        self.cool[0] -= 2*dx[d]
        self.cool[1] -= 2*dy[d]
        return res
    
    def neibor(self, is_hot=True):
        if is_hot:
            self.hot, self.cool = self.cool, self.hot
        res = self._search()
        if is_hot:
            self.hot, self.cool = self.cool, self.hot
        return res
    
    def look(self, d):
        res = ''
        for i in range(1, 10):
            nx, ny = self.hot[0]+dx[d]*i, self.hot[1]+dy[d]*i
            res += str(WALL if not(0<=nx<H and 0<=ny<W) else \
                       HOT if [nx, ny] == self.hot else \
                       self.field[nx][ny])
        return res

    def put(self, d):
        self.field[dx[d]+self.cool[0]][dy[d]+self.cool[1]] = WALL
        return self.neibor(is_hot=False)

    def walk(self, d):
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
                if [i, j] == self.hot:
                    print('H', end='')
                elif [i, j] == self.cool:
                    print('C', end='')
                else:
                    print(self.field[i][j], end='')
            print()
        print()

class ChildManager:
    def __init__(self):
        self.players = []
    
    def add_player(self, player_program):
        self.players.append(subprocess.Popen(player_program, 
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True))
    
    def send_to_player(self, player, message):
        self.players[player].stdin.write(message+'\n')
        self.players[player].stdin.flush()
    
    def receive_from_player(self, player, wait_time) -> str:
        ready, _,_ = select.select([self.players[player].stdout], [], [], wait_time)
        eready, _,_ = select.select([self.players[player].stderr], [], [], 0)
        if len(eready):
            return [False, self.players[player].stderr.read().strip()]
        elif ready:
            output = self.players[player].stdout.readline().strip()
            return [True, output]
        else:
            return [False, "時間切れ。無限ループが発生している可能性があります."]
    
    def stop_players(self):
        for player in self.players:
            player.kill()
            player.wait()

# return log
def play_game(player1, player2, field, turn):
    manager = ChildManager()
    manager.add_player(player1)
    manager.add_player(player2)
    game = Game(field, turn)

    # 0: cool, 1: hot
    player_flag = 0
    winner = "Draw"
    errors = ["", ""]

    while not game.is_done():
        neib = game.neibor(player_flag)

        manager.send_to_player(player_flag, neib)
        ok, result = manager.receive_from_player(player_flag, WAIT_TIME)
        if not ok:
            errors[player_flag] = result
            winner = "COOL" if player_flag else "HOT"
            break
        if not Game.check_operation(result):
            errors[player_flag] = "不正な操作が行われました。"
            winner = "COOL" if player_flag else "HOT"
            break
        manager.send_to_player(player_flag, game.step(result, player_flag))
        player_flag = 1 - player_flag

        # game.print_field()
        # print('player act: ', result)
        # time.sleep(0.5)
    
    if winner == "Draw":
        winner = game.return_winner()

    manager.stop_players()
    return {
        "log": game.logs,
        "winner": winner,
        "player1_error": errors[0],
        "player2_error": errors[1]
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
    player2 = ['python3', './samples/looker.py']
    result = play_game(player1, player2, field, turn)
    print(result)

    import requests

    data = {
        "Acts": result['log'],
        "Winner": result['winner'],
        "Field": field,
        "Turn": turn
    }

    print(data)
    
    res = requests.post("https://hr5gyqk5rkxjtfdeyyskr5nc640kpscb.lambda-url.ap-northeast-1.on.aws/", json=data)

    print(res.text)
