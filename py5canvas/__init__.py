import inspect
from . import run_sketch
import os

def run():
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__
    os.chdir(os.path.basename(filename))
    print("Setting working directory to", os.path.basename(filename))
    run_sketch.main(filename, standalone=True)
