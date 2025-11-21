from py5canvas import *

def parameters():
    # This will expose a 'params' variable
    return {'Width': (100, 10, 200),
            'Height': (100, 10, 200),
            'Color': ([255, 0, 0], {'type':'color'}),
            'Hue': (0.0, 0.0, 1.0),
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
    translate(width/2, height/2)
    if params.show:
        fill(params.color)
        rect(-params.width/2 + 
             np.sin(frame_count/20)*200, 
             -params.height/2, 
             params.width, params.height)
    # Check if text changed. We use the dot notation,
    # as a string to check for a subparameter.
    if param_changed('other.a_text'):
        print('Text changed')
    if param_changed('hue'):
        print('Hue changed')

run()
