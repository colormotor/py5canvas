''' Simple example demonstrating how to manually create
a UI with pyImgui'''

from py5canvas import *
import numpy as np
import imgui

def new_points():
    points = np.random.uniform(-200, 200, (10, 2))*2
    return points

a = new_points()
b = new_points()

radius = 2.0
circle_color = [255, 0, 0, 255]

frame_interval = 60

def setup():
    create_canvas(800, 600)
    color_mode('rgb', 1.0)

def imgui_title(text):
    imgui.push_style_color(imgui.COLOR_HEADER, 0.3, 0.3, 0.3, 1.0)
    imgui.selectable(text, True)
    imgui.pop_style_color()

def imgui_text_separator(text):
    imgui.push_style_color(imgui.COLOR_TEXT, 0.6, 0.6, 0.6, 1.0)
    imgui.text("Text")
    imgui.same_line()
    imgui.separator()
    imgui.pop_style_color()

def imgui_color_button(text, color):
    if len(color) == 3:
        color = np.concatenate([color, [1.0]])
    imgui.push_style_color(imgui.COLOR_BUTTON, *color)
    imgui.button(text)
    imgui.pop_style_color()

def gui():
    #print(sketch.window.get_pixel_ratio())
    imgui_title("General")
    imgui.push_style_color(imgui.COLOR_BUTTON, 1.0, 0.0, 0.0, 1.0)
    imgui.button("Hello world")
    imgui.pop_style_color()


def draw():
    global a, b, radius, circle_color # we are modifying these

    background(0, 0, 0, 0.02) # Clear with alpha will create the "trail effect"
    # Center of screen
    translate(width/2, height/2)

    # Every cycle update points
    if frame_count%frame_interval == 0:
        a, b = b, a
        b = new_points()

    # interpolation step
    t = (frame_count%frame_interval)/frame_interval
    points = a + (b - a)*t

    stroke(1)
    no_fill()
    polyline(points)
    stroke(*circle_color)
    for p in points:
        circle(p, radius)

    imgui.begin("A window", True)
    # See https://pyimgui.readthedocs.io/en/latest/reference/imgui.core.html
    imgui.text("Hello world")
    changed, radius = imgui.slider_float("Radius", radius, 0.5, 60.0)
    changed, circle_color = imgui.color_edit4("Circle Color", *circle_color, imgui.COLOR_EDIT_DISPLAY_HSV)
    #print(circle_color)
    imgui.end()

def key_pressed(key):
    toggle_fullscreen()
    
run()
