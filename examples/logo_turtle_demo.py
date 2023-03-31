import numpy as np
from py5canvas.turtle import Turtle 

def setup():
    sketch.create_canvas(800, 600)
    
def draw():
    c = sketch.canvas
    c.background(0)
    c.translate(c.width/2, c.height/2)
    t = Turtle()
    for i in range(36):
        t.right(10)
        t.circle(120, steps=11)
    c.stroke(255)
    c.no_fill()
    c.shape(t.paths)


