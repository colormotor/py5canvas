def setup():
    create_canvas(600, 512)
    frame_rate(60)

def draw():
    background(0, 0, 0, 8) # Clear with alpha will create the "trail effect"
    push()
    # Center of screen
    translate(width/2, height/2)
    # Draw rotating circle
    fill(255, 0, 0)
    stroke(255)
    rotate(frame_count*0.05)
    circle(100, 0, 20)
    pop()

if __name__== '__main__':
    # This gets automatically called when running with python rather than py5sketch
    import py5canvas
    py5canvas.run()
