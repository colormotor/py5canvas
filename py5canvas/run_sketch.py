#!/usr/bin/env python3
"""A simple p5-inspired interface to the Canvas object
NOTE: this is highly unoptimized, since it uses pycairo for rendering and copies all the screen at each frame
It will probably be significantly slow when using a large canvas size
"""

# importing pyglet module
import pyglet
from pyglet.window import key
import numpy as np
import os, sys, time
from py5canvas import canvas
import traceback

args = lambda: None
args.program = './../examples/basic_animation.py'

class perf_timer:
    def __init__(self, name='', verbose=False): # Set verbose to true for debugging
        #if name and verbose:
        #    print(name)
        self.name = name
        self.verbose = verbose

    def __enter__(self):
        self.t = time.perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        self.elapsed = (time.perf_counter() - self.t)*1000
        if self.name and self.verbose:
            print('%s: elapsed time %.3f milliseconds'%(self.name, self.elapsed))


class FileWatcher:
    """Checks if a file has been modified"""
    def __init__(self, path):
        self._cached_stamp = 0
        self.filename = path

    def modified(self):
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            return True
        return False


class Sketch:
    """Contains our canvas and the pyglet window.
    Takes care of window management and copying the canvas data to the appropriate pyglet image"""
    def __init__(self, path,
                       width,
                       height,
                       title="Sketch"):
        self.window = pyglet.window.Window(width, height, title)
        self.width, self.height = width, height
        self.create_canvas(self.width, self.height)
        self.frame_rate(60)
        self.startup_error = False
        self.runtime_error = False

        self.error_label = pyglet.text.Label('Error',
                           font_name='Arial',
                           font_size=12,
                           x=10, y=50,
                           anchor_x='left',
                           color=(255,0,0,255))

        self.watcher = None
        self.path = path

        self.frame_count = 0
        self.delta_time = 0.0

        self._mouse_pos = None #np.zeros(2)
        self.mouse_pos = np.zeros(2)
        self.prev_mouse = None
        self.mouse_delta = np.zeros(2)
        self.mouse_button = 0
        self.mouse_pressed = False
        self.mouse_moving = False

        self.var_context = {}

    def create_canvas(self, w, h, fullscreen=False):
        print('setting window size')
        self.is_fullscreen = fullscreen
        self.window.set_size(w, h)
        self.window.set_fullscreen(fullscreen)
        self.width, self.height = w, h
        self.canvas = canvas.Canvas(w, h)
        self.window_width, self.window_height = self.window.get_size()

        # Create image and copy initial canvas buffer to it
        buf = self.canvas.get_buffer()
        buf = (pyglet.gl.GLubyte * len(buf))(*buf)
        self.image = pyglet.image.ImageData(w, h, "BGRA", buf)

    def toggle_fullscreen(self):
        self.fullscreen(not self.is_fullscreen)

    def fullscreen(self, flag):
        self.is_fullscreen = flag
        self.window.set_fullscreen(flag)
        self.window_width, self.window_height = self.window.get_size()

    def reload(self, var_context):
        print("Reloading sketch code")
        self.var_context = var_context

        self.frame_count = 0
        if self.watcher is None:
            print("Creating file watcher for " + self.path)
            self.watcher = FileWatcher(self.path)
        try:
            print("Compiling")
            prog = compile(open(self.path).read(), self.path, 'exec')
            exec(prog, var_context)
                # Once we loaded script setup
            var_context['setup']()
            self.startup_error = False
            print("Success")
        except Exception as e:
            print('Error in sketch setup')
            print(e)
            self.startup_error = True
            self.error_label.text = str(e)
            traceback.print_exc()


    def _update_mouse(self):
        if self._mouse_pos is None:
            return

        if self.prev_mouse is None:
            self.mouse_pos = self._mouse_pos

        self.prev_mouse = self.mouse_pos
        self.mouse_pos = self._mouse_pos
        self.mouse_delta = self.mouse_pos - self.prev_mouse

        # if self.mouse_pressed:
        #     print('Mouse:')
        #     print(self.mouse_delta)
        #     print(self.mouse_pos)
        #     print(self.mouse_delta)


    # internal update
    def _update(self, dt):
        self.delta_time = dt
        self._update_mouse()

        with perf_timer('update'):
            if not self.runtime_error or self.frame_count==0:
                try:
                    if 'draw' in self.var_context:
                        self.var_context['draw']()
                    else:
                        print('no draw in var context')
                    self.runtime_error = False
                except Exception as e:
                    print('Error in sketch draw')
                    print(e)
                    self.error_label.text = str(e)
                    self.runtime_error = True
                    traceback.print_exc()

        pitch = self.width * 4
        with perf_timer('get buffer'):
            buf = self.canvas.get_buffer()

        with perf_timer('update image'):
            # https://stackoverflow.com/questions/9035712/numpy-array-is-shown-incorrect-with-pyglet
            buf = (pyglet.gl.GLubyte * len(buf)).from_buffer(buf)
            # The following is slow as hell
            #buf = (pyglet.gl.GLubyte * len(buf))(*buf)

        self.image.set_data("BGRA", -pitch, buf) # Looks like negative sign takes care of C-contiguity

        with perf_timer('update count'):
            # Update timers etc
            self.frame_count += 1

        if self.watcher.modified(): # Every frame check for file modification
            print("File modified, reloading")
            # Reload in global namespace
            self.reload(self.var_context)

    def frame_rate(self, fps):
        pyglet.clock.unschedule(self._update)
        pyglet.clock.schedule_interval(self._update, 1.0/fps)


def main():
    from importlib import reload
    mouse_moving = False

    ## User callbacks, will get overridden by user sketch
    def setup():
        pass

    def draw():
        pass

    def key_pressed(k, modifier):
        pass

    def mouse_moved():
        pass

    def mouse_dragged():
        pass

    if len(sys.argv) < 2:
        print('You need to specify a python sketch file in the arguments')
        assert(0)

    print("Starting up sketch " + sys.argv[1])
    # Create our sketch context and load script
    sketch = Sketch(sys.argv[1], 512, 512)

    @sketch.window.event
    def on_key_press(symbol, modifier):
        # print('Key pressed')
        if 'key_pressed' in sketch.var_context:
            sketch.var_context['key_pressed'](symbol, modifier)

    @sketch.window.event
    def on_mouse_motion(x, y, dx, dy):
        sketch._mouse_pos = np.array([x, sketch.window_height-y])
        #print((x, y, dx, dy))
        if 'mouse_moved' in sketch.var_context:
            sketch.var_context['mouse_moved']()

    @sketch.window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        sketch._mouse_pos = np.array([x, sketch.window_height-y])
        sketch.mouse_pressed = True
        if 'mouse_dragged' in sketch.var_context:
            sketch.var_context['mouse_dragged']()

    @sketch.window.event
    def on_mouse_press(x, y, button, modifiers):
        print("press")
        sketch.mouse_pressed = True
        sketch.mouse_button = button
        sketch._mouse_pos = np.array([x, sketch.window_height-y])

    @sketch.window.event
    def on_mouse_release(x, y, button, modifiers):
        print("release")
        sketch.mouse_pressed = False
        sketch._mouse_pos = np.array([x, sketch.window_height-y])

    sketch.reload(locals())
    key_pressed(0, 0)

    # on draw event
    @sketch.window.event
    def on_draw():
        # clearing the window
        sketch.window.clear()
        sketch.image.blit(0, 0) #, width=sketch.window_width, height=sketch.window_height) #*window.get_size())
        if sketch.startup_error or sketch.runtime_error:
            sketch.error_label.draw()

    print("Starting loop")
    pyglet.app.run()


if __name__ == '__main__':
    main()
