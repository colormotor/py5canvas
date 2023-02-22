from py5canvas import canvas

# Note that this example will require OpenCV to be installed
# By default, use webcam as video input
video = canvas.VideoInput(size=(512, 512))
# Otherwise specify a name to load an actual video
# video = canvas.VideoInput(name='worf.mp4', size=(512, 512))

def setup():
    sketch.create_canvas(512, 512)
    sketch.frame_rate(60)

def draw():
    c = sketch.canvas # Get the base canvas
    c.background(0)
    frame = video.read()
    c.image(frame)
