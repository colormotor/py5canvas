params = {'width': (100, {'min': 10, 'max': 200}),
          'height': (100, {'min': 10, 'max': 200}),
          'color': ([255, 0, 0], {'type':'color'})}
params = sketch.parameters(params)

def setup():
    create_canvas_gui(512, 512)

def draw():
    background(0)
    # Center of screen
    translate(width/2, height/2)
    fill(params.color)
    rectangle(-params.width/2, -params.height/2, params.width, params.height)
