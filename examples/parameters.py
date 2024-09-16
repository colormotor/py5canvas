from py5canvas import *

import numpy as np

def parameters():
    # This will expose a 'params' variable
    return {'Width': (100.0, {'min': 10, 'max': 200}),
            'Height': (100.0, {'min': 10, 'max': 200}),
            'Color': ([255, 0, 0], {'type':'color'}),
            'Hue': (0.0, {'min': 0, 'max': 1}),
            'Show' : True,
            'Other': { # Unused parameters for demo purposes
                'A text' : ('Hello World', {'multiline': True, 'buf_length': 2024}),
                'Selection' : (0, {'selection': ['First option', 'Second option', 'Third option']}),
                'A real number': 0.0,
                'An integer': 0,
                'Int slider' : (0, {'min': 0, 'max': 10}),
                }
            }

def setup():
    create_canvas(512, 512)

def draw():
    background(0)
    # Once processed and by default, parameters are accessed with the labels
    # converted to lowercase and spaces replaced by underscores.
    # Center of screen
    translate(width/2, height/2)
    if params.show:
        fill(params.color)
        rectangle(-params.width/2 + np.sin(frame_count/20)*200, -params.height/2, params.width, params.height)
    # Check if text changed. We use the dot notation,
    # as a string to check for a subparameter.
    if 'other.a_text' in sketch.gui.changed:
        print('Text changed')
    if 'hue' in sketch.gui.changed:
        sketch.set_gui_theme(params.hue)
        print('Hue changed')

run()
