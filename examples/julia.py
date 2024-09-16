''' A simple Julia zoom
    using numpy for computation and matplotlib for colors'''
from py5canvas import *
import numpy as np
import matplotlib

cmap = matplotlib.cm.get_cmap('jet') #'jet')
scale_factor = 300
target = complex(-0.1930840493097, -0.080000106)

def setup():
    create_canvas(800, 600)
    

def draw():
    global scale, target
    background(0)

    iterations = 300

    w, h = width//2, height//2
    a, b = np.meshgrid(np.linspace(-w/scale_factor, w/scale_factor, w), 
                       np.linspace(-h/scale_factor, h/scale_factor, h))
    z = a + b*1j

    # Rotate "camera"
    rot = np.exp(frame_count/30*1j)
    z = z*rot + target

    #C = -0.835 - 0.2321 * 1j
    #C = -0.744 + 0.148*1j
    #C = -0.29609091 + 0.62491*1j
    #C = 0.2412 + 0.523j
    C = -0.013770902239694544 + 0.6759480544032246 * 1j


    img = np.zeros((h, w))
    for i in range(iterations):
        z = z**2 + C
        inds = np.abs(z) < 2
        img[inds] = img[inds] + 1

    img = cmap(np.mod(img/10, 1))  # fixme
    image(img, [0, 0], [width, height])

    # zoom in
    scale *= 1.1

run()