#!/usr/bin/env python3
import numpy as np
from . import canvas
from math import hypot, comb
import os
from PIL import Image, ImageChops, ImageFilter, ImageOps
import numbers

# Keywords/functions made available to the sketch
TWO_PI = 2*np.pi
HALF_PI = np.pi/2
QUARTER_PI = np.pi/4
TAU = 2*np.pi
PI = np.pi
RGB = 'rgb'
HSB = 'hsv'
HSV = 'hsv'
CENTER = 'center'
CORNER = 'corner'
RADIUS = 'radius'
random = np.random.uniform
random_uniform = np.random.uniform
random_choice = np.random.choice
random_int = np.random.randint
random_seed = np.random.seed
randomseed = np.random.seed
radians = canvas.radians
degrees = canvas.degrees
noise = canvas.noise
noise_detail = canvas.noise_detail
noise_seed = canvas.noise_seed
constrain = np.clip

def random_gaussian(mean=0.0, std_dev=1.0):
    return np.random.normal(mean, std_dev)

sin   = np.sin
cos   = np.cos
tan   = np.tan
atan2 = np.arctan2
dot = np.dot

floor = lambda x: np.floor(x).astype(int)
ceil  = lambda x: np.ceil(x).astype(int)
round = lambda x: np.round(x).astype(int)
abs = np.abs

params = None

def Color(*args):
    ''' Create a color'''
    return np.array(args)


def Vector(*args):
    ''' Create a color'''
    return np.array(args)


def dist(*args):
    ''' Computes the (Euclidean) distance between two points'''
    if len(args)==2:
        return np.linalg.norm(np.array(args[0]) -
                              np.array(args[1]))
    elif len(args)==4:
        x1, y1, x2, y2 = args
        return hypot(x2 - x1, y2 - y1)
    else:
        raise ValueError('Wrong number of args to dist')


def lerp(a, b, t):
    ''' Linear interpolation between two values'''
    return a + (b - a)*t


def map(value, *args, within_bounds=False):
    ''' Re-maps a number from one range to another. '''
    if len(args) == 4:
        start1, stop1, start2, stop2 = args
    elif len(args) == 2:
        (start1, stop1), (start2, stop2) = args
    else:
        raise ValueError('map: wrong number of args')

    t = ((value - start1) / (stop1 - start1))
    if within_bounds:
        t = max(0.0, min(t, 1.0))
    return start2 + (stop2 - start2) * t


def to_array(v):
    return np.array(v)


def to_image(ar):
    Image.fromarray(ar)


def load_image(path):
    '''Load an image from disk. Actually returns a PIL image'''
    import inspect

    try:
        im = Image.open(path)
    except FileNotFoundError:
        print(path, ' not found, trying file relative')
        stack = inspect.stack()
        caller_frame = stack[1]
        caller_filepath = caller_frame.filename
        path = os.path.join(os.path.dirname(caller_filepath),
                            path)
        im = Image.open(path)
        print('Success')
    return im

def bezier_point(*args):
    ''' Get the tangent to a bezier curve (cubic) given a parameter value

    Arguments:
    - Four points, specified either as a list of points, a sequence of four points, or a sequence of coordiantes
    - ~t~ the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents
    '''
    if len(args) == 5:
        P, t = args[:4], args[-1]
    elif len(args) == 8:
        P, t = [args[:2],
                args[2:4],
                args[4:6],
                args[6:]], args[-1]
    elif len(args) == 1:
        P, t = args
    P = np.array(P)
    if isinstance(t, numbers.Number):
        return eval_bezier(P, np.ones(1)*t)[0]
    return eval_bezier(P, np.ones(1)*t)


def bezier_tangent(*args):
    ''' Get the tangent to a bezier curve (cubic) given a parameter value

    Arguments:
    - Four points, specified either as a list of points, a sequence of four points, or a sequence of coordiantes
    - ~t~ the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents
    '''
    if len(args) == 5:
        P, t = args[:4], args[-1]
    elif len(args) == 8:
        P, t = [args[:2],
                args[2:4],
                args[4:6],
                args[6:]], args[-1]
    elif len(args) == 1:
        P, t = args
    P = np.array(P)
    if isinstance(t, numbers.Number):
        return eval_bezier(P, np.ones(1)*t, 1)[0]
    return eval_bezier(P, np.ones(1)*t, 1)


def bernstein(n, i):
    bi = comb(n, i)
    return lambda t, bi=bi, n=n, i=i: bi * t**i * (1 - t)**(n - i)


def eval_bezier(P, t, d=0):
    '''Bezier curve of degree len(P)-1. d is the derivative order (0 gives positions)'''
    n = len(P) - 1
    if d > 0:
        Q = np.diff(P, axis=0)*n
        return eval_bezier(Q, t, d-1)
    B = np.vstack([bernstein(n, i)(t) for i, p in enumerate(P)])
    return (P.T @ B).T


remap = map
