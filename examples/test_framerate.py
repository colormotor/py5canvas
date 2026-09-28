#!/usr/bin/env python3
from py5canvas import *
import numpy as np

def setup():
    create_canvas(512, 512)
    frame_rate(60)

def draw():
    background(255*(np.sin(frame_count*0.1)*0.5+0.5))
    fill(255, 0, 0)
    text([20, 20], '%02f'%(1.0/sketch.delta_time))

run()