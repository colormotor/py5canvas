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
import pyglet
pyglet.options['osx_alt_loop'] = True

# from pyglet.window import key
import numpy as np
import os, sys, time
from py5canvas import canvas, sketch_params
import traceback
import importlib
import threading
import cairo
from inspect import signature

# Try getting colored traceback
IPython_loader = importlib.find_loader('IPython')
if IPython_loader is not None:
    from IPython.core.ultratb import ColorTB

#master = tkinter.Tk()
#from tkinter import filedialog

# Optionally import imgui
imgui_loader = importlib.find_loader('imgui')
if imgui_loader is not None:
    import imgui
    from imgui.integrations.pyglet import create_renderer
else:
    imgui = None
# Optionally import easydict
edict_loader = importlib.find_loader('easydict')
if edict_loader is not None:
    from easydict import EasyDict as edict
else:
    edict = None

app_path = os.path.dirname(os.path.realpath(__file__))
print('Running in ' + app_path)

app_settings = {'script': ''}

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
        stamp = os.stat(self.filename).st_mtime
        if self._cached_stamp is None:
            self._cached_stamp = stamp
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
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
    """Contains our canvas and the pyglet window.
    Takes care of window management and copying the canvas data to the appropriate pyglet image"""
    def __init__(self, path,
                       width,
                       height,
                       title="Sketch",
                       standalone=False):
        # config = pyglet.gl.Config(major_version=2, minor_version=1,
        #                           sample_buffers=1,
        #                           samples=4,
        #                           depth_size=16,
        #                           double_buffer=True, )
        self.title = title
        # display = pyglet.canvas.get_display()
        # screens = display.get_screens()
        self.window = pyglet.window.Window(width, height, title) #, style='borderless')
        self.window.set_vsync(False)
        self.standalone = standalone
        self.width, self.height = width, height
        self.var_context = {}
        self.params = None
        self.gui = None
        self.gui_callback = None
        self.gui_focus = False
        if standalone:
            self.toolbar_height = 0
        else:
            self.toolbar_height = 30
        self._gui_visible = True
        self.keep_aspect_ratio = True
        self.create_canvas(self.width, self.height)
        # self.frame_rate(60)
        self.startup_error = False
        self.runtime_error = False

        self.grabbing = ''
        self.num_grab_frames = 0
        self.cur_grab_frame = 0
        self.video_writer = None
        self.video_fps = 30

        self.fps = 0
        self.first_load = True

        self.saving_to_file = ''
        self.recording_context = None
        self.recording_surface = None
        self.done_saving = False

        self.error_label = pyglet.text.Label('Error',
                           font_name='Arial',
                           font_size=12,
                           x=10, y=50,
                           anchor_x='left',
                           color=(255,0,0,255))

        self.watcher = None
        self.path = path
        self.must_reload = False

        self._frame_count = 0
        self._delta_time = 0.0

        self._mouse_pos = None #np.zeros(2)
        self.mouse_pos = np.zeros(2)
        self.prev_mouse = None
        self.mouse_delta = np.zeros(2)
        self.mouse_button = 0
        self.dragging = False
        self.mouse_moving = False

        self.prog_uses_imgui = False

        self.blit_scale_factor = (1.0, 1.0)

        #self.keys = pyglet.window.key

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

    @property
    def frame_count(self):
        return self._frame_count

    @property
    def delta_time(self):
        return self._delta_time

    def parameters(self, params):
        self.params = sketch_params.SketchParams(params, self.path)
        print('Setting params', self.params)
        self.params.load()
        return self.params.params

    def has_error(self):
        return self.startup_error or self.runtime_error

    def open_file_dialog(self, exts, title='Open file...'):
        # See https://github.com/xMGZx/xdialog
        import xdialog
        if np.isscalar(exts):
            exts = [exts]
        filetypes = [(ext + ' files', "*." + ext) for ext in exts]
        return xdialog.open_file(title, filetypes=filetypes, multiple=False)

    def save_file_dialog(self, exts, title='Open file...', filename='untitled'):
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
        import xdialog
        return xdialog.directory(title)

    def _create_canvas(self, w, h, canvas_size=None, fullscreen=False, screen=None):
        self.is_fullscreen = fullscreen
        #if screen is not None:
        #    self.window = pyglet.window.Window(w, h, self.title, screen=screen)
        self.window.set_vsync(False)
        self.window.set_size(w, h)
        self.window.set_fullscreen(fullscreen, screen)
        # Note, the canvas size may be different from the sketch size
        # for example when automatically creating a UI...
        if canvas_size is None:
            canvas_size = (w, h)
        self.width, self.height = canvas_size #w, h
        self.canvas = canvas.Canvas(*canvas_size, recording=False) #, clear_callback=self.clear_callback)
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

        self.window_width, self.window_height = self.window.get_size()

        # Expose canvas globally
        if self.var_context:
            self.update_globals()

        # Create image and copy initial canvas buffer to it
        buf = self.canvas.get_buffer()
        buf = (pyglet.gl.GLubyte * len(buf))(*buf)
        self.image = pyglet.image.ImageData(*canvas_size, "BGRA", buf)

    def create_canvas(self, w, h, gui_width=300, fullscreen=False, with_gui=True, screen=None):
        if imgui is None or not with_gui:
            print("Creating canvas no gui")
            self._create_canvas(w, h, fullscreen=fullscreen, screen=screen)
            return
        has_gui = 'gui' in self.var_context and callable(self.var_context['gui'])
        if self.params or self.gui_callback is not None or has_gui:
            self.create_canvas_gui(w, h, gui_width, fullscreen, screen=screen)
        else:
            self.gui = sketch_params.SketchGui(gui_width)
            self._create_canvas(w, h + self.toolbar_height, (w, h), fullscreen, screen=screen)

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

    def create_canvas_gui(self, w, h, width=300, fullscreen=False, screen=None):
        if imgui is None:
            print('Install ImGui to run UI')
            return self.create_canvas(w, h, fullscreen)
        self.gui = sketch_params.SketchGui(width)
        self._create_canvas(w + self.gui.width, h + self.toolbar_height, (w, h), fullscreen, screen=screen)

    def dump_canvas(self, path):
        ''' Tells the sketch to dump the next frame to an SVG file '''
        if '~' in path:
            path = os.path.expanduser(path)
        self.saving_to_file = os.path.abspath(path)
        print('saving file to', self.saving_to_file)
        # Since this can be called in frame, we need to make sure we don't save svg righ after
        self.done_saving = False
        # Add the recording context so we can replay and save later
        self.canvas.ctx.push_context(self.recording_context)

    save_canvas = dump_canvas

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

    def show_gui(self, flag, screen_index=-1):
        if self.gui is None:
            return
        self._gui_visible = flag
        #screen = self.window.screen
        #if screen_index > -1:
        #    screen = self.get_screen(screen_index)
        self.window.set_fullscreen(False)
        self.create_canvas(self.canvas.width,
                           self.canvas.height,
                           self.gui.width,
                           self.is_fullscreen,
                           flag) #screen=screen)

    def toggle_fullscreen(self, toggle_gui=False, screen_index=-1):
        self.fullscreen(not self.is_fullscreen,
                        toggle_gui=toggle_gui,
                        screen_index=screen_index)

    def get_screen(self, index):
        # TODO fixme
        display = pyglet.canvas.get_display()
        screens = display.get_screens()
        if index < len(screens) and index >= 0:
            return screens[index]
        print("Invalid screen index for display")
        return None

    def fullscreen(self, flag, toggle_gui=False, screen_index=-1):
        # old_window_width = self.canvas_display_width
        # old_window_height = self.canvas_display_height
        if toggle_gui:
            self.is_fullscreen = flag
            self.show_gui(not flag) #, screen_index)
            return

        self.window.set_fullscreen(False)
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

        # Set current directory to script dir
        if self.path:
            path = os.path.abspath(self.path)
            os.chdir(os.path.dirname(path))
            sys.path.append(os.path.dirname(path))
            app_settings['script'] = path

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
            # Expose canvas to the sketch
            print('exposing vars')
            for func in dir(self.canvas):
                if '__' not in func and callable(getattr(self.canvas, func)):
                    var_context[func] = wrap_canvas_method(self, func)
            var_context['TWO_PI'] = 2*np.pi
            var_context['PI'] = np.pi
            var_context['random'] = np.random.uniform
            var_context['random_seed'] = np.random.seed
            var_context['random_seed'] = np.random.seed
            var_context['radians'] = canvas.radians
            var_context['degrees'] = canvas.degrees
            var_context['map'] = canvas.map
            var_context['sin'] = np.sin
            var_context['cos'] = np.cos
            var_context['floor'] = lambda x: np.floor(x).astype(int)
            var_context['ceil'] = lambda x: np.ceil(x).astype(int)
            var_context['round'] = lambda x: np.round(x).astype(int)

            # And basic functions from sketch
            var_context['frame_rate'] = wrap_method(self, 'frame_rate')
            var_context['create_canvas'] = wrap_method(self, 'create_canvas')
            var_context['size'] = var_context['create_canvas'] # For compatibility
            var_context['create_canvas_gui'] = wrap_method(self, 'create_canvas_gui')
            var_context['save_svg'] = wrap_method(self, 'dump_canvas')
            var_context['save_canvas'] = wrap_method(self, 'dump_canvas')
            var_context['VideoInput'] = canvas.VideoInput
            # And also expose canvas as 'c' since the functions in the canvas are quite common names and
            # might be easily overwritten
            self.update_globals()
            # var_context['c'] = self.canvas
            exec(prog, var_context)

            if self.params is not None:
                print('Preload params')
                self.params.load()
            # call setup
            var_context['setup']()
            # User might create parameters in setup
            print('Maybe load params')
            if self.params is not None:
                print('Load params after setup')
                self.params.load()
            self.startup_error = False
            print("Success")
        except Exception as e:
            print('Error in sketch setup')
            print(e)
            self.startup_error = True
            self.error_label.text = str(e)
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
        # Expose canvas globally
        self.var_context['c'] = self.canvas
        # HACK keep mouse_pressed as a flag for backwards compatibility, but must be deprecated

        if 'mouse_pressed' not in self.var_context or not callable(self.var_context['mouse_pressed']):
            self.var_context['mouse_pressed'] = self.dragging
        self.var_context['dragging'] = self.dragging
        self.var_context['mouse_delta'] = self.mouse_delta
        self.var_context['mouse_pos'] = self.mouse_pos

    def _update(self, dt):
        # Almost a dummy function.
        # Scheduling this should force window redraw every frame
        # So we can sync update and drawing by calling frame() in the @draw callback
        # see https://stackoverflow.com/questions/39089578/pyglet-synchronise-event-with-frame-drawing
        self._delta_time = dt

        print('update')

    # internal update
    def frame(self):

        # Setting the framerate in pyglet run seems to break things
        # so make sure it is set when starting up the sketch
        if self.first_load:
            self.frame_rate(self.fps)
            self.first_load = False

        self._update_mouse()
        self.update_globals()

        if self.path:
            if self.must_reload or self.watcher.modified(): # Every frame check for file modification
                print("reloading")
                # Reload in global namespace
                self.reload(self.var_context)
                self.must_reload = False


        if imgui is not None:
            # For some reason this only works here and not in the constructor.
            if self.impl is None:
                imgui.create_context()
                self.impl = create_renderer(self.window)
                sketch_params.set_theme()
            try:
                imgui.new_frame()
            except imgui.core.ImGuiError as e:
                print('Error in imgui new_frame')
                print(e)
                self.error_label.text = str(e)
                self.runtime_error = True
                traceback.print_exc()
            # print('New frame')
            # # For some reason this only works here and not in the constructor.
            # if self.impl is None:
            #     imgui.create_context()
            #     self.impl = create_renderer(self.window)

            # imgui.new_frame()
        if self.saving_to_file:
            self.done_saving = True

        # return

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
                        self.error_label.text = str(e)
                        self.runtime_error = True
                        print_traceback()
                # Check focus
                #self.gui_focus = imgui.core.is_window_hovered()
                #print('gui focus', self.gui_focus)
        with perf_timer('update'):
            if not self.runtime_error or self._frame_count==0:
                try:
                    if 'draw' in self.var_context:
                        self.var_context['draw']()
                    else:
                        pass
                        #print('no draw in var context')
                    self.runtime_error = False
                except Exception as e:
                    print('Error in sketch draw')
                    print(e)
                    self.error_label.text = str(e)
                    self.runtime_error = True
                    print_traceback()

        # Copy canvas image and visualize
        pitch = self.width * 4
        with perf_timer('get buffer'):
            buf = self.canvas.get_buffer()

        with perf_timer('update image'):
            # https://stackoverflow.com/questions/9035712/numpy-array-is-shown-incorrect-with-pyglet
            buf = (pyglet.gl.GLubyte * len(buf)).from_buffer(buf)
            # The following is slow as hell
            #buf = (pyglet.gl.GLubyte * len(buf))(*buf)

        self.image.set_data("BGRA", -pitch, buf) # Looks like negative sign takes care of C-contiguity

        if self.grabbing and not self.must_reload:
            self.grab()

        # Update timers etc
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
                    self.error_label.text = str(e)
                    self.runtime_error = True
                    print_traceback()
            if not self.standalone:
                self.gui.toolbar(self)
            # Required for render to work in draw callback
            try:
                imgui.end_frame()
            except imgui.core.ImGuiError as e:
                print(e)

        if self.saving_to_file and self.done_saving:
            print('saving to ', self.saving_to_file)
            if '.svg' in self.saving_to_file:
                surf = cairo.SVGSurface(self.saving_to_file, self.canvas.width, self.canvas.height)
            elif '.pdf' in self.saving_to_file:
                surf = cairo.PDFSurface(self.saving_to_file, self.canvas.width, self.canvas.height)
            ctx = cairo.Context(surf)
            #ctx.set_source_surface(self.setup_surface)
            #ctx.paint()
            ctx.set_source_surface(self.recording_surface)
            ctx.paint()
            surf.finish()

            # Apply svg fix
            if '.svg' in self.saving_to_file:
                canvas.fix_clip_path(self.saving_to_file, self.saving_to_file)

            self.canvas.ctx.pop_context()
            self.saving_to_file = ''
            self.done_saving = False


        # NB need to check pyglet's draw loop, but clearing here will break when the frame-rate
        # is low or in other cases?
        # # Draw to window
        # self.window.clear()
        # self.image.blit(0, 0)

        # if self.startup_error or self.runtime_error:
        #     self.error_label.draw()

        # if imgui is not None:
        #     imgui.render()
        #     self.impl.render(imgui.get_draw_data())


    def frame_rate(self, fps):

        try:
            print('setting frame rate to ' + str(fps))
        #print('sketch.frame_rate is deprecated for the moment, the function will have no effect')
            event_loop = pyglet.app.event_loop
            event_loop.clock.unschedule(event_loop._redraw_windows)
            if fps > 0:
                event_loop.clock.schedule_interval(event_loop._redraw_windows, 1.0/fps)
            else:
                event_loop.clock.schedule(event_loop._redraw_windows)
            self.fps = fps
        except AttributeError as e:
            print(e)

        # pyglet.clock.unschedule(self._update)
        # pyglet.clock.schedule_interval(self._update, 1.0/fps)


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


def main(path='', standalone=False):
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
    sketch = Sketch(path, 512, 512, standalone=standalone)

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

    #@sketch.window.event
    def on_key_press(symbol, modifier):
        if imgui_focus():
            return
        # print('Key pressed')
        if check_callback('key_pressed'):
            params = [symbol, modifier]
            sig = signature(sketch.var_context['key_pressed'])
            sketch.var_context['key_pressed'](*params[:len(sig.parameters)])

    #@sketch.window.event
    def on_mouse_motion(x, y, dx, dy):
        sketch._mouse_pos = canvas_pos(x, y) #np.array([x, sketch.window_height-y-sketch.toolbar_height])
        #print((x, y, dx, dy))
        if check_callback('mouse_moved'):
            sketch.var_context['mouse_moved']()

    #@sketch.window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        pos = canvas_pos(x, y)
        sketch._mouse_pos = pos #canvas_pos(x, y) #np.array([x, sketch.window_height-y-sketch.toolbar_height])
        if imgui_focus():
            return
        if not point_in_canvas(pos):
            return

        sketch.dragging = True
        if check_callback('mouse_dragged'):
            params = [buttons, modifiers]
            sig = signature(sketch.var_context['mouse_dragged'])
            sketch.var_context['mouse_dragged'](*params[:len(sig.parameters)])

    #@sketch.window.event
    def on_mouse_press(x, y, button, modifiers):
        pos = canvas_pos(x, y)
        if imgui_focus():
            return
        if not point_in_canvas(pos):
            return

        sketch.dragging = True
        sketch.mouse_button = button
        sketch._mouse_pos = pos #np.array([x, sketch.window_height-y-sketch.toolbar_height])
        if check_callback('mouse_pressed'):
            params = [button, modifiers]
            sig = signature(sketch.var_context['mouse_pressed'])
            sketch.var_context['mouse_pressed'](*params[:len(sig.parameters)])

    #@sketch.window.event
    def on_mouse_release(x, y, button, modifiers):
        pos = canvas_pos(x, y)
        sketch.dragging = False
        sketch._mouse_pos = pos #np.array([x, sketch.window_height-y-sketch.toolbar_height])
        if check_callback('mouse_released'):
            params = [button, modifiers]
            sig = signature(sketch.var_context['mouse_released'])
            sketch.var_context['mouse_released'](*params[:len(sig.parameters)])

    sketch.window.push_handlers(on_key_press,
                                on_mouse_motion,
                                on_mouse_drag,
                                on_mouse_press,
                                on_mouse_release)

    # Load settings if they exist
    settings = sketch_params.load_json(os.path.join(app_path, 'settings.json'))
    if settings:
        app_settings.update(settings)

    if not sketch.path:
        sketch.path = app_settings['script']

    if sketch.path:
        if 'exit' in sketch.var_context:
            sketch.var_context['exit']()
        sketch.reload(locals())
    else:
        sketch.var_context = locals()

    # on draw event
    @sketch.window.event
    def on_draw():
        # Updates input and calls draw in the sketch
        sketch.frame()

        # clearing the window
        sketch.window.clear()
        if sketch.keep_aspect_ratio:
            sketch.blit_scale_factor = (sketch.canvas_display_height / sketch.canvas.height,
                                        sketch.canvas_display_height / sketch.canvas.height)
        else:
            sketch.blit_scale_factor = (sketch.canvas_display_width / sketch.canvas.width,
                                      sketch.canvas_display_height / sketch.canvas.height)



        sketch.image.blit(0, 0,
                          width=sketch.canvas.width*sketch.blit_scale_factor[0],
                          height=sketch.canvas.height*sketch.blit_scale_factor[1])

        if sketch.has_error():
            sketch.error_label.draw()

        if not sketch.runtime_error and 'draw_gl' in sketch.var_context:
            try:
                sketch.var_context['draw_gl']()
            except Exception as e:
                print('Error in draw_gl')
                print(e)
                sketch.error_label.text = str(e)
                sketch.runtime_error = True
                print_traceback()


        if imgui is not None:
            try:
                imgui.render()
                sketch.impl.render(imgui.get_draw_data())
            except imgui.core.ImGuiError as e:
                print('Error in imgui render')
                print(e)


    def close():
        # Stop grabbing and finalize
        sketch.finalize_grab()

        # Save params if they exist
        if sketch.params is not None and not sketch.has_error():
            print('Saving params')
            sketch.params.save()

        if 'exit' in sketch.var_context:
            sketch.var_context['exit']()

        print("Saving settings")
        sketch_params.save_json(app_settings, os.path.join(app_path, 'settings.json'))
        sketch.cleanup()
        print("End close")
        
    @sketch.window.event
    def on_close():
        print('Close window event')
        close()

    print("Starting loop")
    pyglet.app.run(interval=0) # Default is max framerate
    print("Exit")
    close()

if __name__ == '__main__':
    main()

