import inspect
import os
from .canvas import Canvas
 
def run(frame_rate=0, renderer=''):
    from . import run_sketch
    if renderer:
        print("Only Cairo renderer is currently supported")
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__
    run_sketch.main(filename, fps=frame_rate, standalone=True)
