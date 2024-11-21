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
CLOSE = 'close'
OPEN = 'OPEN'
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

def random_gaussian(mean=0.0, std_dev=1.0, size=None):
    return np.random.normal(mean, std_dev, size)

sin   = np.sin
cos   = np.cos
tan   = np.tan
atan2 = np.arctan2
dot = np.dot
exp = np.exp
log = np.log

floor = np.floor #lambda x: np.floor(x).astype(int)
ceil  = np.ceil #lambda x: np.ceil(x).astype(int)
round = np.round #lambda x: np.round(x).astype(int)
abs = np.abs

params = None

def Color(*args):
    ''' Create a color'''
    if len(args)==1:
        v = args[0]
    else:
        v = args
    return np.array(v, dtype=np.float32)


def Vector(*args):
    ''' Create a color'''
    if len(args)==1:
        v = args[0]
    else:
        v = args
    return np.array(v, dtype=np.float64)


def range_between(a, b, num, endpoint=True):
    ''' Returns a list of numbers that goes from a and b in a specified number of steps.

        E.g. ~range_betwee(0, 1, 5)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

        Similar to ~np.linspace~
    '''
    return list(np.linspace(a, b, num, endpoint))


def linspace(a, b, num, endpoint=True):
    ''' Returns a list of numbers that goes from a and b in a specified number of steps.

        E.g. ~linspace(0, 1, 5)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

        Similar to ~np.linspace~
    '''
    return np.linspace(a, b, num, endpoint)


def arange(a, b, step):
    ''' Returns a list of numbers that goes from a and b with equal steps

        E.g. ~arange(0, 1, 0.25)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

        Similar to ~np.linspace~
    '''
    return np.arange(a, b, step)


def angle_between(*args):
    ''' Angle between two vectors (2d) [-pi,pi]'''
    if len(args)==2:
        a, b = args
    elif len(args)==4:
        a = args[:2]
        b = args[2:]
    return np.arctan2( a[0]*b[1] - a[1]*b[0], a[0]*b[0] + a[1]*b[1] )


def rotate_vector(*args):
    """Rotate a 2D vector (x, y) by a given angle in radians.
       Input can be two numbers ~x, y~ or a tuple/array, followed by the angle in radians
    """
    numpy = False
    if len(args) == 2:
        x, y = args[0]
        angle = args[1]
        if isinstance(args[0], np.ndarray):
            numpy = True
    elif len(args) == 3:
        x, y, angle = args
    else:
        raise ValueError("Incorrect number of arguments")

    tx = x * np.cos(angle) - y * np.sin(angle)
    ty = x * np.sin(angle) + y * np.cos(angle)
    if numpy:
        return np.array([tx, ty])
    return tx, ty


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


def mag(*args):
    ''' Returns the magnitude (length) of a vector.
    Accepts one vector as an argument or a sequenc of coordinates for each component of the vector
    '''
    if len(args)==1:
        return np.linalg.norm(np.array(args[0]))
    else:
        return np.linalg.norm(np.array(args))


def heading(*args):
    ''' Returns the heading (orientation) in radians of a 2d vector
    '''
    if len(args) == 2:
        x, y = args
    elif len(args) == 1:
        x, y = args[0][0], args[0][1]
    else:
        raise ValueError('Wrong number of arguments for heading')
    return np.arctan2(y, x)


def direction(angle):
    ''' Returns a vector with magnitude 1 and oriented according to an angle specified in radians'''
    return np.array([np.cos(angle), np.sin(angle)])


def lerp(a, b, t):
    ''' Linear interpolation between two values'''
    return a + (b - a)*t


def remap(value, *args, within_bounds=False):
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
    ''' Get a point along a bezier curve (cubic) given a parameter value

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
        return canvas.eval_bezier(P, np.ones(1)*t)[0]
    return canvas.eval_bezier(P, np.ones(1)*t)


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
        return canvas.eval_bezier(P, np.ones(1)*t, 1)[0]
    return canvas.eval_bezier(P, np.ones(1)*t, 1)

