from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

import os
import requests
import random

from gameSystem import *

get_user_program_url = 'https://v523hxaeizl6ffyducbjde67ye0iamfp.lambda-url.ap-northeast-1.on.aws/'

# テスト用curlコマンドは以下の通り
# curl -X POST -H "Content-Type: application/json" -d '{"UserID": "Sample", "slot": 0, "program": "print()", "language": "python"}' https://hpaiddjrprewsmr3kjbbvk5sfe0jmuyd.lambda-url.ap-northeast-1.on.aws/
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/battle", status_code=200)
def battle(body: dict, response: Response):
    """
    @body: dict["c_id": str, "c_slot": int, "h_id": str, "h_slot": int, "board": List[str], "turn": int]
    例えば以下のような形式
    {
        "c_id": "Sample",
        "c_slot": 0,
        "h_id": "Sample",
        "h_slot": 1,
        "board": [
            '000300000300000',
            ...
            '000300000300000',
        ],
        "turn": 100
    """
    delete_files = []
    try:
        board = body['board']
        turn = body['turn']
        if len(board) != 17 or len(board[0]) != 15:
            raise Exception("Invalid board size")
        if turn > 200:
            raise Exception("Invalid turn")
        

        # {'UserID': 'Sample', 'slot': 0}
        c_program = requests.post(get_user_program_url, json={'UserID':  body['c_id'], 'slot': body['c_slot']})
        h_program = requests.post(get_user_program_url, json={'UserID':  body['h_id'], 'slot': body['h_slot']})

        if not (c_program.ok and h_program.ok):
            raise Exception("Failed to get user program")
        
        ch_program = [c_program.json(), h_program.json()]
        ch_script = [[], []]

        # input関数を無効化
        prefix_program = """
def input(*args, **kwargs):
    pass
"""
        for program, script in zip(ch_program, ch_script):
            if program['language'] == 'python':
                script.extend(['pypy3', '-c', prefix_program + program['program']])
            elif program['language'] == 'cpp':
                file_name = str(random.randint(0, 100000000)) + 'exec'
                os.system(f"echo '{c_program['program']}' > {file_name}.cpp")
                os.system(f"g++ {file_name}.cpp -o {file_name}")
                script.extend([f'./{file_name}'])
                delete_files.extend([file_name, f"{file_name}.cpp"])
        
        res = play_game(ch_script[0], ch_script[1], board, turn)
        for file in delete_files:
            os.system(f"rm {file}")
        return res
    except Exception as e:
        for file in delete_files:
            os.system(f"rm {file}")
        response.status_code = 400
        return str(e)