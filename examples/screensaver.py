import numpy as np
import torch

params = {'foo':(30.0, {'min':0.0, 'max':100.0})}
params = sketch.parameters(params)

def new_points():
    points = np.random.uniform(-200, 200, (10, 2))*2
    return points

a = new_points()
b = new_points()

frame_interval = 60


def setup():
    create_canvas(800, 600)
    frame_rate(60)
    
def draw():
    global a, b # we are modifying these

    background(params.foo, 0, 0, 100) # Clear with alpha will create the "trail effect"
    # Center of screen
    translate(c.width/2, c.height/2)

    # Every cycle update points
    if sketch.frame_count%frame_interval == 0:
        a, b = b, a
        b = new_points()

    # interpolation step
    t = (sketch.frame_count%frame_interval)/frame_interval
    points = a + (b - a)*t

    stroke(255)
    no_fill()
    polyline(points)
