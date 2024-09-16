from py5canvas import *

# Converted L-system example from here:
# https://p5js.org/examples/simulate-l-systems.html
# This can be done almost directly using ChatGPT with the following prompt:
# "Convert this code to Python using camel case instead of snake case,
# but keeping exactly the same function and variable names, don't capitalize variables"
# Followed by the p5js code.

# Turtle Stuff
x, y = None, None  # the current position of the turtle
currentangle = 0  # which way the turtle is pointing
step = 20  # how much the turtle moves with each 'F'
angle = 90  # how much the turtle turns with a '-' or '+'

# Lindenmayer Stuff (L-Systems)
thestring = 'A'  # "axiom" or start of the string
numloops = 5  # how many iterations to pre-compute
therules = []  # array for rules
therules.append(['A', '-BF+AFA+FB-'])  # first rule
therules.append(['B', '+AF-BFB-FA+'])  # second rule

whereinstring = 0  # where in the L-system are we?

def setup():
    size(710, 400)
    background(255)
    stroke(0, 0, 0, 255)

    # start the x and y position at lower-left corner
    global x, y
    x = 0
    y = height - 1

    # COMPUTE THE L-SYSTEM
    global thestring
    for i in range(numloops):
        thestring = lindenmayer(thestring)

def draw():
    global whereinstring
    # draw the current character in the string:
    draw_it(thestring[whereinstring])

    # increment the point for where we're reading the string.
    # wrap around at the end.
    whereinstring += 1
    if whereinstring > len(thestring) - 1:
        whereinstring = 0

# interpret an L-system
def lindenmayer(s):
    outputstring = ''  # start a blank output string

    # iterate through 'therules' looking for symbol matches:
    for i in range(len(s)):
        ismatch = 0  # by default, no match
        for j in range(len(therules)):
            if s[i] == therules[j][0]:
                outputstring += therules[j][1]  # write substitution
                ismatch = 1  # we have a match, so don't copy over symbol
                break  # get outta this for() loop
        # if nothing matches, just copy the symbol over.
        if ismatch == 0:
            outputstring += s[i]

    return outputstring  # send out the modified string

# this is a custom function that draws turtle commands
def draw_it(k):
    global x, y, currentangle
    if k == 'F':  # draw forward
        # polar to cartesian based on step and currentangle:
        x1 = x + step * cos(radians(currentangle))
        y1 = y + step * sin(radians(currentangle))
        line(x, y, x1, y1)  # connect the old and the new

        # update the turtle's position:
        x = x1
        y = y1
    elif k == '+':
        currentangle += angle  # turn left
    elif k == '-':
        currentangle -= angle  # turn right

    # give me some random color values:
    r = random(128, 255)
    g = random(0, 192)
    b = random(0, 50)
    a = random(50, 100)

    # pick a gaussian (D&D) distribution for the radius:
    radius = 0
    radius += random(0, 15)
    radius += random(0, 15)
    radius += random(0, 15)
    radius = radius / 3

    # draw the stuff:
    fill(r, g, b, a)
    ellipse(x, y, radius, radius)

run()