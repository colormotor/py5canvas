from py5canvas import *

font = create_font('Fascinate-Regular.ttf', 70)
txt = 'The quick brown fox '

def setup():
    create_canvas(512, 512)
    text_font(font)
    text_align(LEFT, TOP)

def func(t):
    r = width*0.3
    st = sin(t)
    ct = cos(t)*sin(t)**2

    return Vector(ct, st)*r

def draw():
    background(255)
    translate(center)

    n = len(txt) # number of characters
    # Get relative positions of each character in string
    t = [0.0]
    for c in txt:
        t.append(t[-1] + text_width(c))
    # and convert to the 2*PI range (on unit circle)
    t = (np.array(t)/t[-1])*np.pi*2 + frame_count*0.02

    for i in range(n):
        pos = func(t[i])
        delta = func(t[i+1]) - pos

        push_matrix()
        translate(pos)
        rotate(heading(delta))
        #circle(0, 0, 3)
        text(txt[i], 0, 0)
        pop_matrix()
run()
