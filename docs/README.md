
# Canvas API
Defines a drawing canvas (pyCairo) that behaves similarly to p5js

Constructor arguments:

- `width` : (`int`), width of the canvas in pixels
- `height` : (`int`), height of the canvas in pixels
- `clear_callback` (optional): function, a callback to be called when the canvas is cleared (for internal use mostly)

In a notebook you can create a canvas globally with either of:

- `size(width, height)`
- `create_canvas(width, height)`

When using these functions all the canvas functionalities below will become globally available to the notebook.

## Properties
### `center`
The center of the canvas (as a 2d numpy array)

### `width`
The width of canvas

### `height`
The height of canvas

## Methods
### `set_color_scale(...)`
Set color scale:

Arguments:

- `scale` (float): the color scale. if we want to specify colors in the `0...255` range,
 `scale` will be `255`. If we want to specify colors in the `0...1` range, `scale` will be `1`

### `get_width()`
The width of canvas

### `get_height()`
The height of canvas

### `no_fill()`
Do not fill subsequent shapes

### `no_stroke()`
Do not stroke subsequent shapes

### `fill_rule(...)`
Sets the fill rule

### `color_mode(...)`
Set the color mode for the canvas
- `mode` (string): can be one of 'rgb', 'hsv' depending on the desired color mode
- `scale` (float): the scale for the color values (e.g. 255 for 0...255 range, 1 for 0...1 range)
- `*args`: color values in the current color mode

Examples:

- `color_mode('rgb', 1.0)` will set the color mode to RGB in the 0-1 range.

Returns:

- (float): red component value in the current color scale
 

### `red(...)`
Return the red component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): red component value in the current color scale

### `green(...)`
Return the green component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): green component value in the current color scale

### `blue(...)`
Return the blue component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): blue component value in the current color scale

### `hue(...)`
Return the hue component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): hue component value in the current color scale

### `saturation(...)`
Return the saturation component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): saturation component value in the current color scale

### `lightness(...)`
Return the lightness component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): lightness component value in the current color scale

### `brightness(...)`
Return the brightness component of a color.

Arguments:

- `*args`: color values in the current color mode

Returns:

- (float): brightness component value in the current color scale

### `fill(...)`
Set the color of the current fill

Arguments:

- A single argument specifies a grayscale value, e.g `fill(128)` will fill with 50% gray.
- Two arguments specify grayscale with opacity, e.g. `fill(255, 128)` will fill with transparent white.
- Three arguments specify a color depending on the color mode (rgb or hsv)
- Four arguments specify a color with opacity

### `linear_gradient(...)`
Create a linear gradient fill.

Can be called in two ways:
    `linear_gradient(x1, y1, x2, y2, stop1, stop2, ...)`
    `linear_gradient((x1, y1), (x2, y2), stop1, stop2, ...)`

Each stop is a tuple:
   `(offset, color)`
where:
    - offset is between 0 and 1
    - color is a tuple (r, g, b[, a]) in current color mode

Example:
```
    fill(linear_gradient(0, 0, 200, 0,
                        (0, (1, 0, 0)),
                        (1, (0, 0, 1))))
```

### `radial_gradient(...)`
Create a radial gradient fill.

Can be called in two ways:
    `radial_gradient(cx0, cy0, r0, cx1, cy1, r1, stop1, stop2, ...)`
    `radial_gradient((cx0, cy0, r0), (cx1, cy1, r1), stop1, stop2, ...)`

- (cx0, cy0, r0): center and radius of the inner circle
- (cx1, cy1, r1): center and radius of the outer circle

Each stop is a tuple:
    (offset, color)
where:
    - offset is between 0 and 1
    - color is a tuple (r, g, b[, a]) in current color mode

Example:
```
    fill(radial_gradient((100, 100, 0), (100, 100, 80),
                        (0, (1, 1, 1)),
                        (1, (0, 0, 0))))
```

### `stroke(...)`
Set the color of the current stroke

Arguments:
- A single argument specifies a grayscale value, e.g. `stroke(255)` will set the stroke to white.
- Two arguments specify grayscale with opacity, e.g. `stroke(0, 128)` will set the stroke to black with 50% opacity.
- Three arguments specify a color depending on the color mode (rgb or hsv), e.g. `stroke(255, 0, 0)` will set the stroke to red, when the color mode is RGB
- Four arguments specify a color with opacity

### `stroke_weight(...)`
Set the line width

Arguments:
- The width in pixel of the stroke

### `stroke_join(...)`
Specify the 'join' mode for polylines.

Arguments:

- `join` (string): can be one of "miter", "bevel" or "round"

### `blend_mode(...)`
Specify the blending mode

Arguments:

- `mode` (string) can be a one of the blend mode constants:
    - `BLEND = "over"` (default) - Source overwrites canvas
    - `REPLACE = "source"` - Source completely replaces canvas
    - `ADD = "add"` - Source colors added to canvas
    - `MULTIPLY = "multiply"` - Colors multiplied (always darker)
    - `SCREEN = "screen"` - Colors inverted, multiplied, then inverted (always lighter)
    - `OVERLAY = "overlay"` - MULTIPLY for dark areas, SCREEN for light areas
    - `DARKEST = "darken"` - Keeps the darker color value
    - `LIGHTEST = "lighten"` - Keeps the lighter color value
    - `DIFFERENCE = "difference"` - Canvas minus source (absolute value)
    - `EXCLUSION = "exclusion"` - Similar to DIFFERENCE but lower contrast
    - `HARD_LIGHT = "hard_light"` - Like OVERLAY but based on source brightness
    - `SOFT_LIGHT = "soft_light"` - Softer version of HARD_LIGHT
    - `DODGE = "color_dodge"` - Lightens and increases contrast
    - `BURN = "color_burn"` - Darkens and increases contrast
    - `REMOVE = "clear"` - Overlapping pixels become transparent

  or a string, one of: "clear", "source", "over", "in", "out", "atop",
  "dest", "dest_over", "dest_in", "dest_out", "dest_atop", "xor", "add", "saturate", "multiply", "screen", "overlay", "darken", "lighten", "color_dodge", "color_burn", "hard_light", "soft_light", "difference", "exclusion", "hsl_hue", "hsl_saturation", "hsl_color", "hsl_luminosity".
  See [Cairo Graphics Operators](https://www.cairographics.org/operators/) for a discussion on the different operators.

### `stroke_cap(...)`
Specify the 'cap' for lines.

Arguments:

- `cap` (string): can be one of "butt", "round" or "square"

### `text_align(...)`
Specify the text alignment.

Arguments:
- `halign` (string): Horizontal alignment. One of "left", "center" or "right"
- `valign` (string): Horizontal alignment. One of "baseline" (default), "top", "bottom", or "center"

### `text_size(...)`
Specify the text size

N.B. this will also reset the text leading

Arguments:

- `size` (int): the text size

### `text_leading(...)`
Specify the space between consecutive lines of text
if no arguments are specified, returns the text leading values.

Arguments:

- `leading` (int, optional): the text leading

### `text_font(...)`
Specify the font to use for text rendering.

Arguments:

- `font` (string or object): Either a string describing the font file path or system font name, or a font object (created with `create_font`)

### `text_style(...)`
Specify the style (normal, italic, bold, bolditalic) to use for text
rendering.

Arguments:
- `style` (string): the name of a style ("normal", "italic", "bold",
"bolditalic")

### `push_matrix()`
Save the current transformation

### `pop_matrix()`
Restore the previous transformation

### `push_style()`
Save the current drawing state

### `pop_style()`
Restore the previously pushed drawing state

### `push()`
Save the current drawing state and transformations

### `pop()`
Restore the previously pushed drawing state and transformations

### `translate(...)`
Translate by specifying `x` and `y` offset.

Arguments:

- The offset can be specified as an array/list (e.g `translate([x,y])`
  or as single arguments (e.g. `translate(x, y)`)

### `scale(...)`
Apply a scaling transformation.

Arguments:

- Providing a single number will apply a uniform transformation.
- Providing a pair of number will scale in the x and y directions.
- The scale can be specified as an array/list (e.g `scale([x,y])`
or as single arguments (e.g. `scale(x, y)`)'''

### `rotate(...)`
Rotate by `theta` radians (or degrees, depeending on the angle mode)

### `apply_matrix(...)`
Apply an affine (3x3) transformation matrix

### `get_origin()`
Get the origin in canvas coordinates for the current transformation.
Returns a 2d numpy array

### `rotate_deg(...)`
Rotate using degrees

### `hsb(...)`
Return RGB components for a color defined as HSB

### `rgb(...)`
Return HSV components for a color defined as RGB

### `rect_mode(...)`
Set the "mode" for drawing rectangles.

Arguments:
- `mode` (string): can be one of 'corner', 'corners', 'center', 'radius'

### `ellipse_mode(...)`
Set the "mode" for drawing rectangles.

Arguments:
- `mode` (string): can be one of 'corner', 'center'

### `rectangle(...)`
Draw a rectangle.
Can use `rect` equivalently.

Arguments:
The first sequence of arguments is one of

 - `[x, y], [width, height]`,
 - `[x, y], width, height`,
 - `x, y, width, height`
 - `[[topleft_x, topleft_y], [bottomright_x, bottomright_y]]`

Followed by an optional radius parameter that can be used to create rounded rectangles

An optional named `mode` argument allows to ignore the current rect mode since it explictly defines the
corners of the rect

The interpretation of `x` and `y` depends on the current rect mode.
These indicate the center of the rectangle if the rect mode is
`"center"` or `"radius"` and the top-left corner otherwise.

### `square(...)`
Draw a square.

Arguments:

The first sequence of arguments is one of
 - `[x, y], size`,
 - `x, y, size`

The interpretation of `x` and `y` depends on the current rect mode. These indicate the
center of the rectangle if the rect mode is `"center"` and the top left corner otherwise.

### `rect(...)`
Draws a rectangle.

Input arguments can be in the following formats:

 - `[topleft_x, topleft_y], [width, height]`,
 - `[topleft_x, topleft_y], width, height`,
 - `topleft_x, topleft_y, width, height`

Depending on

### `quad(...)`
Draws a quadrangle given four points

Input arguments can be in the following formats:

 - `a, b, c, d` (Four points specified as lists/tuples/numpy arrays
 - `x1, y1, x2, y2, x3, y3, x4, y4`, a sequence of numbers, one for each coordinate

### `line(...)`
Draws a line between two points

Input arguments can be in the following formats:

 - `a, b` (Two points specified as lists/tuples/numpy arrays
 - `x1, y1, x2, y2`, a sequence of numbers, one for each coordinate

### `point(...)`
Draw a point at a given position

Input arguments can be in the following formats:

 - `[x, y]`: a single point specified as a tuple/list/numpy array
 - `x1, y1`: two coordinates

### `arrow(...)`
Draw an arrow between two points

Input arguments can be in the following formats:

 - `a, b` (Two points specified as lists/tuples/numpy arrays
 - `x1, y1, x2, y2`, a sequence of numbers, one for each coordinate

### `triangle(...)`
Draws a triangle given three points

Input arguments can be in the following formats:

 - `a, b, c` (Four points specified as lists/tuples/numpy arrays
 - `x1, y1, x2, y2, x3, y3`

### `circle(...)`
Draw a circle given center and radius

Input arguments can be in the following formats:

- `[center_x, center_y], radius`,
- `center_x, center_y, raidus`

### `ellipse(...)`
Draw an ellipse with center, width and height.

Input arguments can be in the following formats:

- `[center_x, center_y], [width, height]`,
- `[center_x, center_y], width, height`,
- `center_x, center_y, width, height`
- `[center_x, center_y], width`,
- `center_x, center_y, width`,

### `arc(...)`
Draw an ellpitical arc, given the center of the ellipse `x, y`
the size of the ellipse `w, h` and the initial and final angles
in radians  `start, stop`.
A last optional `mode` argument determines the arc's fill style.
The fill modes are a semi-circle (`OPEN`), a closed semi-circle (`CHORD`),
or a closed pie segment (`PIE`).

Input arguments can be in the following formats:

  - `x, y, w, h, start, stop`
  - `[x, y]`, `[w, h]`, `[start, stop]`
  - `[x, y]`, `w, h, start, stop`

### `begin_shape()`
Begin drawing a compound shape

### `end_shape(...)`
End drawing a compound shape

### `begin_contour()`
Begin drawing a contour

### `end_contour(...)`
End drawing a contour

Arguments:

- `close` (bool, optional): if `True` close the contour

### `vertex(...)`
Add a vertex to current contour

Input arguments can be in the following formats:

- `[x, y]`
- `x, y`

### `curve_vertex(...)`
Add a curved vertex to current contour

Input arguments can be in the following formats:

- `[x, y]`
- `x, y`

### `bezier_vertex(...)`
Draw a cubic Bezier segment from the current point
requires a first control point to be already defined with `vertex`.


Requires three points. Input arguments can be in the following formats:

- `[x1, y1], [x2, y2], [x3, y3]`
- `x1, y1, x2, y2, x3, y3`

### `curve_tightness(...)`
Sets the 'tension' parameter for the curve used when using `curve_vertex`

### `cubic(...)`
Draw a cubic bezier curve

Input arguments can be in the following formats:

- `[x1, y1], [x2, y2], [x3, y3]`
- `x1, y1, x2, y2, x3, y3`

### `quadratic(...)`
Draw a quadratic bezier curve

Input arguments can be in the following formats:

-    `[x1, y1], [x2, y2]`
-    `x1, y1, x2, y2`

### `bezier(...)`
Draws a bezier curve segment from current point
    The degree of the curve (2 or 3) depends on the input arguments
Arguments:
Input arguments can be in the following formats:
    `[x1, y1], [x2, y2], [x3, y3]` is cubic
    `x1, y1, x2, y2, x3, y3` is cubic
    `[x1, y1], [x2, y2]` is quadratic
    `x1, y1, x2, y2` is quadratic

### `create_graphics(...)`
Create a new canvas with the specified width and height
E.g. `c = create_graphics(128, 128)` will put a new canvas into
the variable `c`. You can draw the contents of the canvas with the `image` function.

### `image(...)`
Draw an image at position with (optional) size and (optional) opacity

Arguments:

- `img`: The input image. Can be either a PIL image, a numpy array, a Canvas or a pyCairo surface.
- optional arguments: position and size can be specified with the following formats:
    - `x, y`:  position only
    - `x, y, w, h`: position and size
    - `[x, y]`: position only (also a numpy array or tuple are valid)
    - `[x, y], [w, h]`: position and size
if the position is not specified, the original image dimensions will be used

- `opacity`: a value between 0 and 1 specifying image opacity.

### `shape(...)`
Draw a shape represented as a list of polylines, see the `polyline`
method for the format of each polyline. Also accepts a single polyline as an input

### `text(...)`
Draw text at a given position

Arguments:

    - `text`, the text to display
    - the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
    - `align`, horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
    - `valign`, vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`
    (Deprecated) if center=True the text will be horizontally centered

### `text_shape(...)`
Retrieves polylines for a given string of text in the current font

Arguments:

- `text`, the text to sample
- the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
- `dist`, approximate distance between samples
- `align`, horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
- `valign`, vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`

### `text_points(...)`
Retrieves points for a given string of text in the current font

Arguments:

- `text`, the text to sample
- the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
- `dist`, approximate distance between samples
- `align` (named), horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
- `valign` (named), vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`

### `text_bounds(...)`
Returns the bounding box of a string of text at a given position

### `polygon(...)`
Draw a polygon (closed by default).

The polyline is specified as either:

- a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
- a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To create an opne polygon set the named `close` argument to `False`, e.g. `c.polygon(points, close=False)`.

### `curve(...)`
Draw a curve (open by default).

The polyline is specified as either:

- a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
- a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To close the curve set the named `close` argument to `True`, e.g. `c.curve(points, close=True)`.

### `polyline(...)`
Draw a polyline (open by default).

The polyline is specified as either:

- a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
- a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)
- two lists (or numpy array) of numbers, one for each coordinate

To close the polyline set the named `close` argument to `True`, e.g. `c.polyline(points, close=True)`.

### `identity()`
Resets the current matrix to the identity (no transformation)

### `reset_matrix()`
Resets the current matrix to the identity (no transformation)

### `copy(...)`
The first parameter can optionally be an image, if an image is not specified the funtion will use
the canvas image, .
The next four parameters, sx, sy, sw, and sh determine the region to copy from the source image.
(sx, sy) is the top-left corner of the region. sw and sh are the region's width and height.
The next four parameters, dx, dy, dw, and dh determine the region of the canvas to copy into.
(dx, dy) is the top-left corner of the region. dw and dh are the region's width and height.

`copy(src_image, sx, sy, sw, sh, dx, dy, dw, dh)`
or
`copy(sx, sy, sw, sh, dx, dy, dw, dh)`

### `background(...)`
Clear the canvas with a given color
Accepts either an array with the color components, or single color components (as in `fill`)

### `get_image_array()`
Get canvas image as a numpy array

### `get_grayscale_array()`
Get grayscale image of canvas contents as float numpy array (0 to 1 range)

### `get_image()`
Get canvas as a PIL image

### `get_image_grayscale()`
Returns the canvas image as a grayscale numpy array (in 0-1 range)

### `save_image(...)`
Save the canvas to an image

Arguments:

- The path where to save

### `save_svg(...)`
Save the canvas to an svg file

Arguments:

- The path where to save

### `save_pdf(...)`
Save the canvas to an svg file

Arguments:

- The path where to save

### `save(...)`
Save the canvas into a given file path
The file format depends on the file extension

### `show(...)`
Display the canvas in a notebook

### `show_plt(...)`
Show the canvas in a notebook with matplotlib

Arguments:

- `size` (tuple, optional): The size of the displayed image, by default this is the size of the canvas
- `title` (string, optional): A title for the figure
- `axis` (bool, optional): If `True` shows the coordinate axes


# Interactive sketches
No class docstring available

## Properties

### `mouse_x`
The horizontal coordinate of the mouse position

### `mouse_y`
The vertical coordinate of the mouse position

### `frame_count`
The number of frames since the script has loaded

### `clicked`
Returns `True` if mouse was clicked

### `dragging`
Returns `True` if mouse is pressed

### `mouse_is_pressed`
Returns `True` if mouse is pressed

### `mouse_pos`
The current position of the mouse as an array

## Methods

### `millis()`
The number of milliseconds since the script has loaded

### `seconds()`
The number of seconds since the script has loaded

### `open_file_dialog(...)`
Opens a dialog to select a file.
exts: 'png' or ['png', 'jpg'] (extensions without dots)
Returns the selected path (str) or '' if cancelled.

### `save_file_dialog(...)`
Opens a dialog to select a file to be saved,
the first argument is the extension or the file to be saved,
e.g. `'png'` or a list of extensions, e.g. `['png', 'jpg']`

The function returns the path of the file if it is selected or an empty string othewise.

### `open_folder_dialog(...)`
Opens a dialog to select a folder/directory to be opened,

The function returns the path of the directory if it is selected or an empty string othewise.

### `save_canvas(...)`
Tells the sketch to dump the next frame to an SVG file 

### `toggle_gui(...)`
Toggle between GUI and non-gui

### `toggle_fullscreen(...)`
Toggle between fullscreen and windowed mode

### `set_floating(...)`
Sets the sketch windo to floating or not

### `fullscreen(...)`
Sets fullscreen or windowed mode depending on the first argument (`True` or `False`)
        

### `no_loop()`
Stops the drawing loop keeping the last frame fixed on the canvas

### `grab_image_sequence(...)`
Saves a sequence of image files to a directory, one for each frame.
By default this will reload the current script.

Arguments:
- `path` (string), the directory where to save the images
- `num_frames` (int), the number of frames to save
- `reload` (bool), whether to reload the sketch, default: True

### `grab_movie(...)`
Saves a mp4 movie from a number of frames to a specified path.
By default this will reload the current script.

Arguments:
- `path` (string), the directory where to save the video
- `num_frames` (int), the number of frames to save, default: 0
- `framerate` (int), the framerate, default: 30
- `gamma` (float), the gamma correction, default: 1.0 (see the [OpenCV docs](https://docs.opencv.org/4.x/d3/dc1/tutorial_basic_linear_transform.html))
- `reload` (bool), whether to reload the sketch, default: True

### `update_globals()`
Inject globals that are not updated automatically

### `title(...)`
Sets the title of the sketch window

### `description(...)`
Set the description of the current sketch

### `frame_rate(...)`
Set the framerate of the sketch in frames-per-second

### `num_movie_frames(...)`
Set the number of frames to export when saving a video

### `send_osc(...)`
Send an OSC message

