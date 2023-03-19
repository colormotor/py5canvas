#!/usr/bin/env python3
"""A simple p5-inspired interface to the Canvas object
© Daniel Berio (@colormotor) 2023 - ...

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
import importlib
import threading

# Optionally import imgui
imgui_loader = importlib.find_loader('imgui')
if imgui_loader is not None:
    import imgui
    from imgui.integrations.pyglet import create_renderer
else:
    imgui = None

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

def load_json(path):
    import json, codecs
    try:
        with codecs.open(path, encoding='utf8') as fp:
            data = json.load(fp)
        return data
    except IOError as err:
        print(err)
        print ("Unable to load json file:" + path)
        return {}

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

        # Check if OSC is available
        osc_loader = importlib.find_loader('pythonosc')
        if osc_loader is not None:
            self.server_address = '0.0.0.0' # Will listen from all IPs
            self.server_port = 9999
            self.client_address = '127.0.0.1'
            self.client_port = 9998
            self.dispatcher = None
            self.oscserver = None
            self.oscclient = None
            self.server_thread = None
            self.osc_enabled = True
            self.start_osc()
        else:
            print('pythonosc not installed')
            self.osc_enabled = False
            self.oscserver = None
            self.oscclient = None
            self.server_thread = None
            self.osc_enabled = False

        # For IMGUI use
        self.impl = None

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


        if imgui is not None:
            # For some reason this only works here and not in the constructor.
            if self.impl is None:
                imgui.create_context()
                self.impl = create_renderer(self.window)

            imgui.new_frame()

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

        # Draw to window
        self.window.clear()
        self.image.blit(0, 0)

        if self.startup_error or self.runtime_error:
            self.error_label.draw()

        if imgui is not None:
            imgui.render()
            self.impl.render(imgui.get_draw_data())


    def frame_rate(self, fps):
        pyglet.clock.unschedule(self._update)
        pyglet.clock.schedule_interval(self._update, 1.0/fps)

    def start_osc(self):
        # Load server/client data from json
        # startup
        # if 'osc_message' in self.var_context:
        print('starting up OSC')

        from pythonosc import udp_client
        from pythonosc.dispatcher import Dispatcher
        from pythonosc import osc_server

        # Check if OSC setup file exists
        path = os.path.dirname(self.path)
        path = os.path.join(path, 'osc.json')
        oscsetup = load_json(path)
        if oscsetup:
            print('Reading json OSC setup')
            if 'client address' in oscsetup:
                self.client_address = oscsetup['client address']
                print('Setting client address to ' + self.client_address)
            if 'client port' in oscsetup:
                self.client_port = oscsetup['client port']
                print('Setting client port to ' + str(self.client_port))
            if 'server port' in oscsetup:
                self.server_port = oscsetup['server port']
                print('Setting server port to ' + str(self.server_port))

        if self.client_address == 'localhost':
            self.client_address = '127.0.0.1'

        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self._handle_osc)

        print("Starting OSC Server")
        self.oscserver = osc_server.ThreadingOSCUDPServer((self.server_address, self.server_port), self.dispatcher)
        self.server_thread = threading.Thread(target=self.oscserver.serve_forever)
        self.server_thread.start()

        print("Initializing OSC client")
        self.oscclient = udp_client.SimpleUDPClient(self.client_address, self.client_port)

    def send_osc(self, addr, val):
        ''' Send an OSC message'''
        self.oscclient.send_message(addr, val)

    def _handle_osc(self, addr, args):
        print('received: ' + addr)
        print(args)
        if 'received_osc' in self.var_context:
            print('Forwarding')
            self.var_context['received_osc'](addr, args)

    def cleanup(self):
        if self.server_thread is not None:
            print("Stopping server")
            self.oscserver.shutdown()
            self.server_thread.join()
            print("Stopped")
        if imgui is not None:
            self.impl.shutdown()

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

    #@sketch.window.event
    def on_key_press(symbol, modifier):
        # print('Key pressed')
        if 'key_pressed' in sketch.var_context:
            sketch.var_context['key_pressed'](symbol, modifier)

    #@sketch.window.event
    def on_mouse_motion(x, y, dx, dy):
        sketch._mouse_pos = np.array([x, sketch.window_height-y])
        #print((x, y, dx, dy))
        if 'mouse_moved' in sketch.var_context:
            sketch.var_context['mouse_moved']()

    #@sketch.window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        sketch._mouse_pos = np.array([x, sketch.window_height-y])
        sketch.mouse_pressed = True
        if 'mouse_dragged' in sketch.var_context:
            sketch.var_context['mouse_dragged']()

    #@sketch.window.event
    def on_mouse_press(x, y, button, modifiers):
        print("press")
        sketch.mouse_pressed = True
        sketch.mouse_button = button
        sketch._mouse_pos = np.array([x, sketch.window_height-y])

    #@sketch.window.event
    def on_mouse_release(x, y, button, modifiers):
        print("release")
        sketch.mouse_pressed = False
        sketch._mouse_pos = np.array([x, sketch.window_height-y])

    sketch.window.push_handlers(on_key_press,
                                on_mouse_motion,
                                on_mouse_drag,
                                on_mouse_press,
                                on_mouse_release)
    sketch.reload(locals())

    print("Starting loop")
    pyglet.app.run()
    print("Exit")
    sketch.cleanup()

if __name__ == '__main__':
    main()
