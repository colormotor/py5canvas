
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


# Globals and constants

## Functions
### `random_gaussian(mean,std_dev,size)`
Draw random samples from a normal (Gaussian) distribution.
The probability density function of the normal distribution, first
derived by De Moivre and 200 years later by both Gauss and Laplace
independently [2]_, is often called the bell curve because of
its characteristic shape (see the example below).

### `random(low=0.0, high=1.0, size=None)`
Draw samples from a uniform distribution.
Samples are uniformly distributed over the half-open interval
``[low, high)`` (includes low, but excludes high).  In other words,
any value within the given interval is equally likely to be drawn
by `uniform`.


### `rand(low=0.0, high=1.0, size=None)`
Draw samples from a uniform distribution.
Samples are uniformly distributed over the half-open interval
``[low, high)`` (includes low, but excludes high).  In other words,
any value within the given interval is equally likely to be drawn
by `uniform`.


### `random_uniform(low=0.0, high=1.0, size=None)`
Draw samples from a uniform distribution.
Samples are uniformly distributed over the half-open interval
``[low, high)`` (includes low, but excludes high).  In other words,
any value within the given interval is equally likely to be drawn
by `uniform`.


### `random_choice(a, size=None, replace=True, p=None)`
Generates a random sample from a given 1-D array
.. versionadded:: 1.7.0


### `random_int(low, high=None, size=None, dtype=int)`
Return random integers from `low` (inclusive) to `high` (exclusive).
Return random integers from the "discrete uniform" distribution of
the specified dtype in the "half-open" interval [`low`, `high`). If
`high` is None (the default), then results are from [0, `low`).


### `random_normal(loc=0.0, scale=1.0, size=None)`
Draw random samples from a normal (Gaussian) distribution.
The probability density function of the normal distribution, first
derived by De Moivre and 200 years later by both Gauss and Laplace
independently [2]_, is often called the bell curve because of
its characteristic shape (see the example below).


### `random_seed(seed=None)`
Reseed the singleton RandomState instance.
Notes
-----
This is a convenience, legacy function that exists to support
older code that uses the singleton RandomState. Best practice
is to use a dedicated ``Generator`` instance rather than
the random variate generation methods exposed directly in
the random module.


### `randomseed(seed=None)`
Reseed the singleton RandomState instance.
Notes
-----
This is a convenience, legacy function that exists to support
older code that uses the singleton RandomState. Best practice
is to use a dedicated ``Generator`` instance rather than
the random variate generation methods exposed directly in
the random module.


### `radians(x)`
Get radians given an angle in degrees

### `degrees(x)`
Get degrees given an angle in radians

### `constrain(a, a_min, a_max, out=None, **kwargs)`
Given an interval, values outside the interval are clipped to
the interval edges.  For example, if an interval of ``[0, 1]``
is specified, values smaller than 0 become 0, and values larger
than 1 become 1.
Equivalent to but faster than ``np.minimum(a_max, np.maximum(a, a_min))``.


### `create_font(name, size=None, style=None)`
Create a font from a file or from system fonts
Arguments:

- `font` (string or object): Either a string describing the font file path or system font name

### `sin(x)`
Trigonometric sine, element-wise.


### `cos(x)`
Cosine element-wise.


### `tan(x)`
Compute tangent element-wise.
Equivalent to ``np.sin(x)/np.cos(x)`` element-wise.


### `atan2(x1, x2)`
Element-wise arc tangent of ``x1/x2`` choosing the quadrant correctly.
The quadrant (i.e., branch) is chosen so that ``arctan2(x1, x2)`` is
the signed angle in radians between the ray ending at the origin and
passing through the point (1,0), and the ray ending at the origin and
passing through the point (`x2`, `x1`).  (Note the role reversal: the
"`y`-coordinate" is the first function parameter, the "`x`-coordinate"
is the second.)  By IEEE convention, this function is defined for
`x2` = +/-0 and for either or both of `x1` and `x2` = +/-inf (see
Notes for specific values).


### `dot(a, b, out=None)`
Dot product of two arrays. Specifically,
- If both `a` and `b` are 1-D arrays, it is inner product of vectors
  (without complex conjugation).


### `exp(x)`
Calculate the exponential of all elements in the input array.


### `log(x)`
Natural logarithm, element-wise.
The natural logarithm `log` is the inverse of the exponential function,
so that `log(exp(x)) = x`. The natural logarithm is logarithm in base
`e`.


### `floor(x)`
Return the floor (int) of the input, element-wise.

### `ceil(x)`
Return the ceiling (int) of the input, element-wise.

### `round(x,decimals)`
Evenly round to the given number of decimals. Returns integers with `decimals=0` (default)

### `abs(x)`
Calculate the absolute value element-wise.
``np.abs`` is a shorthand for this function.


### `is_number(x)`


### `color(...)`
Create a cector with components specified as comma-separated values.
:returns: A NumPy array representing the specified color components.
This returns either a 3d (RGB) array if 3 or 1 (luminosity) components are specified,
or a 4d (RGBA) array if 4 or 2 components are specified.

### `Color(*args)`
Create a cector with components specified as comma-separated values.
:returns: A NumPy array representing the specified color components.
This returns either a 3d (RGB) array if 3 or 1 (luminosity) components are specified,
or a 4d (RGBA) array if 4 or 2 components are specified.

### `vector(...)`
Create a vector with components specified as comma-separated values
:returns: A NumPy array with the specified components

### `Vector(*args)`
Create a vector with components specified as comma-separated values
:returns: A NumPy array with the specified components

### `create_vector(...)`
Create a vector with components specified as comma-separated values
:returns: A NumPy array with the specified components

### `range_between(a,b,num,endpoint)`
Returns a list of numbers that goes from a and b in a specified number of steps.

E.g. ~range_between(0, 1, 5)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

Similar to ~np.linspace~

### `linspace(a,b,num,endpoint)`
Returns a list of numbers that goes from a and b in a specified number of steps.

E.g. ~linspace(0, 1, 5)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

Similar to ~np.linspace~

### `arange(a,b,step)`
Returns a list of numbers that goes from a and b with equal steps

E.g. ~arange(0, 1, 0.25)~ will give the list ~[0.0, 0.25, 0.5, 0.75, 1.0]~

Similar to ~np.linspace~

### `grid_points(x,y)`
Given two 1d arrays/lists of numbers representing the x and y axes,
return a sequence of points on a grid represented as a numpy array.
It can be useful to accelerate noise computations in vectorized form

### `angle_between(...)`
Angle between two vectors (2d) [-pi,pi]

### `rotate_vector(...)`
Rotate a 2D vector (x, y) by a given angle in radians.
Input can be two numbers ~x, y~ or a tuple/array, followed by the angle in radians

### `dist(...)`
Computes the (Euclidean) distance between two points

### `mag(...)`
Returns the magnitude (length) of a vector.
Accepts one vector as an argument or a sequenc of coordinates for each component of the vector

### `heading(...)`
Returns the heading (orientation) in radians of a 2d vector
    

### `direction(angle)`
Returns a vector with magnitude 1 and oriented according to an angle specified in radians

### `lerp(a,b,t)`
Linear interpolation between two values

### `remap(value,...)`
Re-maps a number from one range to another. 

### `to_array(v)`


### `to_image(ar)`


### `load_image(path)`
Load an image from disk. Actually returns a PIL image

### `bezier_point(...)`
Get a point along a bezier curve (cubic) given a parameter value

Arguments:
- Four points, specified either as a list of points, a sequence of four points, or a sequence of coordiantes
- ~t~ the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents

### `bezier_tangent(...)`
Get the tangent to a bezier curve (cubic) given a parameter value

Arguments:
- Four points, specified either as a list of points, a sequence of four points, or a sequence of coordiantes
- ~t~ the parameter at which to sample the curve. This can also be an array, in which case the result will be a list of tangents

### `noise_seed(seed)`
Sets the seed for the noise generator

### `noise_detail(octaves,falloff,lacunarity,gradient)`
Adjusts the character and level of detail produced by the Perlin noise function.

Arguments:

- `octaves` (int): the number of noise 'octaves'. Each octave has double the frequency of the previous.
- `falloff` (float, default 0.5): a number between 0 and 1 that multiplies the amplitude of each consectutive octave
- `lacunarity` (float, default 2.0): number that multiplies the frequency of each consectutive octave
- `gradient` (bool, default True): If true (default) `noise` uses gradient noise, otherwise it use value noise

### `noise(...)`
Returns noise (between 0 and 1) at a given coordinate or at multiple coordinates.
Noise is created by summing consecutive "octaves" with increasing level of detail.
By default this function returns "gradient noise", a variant of noise similar to Ken Perlin's original version.
Alternatively the function can return "value noise", which is a faster but more blocky version.
By default each octave has double the frequency (lacunarity) of the previous and an amplitude falls off for each octave. By default the falloff is 0.5.
The default number of octaves is `4`.

Use `noise_detail` to set the number of octaves and optionally falloff, lacunarity and whether to use gradient or value noise.

Arguments:

- The arguments to this function can vary from 1 to 3, determining the "space" that is sampled to generate noise.
The function also accepts numpy arrays for each coordinate but these must be of the same size.

### `noise_grid(...)`
Returns a 2d array of noise values (between 0 and 1).
The array can be treated as a grayscale image and is defined by two input 1d array parameters, x and y.
The number of elements in x and y define the number of columns and rows, respectively.
Optionally a third `z` parameter can be specified and it defines the depth of a "slice" in a 3d noise volume.

Arguments:

- The arguments to this function can be either two arrays, say
```python
img = noise_grid(np.linspace(0, width, 100),
                 np.linspace(0, height, 100))
```
or three, where the third parameter can be a scalar
```python
img = noise_grid(np.linspace(0, width, 100),
                 np.linspace(0, height, 100), 3.4)
```


## Constants
### `PI`
`3.141592653589793`

### `TWO_PI`
`6.283185307179586`

### `HALF_PI`
`1.5707963267948966`

### `QUARTER_PI`
`0.7853981633974483`

### `TAU`
`6.283185307179586`

### `RGB`
`'rgb'`

### `HSB`
`'hsv'`

### `HSV`
`'hsv'`

### `CENTER`
`'center'`

### `LEFT`
`'left'`

### `RIGHT`
`'right'`

### `CORNER`
`'corner'`

### `TOP`
`'top'`

### `BOTTOM`
`'bottom'`

### `BASELINE`
`'baseline'`

### `RADIUS`
`'radius'`

### `CLOSE`
`'close'`

### `OPEN`
`'OPEN'`

### `CHORD`
`'chord'`

### `PIE`
`'pie'`

### `MITER`
`'miter'`

### `BEVEL`
`'bevel'`

### `ROUND`
`'round'`

### `SQUARE`
`'square'`

### `PROJECT`
`'project'`

### `DEGREES`
`'degrees'`

### `RADIANS`
`'radians'`

### `BLEND`
`'over'`

### `REPLACE`
`'source'`

### `ADD`
`'add'`

### `MULTIPLY`
`'multiply'`

### `SCREEN`
`'screen'`

### `OVERLAY`
`'overlay'`

### `DARKEST`
`'darken'`

### `LIGHTEST`
`'lighten'`

### `DIFFERENCE`
`'difference'`

### `EXCLUSION`
`'exclusion'`

### `HARD_LIGHT`
`'hard_light'`

### `SOFT_LIGHT`
`'soft_light'`

### `DODGE`
`'color_dodge'`

### `BURN`
`'color_burn'`

### `REMOVE`
`'clear'`

### `SUBTRACT`
`'difference'`

### `dragging`
`None`

### `mouse_is_pressed`
`None`

### `mouse_button`
`None`

### `params`
`None`

