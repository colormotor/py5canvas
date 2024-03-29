import inspect
from . import run_sketch
import os

def run():
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__
    run_sketch.main(filename, standalone=True)
