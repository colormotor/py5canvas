#!/usr/bin/env python3
from py5canvas import *
import numpy as np
from py5canvas import geom

def parameters():
    return {'scale':(0.1, 0.001, 0.1),
            'pos':(0, -10, 10),
            'speed':(0.0, -10.0, 10.0),
            'octaves':(4, 1, 8),
            'grad': True}

def setup():
    create_canvas(400, 300)


def draw():
    t = frame_count / 30
    background(0)
    translate(0, height/2)

    no_fill()
    stroke(0, 255, 255)
    h = height/3
    line(0, h, width, h)
    line(0, -h, width, -h)

    noise_detail(params.octaves)
    x = np.linspace(0, width, 300)
    # v = noise(x*params.scale + params.pos + t*params.speed)
    v = noise(x*params.scale + params.pos, np.ones_like(x)*t*params.speed)
    #v = sin(x*params.scale)*0.5+0.5
    y = (v*2-1)*h

    stroke(255, 0, 0)
    polyline(x, y)

    no_stroke()
    fill(255)
    text(f'{sketch.fps}',[20, -height/2+20])
run()
