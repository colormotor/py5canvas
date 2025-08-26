#!/usr/bin/env python3
from py5canvas import *

font = create_font('fonts/Fascinate-Regular.ttf', 55)

def setup():
    create_canvas(512, 512)
    text_font(font)
    text_align(CENTER, CENTER)

def draw():
    background(255)
    translate(center)
    fill(0)
    no_stroke()
    txt = 'LOREM IPSUM'
    text(txt, [0,0])
    stroke(255, 0, 0)
    no_fill()
    rect_mode(CENTER)
    rect(0, 0, text_width(txt), text_height(txt))
    #print(sketch.canvas.ctx.get_scaled_font().text_extents('ABC'))
run()
