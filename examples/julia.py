''' A simple Julia zoom
    using numpy for computation and matplotlib for colors'''
import numpy as np
import matplotlib

cmap = matplotlib.cm.get_cmap('jet') #'jet')
scale = 300
target = complex(-0.1930840493097, -0.080000106)

def setup():
    sketch.create_canvas(800, 600)
    

def draw():
    global scale, target
    c = sketch.canvas
    c.background(0)

    iterations = 300

    w, h = c.width//2, c.height//2
    a, b = np.meshgrid(np.linspace(-w/scale, w/scale, w), np.linspace(-h/scale, h/scale, h))
    z = a + b*1j

    # Rotate "camera"
    rot = np.exp(sketch.frame_count/30*1j)
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
    c.image(img, [0, 0], [c.width, c.height])

    # zoom in
    scale *= 1.1
