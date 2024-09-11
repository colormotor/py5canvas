import inspect
import os
from .canvas import Canvas
 
def run():
    from . import run_sketch
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__
    run_sketch.main(filename, standalone=True)
