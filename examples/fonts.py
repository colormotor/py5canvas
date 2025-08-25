from py5canvas import *


def setup():
    create_canvas(512, 512)
    background(255)
    frame_rate(60)


def draw():
    background(255)
    no_stroke()

    fill(0)
    text_font("Times New Roman")
    # text_style("normal")
    text_size(35)
    text("steps", [30, 50])

    fill(255, 0, 0)
    text_font("Courier New")
    text_style("italic")
    text_size(45)
    text("stages", [120, 130])

    fill(0, 255, 0)
    text_font("fonts/LibertinusSerifDisplay-Regular.otf")
    text_style("bold")
    text_size(65)
    text("moves", [330, 280])

    fill(0, 0, 255)
    text_font("fonts/Bradley Hand Bold.ttf")
    text_style("bolditalic")
    text_size(75)
    text("measures", [80, 450])


run()
