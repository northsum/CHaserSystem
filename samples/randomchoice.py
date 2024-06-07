import CHaser
import random
import time
acts, directs = 'lw', 'ulrd'

while 1:
    neibor = input()
    act = ''
    for i in range(4):
        if neibor[i*2+1] == '1':
            act = 'p' + directs[i]
            break
        if neibor[i*2+1] == '3':
            act = 'w' + directs[i]
            break
    
    cnt = 0
    while cnt<10:
        cnt += 1
        if act:
            break
        d = random.choice(directs)
        if neibor[directs.index(d)*2+1] != '2':
            act = 'w' + d
            break
    if act == '':
        act = 'lu'
    print(act)
    input()