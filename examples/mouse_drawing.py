from py5canvas import *

import numpy as np
from numpy.linalg import norm # length of a vector

def brush(pos, delta):
    size = norm(delta)
    fill(255, 50)
    stroke(0)
    circle(pos, np.exp(-size*0.03)*100) # 100/(size+1)) #(1+np.exp(-size))*1) # 1+size*10)

def setup():
    create_canvas(800, 600)

def draw():
    if dragging:
        brush(mouse_pos, mouse_delta)

def key_pressed():
    print("Key")

def mouse_pressed():
    print("Mouse down")

def mouse_released():
    print("Mouse up")

run()