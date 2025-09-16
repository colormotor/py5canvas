#!/usr/bin/env python3
import py5canvas
C = py5canvas.Canvas

from py5canvas import *
from slimgui import implot, imgui


def parameters():
    return {'noise freq':(0.01, 0.001, 0.1),
            'show demo': False}


noises = [[], [], []]


def setup():
    create_canvas(800, 800)


def gui():
    if implot.begin_plot('Noise', size=[-1, 200]):
        implot.setup_axes(None, None, implot.AxisFlags.AUTO_FIT, implot.AxisFlags.AUTO_FIT)
        for i, vals in enumerate(noises):
            implot.plot_line('noise %d'%(i+1), np.array(vals))
            if vals:
                implot.plot_text('%.3f'%vals[-1], len(vals), vals[-1])
        implot.end_plot()
    if params.show_demo:
        implot.show_demo_window()


def draw():
    background(0)
    for i, vals in enumerate(noises):
        vals.append(noise(frame_count*params.noise_freq, i)*2-1)
        if len(vals) > 100:
            vals.pop(0)

run(show_toolbar=True)
