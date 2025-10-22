from py5canvas import *

font = create_font('fonts/Fascinate-Regular.ttf', 70)
word = "tremor"

def setup():
    create_canvas(512, 256)
    text_font(font)
    text_size(100)
    text_align(CENTER, CENTER)

def draw():
    background(255)
    translate(center)

    random_factor = 5
    point_dist = 10

    half_width = text_width(word) / 2
    inc = 0
    for i, letter in enumerate(word):

        letter_points = text_points(letter, - half_width  + inc, 0, dist=point_dist)

        # text(letter, - half_width  + inc, 0)

        inc += text_width(letter)

        begin_contour()
        for p in letter_points:
            vertex(p + random(p.shape) * random_factor)
        end_contour()

        # print(letter_points)

run()

