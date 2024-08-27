''' Simple example demonstrating how to manually create
a UI with pyImgui'''

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
    sketch.set_gui_callback(gui)
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

    c.background(0, 0, 0, 0.02) # Clear with alpha will create the "trail effect"
    # Center of screen
    c.translate(c.width/2, c.height/2)

    print('size:', sketch.window_width, sketch.window_height)
    # Every cycle update points
    if sketch.frame_count%frame_interval == 0:
        a, b = b, a
        b = new_points()

    # interpolation step
    t = (sketch.frame_count%frame_interval)/frame_interval
    points = a + (b - a)*t

    c.stroke(1)
    c.no_fill()
    c.polyline(points)
    c.stroke(*circle_color)
    for p in points:
        c.circle(p, radius)

    imgui.begin("A window", True)
    # See https://pyimgui.readthedocs.io/en/latest/reference/imgui.core.html
    imgui.text("Hello world")
    changed, radius = imgui.slider_float("Radius", radius, 0.5, 60.0)
    changed, circle_color = imgui.color_edit4("Circle Color", *circle_color, imgui.COLOR_EDIT_DISPLAY_HSV)
    #print(circle_color)
    imgui.end()

def key_pressed(event, mod=0):
    sketch.toggle_fullscreen()
    print('yo')
if __name__== '__main__':
    import py5canvas
    py5canvas.run()
