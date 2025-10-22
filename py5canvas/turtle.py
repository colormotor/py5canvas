'''
© Daniel Berio (@colormotor) 2021 - ...
turtle - 2d turtle implementation (crudely adapted from Fogelman's axi module) and adapted to
'''

import numpy as np


def vec(*args):
    return np.array(args)


def radians( x ):
    return np.pi/180*x


def degrees( x ):
    return x * (180.0/np.pi)


class Turtle(object):
    def __init__(self, pos=(0,0), canvas=None, autodraw=True):
        self.reset(pos)
        self.canvas = canvas
        self._autodraw = autodraw

    def reset(self, pos=(0,0)):
        self.x = pos[0]
        self.y = pos[1]
        self.h = 0
        self.pen = True
        self._path = [vec(*pos)] #0,0)]
        self._paths = []

    def clear(self):
        self._path = [vec(self.x, self.y)]
        self._paths = []

    @property
    def autodraw(self):
        return self.canvas is not None and self._autodraw

    @property
    def paths(self):
        paths = list(self._paths)
        if len(self._path) > 1:
            paths.append(self._path)
        return [np.array(P) for P in paths]

    def pd(self):
        self.pen = True
        if len(self._path) < 2:
            self._path = [vec(self.x, self.y)]

    pendown = down = pd

    def pu(self):
        self.pen = False
        if len(self._path) > 1:
            self._paths.append(self._path)
            self._path = []
    penup = up = pu

    def isdown(self):
        return self.pen

    def goto(self, x, y=None):
        if y is None:
            x, y = x
        if self.pen:
            self._path.append(vec(x, y))
            if self.autodraw:
                self.canvas.line(self._path[-1], self._path[-2])

        self.x = x
        self.y = y
    setpos = setposition = goto

    def setx(self, x):
        self.goto(x, self.y)

    def sety(self, y):
        self.goto(self.x, y)

    def seth(self, heading):
        self.h = heading
    setheading = seth
    angle = seth

    def home(self):
        self.goto(0, 0)
        self.seth(0)

    def fd(self, distance):
        x = self.x + distance * np.cos(radians(self.h))
        y = self.y + distance * np.sin(radians(self.h))
        self.goto(x, y)
    forward = fd

    def bk(self, distance):
        x = self.x - distance * np.cos(radians(self.h))
        y = self.y - distance * np.sin(radians(self.h))
        self.goto(x, y)
    backward = back = bk

    def rt(self, angle):
        self.seth(self.h + angle)
    right = rt
    rotate = rt

    def lt(self, angle):
        self.seth(self.h - angle)
    left = lt

    def square(self, side):
        for i in range(4):
            self.fd(side)
            self.rt(90)

    def circle(self, radius, extent=None, steps=None):
        if extent is None:
            extent = 360
        if steps is None:
            steps = int(round(abs(2 * np.pi * radius * extent / 180)))
            steps = max(steps, 4)
        cx = self.x + radius * np.cos(radians(self.h + 90))
        cy = self.y + radius * np.sin(radians(self.h + 90))
        a1 = degrees(np.arctan2(self.y - cy, self.x - cx))
        a2 = a1 + extent if radius >= 0 else a1 - extent
        for i in range(steps):
            p = i / float(steps - 1)
            a = a1 + (a2 - a1) * p
            x = cx + abs(radius) * np.cos(radians(a))
            y = cy + abs(radius) * np.sin(radians(a))
            self.goto(x, y)
        if radius >= 0:
            self.seth(self.h + extent)
        else:
            self.seth(self.h - extent)

    def pos(self):
        return vec(self.x, self.y)
    position = pos

    def towards(self, x, y=None):
        if y is None:
            x, y = x
        return degrees(np.arctan2(y - self.y, x - self.x))

    def xcor(self):
        return self.x

    def ycor(self):
        return self.y

    def heading(self):
        return self.h

    def distance(self, x, y=None):
        if y is None:
            x, y = x
        return np.hypot(x - self.x, y - self.y)

    def draw(self):
        if self.canvas is None:
            print("No canvas set for turtle")
            return
        c = self.canvas
        c.shape(self.paths)

    def draw_turtle(self, size=10):
        if self.canvas is None:
            print("No canvas set for turtle")
            return
        c = self.canvas
        c.push()
        c.stroke(0)
        c.stroke_weight(2/size)
        c.fill(1)
        c.translate(self.x, self.y)
        c.rotate_deg(self.h)
        c.scale(size)
        c.polygon([[-0.3, -0.5],
                  [0.7, 0.0],
                   [-0.3, 0.5],
                   [0.0, 0.0]])
        c.pop()
