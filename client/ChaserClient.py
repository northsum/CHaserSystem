import builtins

def print(*args, **kwargs):
    pass

TURN_START = '@'
TURN_END = '#'
GAME_END = '0'

class ChaserClient():
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def turn_end(self, *args, **kwargs):
        pass

    def get_ready(self):
        return input()
    
    def _action(self, action: str):
        builtins.print(action)
        return input()
    
    def walk_right(self):
        return self._action("wr")
    
    def walk_up(self):
        return self._action("wu")
    
    def walk_left(self):
        return self._action("wl")
    
    def walk_down(self):
        return self._action("wd")
    
    def look_right(self):
        return self._action("lr")
    
    def look_up(self):
        return self._action("lu")
    
    def look_left(self):
        return self._action("ll")
    
    def look_down(self):
        return self._action("ld")
    
    def search_right(self):
        return self._action("sr")
    
    def search_up(self):
        return self._action("su")
    
    def search_left(self):
        return self._action("sl")
    
    def search_down(self):
        return self._action("sd")
    
    def put_right(self):
        return self._action("pr")
    
    def put_up(self):
        return self._action("pu")
    
    def put_left(self):
        return self._action("pl")
    
    def put_down(self):
        return self._action("pd")
