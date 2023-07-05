#!/usr/bin/env python3
import importlib

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


import numpy as np
import json, codecs, os


class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


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
            print(val)
            val, opts = val
            key = opts['__key__']
            params[key] = val
    return params


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

    def save(self, path='', encoder=NumpyEncoder):
        if not path:
            path = self.param_path

        print('Saving parameters to ' + path)
        print(self.params)
        with open(path, 'w') as fp:
            json.dump(self.params, fp, indent=4, sort_keys=False, cls=encoder)

    def load(self, path='', encoder=NumpyEncoder):
        if not path:
            path = self.param_path
        print('Loading parameters from ' + path)
        try:
            with codecs.open(path, encoding='utf8') as fp:
                data = json.load(fp)
                # Update so we don't overwrite reference
                self.params.update(data)
        except IOError as err:
            print(err)
            print ("Unable to load json file:" + path)


if imgui is not None:
    def get_param_type(val, opts):
        if isinstance(val, bool):
            return 'checkbox'
        elif isinstance(val, int):
            if 'min' in opts and 'max' in opts:
                return 'int_slider'
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
            if 'type' in opts and opts['type'] == 'color':
                return 'color'
        return ''

    class SketchGui:
        def __init__(self, width):
            self.width = width
            pass

        def show_params(self, params, gui_params, depth=0):
            for name, val in gui_params.items():
                if name == '__key__':
                    continue
                if type(val) == dict: # A dict marks a group
                    key = val['__key__'] # Assume this has been filled automatically
                    if imgui.tree_node(name, imgui.TREE_NODE_DEFAULT_OPEN):
                        self.show_params(params[key], val, depth+1)
                        imgui.tree_pop()
                else:
                    val, opts = val
                    key = opts['__key__'] # Assume this has been filled automatically
                    if 'hide' in opts and opts['hide']:
                        continue

                    param_type = get_param_type(val, opts)
                    if not param_type:
                        continue
                    try:
                        if param_type == 'float_slider':
                            _, params[key] = imgui.slider_float(name, params[key], opts['min'], opts['max'])
                        elif param_type == 'checkbox':
                            _, params[key] = imgui.checkbox(name, params[key])
                    except KeyError as e:
                        print("Key mismatch for parameter", name)
                        print(e)

        def from_params(self, sketch):
            imgui.set_next_window_size(self.width, sketch.height)
            imgui.set_next_window_position(sketch.window_width - self.width, 0)
            imgui.begin("Parameters", True, imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
            if sketch.params is not None:
                self.show_params(sketch.params.params, sketch.params.gui_params)
            imgui.end()

