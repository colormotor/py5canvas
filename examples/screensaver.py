import numpy as np

def new_points():
    points = np.random.uniform(-200, 200, (10, 2))*2
    return points

a = new_points()
b = new_points()

frame_interval = 60

def setup():
    sketch.create_canvas(800, 600)
    sketch.frame_rate(60)

def draw():
    c = sketch.canvas # Get the base canvas
    global a, b # we are modifying these

    c.background(0, 0, 0, 8) # Clear with alpha will create the "trail effect"
    # Center of screen
    c.translate(c.width/2, c.height/2)

    # Every cycle update points
    if sketch.frame_count%frame_interval == 0:
        a, b = b, a
        b = new_points()

    # interpolation step
    t = (sketch.frame_count%frame_interval)/frame_interval
    points = a + (b - a)*t

    c.stroke(255)
    c.no_fill()
    c.polyline(points)
