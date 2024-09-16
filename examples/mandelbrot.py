''' A simple mandelbrot zoom
    using numpy for computation and matplotlib for colors'''
from py5canvas import *
import numpy as np
import matplotlib

cmap = matplotlib.cm.get_cmap('turbo')
scale = 60.0

def setup():
    create_canvas(512, 512)

def draw():
    global scale
    c = canvas
    # Here we will use `c` to reference to the sketch canvas
    # since we redefined `scale` as a global variable and the corresponding
    # global function would not work anymore
    c.background(0)

    iterations = 200

    w, h = c.width//2, c.height//2
    a, b = np.meshgrid(np.linspace(-w/scale, w/scale, w)-1.402, np.linspace(-h/scale, h/scale, h)-0.00003)
    C = (a + 1j*b)
    z = 0
    img = np.zeros((h, w))
    for i in range(iterations):
        z = z**2 + C
        norm = np.abs(z)
        diverged = np.where(norm > 2)
        img[diverged] = i
    img = cmap(np.mod(img/10, 10)/10)  # fixme
    c.image(img, [0, 0], [c.width, c.height])
    # zoom in
    scale *= 1.1

run()