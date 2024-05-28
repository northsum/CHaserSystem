import subprocess
import select
import json

H, W = 17, 15
acts, ds, dx, dy = 'wlsp', 'ldru', [0,-1,0,1], [-1,0,1,0]
WALL, ITEM, COOL, HOT, NOTHING = 2,3,1,1,0

WAIT_TIME = 0.5

class Game:
    logs = []

    # field = ['0C2000', 0002H0']
    def __init__(self, field, turn):
        self.turn = turn
        self.field = [[0]*W for _ in range(H)]
        for i in range(H):
            for j in range(W):
                if self.field[i][j]=='H':
                    self.hot = [i, j]
                elif self.field[i][j]=='C':
                    self.cool = [i, j]
                else:
                    self.field[i][j] = int(field[i][j])
    
    def is_done(self):
        [hi, hj], [ci, cj] = self.hot, self.cool
        outof   = not(0<=hi<H and 0<=hj<W) or not(0<=ci<H and 0<=cj<W)
        mounted = self.hot == self.cool
        puted   = self.field[hi][hj]==WALL or self.field[ci][cj]==WALL
        finish  = self.turn <= 0
        return outof or mounted or puted or finish
    
    def step(self, order, is_hot=True):
        if is_hot:
            self.cool, self.hot = self.hot, self.cool

        act, direct = order
        d = ds.index(direct)
        result= self.walk(d) if act=='w' else \
                self.look(d) if act=='l' else \
                self.search() if act=='s' else \
                self.put(d)
        
        self.logs.append(order)
        self.turn -= 1

        if is_hot:
            self.cool, self.hot = self.hot, self.cool
        
        return result
    
    def check_operation(order):
        act, direct = order
        return act in acts and direct in ds

    def _search(self, x, y):
        res = ''
        for i in range(-1,2):
            for j in range(-1,2):
                nx, ny = x+i, y+j
                e = str(HOT if [nx, ny] == self.hot else \
                        WALL if not(0<=nx<H and 0<=ny<W) else \
                        self.field[nx][ny])
                res += e
        return res
    
    def search(self, x, y, d):
        return self._search(x+2*dx[d], y+2*dy[d])
    
    def neibor(self):
        return self._search(*self.hot)
    
    def look(self, d):
        res = ''
        for i in range(1, 10):
            nx, ny = self.hot[0]+dx[d]*i, self.hot[1]+dy[d]*i
            res += str(WALL if not(0<=nx<H and 0<=ny<W) else \
                       HOT if [nx, ny] == self.hot else \
                       self.field[nx][ny])
        return res

    def put(self, d):
        self.field[dx[d]+self.cool[0]][dy[d]+self.self.cool[1]] = WALL

    def walk(self, d):
        self.hot[0] += dx[d]
        self.hot[1] += dy[d]
    
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
    

class ChildManager:
    def __init__(self):
        self.players = []
    
    def add_player(self, player_program):
        self.players.append(subprocess.Popen(player_program, 
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE))
    
    def send_to_player(self, player, message):
        self.players[player].stdin.write(message.encode())
        self.players[player].stdin.flush()
    
    def receive_from_player(self, player, wait_time) -> str:
        ready, _,_ = select.select([self.players[player].stdout], [], [], wait_time)
        if ready:
            return [True, self.players[player].stdout.readline().decode().strip()]
        
        err = self.players[player].stderr.read().decode().strip()
        return [False, err if len(err) > 0 else "時間切れ。無限ループが発生している可能性があります."]
    
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
    errors = ["", ""]

    while not game.is_done():
        neib = game.neibor()
        manager.send_to_player(player_flag, neib)
        ok, result = manager.receive_from_player(player_flag, WAIT_TIME)
        if not ok:
            errors[player_flag] = result
            break
        if not Game.check_operation(result):
            errors[player_flag] = "不正な操作が行われました。"
            break
        manager.send_to_player(game.step(result))
        player_flag = 1 - player_flag
    
    manager.stop_players()
    return {
        "log": game.logs,
        "player1_error": errors[0],
        "player2_error": errors[1]
    }



# def api(event, context):
#     body = json.loads(event['body'])
#     player1 = body['player1']
#     player2 = body['player2']
#     field = body['field']
#     turn = body['turn']
#     result = play_game(player1, player2, field, turn)
#     return {
#         "statusCode": 200,
#         "body": json.dumps(result)
#     }