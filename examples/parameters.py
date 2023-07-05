params = {'width': (100.0, {'min': 10, 'max': 200}),
          'height': (100.0, {'min': 10, 'max': 200}),
          'color': ([255, 0, 0], {'type':'color'}),
          'show' : True}
params = sketch.parameters(params)

def setup():
    create_canvas_gui(512, 512, 200)

def draw():
    background(0)
    # Center of screen
    translate(width/2, height/2)
    if params.show:
        fill(params.color)
        rectangle(-params.width/2, -params.height/2, params.width, params.height)
