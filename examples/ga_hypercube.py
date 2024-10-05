#!/usr/bin/env python3
from py5canvas import *
import time
import math
import os
os.environ['NUMBA_DISABLE_JIT'] = "1"
import numpy as np
# Example using projective geometric algebra to create a rotating hypercube
# Must install clifford https://clifford.readthedocs.io/en/latest/ to run
from numpy import uint32, float32
import numba
print(numba.__version__)
from math import e, pi
from clifford import Cl
from itertools import combinations




dim = 4

layout, blades = Cl(dim, 0, 1, firstIdx=0)
e0 = blades['e0']
b = blades
e12 = blades['e12']
e13 = blades['e13']
rot34 = 1.3


def is_ok(d):
    return d==2 #(not d%2) and d > 1 and d < dim


rotation_bases = [k for k in blades.keys() if is_ok(len(k)-1) and not '0' in k] #not len(k)%2 and len(k) > ==dim and '0' not in k]

print(blades.keys())
print(rotation_bases[-1])
print(rotation_bases)


def hypercube_graph(dim, R, offset=None):
    c = sketch.canvas
    w, h = c.width, c.height
    bases = [blades['e%d'%(i+1)] for i in range(dim)]
    def point(p):
        return np.sum([1.0*e0] + [v*b for v, b in zip(p, bases)]).dual()
    def to_screen(p):
        return p*200 + [w*0.5, h*0.5]
    n = 2**dim
    multi = []
    center = np.ones(dim)*0.5
    if offset is not None:
        center[:len(offset)] = offset

    for i in range(n):
        p = np.array([float32((i>>j)&0x1) for j in range(dim)]) - center
        q = point(p)
        q = R*q*(~R)
        q = q.vee(e0.dual())^(blades['e3']+1.2*e0)

        multi.append(q)

    edges = []
    segments = []

    for a, b in combinations(range(n), 2):
        d = a^b
        if d.bit_count() == 1:
            edges.append((a, b))
            pa = multi[a].dual()
            pb = multi[b].dual()
            p1 = np.array([pa[bases[0]], pa[bases[1]]])
            p2 = np.array([pb[bases[0]], pb[bases[1]]])
            segments.append(np.array([to_screen(p1), to_screen(p2)]))
    return segments


def setup():
    create_canvas(512, 512)


def draw():
    c = sketch.canvas
    c.set_color_scale(1.0)

    c.background(0)
    t = frame_count / 300

    R = e**(t*b['e13']) * e**(t*2*b['e12'])
    R = R*e**(rot34*b['e34']) #rotation_bases[-1]])
    R = R*e**(2*np.sin(t)*b['e24'])

    p = np.zeros(dim)+0.5
    segments = hypercube_graph(dim, R, p)

    c.stroke(1, 0.5)
    for p1, p2 in segments:
        c.line(p1, p2)
    c.fill(0.2,0.7,1)
    for p1, p2 in segments:
        c.circle(p1, 4)
        c.circle(p2, 4)

run()
