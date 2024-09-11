import numpy as np
from . import canvas
import inspect
from .dummy_globals import *

TWO_PI = 2*np.pi
PI = np.pi
random = np.random.uniform
randomseed = np.random.seed
randomseed = np.random.seed
radians = canvas.radians
degrees = canvas.degrees
map  = canvas.map
sin  = np.sin
cos  = np.cos
floor = lambda x: np.floor(x).astype(int)
ceil = lambda x: np.ceil(x).astype(int)
round = lambda x: np.round(x).astype(int)

_canvas = None

def create_canvas(w, h):
    global _canvas
    # Create the canvas
    _canvas = canvas.Canvas(w, h)

    # Code injection trick
    def wrap_method(obj, func):
        # print('wrapping ' + func)
        def wrapper(*args, **kwargs):
            # print('calling wrapped ', func, args)
            return getattr(obj, func)(*args, **kwargs)
        return wrapper

    # We want to inject the canvas functions to the globals of the caller
    caller_frame = inspect.stack()[1].frame
    # Get the globals dictionary of the caller's context
    var_context = caller_frame.f_globals
    # Inject functions in caller globals
    for func in dir(_canvas):
        if '__' not in func and callable(getattr(_canvas, func)):
            var_context[func] = wrap_method(_canvas, func)

    return _canvas
