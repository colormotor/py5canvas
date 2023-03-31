import numpy as np
from numpy.linalg import norm # length of a vector
#
def brush(c, pos, delta):
    size = norm(delta)
    c.fill(255, 50)
    c.stroke(0)
    c.circle(pos, np.exp(-size*0.03)*100) # 100/(size+1)) #(1+np.exp(-size))*1) # 1+size*10)

def setup():
    sketch.create_canvas(800, 600)

def draw():
    c = sketch.canvas # Get the base canvas
    print(sketch.mouse_delta)
    if sketch.mouse_pressed:
        print(sketch.mouse_pos)
        brush(c, sketch.mouse_pos, sketch.mouse_delta)
