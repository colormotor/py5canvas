import numpy as np
from numpy.linalg import norm # length of a vector
#
def brush(pos, delta):
    size = norm(delta)
    fill(255, 50)
    stroke(0)
    circle(pos, np.exp(-size*0.03)*100) # 100/(size+1)) #(1+np.exp(-size))*1) # 1+size*10)

def setup():
    create_canvas(800, 600)

def draw():
    if mouse_pressed:
        brush(mouse_pos, mouse_delta)
