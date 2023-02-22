#!/usr/bin/env python3
import numpy as np

def setup():
    sketch.frame_rate(10)

def draw():
    c = sketch.canvas # Get the base canvas

    c.background(255*(np.sin(c.frame_count*0.1)*0.5+0.5))
    c.fill(255, 0, 0)
    c.text([20, 20], '%02f'%(1.0/c.delta_time))
