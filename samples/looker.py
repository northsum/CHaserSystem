import CHaser
import random

c = CHaser.Client()

while 1:
    c.get_ready()
    choose_list = [c.look_right, c.look_up, c.look_left, c.look_down]
    random.choice(choose_list)()