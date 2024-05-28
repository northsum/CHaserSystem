import random
acts, directs = 'w', 'ldru'

while 1:
    neibor = input()
    print(random.choice(acts)+random.choice(directs))
    neib = input()