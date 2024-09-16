from py5canvas import *

# Note that this example will require OpenCV to be installed
# By default, use webcam as video input
# video = VideoInput(size=(512, 512))
# Or use a video file
video = VideoInput(name='./images/fingers.mov')

def setup():
    create_canvas(512, 512)

def draw():
    background(0)
    frame = video.read()
    image(frame, 0, 0, width, height)

run()