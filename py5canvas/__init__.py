import inspect
import numpy as np
import os
from .canvas import Canvas, VideoInput
import pdb

# Tricks the linter into knowing the symbols we inject
from .dummy_globals import *
from .globals import *

_canvas = None

def create_canvas(w, h, save_background=False):
    global _canvas

    # Create the canvas
    _canvas = canvas.Canvas(w, h, save_background=save_background)
    width, height = w, h
    center = np.array([w/2, h/2])

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
            #pdb.set_trace()
            var_context[func] = wrap_method(_canvas, func)

    # Inject properties
    var_context['width'] = w
    var_context['height'] = h
    var_context['center'] = np.array([w/2, h/2])

    return _canvas

size = create_canvas

def run(frame_rate=60, inject=True, show_toolbar=False, renderer=''):
    if renderer:
        print("Only Cairo renderer is currently supported")
    # Make sure we are in a Python script if this is called,
    # otherwise things will break. Avoids the need for if __name__=='__main__'
    stack = inspect.stack()
    caller_frame = inspect.stack()[1].frame
    var_context = caller_frame.f_globals
    caller_module = inspect.getmodule(caller_frame)
    if '__loaded_py5sketch__' in var_context:
        pass
    else:
        from . import run_sketch
        if caller_module is None:
            filename = caller_frame.f_code.co_filename
        else:
            filename = caller_module.__file__
        run_sketch.main(filename, fps=frame_rate, inject=inject, show_toolbar=show_toolbar)
