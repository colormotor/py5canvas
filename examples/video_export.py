''' Simple example showing how to create and export
a video loop'''
from py5canvas import *

num_frames = 150

def setup():
    create_canvas(512, 512)
    set_color_scale(1.0)
    frame_rate(30)
    num_movie_frames(num_frames) # You can set this also from the UI

def draw():
    background(0.0)
    t = frame_count / num_frames
    identity()
    translate(width/2, height/2)
    rotate_deg(t*360)
    fill(1.0)
    circle([200, 0], 20)

run(show_toolbar=True)
