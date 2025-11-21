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
    background(0)

    iterations = 300
    w, h = width//2, height//2
    target = complex(1.402015885, 0.0000289991)
    a, b = np.meshgrid(np.linspace(-w/scale, w/scale, w)-target.real, 
                       np.linspace(-h/scale, h/scale, h)-target.imag)
    C = (a + 1j*b)
    z = 0
    img = np.zeros((h, w))
    for i in range(iterations):
        z = z**2 + C
        norm = np.abs(z)
        diverged = np.where(norm > 2)
        img[diverged] = i
    img = cmap(np.mod(img/10, 10)/10)  # fixme
    image(img, [0, 0], [width, height])
    # zoom in
    scale *= 1.1

run()