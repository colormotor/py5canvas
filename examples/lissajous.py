import numpy as np

def lissajous(t, a, b, omega, delta):
    return np.vstack([a*np.cos(omega*t + delta),
                      b*np.sin(t)]).T

def setup():
    sketch.create_canvas(800, 600)
    

def draw():
    c = sketch.canvas # Get the base canvas
    global a, b # we are modifying these

    c.background(0) 
    # Center of screen
    c.translate(c.width/2, c.height/2)

    np.random.seed(100)
    n = 300
    t = np.linspace(0, np.pi*2, n)
    delta = np.random.uniform(-np.pi/2, np.pi/2)
    da = np.random.uniform(-np.pi/2, np.pi/2)
    db = np.random.uniform(-np.pi/2, np.pi/2)
    omega = 3

    paths = []
    for o in np.linspace(0, 2.0, 25):
        a = np.sin(np.linspace(0, np.pi*8, n) + da + o*0.5)*230
        b = np.cos(np.linspace(0, np.pi*8, n) + db + o*1.0)*230
        P = lissajous(t, a,
                         b,
                         omega,
                         delta)
        paths.append(P)

    c.stroke_weight(1)
    c.stroke(255)
    c.no_fill()
    c.shape(paths)
