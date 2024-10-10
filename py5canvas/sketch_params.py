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

import importlib
import traceback
import importlib.util


# Optionally import imgui
imgui_loader = importlib.util.find_spec('imgui')
if imgui_loader is not None:
    import imgui
    # from imgui.integrations.pyglet import create_renderer
else:
    imgui = None

# Optionally import easydict
edict_loader = importlib.util.find_spec('easydict')
if edict_loader is not None:
    from easydict import EasyDict as edict
else:
    edict = None


import numpy as np
import json, codecs, os, copy, shutil


class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float16, np.float32,
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        elif isinstance(obj, (np.bool)):
            return bool(obj)
        elif isinstance(obj, (np.complex128)):
            return complex(bool)

        return json.JSONEncoder.default(self, obj)

def load_json(path, encoder=NumpyEncoder):
    try:
        with codecs.open(path, encoding='utf8') as fp:
            data = json.load(fp)
            return data
    except IOError as err:
        print(err)
        print ("Unable to load json file:" + path)
        return {}

def save_json(data, path, encoder=NumpyEncoder):
    with open(path, 'w') as fp:
        json.dump(data, fp, indent=4, sort_keys=False, cls=encoder)

def preprocess_guiparams(_gui_params):
    ''' Makes sure options are available for all parameters
    and creates a key entry for each paramter or group'''
    gui_params = {}
    for name, val in _gui_params.items():
        key = '_'.join(name.lower().split(' '))
        if isinstance(val, dict):
            gui_params[name] = preprocess_guiparams(val)
            gui_params[name]['__key__'] = key
        else:
            if isinstance(val, (tuple, list)):
                val, opts = val
            else:
                opts = {}
            opts['__key__'] = key
            gui_params[name] = (val, opts)
    return gui_params


def fetch_params(gui_params):
    ''' Fetches the parameters from the gui_params dictionary'''
    params = {}
    for name, val in gui_params.items():
        if name == '__key__': # Avoid key entry for groups
            continue
        if isinstance(val, dict):
            key = val['__key__']
            params[key] = fetch_params(val)
        else:
            val, opts = val
            key = opts['__key__']
            params[key] = val
    return params

def filter_params(params):
    res = {}
    for key, val in params.items():
        if isinstance(val, dict):
            res[key] = filter_params(val)
        else:
            if not callable(val):
                res[key] = val
    return res

def update_params(params, new_params):
    for key, val in new_params.items():
        if key not in params:
            continue
        if isinstance(val, dict) and isinstance(params[key], dict):
            update_params(params[key], val)
        else:
            params[key] = val

class SketchParams:
    ''' Handle the parameters of a sketch.
    Stores two dictionaries, one for easy access to sketch parameters,
    through EasyDict (if available) and one for the GUI.
    Both can be nested dictionaries. '''
    def __init__(self, gui_params, path):
        ''' params: a (possibly nested) dictionary of parameters,
        entries with a tuple or list consist of (value, options) pairs
        nested dictionaries are treated as groups,
        and will be displayed as such in the GUI'''
        self.gui_params = preprocess_guiparams(gui_params)
        print('Creating gui params')
        self.params = fetch_params(self.gui_params)
        # Use EasyDict if available
        if edict is not None:
            self.params = edict(self.params)
        # Set default parameter path at same level as sketch
        self.param_path = os.path.splitext(path)[0] + '.json'
        self.presets = {}
        self.aux = {}
        self.current_preset = -1

    def save(self, path=''):
        if not path:
            path = self.param_path

        data = {'params': filter_params(self.params),
                'presets': filter_params(self.presets),
                'aux': self.aux}
        save_json(data, path)

    def load(self, path=''):
        if not path:
            path = self.param_path

        print('Loading parameters from ' + path)
        #print('Pre: ', self.params)
        data = load_json(path)
        if not data:
            return
        update_params(self.params, data['params'])
        #self.params.update(data['params'])
        self.presets = data['presets']
        self.aux.update(data['aux'])
        #print('Post: ', self.params)
        self.current_preset = -1

    def preset_index(self, name):
        for i, k in enumerate(self.presets.keys()):
            if k == name:
                return i
        return -1

    def apply_preset(self, name):
        if name in self.presets:
            update_params(self.params, self.presets[name])
            #self.params.update(self.presets[name])

    def add_preset(self, name):
        self.presets[name] = copy.deepcopy(self.params)

    def delete_preset(self, name):
        if name in self.presets:
            self.presets.pop(name)


if imgui is not None:
    def set_theme(hue=0.127):
        sat_mul = 0.5
        col_main_sat = (sat_mul*120) / 255
        col_main_val = 161 / 255
        col_area_sat = (sat_mul*104) / 255
        col_area_val = 60 / 255
        col_back_sat = (sat_mul*59) / 255
        col_back_val = 40 / 255

        col_text = imgui.color_convert_hsv_to_rgb(hue, 20 / 255, 235 / 255)
        col_main = imgui.color_convert_hsv_to_rgb(hue, col_main_sat, col_main_val)
        col_back = imgui.color_convert_hsv_to_rgb(hue, col_back_sat, col_back_val)
        col_area = imgui.color_convert_hsv_to_rgb(hue, col_area_sat, col_area_val)

        style = imgui.get_style() # override active style
        imgui.style_colors_dark(style) # optional: set base colors from "Dark" (or any other) style

        style.window_rounding = 0.0
        style.indent_spacing = 5

        style.colors[imgui.COLOR_TEXT] = \
        [col_text[0], col_text[1], col_text[2], 1.00]
        style.colors[imgui.COLOR_TEXT_DISABLED] = \
        [col_text[0], col_text[1], col_text[2], 0.58]
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = \
        [col_back[0], col_back[1], col_back[2], 1.00]
        style.colors[imgui.COLOR_CHILD_BACKGROUND] = \
        [col_back[0] * 0.7, col_back[1] * 0.7, col_back[2] * 0.7, 1.0]
        style.colors[imgui.COLOR_BORDER] = \
        [col_text[0], col_text[1], col_text[2], 0.30]
        style.colors[imgui.COLOR_BORDER_SHADOW] = \
        [0.0, 0.0, 0.0, 0.0]
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = \
        [col_area[0], col_area[1], col_area[2], 1.00]
        style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 0.68]
        style.colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = \
        [col_main[0], col_main[1], col_main[2], 0.45]
        style.colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED] = \
        [col_main[0], col_main[1], col_main[2], 0.35]
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 0.78]
        style.colors[imgui.COLOR_MENUBAR_BACKGROUND] = \
        [col_area[0], col_area[1], col_area[2], 0.57]
        style.colors[imgui.COLOR_SCROLLBAR_BACKGROUND] = \
        [col_area[0], col_area[1], col_area[2], 1.00]
        style.colors[imgui.COLOR_SCROLLBAR_GRAB] = \
        [col_main[0], col_main[1], col_main[2], 0.31]
        style.colors[imgui.COLOR_SCROLLBAR_GRAB_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 0.78]
        style.colors[imgui.COLOR_SCROLLBAR_GRAB_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_POPUP_BACKGROUND] = \
        [col_area[0], col_area[1], col_area[2], 1.00]
        style.colors[imgui.COLOR_CHECK_MARK] = \
        [col_main[0], col_main[1], col_main[2], 0.80]
        style.colors[imgui.COLOR_SLIDER_GRAB] = \
        [col_main[0]*0.7, col_main[1]*0.7, col_main[2]*0.7, 1.0]
        style.colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_BUTTON] = \
        [col_main[0], col_main[1], col_main[2], 0.44]
        style.colors[imgui.COLOR_BUTTON_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 0.86]
        style.colors[imgui.COLOR_BUTTON_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_HEADER] = \
        [col_main[0], col_main[1], col_main[2], 0.76]
        style.colors[imgui.COLOR_HEADER_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 0.86]
        style.colors[imgui.COLOR_HEADER_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_SEPARATOR] = \
        [col_text[0], col_text[1], col_text[2], 0.32]
        style.colors[imgui.COLOR_SEPARATOR_HOVERED] = \
        [col_text[0], col_text[1], col_text[2], 0.78]
        style.colors[imgui.COLOR_SEPARATOR_ACTIVE] = \
        [col_text[0], col_text[1], col_text[2], 1.00]
        style.colors[imgui.COLOR_RESIZE_GRIP] = \
        [col_main[0], col_main[1], col_main[2], 0.20]
        style.colors[imgui.COLOR_RESIZE_GRIP_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 0.78]
        style.colors[imgui.COLOR_RESIZE_GRIP_ACTIVE] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_PLOT_LINES] = \
        [col_text[0], col_text[1], col_text[2], 0.63]
        style.colors[imgui.COLOR_PLOT_LINES_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_PLOT_HISTOGRAM] = \
        [col_text[0], col_text[1], col_text[2], 0.63]
        style.colors[imgui.COLOR_PLOT_HISTOGRAM_HOVERED] = \
        [col_main[0], col_main[1], col_main[2], 1.00]
        style.colors[imgui.COLOR_TEXT_SELECTED_BACKGROUND] = \
        [col_main[0], col_main[1], col_main[2], 0.43]
        style.colors[imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND] = \
        [0.20, 0.20, 0.20, 0.35]


    def get_param_type(val, opts):
        if isinstance(val, bool):
            return 'checkbox'
        elif isinstance(val, int):
            if 'min' in opts and 'max' in opts:
                return 'int_slider'
            elif 'selection' in opts:
                return 'selection'
            return 'int'
        elif isinstance(val, float):
            if 'min' in opts and 'max' in opts:
                return 'float_slider'
            return 'float'
        elif isinstance(val, str):
            return 'text'
        elif callable(val):
            return 'button'
        elif not np.isscalar(val): # Assume array
            if 'type' in opts:
                if opts['type'] == 'color':
                    return 'color'
            else:
                if isinstance(val[0], int):
                    return 'int_array'
                elif isinstance(val[0], float):
                    return 'float_array'

        return ''

    class SketchGui:
        def __init__(self, width):
            self.width = width
            self.changed = set()
            self.cur_preset_name = ''

        def force_changed(self, params, gui_params, parent=''):
            for name, val in gui_params.items():
                if name == '__key__':
                    continue

                if type(val) == dict:
                    key = val['__key__']
                    self.force_changed(params[key], val, parent + key + '.')
                else:
                    val, opts = val
                    key = opts['__key__']
                    self.changed.add(parent + key)

        def show_params(self, params, gui_params, parent='', depth=0):

            for name, val in gui_params.items():
                if name == '__key__':
                    continue
                if type(val) == dict: # A dict marks a group
                    key = val['__key__'] # Assume this has been filled automatically
                    if imgui.tree_node(name, imgui.TREE_NODE_DEFAULT_OPEN):
                        imgui.push_id(name)
                        self.show_params(params[key], val, parent + key + '.', depth+1)
                        imgui.pop_id()
                        imgui.tree_pop()
                else:
                    val, opts = val
                    key = opts['__key__'] # Assume this has been filled automatically
                    if 'hide' in opts and opts['hide']:
                        continue
                    if 'sameline' in opts and opts['sameline']:
                        imgui.same_line()
                    param_type = get_param_type(val, opts)
                    if not param_type:
                        continue
                    try:
                        changed = False
                        if param_type == 'int':
                            changed, params[key] = imgui.input_int(name, params[key])
                        elif param_type == 'button':
                            if imgui.button(name):
                                val()
                        elif param_type == 'text':
                            buf_length = 1024
                            if 'buf_length' in opts:
                                buf_length = opts['buf_length']
                            if 'multiline' in opts and opts['multiline']:
                                changed, params[key] = imgui.input_text_multiline(name, params[key], buf_length, 0, 0, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
                            else:
                                changed, params[key] = imgui.input_text(name, params[key], buf_length, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
                        elif param_type == 'selection':
                            changed, params[key] = imgui.combo(name, params[key], opts['selection'])
                        elif param_type == 'float':
                            changed, params[key] = imgui.input_float(name, params[key])
                        elif param_type == 'float_slider':
                            changed, params[key] = imgui.slider_float(name, params[key], opts['min'], opts['max'])
                        elif param_type == 'int_slider':
                            changed, params[key] = imgui.slider_int(name, params[key], opts['min'], opts['max'])
                        elif param_type == 'checkbox':
                            changed, params[key] = imgui.checkbox(name, params[key])
                        elif param_type == 'color':
                            clr = np.array(params[key], dtype=np.float32)
                            clr /= self.sketch.canvas.color_scale[:len(clr)]
                            if len(clr) == 3:
                                changed, clr = imgui.color_edit3(name, *clr) #, imgui.COLOR_EDIT_DISPLAY_HSV)
                            else:
                                changed, clr = imgui.color_edit4(name, *clr) #, imgui.COLOR_EDIT_DISPLAY_HSV)
                            params[key] = np.array(clr)*self.sketch.canvas.color_scale[:len(clr)]
                        if changed:
                            self.changed.add(parent + key)
                            if parent:
                                self.changed.add(parent[:-1])

                    except KeyError as e:
                        print(e)
                        print("Key mismatch for parameter", name)
                        print(param_type)
                        print(key)
                        print(params)

        def toolbar(self, sketch):
            self.sketch = sketch
            # Top bar
            ratio = sketch.get_pixel_ratio()
            imgui.set_next_window_size(sketch.window_width, sketch.toolbar_height)
            imgui.set_next_window_position(0, 0)
            imgui.begin("Toolbar", True, (imgui.WINDOW_NO_RESIZE |
                                            imgui.WINDOW_NO_TITLE_BAR |
                                            imgui.WINDOW_NO_SAVED_SETTINGS |
                                            imgui.WINDOW_NO_SCROLLBAR))

            if imgui.button('Load sketch...'):
                path = sketch.open_file_dialog('py')
                if path:
                    sketch.load(path)
            imgui.same_line()
            if imgui.button('Backup...'):
                name = os.path.splitext(os.path.basename(sketch.path))[0]
                path = sketch.save_file_dialog('py', filename=name+'_backup')
                if path:
                    shutil.copy(sketch.path, path)
                    json_path = sketch.path.replace('.py', '.json')
                    if os.path.isfile(json_path):
                        shutil.copy(json_path, path.replace('.py', '.json'))
            if imgui.is_item_hovered():
                with imgui.begin_tooltip():
                    imgui.text('Save a copy of the current sketch')
                    imgui.text('and its parameters')
            imgui.same_line()
            if imgui.button('Reload'):
                sketch.must_reload = True
            if imgui.is_item_hovered():
                with imgui.begin_tooltip():
                    imgui.text('Force reload sketch')
            imgui.same_line()
            if imgui.button('Save SVG...'):
                name = os.path.splitext(os.path.basename(sketch.path))[0]
                path = sketch.save_file_dialog('svg', filename=name)
                if path:
                    sketch.dump_canvas(path)
            imgui.same_line()
            if imgui.button('Save PDF...'):
                name = os.path.splitext(os.path.basename(sketch.path))[0]
                path = sketch.save_file_dialog('pdf', filename=name)
                if path:
                    sketch.dump_canvas(path)
            if imgui.is_item_hovered():
                with imgui.begin_tooltip():
                    imgui.text('Save sketch output as SVG')

            imgui.same_line()
            imgui.push_style_color(imgui.COLOR_TEXT, 0.5, 0.5, 0.5)
            script_name = os.path.basename(sketch.path)
            imgui.text('Sketch: ' + script_name)
            imgui.pop_style_color(1)
            imgui.end()

        def begin_gui(self, sketch):
            self.sketch = sketch
            ratio = 1 #sketch.window.get_pixel_ratio()
            imgui.set_next_window_size(self.width, (sketch.window_height - sketch.toolbar_height)*ratio)
            imgui.set_next_window_position((sketch.window_width - self.width)*ratio, sketch.toolbar_height)
            imgui.begin("Py5sketch", True, (imgui.WINDOW_NO_RESIZE |
                                            imgui.WINDOW_NO_TITLE_BAR |
                                            imgui.WINDOW_NO_SAVED_SETTINGS))
            imgui.begin_child("Sketch")

        def show_sketch_controls(self):
            return imgui.collapsing_header("Controls", None, imgui.TREE_NODE_DEFAULT_OPEN)[0]

        def from_params(self, sketch, callback=None, init=True):
            self.sketch = sketch
            self.changed = set()
            if init:
                self.begin_gui()
            

            if imgui.collapsing_header("Parameters", None, imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                if sketch.params is not None:
                    self.show_params(sketch.params.params, sketch.params.gui_params)

            # Presets
            imgui.spacing()
            imgui.spacing()

            if sketch.params is not None:
                if imgui.collapsing_header("Presets", None, imgui.TREE_NODE_DEFAULT_OPEN):
                    preset_names = [k for k in sketch.params.presets.keys()]
                    preset_name = ''
                    if 0 <= sketch.params.current_preset < len(preset_names):
                        preset_name = preset_names[sketch.params.current_preset]

                    buttons = False
                    if self.cur_preset_name:
                        buttons = True
                        if imgui.button('+'):
                            sketch.params.add_preset(self.cur_preset_name)
                            preset_names = [k for k in sketch.params.presets.keys()]
                            sketch.current_preset = sketch.params.preset_index(self.cur_preset_name)
                            preset_name = self.cur_preset_name
                        if imgui.is_item_hovered():
                            with imgui.begin_tooltip():
                                if self.cur_preset_name == preset_name:
                                    imgui.text('Update preset')
                                else:
                                    imgui.text('Add new preset')

                    if preset_name:
                        if buttons:
                            imgui.same_line()
                        buttons = True
                        if imgui.button('-'):
                            sketch.params.delete_preset(preset_name)
                            sketch.params.current_preset = -1
                        if imgui.is_item_hovered():
                            with imgui.begin_tooltip():
                                imgui.text('Delete selected preset')

                    if buttons:
                        imgui.same_line()
                    changed, self.cur_preset_name = imgui.input_text('Name', self.cur_preset_name, 512, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
                    if preset_name:
                        if imgui.is_item_hovered():
                            with imgui.begin_tooltip():
                                imgui.text('Press enter to update preset name')


                    clicked, sketch.params.current_preset = imgui.listbox("Presets", sketch.params.current_preset, preset_names)

                    if clicked:
                        sketch.params.apply_preset(preset_names[sketch.params.current_preset])
                        self.cur_preset_name = preset_names[sketch.params.current_preset]
                        self.force_changed(sketch.params.params, sketch.params.gui_params)


                    if changed:
                        if preset_name: #self.cur_preset_name in sketch.params.presets:
                            sketch.params.presets[self.cur_preset_name] = sketch.params.presets.pop(preset_name)
                            sketch.params.current_preset = sketch.params.preset_index(self.cur_preset_name)
                            preset_names = [k for k in sketch.params.presets.keys()]

            imgui.end_child()
            imgui.end()

            # imgui.begin("Style editor")
            # imgui.show_style_editor()
            # imgui.end()
