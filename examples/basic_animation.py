def setup():
    sketch.create_canvas(512, 512)
    sketch.frame_rate(60)

def draw():
    c = sketch.canvas # Get the base canvas

    c.background(0, 0, 0, 8) # Clear with alpha will create the "trail effect"
    c.push()
    # Center of screen
    c.translate(c.width/2, c.height/2)
    # Draw rotating circle
    c.fill(255, 0, 0)
    c.stroke(255)
    c.rotate(sketch.frame_count*0.05)
    c.circle(100, 0, 20)
    c.pop()
