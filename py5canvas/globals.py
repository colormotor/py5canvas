#!/usr/bin/env python3
import numpy as np
from . import canvas
from math import hypot, comb
import os
from PIL import Image, ImageChops, ImageFilter, ImageOps
import numbers
import rumore

# Keywords/functions made available to the sketch
PI = np.pi
TWO_PI = 2*np.pi
HALF_PI = np.pi/2
QUARTER_PI = np.pi/4
TAU = 2*np.pi
RGB = 'rgb'
HSB = 'hsv'
HSV = 'hsv'
CENTER = 'center'
LEFT = 'left'
RIGHT = 'right'
CORNER = 'corner'
TOP = 'top'
BOTTOM = 'bottom'
BASELINE = 'baseline'
RADIUS = 'radius'
CLOSE = 'close'
OPEN = 'OPEN'
CHORD = 'chord'
PIE = 'pie'
CHORD = 'chord'
MITER = 'miter'
BEVEL = 'bevel'
ROUND = 'round'
SQUARE = 'square'
PROJECT = 'project'
DEGREES = "degrees"
RADIANS = "radians"

# Blend modes
BLEND = "over"
REPLACE = "source"
ADD = "add"
MULTIPLY = "multiply"
SCREEN = "screen"
OVERLAY = "overlay"
DARKEST = "darken"
LIGHTEST = "lighten"
DIFFERENCE = "difference"
EXCLUSION = "exclusion"
HARD_LIGHT = "hard_light"
SOFT_LIGHT = "soft_light"
DODGE = "color_dodge"
BURN = "color_burn"
REMOVE = "clear"
SUBTRACT = "difference"  # Using difference as closest approximation


def random_gaussian(mean=0.0, std_dev=1.0, size=None):
    """Draw random samples from a normal (Gaussian) distribution.
    The probability density function of the normal distribution, first
    derived by De Moivre and 200 years later by both Gauss and Laplace
    independently [2]_, is often called the bell curve because of
    its characteristic shape (see the example below)."""
    return np.random.normal(mean, std_dev, size)


random = np.random.uniform
rand = np.random.uniform
random_uniform = np.random.uniform
random_choice = np.random.choice
random_int = np.random.randint
random_normal = np.random.normal
random_seed = np.random.seed
randomseed = np.random.seed
radians = canvas.radians
degrees = canvas.degrees
constrain = np.clip

create_font = canvas.create_font

dragging = None
mouse_is_pressed = None
mouse_button = None
params = None


sin   = np.sin
cos   = np.cos
tan   = np.tan
atan2 = np.arctan2
dot = np.dot
exp = np.exp
log = np.log
sqrt = np.sqrt

def floor(x):
    """Return the floor (int) of the input, element-wise."""
    return np.floor(x).astype(int)

def ceil(x):
    """Return the ceiling (int) of the input, element-wise."""
    return np.ceil(x).astype(int)

def round(x, decimals=0):
    """Evenly round to the given number of decimals. Returns integers with `decimals=0` (default)"""
    if decimals == 0:
        return np.round(x).astype(int)
    return np.round(x, decimals)

abs = np.abs

def is_number(x):
    return isinstance(x, numbers.Number)

def color(*args):
    ''' Create a cector with components specified as comma-separated values.
    :returns: A NumPy array representing the specified color components.
    This returns either a 3d (RGB) array if 3 or 1 (luminosity) components are specified,
    or a 4d (RGBA) array if 4 or 2 components are specified.
    '''
    if len(args) == 1:
        if is_number(args[0]):
            # Assume this is Luminosity and convert to RGB
            return np.ones(3, dtype=np.float32)*args[0]
        else:
            # Assume this is either RGB or RGBA
            return np.array(args).astype(np.float32)
    else:
        if len(args) == 2:
            # Assume this is Luminosity and Alpha
            return np.concatenate([np.ones(3)*args[0], [args[1]]]).astype(np.float32)
        else:
            return np.array(args).astype(np.float32)

Color = color

def vector(*args):
    ''' Create a vector with components specified as comma-separated values
    :returns: A NumPy array with the specified components
    '''
    if len(args)==1:
        v = args[0]
    else:
        v = args
    return np.array(v, dtype=np.float64)

Vector = vector

def create_vector(*args):
    ''' Create a vector with components specified as comma-separated values
    :returns: A NumPy array with the specified components
    '''
    return vector(*args)

def range_between(a, b, num, endpoint=True):
    ''' Returns a list of numbers that goes from a and b in a specified number of steps.

        E.g. `range_between(0, 1, 5)` will give the list `[0.0, 0.25, 0.5, 0.75, 1.0]`

        Similar to `np.linspace`
    '''
    return list(np.linspace(a, b, num, endpoint))


def linspace(a, b, num, endpoint=True):
    ''' Returns a list of numbers that goes from a and b in a specified number of steps.

        E.g. `linspace(0, 1, 5)` will give the list `[0.0, 0.25, 0.5, 0.75, 1.0]`

        Similar to `np.linspace`
    '''
    return np.linspace(a, b, num, endpoint)


def arange(a, b, step):
    ''' Returns a list of numbers that goes from a and b with equal steps

        E.g. `arange(0, 1, 0.25)` will give the list `[0.0, 0.25, 0.5, 0.75, 1.0]`

        Similar to `np.linspace`
    '''
    return np.arange(a, b, step)


def grid_points(x, y):
    ''' Given two 1d arrays/lists of numbers representing the x and y axes,
       return a sequence of points on a grid represented as a numpy array.
       It can be useful to accelerate noise computations in vectorized form
    '''
    xx, yy = np.meshgrid(x, y)
    return np.stack([xx.ravel(), yy.ravel()], axis=-1)


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
       Input can be two numbers `x, y` or a tuple/array, followed by the angle in radians
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
    if im.mode == 'P':
        if 'transparency' in im.info:
            im = im.convert('RGBA')
        else:
            im = im.convert('RGB')

    return im

def bezier_point(*args):
    ''' Get a point along a bezier curve (cubic) given a parameter value

    Arguments:
    - Four points, specified either as a list of points, a sequence of four points, or a sequence of coordiantes
    - `t` the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents
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
    - `t` the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents
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


# Optional perlin noise init
_noise_octaves = 4
_noise_grad = True
_noise_funcs = [rumore.value_noise, rumore.grad_noise]


def noise_seed(seed):
    """Sets the seed for the noise generator"""
    rumore.cfg.seed = seed


def _noise_func(*args):
    args = list(args)
    narg = len(args)
    # Make sure all elements are arrays if the first one is
    if narg > 1:
        if not is_number(args[0]):
            for i in range(1, narg):
                if is_number(args[i]):
                    args[i] = np.ones_like(args[0]) * args[i]
    return _noise_funcs[_noise_grad](*args, octaves=_noise_octaves)


def noise_detail(octaves, falloff=0.5, lacunarity=2.0, gradient=True):
    """Adjusts the character and level of detail produced by the Perlin noise function.

    Arguments:

    - `octaves` (int): the number of noise 'octaves'. Each octave has double the frequency of the previous.
    - `falloff` (float, default 0.5): a number between 0 and 1 that multiplies the amplitude of each consectutive octave
    - `lacunarity` (float, default 2.0): number that multiplies the frequency of each consectutive octave
    - `gradient` (bool, default True): If true (default) `noise` uses gradient noise, otherwise it use value noise
    """
    global _noise_octaves, _noise_grad
    # no < 1 octaves, thank you
    octaves = int(max(1, octaves))
    rumore.cfg.falloff = falloff
    rumore.cfg.lacunarity = lacunarity
    _noise_octaves = octaves
    _noise_grad = int(gradient)


def noise(*args):
    """Returns noise (between 0 and 1) at a given coordinate or at multiple coordinates.
    Noise is created by summing consecutive "octaves" with increasing level of detail.
    By default this function returns "gradient noise", a variant of noise similar to Ken Perlin's original version.
    Alternatively the function can return "value noise", which is a faster but more blocky version.
    By default each octave has double the frequency (lacunarity) of the previous and an amplitude falls off for each octave. By default the falloff is 0.5.
    The default number of octaves is `4`.

    Use `noise_detail` to set the number of octaves and optionally falloff, lacunarity and whether to use gradient or value noise.

    Arguments:

    - The arguments to this function can vary from 1 to 3, determining the "space" that is sampled to generate noise.
    The function also accepts numpy arrays for each coordinate but these must be of the same size.
    """
    res = _noise_func(*args)  # _noise_funcs[_noise_grad](*args, octaves=_noise_octaves)
    return res * 0.5 + 0.5


def noise_grid(*args, **kwargs):
    """Returns a 2d array of noise values (between 0 and 1).
    The array can be treated as a grayscale image and is defined by two input 1d array parameters, x and y.
    The number of elements in x and y define the number of columns and rows, respectively.
    Optionally a third `z` parameter can be specified and it defines the depth of a "slice" in a 3d noise volume.

    Arguments:

    - The arguments to this function can be either two arrays, say
    ```python
    img = noise_grid(np.linspace(0, width, 100),
                     np.linspace(0, height, 100))
    ```
    or three, where the third parameter can be a scalar
    ```python
    img = noise_grid(np.linspace(0, width, 100),
                     np.linspace(0, height, 100), 3.4)
    ```
    """
    return (
        rumore.noise_grid(*args, gradient=_noise_grad, octaves=_noise_octaves, **kwargs)
        * 0.5
        + 0.5
    )



class VideoInput:
    """
    Video Input utility (requires OpenCV to be installed).
    Allows for reading frames from a video file or camera.

    Arguments:

    - `name`: Either an integer indicating the device number, or a string indicating the path of a video file
    - `size`: A tuple indicating the desired size of the video frames (width, height)
    - `resize_mode`: A string indicating the desired resize mode. Can be 'crop' or 'stretch'
    - `flipped`: Boolean indicating if the frame should be flipped horizontally. Defaults to None
    - `vertical_flipped`: Boolean indicating if the frame should be flipped vertically. Defaults to None
    """

    def __init__(
        self, name=0, size=None, resize_mode="crop", flipped=None, vertical_flipped=None
    ):
        """Constructor"""
        import cv2

        # define a video capture object
        self.vid = cv2.VideoCapture(name)
        if size is not None:
            self.size = size
        else:
            self.size = (
                int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
        self.resize_mode = resize_mode
        self.name = name
        self.flipped = flipped
        self.vertical_flipped = vertical_flipped

    def close(self):
        self.vid.release()

    def read(self, loop_flag=False, pil=True, grayscale=False):
        import cv2

        # Capture video frame by frame
        success, img = self.vid.read()

        if not success:
            if (
                type(self.name) == str and not loop_flag
            ):  # If a video loop automatically
                self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return self.read(True)
            else:
                print("No video")
                if self.size is not None:
                    return np.zeros((self.size[1], self.size[0], 3)).astype(np.uint8)
                else:
                    return np.zeros((16, 16, 3)).astype(np.uint8)

        if self.size is not None:
            src_w, src_h = img.shape[1], img.shape[0]
            dst_w, dst_h = self.size

            if self.resize_mode == "crop":
                # Keep aspect ratio by cropping
                aspect = dst_w / dst_h

                # Check if aspect ratio match
                asrc_w = int(aspect * src_h)
                if asrc_w > src_w:  # aspect ratio > 1
                    asrc_h = int(src_h / aspect)
                    d = (src_h - asrc_h) // 2
                    img = img[d : d + asrc_h, :, :]
                elif asrc_w < src_w:  # aspect ratio < 1
                    d = (src_w - asrc_w) // 2
                    img = img[:, d : d + asrc_w, :]

            # Resize the image frames
            img = cv2.resize(img, self.size)

        if self.flipped:
            img = img[:, ::-1]

        if self.vertical_flipped:
            img = img[::-1]

        img = img[:, :, ::-1]
        if pil:
            if grayscale:
                return Image.gromarray(img).convert("L")
            return Image.fromarray(img)
        if grayscale:
            return np.mean(img / 255, axis=-1)
        return img
