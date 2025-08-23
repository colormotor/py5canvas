#!/usr/bin/env python3
from py5canvas import *

def setup():
    create_canvas(512, 512)
    fill(0)
    no_stroke()
    text_font('Fascinate-Regular.ttf')
    text_align('center')
    text_size(55)

def draw():
    background(255)
    translate(center)
    text('LOREM IPSUM', [0,0])

run()
