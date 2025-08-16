#!/usr/bin/env python3
from py5canvas import *
import numpy as np
from py5canvas import geom

def parameters():
    return {'scale':(1.0, 0.1, 2.0),
            'speed':(0.0, -1.0, 1.0),
            'octaves':(4, 1, 8),
            'grad': True}

def setup():
    create_canvas(400, 400)


def draw():
    background(0)
    translate(center)

    no_fill()
    stroke(0, 255, 255)

    phase = (frame_count / 30)*params.speed
    theta = np.linspace(0, np.pi*2, 150, endpoint=False)
    x = np.cos(theta)
    y = np.sin(theta)
    noise_detail(params.octaves)
    #r = 50 + noise(x*params.scale, y*params.scale, np.ones_like(x)*phase)*100
    r = 50 + noise(x*params.scale, y*params.scale + phase)*100
    polygon(x*r, y*r)

    no_stroke()
    fill(255)
    text(f'{sketch.fps}',[-width/2+20, -height/2+20])
run()
