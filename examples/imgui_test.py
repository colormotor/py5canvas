import numpy as np
import imgui

def new_points():
    points = np.random.uniform(-200, 200, (10, 2))*2
    return points

a = new_points()
b = new_points()

radius = 2.0
circle_color = [1, 0, 0, 1]

frame_interval = 60

def setup():
    sketch.create_canvas(800, 600)
    sketch.frame_rate(60)
    sketch.canvas.color_mode('rgb', 1.0)


def draw():
    c = sketch.canvas # Get the base canvas
    global a, b, radius, circle_color # we are modifying these

    c.background(0, 0, 0, 0.02) # Clear with alpha will create the "trail effect"
    # Center of screen
    c.translate(c.width/2, c.height/2)


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
    changed, circle_color = imgui.color_edit4("Circle Color", *circle_color, imgui.COLOR_EDIT_HSV)
    print(circle_color)
    imgui.end()
