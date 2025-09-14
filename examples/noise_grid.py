#!/usr/bin/env python3
from py5canvas import *
import numpy as np
import imgui

def parameters():
    return {
            'scale':(0.1, 0.001, 0.1),
            'xpos':(0, -10, 10),
            'ypos':(0, -10, 10),
            'speed':(0.0, -10.0, 10.0),
            'octaves':(4, 1, 8) }

def setup():
    create_canvas(256, 256)


def draw():
    t = frame_count / 30

    # x = np.linspace(0, params.scale*100, width) + params.xpos + t*params.speed
    # y = np.linspace(0, params.scale*100, height) + params.ypos
    # img = util.grad_noise_grid(x, y, params.octaves)

    x = np.linspace(0, params.scale*100, width) + params.xpos
    y = np.linspace(0, params.scale*100, height) + params.ypos
    #img = rumore.grad_fbm_grid3(x, y, t*params.speed, params.octaves)
    noise_detail(params.octaves)
    img = noise_grid(x, y, t*params.speed)
    image(img) #(img + 1)*0.5) #*0.5 + 0.5)
    text(f'{sketch.fps}',[20, 20])

run()
