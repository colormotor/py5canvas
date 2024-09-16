from py5canvas import *

# Converted spirograph example from here:
# https://p5js.org/examples/simulate-spirograph.html
# This can be done almost directly using ChatGPT with the following prompt:
# "Convert this code to Python using camel case instead of snake case,
# but keeping exactly the same function and variable names, don't capitalize variables"
# Followed by the p5js code.

numsines = 20  # how many of these things can we do at once?
sines = [0] * numsines  # an array to hold all the current angles
rad = None  # an initial radius value for the central sine
i = None  # a counter variable

# play with these to get a sense of what's going on:
fund = 0.005  # the speed of the central sine
ratio = 1  # what multiplier for speed is each additional sine?
alpha = 50  # how opaque is the tracing system

trace = False  # are we tracing?

def setup():
    create_canvas(710, 400)
    frame_rate(60)
    global rad, i
    rad = height / 4  # compute radius for central circle
    background(204)  # clear the screen

    for i in range(len(sines)):
        sines[i] = PI  # start EVERYBODY facing NORTH

def draw():
    global rad, i
    if not trace:
        background(204)  # clear screen if showing geometry
        stroke(0, 255)  # black pen
        no_fill()  # don't fill

    # MAIN ACTION
    push()  # start a transformation matrix
    translate(width / 2, height / 2)  # move to middle of screen

    for i in range(len(sines)):
        erad = 0  # radius for small "point" within circle... this is the 'pen' when tracing
        # setup for tracing
        if trace:
            stroke(0, 0, 255 * (float(i) / len(sines)), alpha)  # blue
            fill(0, 0, 255, alpha / 2)  # also, um, blue
            erad = 5.0 * (1.0 - float(i) / len(sines))  # pen width will be related to which sine
        radius = rad / (i + 1)  # radius for circle itself
        rotate(sines[i])  # rotate circle
        if not trace:
            ellipse(0, 0, radius * 2, radius * 2)  # if we're simulating, draw the sine
        push()  # go up one level
        translate(0, radius)  # move to sine edge
        if not trace:
            ellipse(0, 0, 5, 5)  # draw a little circle
        if trace:
            ellipse(0, 0, erad, erad)  # draw with erad if tracing
        pop()  # go down one level
        translate(0, radius)  # move into position for next sine
        sines[i] = (sines[i] + (fund + (fund * i * ratio))) % TWO_PI  # update angle based on fundamental

    pop()  # pop down final transformation

def key_pressed(c, modifier):
    global trace
    trace = not trace
    background(255)

run()