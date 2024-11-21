# Autogenerated canvas/sketch methods as globals to trick the linter

def set_color_scale(*args):
    """Set color scale:

Arguments:

- ~scale~ (float): the color scale. if we want to specify colors in the ~0...255~ range,
 ~scale~ will be ~255~. If we want to specify colors in the ~0...1~ range, ~scale~ will be ~1~ """
    pass  # Dummy method for linter

cur_fill = ''

def cur_fill(*args):
    pass  # Dummy method for linter

cur_stroke = ''

def cur_stroke(*args):
    pass  # Dummy method for linter

center = 'The center of the canvas (as a 2d numpy array)'

def get_width():
    """The width of canvas """
    pass  # Dummy method for linter

def get_height():
    """The height of canvas """
    pass  # Dummy method for linter

width = 'The width of canvas'

height = 'The height of canvas'

surface = ''

def no_fill():
    """Do not fill subsequent shapes """
    pass  # Dummy method for linter

def no_stroke():
    """Do not stroke subsequent shapes """
    pass  # Dummy method for linter

def fill_rule(*args):
    """Sets the fill rule

         """
    pass  # Dummy method for linter

def color_mode(*args):
    """Set the color mode for the canvas

Arguments:

- ~mode~ (string): can be one of 'rgb', 'hsv' depending on the desired color mode
- ~scale~ (float): the scale for the color values (e.g. 255 for 0...255 range, 1 for 0...1 range)

Examples:

- ~color_mode('rgb', 1.0)~ will set the color mode to RGB in the 0-1 range. """
    pass  # Dummy method for linter

def fill(*args):
    """Set the color of the current fill

Arguments:

- A single argument specifies a grayscale value, e.g ~fill(128)~ will fill with 50% gray.
- Two arguments specify grayscale with opacity, e.g. ~fill(255, 128)~ will fill with transparent white.
- Three arguments specify a color depending on the color mode (rgb or hsv)
- Four arguments specify a color with opacity """
    pass  # Dummy method for linter

def stroke(*args):
    """Set the color of the current stroke

Arguments:
- A single argument specifies a grayscale value, e.g. ~stroke(255)~ will set the stroke to white.
- Two arguments specify grayscale with opacity, e.g. ~stroke(0, 128)~ will set the stroke to black with 50% opacity.
- Three arguments specify a color depending on the color mode (rgb or hsv), e.g. ~stroke(255, 0, 0)~ will set the stroke to red, when the color mode is RGB
- Four arguments specify a color with opacity """
    pass  # Dummy method for linter

def stroke_weight(*args):
    """Set the line width

Arguments:
- The width in pixel of the stroke """
    pass  # Dummy method for linter

def line_join(*args):
    """Specify the 'join' mode for polylines.

Arguments:

- ~join~ (string): can be one of "miter", "bevel" or "round" """
    pass  # Dummy method for linter

def blend_mode(*args):
    """Specify the blending mode

Arguments:

- ~mode~ (string) can be one of: "clear", "source", "over", "in", "out", "atop",
  "dest", "dest_over", "dest_in", "dest_out", "dest_atop", "xor", "add", "saturate", "multiply", "screen", "overlay", "darken", "lighten", "color_dodge", "color_burn", "hard_light", "soft_light", "difference", "exclusion", "hsl_hue", "hsl_saturation", "hsl_color", "hsl_luminosity"
  See [[https://www.cairographics.org/operators/]] for a discussion on the different operators. """
    pass  # Dummy method for linter

def line_cap(*args):
    """Specify the 'cap' for lines.

Arguments:

- ~cap~ (string): can be one of "butt", "round" or "square" """
    pass  # Dummy method for linter

def text_align(*args):
    """Specify the text alignment

Arguments:
- ~halign~ (string): Horizontal alignment. One of "left", "center" or "right"
- ~valign~ (string): Horizontal alignment. One of "bottom" (default), "top" or "center" """
    pass  # Dummy method for linter

def text_size(*args):
    """Specify the text size

Arguments:

- ~size~ (int): the text size """
    pass  # Dummy method for linter

def text_font(*args):
    """Specify the font to use for text rendering
Arguments:

- ~font~ (string): the name of a system font """
    pass  # Dummy method for linter

def push_matrix():
    """Save the current transformation """
    pass  # Dummy method for linter

def pop_matrix():
    """Restore the previous transformation """
    pass  # Dummy method for linter

def push_style():
    """Save the current drawing state """
    pass  # Dummy method for linter

def pop_style():
    """Restore the previously pushed drawing state """
    pass  # Dummy method for linter

def push():
    """Save the current drawing state and transformations """
    pass  # Dummy method for linter

def pop():
    """Restore the previously pushed drawing state and transformations """
    pass  # Dummy method for linter

def translate(*args):
    """Translate by specifying ~x~ and ~y~ offset.

Arguments:

- The offset can be specified as an array/list (e.g ~translate([x,y])~
  or as single arguments (e.g. ~translate(x, y)~) """
    pass  # Dummy method for linter

def scale(*args):
    """Apply a scaling transformation.

Arguments:

- Providing a single number will apply a uniform transformation.
- Providing a pair of number will scale in the x and y directions.
- The scale can be specified as an array/list (e.g ~scale([x,y])~
or as single arguments (e.g. ~scale(x, y)~)''' """
    pass  # Dummy method for linter

def rotate(*args):
    """Rotate by ~theta~ radians """
    pass  # Dummy method for linter

def apply_matrix(*args):
    """Apply an affine (3x3) transformation matrix """
    pass  # Dummy method for linter

def rotate_deg(*args):
    """Rotate using degrees """
    pass  # Dummy method for linter

def hsv(*args):
    pass  # Dummy method for linter

def rect_mode(*args):
    """Set the "mode" for drawing rectangles.

Arguments:
- ~mode~ (string): can be one of 'corner', 'corners', 'center', 'radius' """
    pass  # Dummy method for linter

def ellipse_mode(*args):
    """Set the "mode" for drawing rectangles.

Arguments:
- ~mode~ (string): can be one of 'corner', 'center' """
    pass  # Dummy method for linter

def rectangle(*args):
    """Draw a rectangle.
Can use ~rect~ equivalently.

Arguments:
The first sequence of arguments is one of

 - ~[x, y], [width, height]~,
 - ~[x, y], width, height~,
 - ~x, y, width, height~
 - ~[[topleft_x, topleft_y], [bottomright_x, bottomright_y]]~

The last option will ignore the rect mode since it explictly defines the corners of the rect

The interpretation of ~x~ and ~y~ depends on the current rect mode. These indicate the
center of the rectangle if the rect mode is ~"center"~ and the top left corner otherwise. """
    pass  # Dummy method for linter

def square(*args):
    """Draw a square.

Arguments:

The first sequence of arguments is one of
 - ~[x, y], size~,
 - ~x, y, size~

The interpretation of ~x~ and ~y~ depends on the current rect mode. These indicate the
center of the rectangle if the rect mode is ~"center"~ and the top left corner otherwise. """
    pass  # Dummy method for linter

def rect(*args):
    """Draws a rectangle.

Input arguments can be in the following formats:

 - ~[topleft_x, topleft_y], [width, height]~,
 - ~[topleft_x, topleft_y], width, height~,
 - ~topleft_x, topleft_y, width, height~

Depending on """
    pass  # Dummy method for linter

def quad(*args):
    """Draws a quadrangle given four points

Input arguments can be in the following formats:

 - ~a, b, c, d~ (Four points specified as lists/tuples/numpy arrays
 - ~x1, y1, x2, y2, x3, y3, x4, y4~, a sequence of numbers, one for each coordinate """
    pass  # Dummy method for linter

def line(*args):
    """Draws a line between two points

Input arguments can be in the following formats:

 - ~a, b~ (Two points specified as lists/tuples/numpy arrays
 - ~x1, y1, x2, y2~, a sequence of numbers, one for each coordinate """
    pass  # Dummy method for linter

def point(*args):
    """Draw a point at a given position

Input arguments can be in the following formats:

 - ~[x, y]~: a single point specified as a tuple/list/numpy array
 - ~x1, y1~: two coordinates """
    pass  # Dummy method for linter

def arrow(*args):
    """Draw an arrow between two points

Input arguments can be in the following formats:

 - ~a, b~ (Two points specified as lists/tuples/numpy arrays
 - ~x1, y1, x2, y2~, a sequence of numbers, one for each coordinate """
    pass  # Dummy method for linter

def triangle(*args):
    """Draws a triangle given three points

Input arguments can be in the following formats:

 - ~a, b, c~ (Four points specified as lists/tuples/numpy arrays
 - ~x1, y1, x2, y2, x3, y3~ """
    pass  # Dummy method for linter

def circle(*args):
    """Draw a circle given center and radius

Input arguments can be in the following formats:

- ~[center_x, center_y], radius~,
- ~center_x, center_y, raidus~ """
    pass  # Dummy method for linter

def ellipse(*args):
    """Draw an ellipse with center, width and height.

Input arguments can be in the following formats:

- ~[center_x, center_y], [width, height]~,
- ~[center_x, center_y], width, height~,
- ~center_x, center_y, width, height~ """
    pass  # Dummy method for linter

def arc(*args):
    """Draw an arc given the center of the ellipse ~x, y~
the size of the ellipse ~w, h~ and the initial and final angles
in radians  ~start, stop~.
NB. this differs from Processing/P5js as it always draws

Input arguments can be in the following formats:

  - ~x, y, w, h, start, stop~
  - ~[x, y]~, ~[w, h]~, ~[start, stop]~
  - ~[x, y]~, ~w, h, start, stop~ """
    pass  # Dummy method for linter

def clear_segments():
    pass  # Dummy method for linter

def begin_shape():
    """Begin drawing a compound shape """
    pass  # Dummy method for linter

def end_shape(*args):
    """End drawing a compound shape """
    pass  # Dummy method for linter

def begin_contour():
    """Begin drawing a contour """
    pass  # Dummy method for linter

def end_contour(*args):
    """End drawing a contour

Arguments:

- ~close~ (bool, optional): if ~True~ close the contour """
    pass  # Dummy method for linter

def vertex(*args):
    """Add a vertex to current contour

Input arguments can be in the following formats:

- ~[x, y]~
- ~x, y~ """
    pass  # Dummy method for linter

def curve_vertex(*args):
    """Add a curved vertex to current contour

Input arguments can be in the following formats:

- ~[x, y]~
- ~x, y~ """
    pass  # Dummy method for linter

def bezier_vertex(*args):
    """Draw a cubic Bezier segment from the current point
requires a first control point to be already defined with ~vertex~.


Requires three points. Input arguments can be in the following formats:

- ~[x1, y1], [x2, y2], [x3, y3]~
- ~x1, y1, x2, y2, x3, y3~ """
    pass  # Dummy method for linter

def curve_tightness(*args):
    """Sets the 'tension' parameter for the curve used when using ~curve_vertex~
         """
    pass  # Dummy method for linter

def cubic(*args):
    """Draw a cubic bezier curve

Input arguments can be in the following formats:

- ~[x1, y1], [x2, y2], [x3, y3]~
- ~x1, y1, x2, y2, x3, y3~ """
    pass  # Dummy method for linter

def quadratic(*args):
    """Draw a quadratic bezier curve

Input arguments can be in the following formats:

-    ~[x1, y1], [x2, y2]~
-    ~x1, y1, x2, y2~ """
    pass  # Dummy method for linter

def bezier(*args):
    """Draws a bezier curve segment from current point
    The degree of the curve (2 or 3) depends on the input arguments
Arguments:
Input arguments can be in the following formats:
    ~[x1, y1], [x2, y2], [x3, y3]~ is cubic
    ~x1, y1, x2, y2, x3, y3~ is cubic
    ~[x1, y1], [x2, y2]~ is quadratic
    ~x1, y1, x2, y2~ is quadratic """
    pass  # Dummy method for linter

def create_graphics(*args):
    """Create a new canvas with the specified width and height
E.g. ~c = create_graphics(128, 128)~ will put a new canvas into
the variable ~c~. You can draw the contents of the canvas with the ~image~ function. """
    pass  # Dummy method for linter

def image(*args):
    """Draw an image at position with (optional) size and (optional) opacity

Arguments:

- ~img~: The input image. Can be either a PIL image, a numpy array, a Canvas or a pyCairo surface.
- optional arguments: position and size can be specified with the following formats:
    - ~x, y~:  position only
    - ~x, y, w, h~: position and size
    - ~[x, y]~: position only (also a numpy array or tuple are valid)
    - ~[x, y], [w, h]~: position and size
if the position is not specified, the original image dimensions will be used

- ~opacity~: a value between 0 and 1 specifying image opacity. """
    pass  # Dummy method for linter

def shape(*args):
    """Draw a shape represented as a list of polylines, see the ~polyline~
method for the format of each polyline """
    pass  # Dummy method for linter

def text(*args):
    """Draw text at a given position

Arguments:

    - ~text`, the text to display
    - the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
    - ~align~, horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
    - ~valign~, vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~
    (Deprecated) if center=True the text will be horizontally centered """
    pass  # Dummy method for linter

def text_shape(*args):
    """Retrieves polylines for a given string of text in the current font

Arguments:

- ~text`, the text to sample
- the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
- ~dist~, approximate distance between samples
- ~align~, horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
- ~valign~, vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~ """
    pass  # Dummy method for linter

def text_points(*args):
    """Retrieves points for a given string of text in the current font

Arguments:

- ~text`, the text to sample
- the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
- ~dist~, approximate distance between samples
- ~align~ (named), horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
- ~valign~ (named), vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~ """
    pass  # Dummy method for linter

def text_bounds(*args):
    """Returns the bounding box of a string of text at a given position """
    pass  # Dummy method for linter

def polygon(*args):
    """Draw a polygon (closed by default).

The polyline is specified as either:

- a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
- a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To create an opne polygon set the named ~close~ argument to ~False~, e.g. ~c.polygon(points, close=False)~. """
    pass  # Dummy method for linter

def curve(*args):
    """Draw a curve (open by default).

The polyline is specified as either:

- a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
- a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To close the curve set the named ~close~ argument to ~True~, e.g. ~c.curve(points, close=True)~. """
    pass  # Dummy method for linter

def polyline(*args):
    """Draw a polyline (open by default).

The polyline is specified as either:

- a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
- a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To close the polyline set the named ~close~ argument to ~True~, e.g. ~c.polyline(points, close=True)~. """
    pass  # Dummy method for linter

def identity():
    pass  # Dummy method for linter

def copy(*args):
    """The first parameter can optionally be an image, if an image is not specified the funtion will use
the canvas image, .
The next four parameters, sx, sy, sw, and sh determine the region to copy from the source image.
(sx, sy) is the top-left corner of the region. sw and sh are the region's width and height.
The next four parameters, dx, dy, dw, and dh determine the region of the canvas to copy into.
(dx, dy) is the top-left corner of the region. dw and dh are the region's width and height.

~copy(src_image, sx, sy, sw, sh, dx, dy, dw, dh)~
or
~copy(sx, sy, sw, sh, dx, dy, dw, dh)~ """
    pass  # Dummy method for linter

def background(*args):
    """Clear the canvas with a given color
Accepts either an array with the color components, or single color components (as in ~fill~) """
    pass  # Dummy method for linter

def get_buffer():
    pass  # Dummy method for linter

def get_image():
    """Get canvas image as a numpy array  """
    pass  # Dummy method for linter

def get_image_grayscale():
    """Returns the canvas image as a grayscale numpy array (in 0-1 range) """
    pass  # Dummy method for linter

def save_image(*args):
    """Save the canvas to an image

Arguments:

- The path where to save """
    pass  # Dummy method for linter

def save_svg(*args):
    """Save the canvas to an svg file

Arguments:

- The path where to save """
    pass  # Dummy method for linter

def save_pdf(*args):
    """Save the canvas to an svg file

Arguments:

- The path where to save """
    pass  # Dummy method for linter

def Image():
    pass  # Dummy method for linter

def save(*args):
    """Save the canvas into a given file path
The file format depends on the file extension """
    pass  # Dummy method for linter

def show(*args):
    """Display the canvas in a notebook """
    pass  # Dummy method for linter

def show_plt(*args):
    """Show the canvas in a notebook with matplotlib

Arguments:

- ~size~ (tuple, optional): The size of the displayed image, by default this is the size of the canvas
- ~title~ (string, optional): A title for the figure
- ~axis~ (bool, optional): If ~True~ shows the coordinate axes """
    pass  # Dummy method for linter

mouse_x = 'The horizontal coordinate of the mouse position'

mouse_y = 'The vertical coordinate of the mouse position'

frame_count = 'The number of frames since the script has loaded'

dragging = 'Returns ~True~ if mouse is pressed'

mouse_is_pressed = 'Returns ~True~ if mouse is pressed'

delta_time = ''

def has_error():
    pass  # Dummy method for linter

def open_file_dialog(*args):
    """Opens a dialog to select a file to be opened,
the first argument is the extension or the file to be opened,
e.g. ~'png'~ or a list of extensions, e.g. ~['png', 'jpg']

The function returns the path of the file if it is selected or an empty string othewise. """
    pass  # Dummy method for linter

def save_file_dialog(*args):
    """Opens a dialog to select a file to be saved,
the first argument is the extension or the file to be saved,
e.g. ~'png'~ or a list of extensions, e.g. ~['png', 'jpg']

The function returns the path of the file if it is selected or an empty string othewise. """
    pass  # Dummy method for linter

def open_folder_dialog(*args):
    """Opens a dialog to select a folder/directory to be opened,

The function returns the path of the directory if it is selected or an empty string othewise. """
    pass  # Dummy method for linter

def create_canvas(*args):
    pass  # Dummy method for linter

current_canvas = ''

canvas_display_width = ''

canvas_display_height = ''

def create_canvas_gui(*args):
    pass  # Dummy method for linter

def get_pixel_ratio():
    pass  # Dummy method for linter

def save_canvas(*args):
    """Tells the sketch to dump the next frame to an SVG file  """
    pass  # Dummy method for linter

def toggle_gui(*args):
    """Toggle between GUI and non-gui """
    pass  # Dummy method for linter

def show_gui(*args):
    pass  # Dummy method for linter

def toggle_fullscreen(*args):
    """Toggle between fullscreen and windowed mode """
    pass  # Dummy method for linter

def fullscreen(*args):
    """Sets fullscreen or windowed mode depending on the first argument (~True~ or ~False~)
         """
    pass  # Dummy method for linter

def no_loop():
    """Stops the drawing loop keeping the last frame fixed on the canvas """
    pass  # Dummy method for linter

def set_gui_theme(*args):
    pass  # Dummy method for linter

def set_gui_callback(*args):
    pass  # Dummy method for linter

def load(*args):
    pass  # Dummy method for linter

def grab_image_sequence(*args):
    """Saves a sequence of image files to a directory, one for each frame.
By default this will reload the current script.

Arguments:
- ~path~ (string), the directory where to save the images
- ~num_frames~ (int), the number of frames to save """
    pass  # Dummy method for linter

def grab_movie(*args):
    """Saves a mp4 movie from a number of frames to a specified path.
By default this will reload the current script.

Arguments:
- ~path~ (string), the directory where to save the video
- ~num_frames~ (int), the number of frames to save """
    pass  # Dummy method for linter

def stop_grabbing():
    pass  # Dummy method for linter

def finalize_grab():
    pass  # Dummy method for linter

def grab():
    pass  # Dummy method for linter

def reload(*args):
    pass  # Dummy method for linter

def update_globals():
    pass  # Dummy method for linter

def check_reload():
    pass  # Dummy method for linter

def frame(*args):
    pass  # Dummy method for linter

def title(*args):
    """Sets the title of the sketch window """
    pass  # Dummy method for linter

def frame_rate(*args):
    """Set the framerate of the sketch in frames-per-second """
    pass  # Dummy method for linter

def start_osc():
    pass  # Dummy method for linter

def send_osc(*args):
    """Send an OSC message """
    pass  # Dummy method for linter

def cleanup():
    pass  # Dummy method for linter

