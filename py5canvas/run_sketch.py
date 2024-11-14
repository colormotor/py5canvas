#!/usr/bin/env python3
"""
```
             eeeee
eeeee e    e 8     eeee eeeee eeeee ee   e eeeee eeeee
8   8 8    8 8eeee 8  8 8   8 8   8 88   8 8   8 8   "
8eee8 8eeee8     8 8e   8eee8 8e  8 88  e8 8eee8 8eeee
88      88       8 88   88  8 88  8  8  8  88  8    88
88      88   eeee8 88e8 88  8 88  8  8ee8  88  8 8ee88

```
A simple p5-inspired interface to the Canvas object
© Daniel Berio (@colormotor) 2023 - ...

NOTE: this is highly unoptimized, since it uses pycairo for rendering and copies all the screen at each frame
It will probably be significantly slow when using a large canvas size
"""

# importing pyglet module
#import pyglet
#pyglet.options['osx_alt_loop'] = True

# from pyglet.window import key
import numpy as np
import os, sys, time
from py5canvas import canvas, sketch_params
from py5canvas import globals as glob
import traceback
import importlib, inspect
import importlib.util
import threading
import cairo
from inspect import signature

import glfw
import moderngl as mgl
import pdb


# Try getting colored traceback
IPython_loader = importlib.util.find_spec('IPython')
if IPython_loader is not None:
    from IPython.core.ultratb import ColorTB

#master = tkinter.Tk()
#from tkinter import filedialog

# Optionally import imgui
imgui_loader = importlib.util.find_spec('imgui')
if imgui_loader is not None:
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    #from imgui.integrations.glfw import create_renderer
else:
    imgui = None
# Optionally import easydict
edict_loader = importlib.util.find_spec('easydict')
if edict_loader is not None:
    from easydict import EasyDict as edict
else:
    print("Easydict is not installed. It is recommended for parameter handling.")
    print("Install with `pip install easydict`")
    edict = None

app_path = os.path.dirname(os.path.realpath(__file__))

def print_traceback():
    if IPython_loader is not None:
        # https://stackoverflow.com/questions/14775916/coloring-exceptions-from-python-on-a-terminal
        print(''.join(ColorTB().structured_traceback(*sys.exc_info())))
    else:
        traceback.print_exc()

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
        self._cached_stamp = None
        self.filename = path

    def modified(self):
        try:
            stamp = os.stat(self.filename).st_mtime
            if self._cached_stamp is None:
                self._cached_stamp = stamp
            if stamp != self._cached_stamp:
                self._cached_stamp = stamp
                return True
            return False
        except FileNotFoundError as e:
            pass # Issue happens once, need to slow down polling

class Key:
    def __init__(self, name, chars):
        self.chars = chars
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if other in self.chars:
            return True
        return False

# Code injection
def wrap_method(obj, func):
    # print('wrapping ' + func)
    def wrapper(*args, **kwargs):
        # print('calling wrapped ', func, args)
        return getattr(obj, func)(*args, **kwargs)
    return wrapper

def wrap_canvas_method(sketch, func):
    # print('wrapping ' + func)
    def wrapper(*args, **kwargs):
        # print('calling wrapped ', func, args)
        return getattr(sketch.canvas, func)(*args, **kwargs)
    return wrapper


class Sketch:
    """In Py5Canvas a sketch is a Python script with a custom defined ~setup~ and ~draw~ functions,
    that allow to create interactive apps in a way similar to P5js or Processing. For the system to work
    you must defiine a sketch similar to what follows:

    #+begin_src python
    from py5canvas import *

    def setup():
        create_canvas(400, 400)

    def draw():
        background(0)

    run()
    #+end_src

    Canvas drawing code can go in either ~draw~ or ~setup~. To run a sketch, simply run the script from
    a terminal or from your editor of choice. For the system to work, you must import Py5Canvas at the beginning
    and call ~run~ at the end.
    """
    def __init__(self, path,
                       width,
                       height,
                       title="Sketch",
                       inject=False,
                       show_toolbar=False):
        # config = pyglet.gl.Config(major_version=2, minor_version=1,
        #                           sample_buffers=1,
        #                           samples=4,
        #                           depth_size=16,
        #                           double_buffer=True, )
        # display = pyglet.canvas.get_display()
        # screens = display.get_screens()

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.RESIZABLE, False)

        self.window = glfw.create_window(width, height, title, None, None)
        glfw.make_context_current(self.window)

        # OpenGL context, shader and vao for rendering canvas
        self.glctx = mgl.create_context()
        prog = self.glctx.program(vertex_shader=quad_vertex_shader, fragment_shader=quad_fragment_shader)
        vertices = np.array([
            # x, y, u, v
            -1.0, -1.0, 0.0, 1.0,
            1.0, -1.0, 1.0, 1.0,
            1.0,  1.0, 1.0, 0.0,

            -1.0, -1.0, 0.0, 1.0,
            1.0,  1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 0.0,
        ], dtype='f4')
        vbo = self.glctx.buffer(vertices.tobytes())
        self.quad_vao = self.glctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_text')

        #self.window.set_vsync(False)
        self.inject = inject
        self.show_toolbar = show_toolbar
        self.width, self.height = width, height
        self.canvas_tex = None
        self.var_context = {}
        self.params = None
        self.gui = None
        self.gui_callback = None
        self.gui_focus = False
        if not show_toolbar:
            self.toolbar_height = 0
        else:
            self.toolbar_height = 30
        self._gui_visible = True
        self.keep_aspect_ratio = True

        # For IMGUI use, initialized on first frame
        self.impl = None
        # Saving window position for fullscreen toggle
        self.last_window_pos = None

        self.create_canvas(self.width, self.height)
        # self.frame_rate(60)
        self.startup_error = False
        self.runtime_error = False
        self.fps = 60
        self.first_load = True
        self._no_loop = False

        # Frame grabbing utils (OpenCV dependent)
        self.grabbing = ''
        self.num_grab_frames = 0
        self.cur_grab_frame = 0
        self.video_writer = None
        self.video_fps = 30

        # SVG/PDF saving
        self.saving_to_file = ''
        self.recording_context = None
        self.recording_surface = None
        self.done_saving = False

        # self.error_label = pyglet.text.Label('Error',
        #                    font_name='Arial',
        #                    font_size=12,
        #                    x=10, y=50,
        #                    anchor_x='left',
        #                    color=(255,0,0,255))

        # Live reloading
        self.watcher = None
        self.path = path
        self.must_reload = False

        # Local info
        self._frame_count = 0
        self._delta_time = 0.0

        self._mouse_pos = None #np.zeros(2)
        self.mouse_pos = np.zeros(2)
        self.prev_mouse = None
        self.mouse_delta = np.zeros(2)
        self.mouse_button = 0
        self._dragging = False
        self.mouse_moving = False
        self.modifiers = 0
        self.prog_uses_imgui = False

        self.blit_scale_factor = (1.0, 1.0)

        # Check if OSC is available
        osc_loader = importlib.util.find_spec('pythonosc')
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

    @property
    def mouse_x(self):
        ''' The horizontal coordinate of the mouse position'''
        return self.mouse_pos[0]

    @property
    def mouse_y(self):
        ''' The vertical coordinate of the mouse position'''
        return self.mouse_pos[1]

    @property
    def frame_count(self):
        ''' The number of frames since the script has loaded'''
        return self._frame_count

    @property
    def dragging(self):
        ''' Returns ~True~ if mouse is pressed'''
        return self._dragging

    @property
    def mouse_is_pressed(self):
        ''' Returns ~True~ if mouse is pressed'''
        return self._dragging

    @property
    def delta_time(self):
        return self._delta_time

    def _prepare_parameters(self, params):
        self.params = sketch_params.SketchParams(params, self.path)
        print('Setting params', self.params)
        self.params.load()
        return self.params.params

    def has_error(self):
        return self.startup_error or self.runtime_error

    def open_file_dialog(self, exts, title='Open file...'):
        ''' Opens a dialog to select a file to be opened,
        the first argument is the extension or the file to be opened,
        e.g. ~'png'~ or a list of extensions, e.g. ~['png', 'jpg']

        The function returns the path of the file if it is selected or an empty string othewise.
        '''
        # See https://github.com/xMGZx/xdialog
        import xdialog
        if np.isscalar(exts):
            exts = [exts]
        filetypes = [(ext + ' files', "*." + ext) for ext in exts]
        return xdialog.open_file(title, filetypes=filetypes, multiple=False)

    def save_file_dialog(self, exts, title='Open file...', filename='untitled'):
        ''' Opens a dialog to select a file to be saved,
        the first argument is the extension or the file to be saved,
        e.g. ~'png'~ or a list of extensions, e.g. ~['png', 'jpg']

        The function returns the path of the file if it is selected or an empty string othewise.
        '''
        import xdialog
        if np.isscalar(exts):
            exts = [exts]
        filetypes = [(filename, "*." + ext) for ext in exts]
        file_path = xdialog.save_file(title, filetypes=filetypes)
        root, ext = os.path.splitext(file_path)
        # Check if the current extension is in the list of allowed extensions
        if ext.lower() not in [f".{e.lower()}" for e in exts]:
            # If not, append the first extension from the list
            file_path = f"{file_path}.{exts[0].lstrip('.')}"
        return file_path

    def open_folder_dialog(self, title='Open folder...'):
        ''' Opens a dialog to select a folder/directory to be opened,

        The function returns the path of the directory if it is selected or an empty string othewise.
        '''
        import xdialog
        return xdialog.directory(title)

    def _create_canvas(self, w, h, canvas_size=None, fullscreen=False, screen=None, save_background=False):
        self.is_fullscreen = fullscreen
        glfw.swap_interval(0)
        #if screen is not None:
        #    self.window = pyglet.window.Window(w, h, self.title, screen=screen)
        #self.window.set_vsync(False)
        x, y = glfw.get_window_pos(self.window)
        if fullscreen:
            monitors = glfw.get_monitors()

            for monitor in monitors:
                mode = glfw.get_video_mode(monitor)
                px, py = glfw.get_monitor_pos(monitor)
                pw, ph = mode.size
                # This crashes on mac
                # px, py, pw, ph = glfw.get_monitor_workarea(monitor)
                if x >= px and y >= py and x <= px+pw and y < py+ph:
                    break
            w, h = mode.size
            self.last_window_pos = [x, y]
            glfw.set_window_monitor(self.window, monitor, 0, 0, w, h, glfw.DONT_CARE)

        else:
            if self.last_window_pos is not None:
                x, y = self.last_window_pos
            glfw.set_window_monitor(self.window, None, x, y, w, h, glfw.DONT_CARE)

        # Note, the canvas size may be different from the sketch size
        # for example when automatically creating a UI...
        if canvas_size is None:
            canvas_size = (w, h)
        self.width, self.height = canvas_size # TODO fixme
        self.canvas = canvas.Canvas(*canvas_size, recording=False, save_background=save_background) #, clear_callback=self.clear_callback)
        # When createing a canvas we create a recording surface
        # This will enable recording of drawing commands that are called in setup, if any,
        # and then we can pass these into a svg if we want to save one
        print('Setting up recording surface')
        self.recording_surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
        self.recording_context = cairo.Context(self.recording_surface)
        self.canvas.ctx.push_context(self.recording_context)
        # self.setup_surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
        # self.setup_ctx = cairo.Context(self.setup_surface)
        #self.canvas.ctx.push_context(self.setup_ctx)

        self.window_width, self.window_height = w, h

        # Expose canvas globally
        if self.var_context:
            self.update_globals()

        if self.canvas_tex is not None:
            self.canvas_tex.release()
        self.canvas_tex = self.glctx.texture(canvas_size, 4, self.canvas.get_buffer())
        self.canvas_tex.swizzle = 'BGRA' # Internal Cairo format

        # # Create image and copy initial canvas buffer to it
        # buf = self.canvas.get_buffer()
        # buf = (pyglet.gl.GLubyte * len(buf))(*buf)
        # self.image = pyglet.image.ImageData(*canvas_size, "BGRA", buf)

    def create_canvas(self, w, h, gui_width=300, fullscreen=False, with_gui=True, screen=None, save_background=False):
        if imgui is None or not with_gui:
            print("Creating canvas no gui")
            self._create_canvas(w, h, fullscreen=fullscreen, screen=screen, save_background=save_background)
            return
        has_gui = 'gui' in self.var_context and callable(self.var_context['gui'])
        if self.params or self.gui_callback is not None or has_gui:
            print("Creating GUI window/canvas")
            self.create_canvas_gui(w, h, gui_width, fullscreen, screen=screen, save_background=save_background)
        else:
            self.gui = sketch_params.SketchGui(gui_width)
            self._create_canvas(w, h + self.toolbar_height, (w, h), fullscreen, screen=screen, save_background=save_background)


    @property
    def current_canvas(self):
        return self.canvas

    @property
    def canvas_display_width(self):
        if self._gui_visible:
            return self.window_width - self.gui.width
        return self.window_width

    @property
    def canvas_display_height(self):
        if self._gui_visible:
            return self.window_height - self.toolbar_height
        return self.window_height

    def create_canvas_gui(self, w, h, width=300,
                          fullscreen=False,
                          screen=None,
                          save_background=False):
        if imgui is None:
            print('Install ImGui to run UI')
            return self.create_canvas(w, h, fullscreen)
        self.gui = sketch_params.SketchGui(width)
        self._create_canvas(w + self.gui.width, h + self.toolbar_height, (w, h), fullscreen,
                            screen=screen,
                            save_background=save_background)

    def get_pixel_ratio(self):
        return 1

    def save_canvas(self, path):
        ''' Tells the sketch to dump the next frame to an SVG file '''
        if '~' in path:
            path = os.path.expanduser(path)
        self.saving_to_file = os.path.abspath(path)
        print('saving file to', self.saving_to_file)
        # Since this can be called in frame, we need to make sure we don't save svg righ after
        self.done_saving = False
        # Add the recording context so we can replay and save later
        self.canvas.ctx.push_context(self.recording_context)

    dump_canvas = save_canvas

    # def get_screen(self):
    #     window_x, window_y = self.window.get_location()
    #     display = pyglet.canvas.get_display()
    #     print(display.get_screens())
    #     for screen in display.get_screens():

    #         screen_x, screen_y = screen.x, screen.y
    #         screen_width, screen_height = screen.width, screen.height

    #         if (screen_x <= window_x < screen_x + screen_width and
    #             screen_y <= window_y < screen_y + screen_height):
    #             print("Found screen")
    #             return screen

    #     return None

    def toggle_gui(self, screen_index=-1):
        ''' Toggle between GUI and non-gui'''
        self.show_gui(not self._gui_visible)

    def show_gui(self, flag, screen_index=-1):
        if self.gui is None:
            return
        self._gui_visible = flag
        #screen = self.window.screen
        #if screen_index > -1:
        #    screen = self.get_screen(screen_index)
        #self.window.set_fullscreen(False)
        self.create_canvas(self.canvas.width,
                           self.canvas.height,
                           self.gui.width,
                           self.is_fullscreen,
                           flag) #screen=screen)

    def toggle_fullscreen(self, toggle_gui=False, screen_index=-1):
        ''' Toggle between fullscreen and windowed mode'''
        self.fullscreen(not self.is_fullscreen,
                        toggle_gui=toggle_gui,
                        screen_index=screen_index)

    # def get_screen(self, index):
    #     # TODO fixme
    #     display = pyglet.canvas.get_display()
    #     screens = display.get_screens()
    #     if index < len(screens) and index >= 0:
    #         return screens[index]
    #     print("Invalid screen index for display")
    #     return None

    def fullscreen(self, flag, toggle_gui=False, screen_index=-1):
        ''' Sets fullscreen or windowed mode depending on the first argument (~True~ or ~False~)
        '''
        # old_window_width = self.canvas_display_width
        # old_window_height = self.canvas_display_height
        if toggle_gui:
            self.is_fullscreen = flag
            self.show_gui(not flag) #, screen_index)
            return

        #self.window.set_fullscreen(False)
        self.create_canvas(self.canvas.width,
                           self.canvas.height,
                           self.gui.width,
                           flag,
                           flag)
                           #screen=self.get_screen(screen_index))


        # self.window.set_fullscreen(flag)
        # self.window_width, self.window_height = self.window.get_size()
        # print('Window size:', self.window_width, self.window_height)

        # self.is_fullscreen = flag

    def no_loop(self):
        ''' Stops the drawing loop keeping the last frame fixed on the canvas'''
        self._no_loop = True

    def set_gui_theme(self, hue):
        if self.gui is not None:
            sketch_params.set_theme(hue)

    def set_gui_callback(self, func):
        print("set_gui_callback is deprectated. Use the `gui` function in your sketch instead")
        self.gui_callback = func

    def load(self, path):
        self.watcher = None
        self.gui = None
        self.path = path
        self.must_reload = True

    def grab_image_sequence(self, path, num_frames, reload=True):
        ''' Saves a sequence of image files to a directory, one for each frame.
        By default this will reload the current script.

        Arguments:
        - ~path~ (string), the directory where to save the images
        - ~num_frames~ (int), the number of frames to save
        '''
        if '~' in path:
            path = os.path.expanduser(path)
        path = os.path.abspath(path)
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise OSError
        self.grabbing = path
        self.must_reload=reload
        self.num_grab_frames = num_frames

    def grab_movie(self, path, num_frames, framerate=30, reload=True):
        ''' Saves a mp4 movie from a number of frames to a specified path.
        By default this will reload the current script.

        Arguments:
        - ~path~ (string), the directory where to save the video
        - ~num_frames~ (int), the number of frames to save
        '''
        path = os.path.abspath(path)
        self.grabbing = path
        self.must_reload = reload
        self.num_grab_frames = num_frames
        self.video_fps = framerate
        print('Saving video to ' + path)

    def stop_grabbing(self):
        self.num_grab_frames = self.current_grab_frame

    def finalize_grab(self):
        if not self.grabbing:
            return
        self.cur_grab_frame = 0
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None


    def grab(self):
        if not self.grabbing:
            return
        if 'mp4' in self.grabbing:
            # Grap mp4 frame
            if self.video_writer is None:
                print('Creating video writer')
                import cv2
                fmt = cv2.VideoWriter_fourcc(*'mp4v') #cv2.cv.CV_FOURCC(*'mp4v')
                self.video_writer = cv2.VideoWriter(self.grabbing, fmt, self.video_fps, (self.canvas.width,
                                                                                         self.canvas.height))
            img = self.canvas.get_image()
            img = img[:,:,::-1]
            self.video_writer.write(img)
        else:
            # Grab png frame
            path = self.grabbing
            self.canvas.save_image(os.path.join(path, '%d.png'%(self.cur_grab_frame+1)))
        print('Saving frame %d of %d' % (self.cur_grab_frame+1, self.num_grab_frames))
        self.cur_grab_frame += 1
        if self.cur_grab_frame >= self.num_grab_frames:
            self.finalize_grab()
            print("Stopping grab")
            self.grabbing = ''
            # self.cur_grab_frame = 0
            # if self.video_writer is not None:
            #     self.video_writer.release()
            #     self.video_writer = None


    def reload(self, var_context):
        print("Reloading sketch code")
        self.finalize_grab()

        #var_context = {}
        self.var_context = var_context

        self._frame_count = 0
        self._delta_time = 0.0

        # Save params if they exist
        if self.params is not None and not self.has_error():
            self.params.save()

        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        # Call exit callback if any
        if 'exit' in var_context:
            try:
                var_context['exit']()
                var_context.pop('exit')
            except Exception as e:
                print('Error in exit')
                print(e)
                print_traceback()

        # And reset
        self.params = None
        self.gui_callback = None
        self._no_loop = False

        # Set current directory to script dir
        if self.path:
            path = os.path.abspath(self.path)
            os.chdir(os.path.dirname(path))
            sys.path.append(os.path.dirname(path))

        # Create filewatcher on first load
        if self.watcher is None:
            print("Creating file watcher for " + self.path)
            self.watcher = FileWatcher(self.path)
        # Attempt to compile script
        try:
            print("Compiling script", self.path)
            prog_text = open(self.path).read()
            if 'imgui.' in prog_text:
                self.prog_uses_imgui = True
            else:
                self.prog_uses_imgui = False
                
            prog = compile(prog_text, self.path, 'exec')
            print(type(prog))

            # Exposes classes before load because these might be used outside of functions
            var_context['VideoInput'] = canvas.VideoInput
            var_context['__loaded_py5sketch__'] = True

            # And also expose canvas as 'c' since the functions in the canvas are quite common names and
            # might be easily overwritten
            self.update_globals()

            # Default setup, so user is not obliged to define it
            var_context['setup'] = lambda: self.create_canvas(512, 512)
            var_context['sketch'] = self

            exec(prog, var_context)

            # *ISSUE* here. This injects all the canvas functionalities as globals
            # in the script. However, this means that any conflicting global in the
            # script will be overridden. As an example, if the script defines ~scale~ as a number
            # then this will be overridden by the ~Canvas.scale~ function.
            # The opposite behavior would be possible, but that would not allow to include
            # the "dummy_globals.py" file that tricks linters into knowing the funtions.
            # One reasonable solution would be to add a flag to the "run" function,
            # so that it can stop the injection from happening. Then these parameters
            # would be accesible through the ~sketch~ variable.
            def can_inject(func):
                if func not in var_context:
                    return True
                try:
                    return (func not in var_context or
                            'dummy_globals' in inspect.getmodule(var_context[func]).__name__ or
                            'py5canvas' in inspect.getmodule(var_context[func]).__name__)
                except AttributeError as e:
                    print("'%s' seems to be defined in script and conflicting with Py5canvas built in function"%func)
                return False

            if self.inject:
                for func in dir(self.canvas):
                    if '__' not in func and callable(getattr(self.canvas, func)):
                        if can_inject(func):
                            var_context[func] = wrap_canvas_method(self, func)
                        # else:
                        #     import inspect
                        #     pdb.set_trace()

            for g in dir(glob):
                if '__' not in g:
                    var_context[g] = getattr(glob, g)

            # And basic functions from sketch
            if self.inject:
                export_methods = ['title',
                                'frame_rate',
                                'create_canvas',
                                'create_canvas_gui',
                                'dump_canvas',
                                'no_loop',
                                'grab_movie',
                                'grab_image_sequence',
                                'fullscreen',
                                'show_gui',
                                'toggle_gui',
                                'toggle_fullscreen',
                                'open_file_dialog',
                                'save_file_dialog',
                                'open_folder_dialog']
                for method in export_methods:
                    #if method not in var_context:
                    var_context[method] = wrap_method(self, method)
                # For compatibility expose "size"
                if can_inject('size'):
                    var_context['size'] = wrap_method(self, 'create_canvas')
                # else:
                #     pdb.set_trace()

            var_context['save'] = wrap_method(self, 'dump_canvas')

            # var_context['title'] = wrap_method(self, 'title')
            # var_context['frame_rate'] = wrap_method(self, 'frame_rate')
            # var_context['create_canvas'] = wrap_method(self, 'create_canvas')
            # var_context['size'] = var_context['create_canvas'] # For compatibility
            # var_context['create_canvas_gui'] = wrap_method(self, 'create_canvas_gui')
            # var_context['save_svg'] = wrap_method(self, 'dump_canvas')
            # var_context['save_canvas'] = wrap_method(self, 'dump_canvas')
            # var_context['no_loop'] = wrap_method(self, 'no_loop')
            # var_context['grab_movie'] = wrap_method(self, 'grab_movie')
            # var_context['grab_image_sequence'] = wrap_method(self, 'grab_movie')

            # Check if user defined a parameters callback
            if 'parameters' in var_context and callable(var_context['parameters']):
                self.params = sketch_params.SketchParams(var_context['parameters'](), self.path)
                var_context['params'] = self.params.params # Expose to script

            if self.params is not None:
                print('Preloading params')
                self.params.load()

            # call setup
            var_context['setup']()
            # User might create parameters in setup
            if self.params is not None:
                # print('Load params after setup')
                self.params.load()
            self.startup_error = False

        except Exception as e:
            print('Error in sketch setup')
            print(e)
            self.startup_error = True
            #self.error_label.text = str(e)
            print_traceback()
        # create_canvas created and added a recording context so pop it in case (if no error)
        if len(self.canvas.ctx.ctxs) > 1:
            print('Removing setup recording context')
            self.canvas.ctx.pop_context()

    def _update_mouse(self):
        # workaround for backwards compatibility (deprecating 'mouse_pressed')
        self.mouse_pressed = self.dragging

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


    def update_globals(self):
        self.var_context['delta_time'] = self._delta_time
        self.var_context['frame_count'] = self._frame_count
        self.var_context['width'] = self.width
        self.var_context['height'] = self.height
        self.var_context['center'] = self.canvas.center

        # HACK keep mouse_pressed as a flag for backwards compatibility, but must be deprecated

        if 'mouse_pressed' not in self.var_context or not callable(self.var_context['mouse_pressed']):
            self.var_context['mouse_pressed'] = self.dragging
        self.var_context['dragging'] = self.dragging
        self.var_context['mouse_is_pressed'] = self.dragging # For compatibility with p5py
        self.var_context['mouse_delta'] = self.mouse_delta
        self.var_context['mouse_pos'] = self.mouse_pos
        self.var_context['mouse_x'] = self.mouse_x
        self.var_context['mouse_y'] = self.mouse_y


    def _update(self, dt):
        # Almost a dummy function.
        # Scheduling this should force window redraw every frame
        # So we can sync update and drawing by calling frame() in the @draw callback
        # see https://stackoverflow.com/questions/39089578/pyglet-synchronise-event-with-frame-drawing
        self._delta_time = dt

        print('update')

    def check_reload(self):
        if self.path:
            if self.must_reload or self.watcher.modified(): # Every frame check for file modification
                print("reloading")
                # Reload in global namespace
                self.reload(self.var_context)
                self.must_reload = False
                self.first_load = True

    # internal update
    def frame(self, draw_frame):
        if self.first_load:
            # Do stuff on first load
            self.first_load = False
            draw_frame = True

        self._update_mouse()
        self.update_globals()

        if imgui is not None:
            # For some reason this only works here and not in the constructor.
            if self.impl is None:
                imgui.create_context()
                # Forwarding callbacks manually since Imgui eats these otherwise
                self.impl = GlfwRenderer(self.window, attach_callbacks=False)
                sketch_params.set_theme()
            try:
                imgui.new_frame()
            except imgui.core.ImGuiError as e:
                print('Error in imgui new_frame')
                print(e)
                #self.error_label.text = str(e)
                self.runtime_error = True
                traceback.print_exc()
            # print('New frame')
            # # For some reason this only works here and not in the constructor.
            # if self.impl is None:
            #     imgui.create_context()
            #     self.impl = create_renderer(self.window)

            # imgui.new_frame()
        #print('Display scale', self.impl.io.display_fb_scale)

        if self.saving_to_file:
            self.done_saving = True
            draw_frame = True
            if self.no_loop:
                self.canvas.background(self.canvas.last_background)

        # Optional imGUI init and visualization
        if imgui is not None and self._gui_visible:
            if self.gui is not None:
                if (self.params or
                    self.gui_callback is not None or
                    self.prog_uses_imgui):
                    self.gui.begin_gui(self)

                # User can add a 'gui()' function that will be automatically called
                # But also imgui calls in draw will be valid
                if 'gui' in self.var_context and callable(self.var_context['gui']):
                    try:
                        if (self.gui.show_sketch_controls() and
                            not self.runtime_error):
                            self.var_context['gui']()
                    except Exception as e:
                        print('Error in sketch gui()')
                        print(e)
                        #self.error_label.text = str(e)
                        self.runtime_error = True
                        print_traceback()
                # Check focus
                #self.gui_focus = imgui.core.is_window_hovered()
                #print('gui focus', self.gui_focus)
        with perf_timer('update'):
            if not self.runtime_error or self._frame_count==0:
                try:
                    if 'draw' in self.var_context and draw_frame:
                        self.canvas.identity()
                        self.var_context['draw']()
                    else:
                        pass
                        #print('no draw in var context')
                    self.runtime_error = False
                except Exception as e:
                    print('Error in sketch draw')
                    print(e)
                    #self.error_label.text = str(e)
                    self.runtime_error = True
                    print_traceback()

        # Copy canvas image and visualize
        pitch = self.width * 4
        with perf_timer('get buffer'):
            buf = self.canvas.get_buffer()

        # with perf_timer('update image'):
        #     # https://stackoverflow.com/questions/9035712/numpy-array-is-shown-incorrect-with-pyglet
        #     buf = (pyglet.gl.GLubyte * len(buf)).from_buffer(buf)
        #     # The following is slow as hell
        #     #buf = (pyglet.gl.GLubyte * len(buf))(*buf)

        # self.image.set_data("BGRA", -pitch, buf) # Looks like negative sign takes care of C-contiguity

        if self.grabbing and not self.must_reload and draw_frame:
            self.grab()

        # Update timers and copy to texture
        if draw_frame:
            self.canvas_tex.write(self.canvas.get_buffer())
            self._frame_count += 1

        # Finalize gui visualization
        if imgui is not None and self._gui_visible:
            if self.gui is not None:
                if (self.params or
                    self.gui_callback is not None or
                    self.prog_uses_imgui):
                    self.gui.from_params(self, self.gui_callback, init=False)
            if ('gui_window' in self.var_context and
                callable(self.var_context['gui_window'])):
                try:
                    self.var_context['gui_window']()
                except Exception as e:
                    print('Error in sketch gui_window()')
                    print(e)
                    # self.error_label.text = str(e)
                    self.runtime_error = True
                    print_traceback()
            if self.show_toolbar:
                self.gui.toolbar(self)
            # Required for render to work in draw callback
            try:
                imgui.end_frame()
            except imgui.core.ImGuiError as e:
                print(e)

        if self.saving_to_file and self.done_saving:
            print('saving to ', self.saving_to_file)
            if ('.png' in self.saving_to_file or '.jpg' in self.saving_to_file):
                self.canvas.save(self.saving_to_file)
            else:
                if '.svg' in self.saving_to_file:
                    surf = cairo.SVGSurface(self.saving_to_file, self.canvas.width, self.canvas.height)
                elif '.pdf' in self.saving_to_file:
                    surf = cairo.PDFSurface(self.saving_to_file, self.canvas.width, self.canvas.height)
                else:
                    surf = self.canvas.surf
                ctx = cairo.Context(surf)
                #ctx.set_source_surface(self.setup_surface)
                #ctx.paint()
                ctx.set_source_surface(self.recording_surface)
                ctx.paint()
                surf.finish()

                # Apply svg fix
                try:
                    if '.svg' in self.saving_to_file:
                        canvas.fix_clip_path(self.saving_to_file, self.saving_to_file)
                except AttributeError as e:
                    print(e)
                    pass

            self.canvas.ctx.pop_context()
            self.saving_to_file = ''
            self.done_saving = False


    def title(self, title):
        ''' Sets the title of the sketch window'''
        glfw.set_window_title(self.window, title)

    def frame_rate(self, fps):
        ''' Set the framerate of the sketch in frames-per-second'''
        self.fps = fps


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

    def _handle_osc(self, addr, *args):
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
            print("Stopping imgui")
            self.impl.shutdown()
        if self.params is not None and not self.has_error():
            print("Saving params")
            self.params.save()
        print("End cleanup")


def main(path='', fps=0, inject=True, show_toolbar=False):
    from importlib import reload
    mouse_moving = False

    ## User callbacks, will get overridden by user sketch
    def setup():
        pass

    def draw():
        pass

    def exit():
        pass

    # def key_pressed(k, modifier):
    #     pass

    # def mouse_moved():
    #     pass

    # def mouse_dragged():
    #     pass

    # def mouse_pressed():
    #     pass

    # def mouse_released():
    #     pass

    # if len(sys.argv) < 2:
    #     print('You need to specify a python sketch file in the arguments')
    #     assert(0)


    if len(sys.argv) > 1:
        path = sys.argv[1]

    # else:
    #     path

    print("Starting up sketch " + path)
    # Create our sketch context and load script
    if not glfw.init():
        print("GLFW init failed")
        return

    sketch = Sketch(path, 512, 512, inject=inject, show_toolbar=show_toolbar)
    sketch.fps = fps

    def canvas_pos(x, y):
        return np.array([x, sketch.window_height-y-sketch.toolbar_height])

    def check_callback(name):
        if not name in sketch.var_context:
            return False
        return callable(sketch.var_context[name])

    def imgui_focus():
        if imgui is None:
            return False
        #return False
        return imgui.core.is_any_item_active()

    def point_in_canvas(p):
        return (p[0] >= 0 and p[0] < sketch.canvas.width and
                p[1] >= 0 and p[1] < sketch.canvas.height)

    # #@sketch.window.event
    # def on_key_press(symbol, modifier):
    #     if imgui_focus():
    #         return
    #     # print('Key pressed')
    #     if check_callback('key_pressed'):
    #         params = [symbol, sketch.modifiers]
    #         sig = signature(sketch.var_context['key_pressed'])
    #         sketch.var_context['key_pressed'](*params[:len(sig.parameters)])

    # #@sketch.window.event
    # def on_mouse_motion(x, y, dx, dy):
    #     sketch._mouse_pos = canvas_pos(x, y) #np.array([x, sketch.window_height-y-sketch.toolbar_height])
    #     #print((x, y, dx, dy))
    #     if check_callback('mouse_moved'):
    #         sketch.var_context['mouse_moved']()

    # #@sketch.window.event
    # def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    #     pos = canvas_pos(x, y)
    #     sketch._mouse_pos = pos #canvas_pos(x, y) #np.array([x, sketch.window_height-y-sketch.toolbar_height])
    #     if imgui_focus():
    #         return
    #     if not point_in_canvas(pos):
    #         return

    #     sketch.dragging = True
    #     if check_callback('mouse_dragged'):
    #         params = [buttons, modifiers]
    #         sig = signature(sketch.var_context['mouse_dragged'])
    #         sketch.var_context['mouse_dragged'](*params[:len(sig.parameters)])

    # #@sketch.window.event
    # def on_mouse_press(x, y, button, modifiers):
    #     pos = canvas_pos(x, y)
    #     if imgui_focus():
    #         return
    #     if not point_in_canvas(pos):
    #         return

    #     sketch.dragging = True
    #     sketch.mouse_button = button
    #     sketch._mouse_pos = pos #np.array([x, sketch.window_height-y-sketch.toolbar_height])
    #     if check_callback('mouse_pressed'):
    #         params = [button, modifiers]
    #         sig = signature(sketch.var_context['mouse_pressed'])
    #         sketch.var_context['mouse_pressed'](*params[:len(sig.parameters)])

    # #@sketch.window.event
    # def on_mouse_release(x, y, button, modifiers):
    #     pos = canvas_pos(x, y)
    #     sketch.dragging = False
    #     sketch._mouse_pos = pos #np.array([x, sketch.window_height-y-sketch.toolbar_height])
    #     if check_callback('mouse_released'):
    #         params = [button, modifiers]
    #         sig = signature(sketch.var_context['mouse_released'])
    #         sketch.var_context['mouse_released'](*params[:len(sig.parameters)])

    # See https://www.glfw.org/docs/latest/input_guide.html
    def key_callback(window, key, scancode, action, mods):
        if sketch.impl is not None:
            sketch.impl.keyboard_callback(window, key, scancode, action, mods)
        sketch.modifiers = mods
        if action == glfw.PRESS:
            if imgui_focus():
                return
            if check_callback('key_pressed'):
                name = glfw.get_key_name(key, scancode)
                if name is None: # If name is not none consider this a char
                    if key in glfw_keymap:
                        params = [glfw_keymap[key], mods]
                        sig = signature(sketch.var_context['key_pressed'])
                        sketch.var_context['key_pressed'](*params[:len(sig.parameters)])


    def char_callback(window, char):
        if sketch.impl is not None:
            sketch.impl.char_callback(window, char)
        if imgui_focus():
            return
        if check_callback('key_pressed'):
            params = [chr(char), None]
            sig = signature(sketch.var_context['key_pressed'])
            sketch.var_context['key_pressed'](*params[:len(sig.parameters)])
        pass

    def scroll_callback(window, x, y):
        if sketch.impl is not None:
            sketch.impl.scroll_callback(window, x, y)
        pass

    def resize_callback(window, width, height):
        if sketch.impl is not None:
            sketch.impl.resize_callback(window, width, height)
        pass

    def cursor_position_callback(window, x, y):
        sketch._mouse_pos = pos = canvas_pos(x, y)
        if sketch._dragging:
            if imgui_focus():
                return
            if not point_in_canvas(pos):
                return
            if check_callback('mouse_dragged'):
                params = [sketch.mouse_button, sketch.modifiers]
                sig = signature(sketch.var_context['mouse_dragged'])
                sketch.var_context['mouse_dragged'](*params[:len(sig.parameters)])

        else:
            if check_callback('mouse_moved'):
                sketch.var_context['mouse_moved']()

    def mouse_button_callback(window, button, action, mods):
        sketch.modifiers = mods
        pos = sketch._mouse_pos
        if action == glfw.PRESS:
            if imgui_focus():
                return
            if not point_in_canvas(pos):
                return
            sketch.mouse_button = button
            sketch._dragging = True
            if check_callback('mouse_pressed'):
                params = [button, mods]
                sig = signature(sketch.var_context['mouse_pressed'])
                sketch.var_context['mouse_pressed'](*params[:len(sig.parameters)])
        elif action == glfw.RELEASE:
            sketch.mouse_button = button
            sketch._dragging = False
            if check_callback('mouse_released'):
                params = [button, mods]
                sig = signature(sketch.var_context['mouse_released'])
                sketch.var_context['mouse_released'](*params[:len(sig.parameters)])

    def window_content_scale_callback(window, xscale, yscale):
        #print("Content scale", xscale, yscale)
        pass
        # if sketch.impl is not None:
        #     sketch.impl.process_inputs() #io.display_size = glfw.get_framebuffer_size(window)
        #print(sketch.impl.io.display_fb_scale, sketch.impl.io.display_size)

    def framebuffer_size_callback(window, w, h):
        pass
        # print("Fb size", w, h)
        # if sketch.impl is not None:
        #     sketch.impl.process_inputs() #
        # #
    def window_pos_callback(window, x, y):
        pass #print("Window pos", x, y)

    # pdb.set_trace()
    glfw.set_window_content_scale_callback(sketch.window, window_content_scale_callback)
    glfw.set_key_callback(sketch.window, key_callback)
    glfw.set_char_callback(sketch.window, char_callback)
    glfw.set_cursor_pos_callback(sketch.window, cursor_position_callback)
    glfw.set_mouse_button_callback(sketch.window, mouse_button_callback)
    glfw.set_framebuffer_size_callback(sketch.window, framebuffer_size_callback)
    glfw.set_window_pos_callback(sketch.window, window_pos_callback)
    # sketch.window.push_handlers(on_key_press,
    #                             on_mouse_motion,
    #                             on_mouse_drag,
    #                             on_mouse_press,
    #                             on_mouse_release)

    # Load settings if they exist
    # settings = sketch_params.load_json(os.path.join(app_path, 'settings.json'))
    # if settings:
    #     app_settings.update(settings)

    # if not sketch.path:
    #     sketch.path = app_settings['script']

    if sketch.path:
        if 'exit' in sketch.var_context:
            sketch.var_context['exit']()
        sketch.reload({}) #globals()) #{}) #locals())
    else:
        sketch.var_context = {} #globals() #{} #locals()

    def close():
        # Stop grabbing and finalize
        sketch.finalize_grab()

        # Save params if they exist
        if sketch.params is not None and not sketch.has_error():
            print('Saving params')
            sketch.params.save()

        if 'exit' in sketch.var_context:
            sketch.var_context['exit']()

        #print("Saving settings")
        #sketch_params.save_json(app_settings, os.path.join(app_path, 'settings.json'))
        sketch.cleanup()
        print("End close")

    prev_t = 0 #100000 #time.perf_counter()

    while not glfw.window_should_close(sketch.window):
        # Updates input and calls draw in the sketch
        # Poll for and process events
        glfw.poll_events()
        sketch._mouse_pos = np.array(glfw.get_cursor_pos(sketch.window))

        do_frame = False
        if sketch.fps <= 0:
            do_frame = True
        else:
            if time.perf_counter() - prev_t >= 1.0 / sketch.fps:
                do_frame = True
                prev_t = time.perf_counter()

        if sketch._no_loop:
            do_frame = False

        if sketch.first_load:
            do_frame = True

        # Check if we need to reload
        sketch.check_reload()

        sketch.frame(do_frame)


        if sketch.impl is not None:
            sketch.impl.process_inputs()

        sketch.canvas_tex.use(0)
        content_scale = glfw.get_window_content_scale(sketch.window)
        content_scale = [int(s) for s in content_scale] # Hack for floating point scale?
        sketch.glctx.clear(1.0, 1.0, 1.0)  # Clear the screen to white
        #prev_viewport = sketch.glctx.viewport
        sketch.glctx.viewport = (0, 0, sketch.canvas.width*content_scale[0], sketch.canvas.height*content_scale[1])
        sketch.quad_vao.render(mgl.TRIANGLES)  # Render the VAO
        sketch.glctx.viewport = (0, 0, sketch.window_width*content_scale[0], sketch.window_height*content_scale[1])
        #sketch.glctx.viewport = prev_viewport

        # if sketch.keep_aspect_ratio:
        #     sketch.blit_scale_factor = (sketch.canvas_display_height / sketch.canvas.height,
        #                                 sketch.canvas_display_height / sketch.canvas.height)
        # else:
        #     sketch.blit_scale_factor = (sketch.canvas_display_width / sketch.canvas.width,
        #                               sketch.canvas_display_height / sketch.canvas.height)



        # sketch.image.blit(0, 0,
        #                   width=sketch.canvas.width*sketch.blit_scale_factor[0],
        #                   height=sketch.canvas.height*sketch.blit_scale_factor[1])

        # if sketch.has_error():
        #     sketch.error_label.draw()

        if not sketch.runtime_error and 'draw_gl' in sketch.var_context:
            try:
                sketch.var_context['draw_gl']()
            except Exception as e:
                print('Error in draw_gl')
                print(e)
                # sketch.error_label.text = str(e)
                sketch.runtime_error = True
                print_traceback()

                if sketch.impl is not None:
                    sketch.impl.process_inputs()


        if imgui is not None:
            try:
                imgui.render()
                # pdb.set_trace()
                sketch.impl.render(imgui.get_draw_data())

            except imgui.core.ImGuiError as e:
                print('Error in imgui render')
                print(e)



        # Swap front and back buffers
        glfw.swap_buffers(sketch.window)

    close()
    glfw.terminate()

quad_vertex_shader = """
#version 330
in vec2 in_vert;
in vec2 in_text;
out vec2 v_text;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_text = in_text;
}
"""

quad_fragment_shader = """
#version 330
uniform sampler2D Texture;
in vec2 v_text;
out vec4 f_color;
void main() {
    f_color = texture(Texture, v_text);
}
"""

# Key to string map, glfw
glfw_keymap = {
    glfw.KEY_ESCAPE: "ESCAPE",
    glfw.KEY_ENTER: "ENTER",
    glfw.KEY_TAB: "TAB",
    glfw.KEY_BACKSPACE: "BACKSPACE",
    glfw.KEY_INSERT: "INSERT",
    glfw.KEY_DELETE: "DELETE",
    glfw.KEY_RIGHT: "RIGHT",
    glfw.KEY_LEFT: "LEFT",
    glfw.KEY_DOWN: "DOWN",
    glfw.KEY_UP: "UP",
    glfw.KEY_PAGE_UP: "PAGE_UP",
    glfw.KEY_PAGE_DOWN: "PAGE_DOWN",
    glfw.KEY_HOME: "HOME",
    glfw.KEY_END: "END",
    glfw.KEY_CAPS_LOCK: "CAPS_LOCK",
    glfw.KEY_SCROLL_LOCK: "SCROLL_LOCK",
    glfw.KEY_NUM_LOCK: "NUM_LOCK",
    glfw.KEY_PRINT_SCREEN: "PRINT_SCREEN",
    glfw.KEY_PAUSE: "PAUSE",
    glfw.KEY_F1: "F1",
    glfw.KEY_F2: "F2",
    glfw.KEY_F3: "F3",
    glfw.KEY_F4: "F4",
    glfw.KEY_F5: "F5",
    glfw.KEY_F6: "F6",
    glfw.KEY_F7: "F7",
    glfw.KEY_F8: "F8",
    glfw.KEY_F9: "F9",
    glfw.KEY_F10: "F10",
    glfw.KEY_F11: "F11",
    glfw.KEY_F12: "F12",
    glfw.KEY_F13: "F13",
    glfw.KEY_F14: "F14",
    glfw.KEY_F15: "F15",
    glfw.KEY_F16: "F16",
    glfw.KEY_F17: "F17",
    glfw.KEY_F18: "F18",
    glfw.KEY_F19: "F19",
    glfw.KEY_F20: "F20",
    glfw.KEY_F21: "F21",
    glfw.KEY_F22: "F22",
    glfw.KEY_F23: "F23",
    glfw.KEY_F24: "F24",
    glfw.KEY_F25: "F25",
    glfw.KEY_KP_0: "KP_0",
    glfw.KEY_KP_1: "KP_1",
    glfw.KEY_KP_2: "KP_2",
    glfw.KEY_KP_3: "KP_3",
    glfw.KEY_KP_4: "KP_4",
    glfw.KEY_KP_5: "KP_5",
    glfw.KEY_KP_6: "KP_6",
    glfw.KEY_KP_7: "KP_7",
    glfw.KEY_KP_8: "KP_8",
    glfw.KEY_KP_9: "KP_9",
    glfw.KEY_KP_DECIMAL: "KP_DECIMAL",
    glfw.KEY_KP_DIVIDE: "KP_DIVIDE",
    glfw.KEY_KP_MULTIPLY: "KP_MULTIPLY",
    glfw.KEY_KP_SUBTRACT: "KP_SUBTRACT",
    glfw.KEY_KP_ADD: "KP_ADD",
    glfw.KEY_KP_ENTER: "KP_ENTER",
    glfw.KEY_KP_EQUAL: "KP_EQUAL",
    glfw.KEY_LEFT_SHIFT: "LEFT_SHIFT",
    glfw.KEY_LEFT_CONTROL: "LEFT_CONTROL",
    glfw.KEY_LEFT_ALT: "LEFT_ALT",
    glfw.KEY_LEFT_SUPER: "LEFT_SUPER",
    glfw.KEY_RIGHT_SHIFT: "RIGHT_SHIFT",
    glfw.KEY_RIGHT_CONTROL: "RIGHT_CONTROL",
    glfw.KEY_RIGHT_ALT: "RIGHT_ALT",
    glfw.KEY_RIGHT_SUPER: "RIGHT_SUPER",
}

if __name__ == '__main__':
    main()

