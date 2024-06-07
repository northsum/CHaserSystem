from fastapi import FastAPI, Response
import boto3
import os
import json
import requests
import random

from gameSystem import *

get_user_program_url = 'https://v523hxaeizl6ffyducbjde67ye0iamfp.lambda-url.ap-northeast-1.on.aws/'

# テスト用curlコマンドは以下の通り
# curl -X POST -H "Content-Type: application/json" -d '{"UserID": "Sample", "slot": 0, "program": "print()", "language": "python"}' https://hpaiddjrprewsmr3kjbbvk5sfe0jmuyd.lambda-url.ap-northeast-1.on.aws/
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# 入力json形式は以下の通り
# {
#     "c_id": str,
#     "c_slot": int,
#     "h_id": str,
#     "h_slot": int
#     "board": [
#         '000300000300000',
#         ...
#         '000003000003000'
#     ],
#     "turn": 100
# }
@app.post("/battle", status_code=200)
def battle(body: dict, response: Response):
    delete_files = []
    try:
        board = body['board']
        turn = body['turn']

        # {'UserID': 'Sample', 'slot': 0}
        c_program = requests.post(get_user_program_url, json={'UserID':  body['c_id'], 'slot': body['c_slot']})
        h_program = requests.post(get_user_program_url, json={'UserID':  body['h_id'], 'slot': body['h_slot']})

        if not (c_program.ok and h_program.ok):
            response.status_code = 400
            return "Failed to get user program"
        
        ch_program = [c_program.json(), h_program.json()]
        ch_script = [[], []]
        for program, script in zip(ch_program, ch_script):
            if program['language'] == 'python':
                script.extend(['python3', '-c', program['program']])
            elif program['language'] == 'cpp':
                file_name = str(random.randint(0, 100000000)) + 'exec'
                os.system(f"echo '{c_program['program']}' > {file_name}.cpp")
                os.system(f"g++ {file_name}.cpp -o {file_name}")
                script.extend([f'./{file_name}'])
                delete_files.extend([file_name, f"{file_name}.cpp"])
    except Exception as e:
        for file in delete_files:
            os.system(f"rm {file}")
        response.status_code = 400
        return str(e)
    
    res = play_game(ch_script[0], ch_script[1], board, turn)
    for file in delete_files:
        os.system(f"rm {file}")

    return res