#!/usr/bin/env python3
"""
```
             eeeee
eeeee e    e 8     eeee eeeee eeeee ee   e eeeee eeeee
8   8 8    8 8eeee 8  8 8   8 8   8 88   8 8   8 8   "
8eee8 8eeee8     8 8e   8eee8 8e  8 88  e8 8eee8 8eeee
88      88       8 88   88  8 88  8  8  8  88  8    88
88      88   eeee8 88e8 88  8 88  8  8ee8  88  8 8ee88

```
Simplistic utilty to mimic [P5js](https://p5js.org) in Python/Jupyter notebooks.
© Daniel Berio (@colormotor) 2023 - ...

## Dependencies
This module depends on matplotlib, numpy and and pycairo.
To install these with conda do:
```
conda install -c conda-forge matplotlib
conda install -c conda-forge pycairo
```

When using Google Colab, matplotlib and numpy will already be installed. To
install pycairo add and execute the following in a code cell:
```
!apt-get install libcairo2-dev libjpeg-dev libgif-dev
!pip install pycairo
```

## Usage
Place the `canvas.py` file in the same directory as your notebook.
If using Google Colab fetch the latest version of the module with
```
!wget https://raw.githubusercontent.com/colormotor/DMLAP/main/python/canvas.py
```

## Example
The following is the conversion of a simple example in P5js to the `canvas` API.
In Javascript we may have:

```Javascript
function setup() {
  createCanvas(512, 512);
  // Clear background to black
  background(0);
  // Set stroke only and draw circle
  stroke(128);
  noFill();
  strokeWeight(5);
  circle(width/2, height/2, 200);
  // Draw red text
  fill(255, 0, 0);
  noStroke();
  textSize(30);
  textAlign(CENTER);
  text("Hello world", width/2, 40);
}

function draw() {
}
```

The equivalent Python version will be:

```Python
import canvas

# Create our canvas object
c = canvas.Canvas(512, 512)

# Clear background to black
c.background(0)
# Set stroke only and draw circle
c.stroke(128)
c.no_fill()
c.stroke_weight(5)
c.circle(c.width/2, c.height/2, 100)
# Draw red text
c.fill(255, 0, 0)
c.text_size(30)
c.text([c.width/2, 40], "Hello world", center=True)
c.show()
```
"""

#%%
import matplotlib.pyplot as plt
import numpy as np
import cairo
import numbers
import copy
from math import fmod, pi
import types
from PIL import Image

def is_number(x):
    return isinstance(x, numbers.Number)



def wrapper(self, fn):
    def result(*args, **kwargs):
        res = None
        self.dirty = True
        for ctx in self.ctxs: #[::-1]:
            res = getattr(ctx, fn)(*args, **kwargs)
        return res

    return result


class MultiContext:
    ''' Workaround for TeeSurface not working on Mac (at least)
    This should enable rendering to multiple surfaces (each with their own context)
    '''
    def __init__(self, surf):
        self.surface = surf
        self.dirty = False
        self.ctxs = [cairo.Context(surf)]
        for key, value in cairo.Context.__dict__.items( ):
            if hasattr( value, '__call__' ):
                self.__dict__[key] = wrapper(self, key)

    def push_context(self, ctx):
        self.ctxs.append(ctx)

    def pop_context(self):
        self.ctxs.pop()

class CanvasState:
    def __init__(self, c):
        self.cur_fill = c._convert_rgba([255.0])
        self.cur_stroke = None


class Canvas:
    """
    Creates a a pycairo surface that behaves similarly to p5js

    param width: int, width of the canvas in pixels
    param height: int, height of the canvas in pixels
    param clear_callback: function, a callback to be called when the canvas is cleared (for internal use mostly)
    """
    def __init__(self, width, height, background=(0.0, 0.0, 0.0, 255.0), clear_callback=lambda: None, output_file='', recording=True):
        """ Constructor"""
        # See https://pycairo.readthedocs.io/en/latest/reference/context.html
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = MultiContext(surf) #cairo.Context(surf)

        # Create SVG surface for saving
        self.color_scale = 255.0

        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD) #FILL_RULE_WINDING) #EVEN_ODD)
        ctx.set_line_join(cairo.LINE_JOIN_MITER)
        ctx.set_source_rgba(*background)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # This is useful for py5sketch to reset SVG each time background is cleared
        self.clear_callback = clear_callback

        self._color_mode = 'rgb'
        self._width = width
        self._height = height
        self.surf = surf
        self.ctx = ctx

        self.draw_states = [CanvasState(self)]

        # self.cur_fill = self._convert_rgba([255.0])
        # self.cur_stroke = None
        self._rect_mode = 'corner'

        self.no_draw = False

        self.ctx.select_font_face("sans-serif")
        self.ctx.set_font_size(16)
        self.line_cap('round')

        self.tension = 0.5

        # Constants
        self.PI = pi
        self.TWO_PI = pi*2
        self.HALF_PI = pi/2
        self.QUARTER_PI = pi/4

        # Utils
        self._cur_point = []

        self.output_file = output_file
        self.recording_surface = None
        if output_file or recording:
            self.recording_surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
            recording_context = cairo.Context(self.recording_surface)
            self.ctx.push_context(recording_context)
        else:
            print("Not creating recording context")

    def set_color_scale(self, scale):
        """Set color scale, e.g. if we want to specify colors in the `0`-`255` range, scale would be `255`,
        or if the colors are in the `0`-`1` range, scale will be `1`"""
        self.color_scale = scale

    def rect_mode(self, mode):
        """ Set the mode for drawing rectangles.
        param mode: string, can be one of 'corner', 'center', 'radius'
        """
        if mode not in ['corner', 'center', 'radius']:
            print('rect_mode: invalid mode')
            print('choose one among: corner, center, radius')
            return
        self._rect_mode = mode

    @property
    def cur_fill(self):
        return self.draw_states[-1].cur_fill
    @cur_fill.setter
    def cur_fill(self, value):
        self.draw_states[-1].cur_fill = value

    @property
    def cur_stroke(self):
        return self.draw_states[-1].cur_stroke
    @cur_stroke.setter
    def cur_stroke(self, value):
        self.draw_states[-1].cur_stroke = value

    def get_stroke_or_fill_color(self):
        """
        Get the current stroke color if set, the fill color otherwise
        returns the current stroke or fill color as a numpy array, or None if no color is set
        """
        if self.cur_stroke is not None:
            return np.array(self.cur_stroke)*self.color_scale
        if self.cur_fill is not None:
            return np.array(self.cur_fill)*self.color_scale
        return None #self.cur_fill

    @property
    def center(self):
        """ Center of the canvas"""
        return np.array([self._width/2,
                         self._height/2])

    @property
    def width(self):
        """ Width of canvas"""
        return self._width

    @property
    def height(self):
        """ Height of canvas"""
        return self._height

    @property
    def surface(self):
        return self.surf

    def no_fill(self):
        self.fill(None)

    def no_stroke(self):
        self.stroke(None)

    def color_mode(self, mode, scale=None):
        """ Set the color mode for the canvas

        param mode: string, can be one of 'rgb', 'hsv'
        param scale: float, the scale for the color values (e.g. 255 for 0-255 range, 1 for 0-1 range)
        """
        self._color_mode = mode
        if scale is not None:
            self.color_scale = scale

    def _apply_colormode(self, clr):
        if self._color_mode == 'hsv':
            return hsv_to_rgb(clr)
        return clr

    def fill(self, *args):
        if args[0] is None:
            self.cur_fill = None
        else:
            self.cur_fill = self._apply_colormode(self._convert_rgba(args))

    def stroke(self, *args):
        if args[0] is None:
            self.cur_stroke = None
        else:
            self.cur_stroke = self._apply_colormode(self._convert_rgba(args))

    def stroke_weight(self, w):
        """Set the line width"""
        self.ctx.set_line_width(w)

    def line_join(self, join):
        """Specify the 'join' for polylines.
        Args:
        join (string): can be one of "miter", "bevel" or "round"
        """
        joins = {'miter': cairo.LINE_JOIN_MITER,
                'bevel': cairo.LINE_JOIN_BEVEL,
                'round': cairo.LINE_CAP_ROUND}
        if join not in joins:
            print(str(join) + ' not a valid line join')
            print('Choose one of ' + str(joins.keys()))
            return

        self.ctx.set_line_join(joins[join])

    def blend_mode(self, mode="over"):
        blend_modes = {
            "clear": cairo.OPERATOR_CLEAR,
            "source": cairo.OPERATOR_SOURCE,
            "over": cairo.OPERATOR_OVER,  # This is the default blend mode
            "in": cairo.OPERATOR_IN,
            "out": cairo.OPERATOR_OUT,
            "atop": cairo.OPERATOR_ATOP,
            "dest": cairo.OPERATOR_DEST,
            "dest_over": cairo.OPERATOR_DEST_OVER,
            "dest_in": cairo.OPERATOR_DEST_IN,
            "dest_out": cairo.OPERATOR_DEST_OUT,
            "dest_atop": cairo.OPERATOR_DEST_ATOP,
            "xor": cairo.OPERATOR_XOR,
            "add": cairo.OPERATOR_ADD,
            "saturate": cairo.OPERATOR_SATURATE,
            "multiply": cairo.OPERATOR_MULTIPLY,
            "screen": cairo.OPERATOR_SCREEN,
            "overlay": cairo.OPERATOR_OVERLAY,
            "darken": cairo.OPERATOR_DARKEN,
            "lighten": cairo.OPERATOR_LIGHTEN,
            "color_dodge": cairo.OPERATOR_COLOR_DODGE,
            "color_burn": cairo.OPERATOR_COLOR_BURN,
            "hard_light": cairo.OPERATOR_HARD_LIGHT,
            "soft_light": cairo.OPERATOR_SOFT_LIGHT,
            "difference": cairo.OPERATOR_DIFFERENCE,
            "exclusion": cairo.OPERATOR_EXCLUSION,
            "hsl_hue": cairo.OPERATOR_HSL_HUE,
            "hsl_saturation": cairo.OPERATOR_HSL_SATURATION,
            "hsl_color": cairo.OPERATOR_HSL_COLOR,
            "hsl_luminosity": cairo.OPERATOR_HSL_LUMINOSITY
        }

        mode = mode.lower()

        # Set the blend mode if it exists in the dictionary
        if mode in blend_modes:
            self.ctx.set_operator(blend_modes[mode])
        else:
            raise ValueError(f"Invalid blend mode: {mode}")


    def line_cap(self, cap):
        """Specify the 'cap' for lines.
        Args:
        cap (string): can be one of "butt", "round" or "square"
        """
        caps = {'butt': cairo.LINE_CAP_BUTT,
                'round': cairo.LINE_CAP_ROUND,
                'square': cairo.LINE_CAP_SQUARE}
        if cap not in caps:
            print(str(cap) + ' not a valid line cap')
            print('Choose one of ' + str(caps.keys()))
            return

        self.ctx.set_line_cap(caps[cap])

    def text_size(self, size):
        self.ctx.set_font_size(size)

    def push(self):
        self.ctx.save()
        self.draw_states.append(copy.deepcopy(self.draw_states[-1]))

    def pop(self):
        self.ctx.restore()
        self.draw_states.pop()

    def translate(self, *args):
        """Translate by specifying `x` and `y` offset.

        Args:
            The offset can be specified as an array/list (e.g `c.translate([x,y])`
            or as single arguments (e.g. `c.translate(x, y)`)
        Returns:
            Nothing
        """
        if len(args)==1:
            v = args[0]
        else:
            v = args
        self.ctx.translate(*v)

    def scale(self, *args):
        """Apply a scaling transformation.

        Args:
        Providing a single number will apply a uniform transformation.
        Providing a pair of number will scale in the x and y directions.
        The scale can be specified as an array/list (e.g `c.scale([x,y])`
        or as single arguments (e.g. `c.scale(x, y)`)'''

        Returns:
        type: nothing
        """

        if len(args)==1:
            s = args[0]
            if is_number(s):
                s = [s, s]
        else:
            s = args
        self.ctx.scale(*s)

    def rotate(self, theta):
        ''' Rotate by `theta` radians'''
        self.ctx.rotate(theta)

    rotate_rad = rotate

    def apply_matrix(self, mat):
        matrix = cairo.Matrix(mat[0][0], mat[1][0], mat[0][1], mat[1][1], mat[0][2], mat[1][2])
        self.ctx.transform(matrix)

    def rotate_deg(self, deg):
        ''' Rotate using degrees'''
        self.ctx.rotate(radians(deg))

    def hsv(self, *args):
        if len(args) > 1:
            return hsv_to_rgb(np.array(args))*self.color_scale
        else:
            return hsv_to_rgb(np.array(args[0]))*self.color_scale
            
    def _fillstroke(self):
        if self.no_draw: # we are in a begin_shape end_shape pair
           return

        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)
            if self.cur_stroke is not None:
                self.ctx.fill_preserve()
            else:
                self.ctx.fill()
        if self.cur_stroke is not None:
            self.ctx.set_source_rgba(*self.cur_stroke)
            self.ctx.stroke()

    def rectangle(self, *args):
        """Draw a rectangle given top-left corner, width and heght.

        Args:
        Input arguments can be in the following formats:
         - `[topleft_x, topleft_y], [width, height]`,
         - `[topleft_x, topleft_y], width, height`,
         - `topleft_x, topleft_y, width, height`
         - '[[topleft_x, topleft_y], [bottomright_x, bottomright_y]]'
        """

        if len(args) == 1:
            p = args[0][0]
            size = [args[0][1][0]-args[0][0][0], args[0][1][1]-args[0][0][1]]
        elif len(args) == 2:
            p, size = args
        elif len(args) == 3:
            p = args[0]
            size = args[1:]
        elif len(args) == 4:
            p = args[:2]
            size = args[2:]
        p = np.array(p).astype(float)
        size = np.array(size).astype(float)
        if self._rect_mode == 'center':
            p -= size/2
        elif self._rect_mode == 'radius':
            p -= size
            size *= 2

        self.ctx.rectangle(*p, *size)
        self._fillstroke()

    def rect(self, *args):
        """Draw a rectangle given top-left corner, width and heght.

        Args:
        Input arguments can be in the following formats:
         - `[topleft_x, topleft_y], [width, height]`,
         - `[topleft_x, topleft_y], width, height`,
         - `topleft_x, topleft_y, width, height`

        """
        return self.rectangle(*args)

    def quad(self, *args):
        """Draws a quadrangle given four points

        Args:
        Input arguments can be in the following formats:
         - `a, b, c, d` (Four points specified as lists/tuples/numpy arrays
         - `x1, y1, x2, y2, x3, y3, x4, y4`
        """

        if len(args)==4:
            self.polygon(args)
        else:
            self.polygon([[args[i*2], args[i*2+1]] for i in range(4)])

    def line(self, *args):
        self.push()
        if self.cur_stroke is None:
            if self.cur_fill is not None:
                self.cur_stroke = self.cur_fill
            else:
                print('line: No color is set')
        if len(args)==2:
            self.polyline(args[0], args[1])
        if len(args)==4:
            self.polyline([[args[0], args[1]], [args[2], args[3]]])
        self.pop()

    def arrow(self, a, b, size=2.5, overhang=0.7, length=2.0):
        w = self.ctx.get_line_width()*size
        # Arrow width and 'height' (length)
        h = w*length
        a = np.array(a)
        b = np.array(b)
        # direction
        d = b-a
        l = np.linalg.norm(d)
        d = d / (np.linalg.norm(d)+1e-10)
        # Shift end of segment so arrow tip is at end
        b = a+d*max(0.0, l-h)
        p = np.array([-d[1], d[0]])
        # arrow polygon
        P = [b + p*w - d*w*overhang, b + d*h, b - p*w - d*w*overhang, b]
        # draw
        self.line(a, b)
        self.push()
        self.fill(self.get_stroke_or_fill_color())
        self.no_stroke()
        self.polygon(P)
        self.pop()

    def triangle(self, *args):
        """Draws a triangle given three points

        Args:
        Input arguments can be in the following formats:
         - `a, b, c` (Four points specified as lists/tuples/numpy arrays
         - `x1, y1, x2, y2, x3, y3`
        """

        if len(args)==3:
            self.polygon(args)
        else:
            self.polygon([[args[i*2], args[i*2+1]] for i in range(3)])

    def circle(self, *args):
        """Draw a circle given center and radius

        Args:
        Input arguments can be in the following formats:
        - `[center_x, center_y], radius`,
        - `center_x, center_y, raidus`
        """

        if len(args)==3:
            center = args[:2]
            radius = args[2]
        else:
            center, radius = args
        self.ctx.new_sub_path()
        self.ctx.arc(*center, radius, 0, np.pi*2.)
        self._fillstroke()

    def ellipse(self, *args):
        """Draw an ellipse with center, width and height.

        Args:
        Input arguments can be in the following formats:
        - `[center_x, center_y], [width, height]`,
        - `[center_x, center_y], width, height`,
        - `center_x, center_y, width, height`
        """

        if len(args) == 3:
            center = args[0]
            w, h = args[1:]
        elif len(args) == 4:
            center = args[:2]
            w, h = args[2:]
        else:
            center = args[0]
            w, h = args[1]

        self.push()
        self.translate(center)
        self.scale([w/2,h/2])
        self.ctx.new_sub_path()
        self.ctx.arc(0, 0, 1, 0,np.pi*2.)
        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)
            if self.cur_stroke is not None:
                self.ctx.fill_preserve()
            else:
                self.ctx.fill()
        self.pop()
        
        if self.cur_stroke is not None:
            self.ctx.set_source_rgba(*self.cur_stroke)
            self.ctx.stroke()

    def arc(self, *args):
        """Draw an arc given the center of the ellipse `x, y`
        the size of the ellipse `w, h` and the initial and final angles
        in radians  `start, stop`.

        Args:
          Input arguments can be in the following formats:
          -`x, y, w, h, start, stop`
          -`[x, y]', '[w, h]', '[start, stop]'
          -`[x, y]', w, h, start, stop`

        """
        if len(args) == 3:
            x, y = args[0]
            w, h = args[1]
            start, stop = args[2]
        elif len(args) == 6:
            x, y, w, h, start, stop = args
        else:
            x, y = args[0]
            w, h, start, stop = args[1:]

        self.push()
        self.translate(x, y)
        self.scale(w/2,h/2)
        self.ctx.new_sub_path()
        self.ctx.arc(0, 0, 1, start, stop)
        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)
            if self.cur_stroke is not None:
                self.ctx.fill_preserve()
            else:
                self.ctx.fill()
        self.pop()

        if self.cur_stroke is not None:
            self.ctx.set_source_rgba(*self.cur_stroke)
            self.ctx.stroke()


    def clear_segments(self):
        self.curve_segments = []
        self.curve_segment_types = []

    def begin_shape(self):
        ''' Begin drawing a compound shape'''
        self.no_draw = True
        self.clear_segments()

    def end_shape(self, close=False):
        ''' End drawing a compound shape'''
        self.no_draw = False
        self.end_contour(close)
        # if close:
        #     self.ctx.close_path()
        # self._fillstroke()

    def begin_contour(self):
        ''' Begin drawing a contour'''
        self.clear_segments()
        self.ctx.new_sub_path()
        self._first_point = True

    def end_contour(self, close=False):
        ''' End drawing a contour'''
        if not self.curve_segments:
            if close:
                self.ctx.close_path()
            self._fillstroke()
            return
        if (len(self.curve_segments)==1 and
            self.curve_segment_types[-1] == 'C'):
            P = self.curve_segments[-1]
            if len(P) < 3:
                raise ValueError('Insufficient points for spline')
            Cp = cardinal_spline(P, self.tension, close)
            #c.begin_contour()
            self.ctx.move_to(*Cp[0])
            for i in range(0, len(Cp)-1, 3):
                self.ctx.curve_to(*Cp[i+1], *Cp[i+2], *Cp[i+3])
            #c.end_contour(close)
        else:
            #c.begin_contour()
            cur = self.curve_segments[0].pop(0)
            self.ctx.move_to(*cur)
            for seg, type in zip(self.curve_segments, self.curve_segment_types):
                if type=='C':
                    P = [cur] + seg
                    Cp = cardinal_spline(P, self.tension, False)
                    # for p in Cp:
                    #     self.ctx.line_to(*p)
                    for i in range(0, len(Cp)-1, 3):
                        self.ctx.curve_to(*Cp[i+1], *Cp[i+2], *Cp[i+3])
                else:
                    for p in seg:
                        self.ctx.line_to(*p)
                cur = seg[-1]
            #c.end_contour()

        if close:
            self.ctx.close_path()
        self._fillstroke()

    def _add_curve_segment(self, type):
        self.curve_segments.append([])
        self.curve_segment_types.append(type)

    def vertex(self, x, y=None):
        ''' Add a vertex to current contour
        Args:
        Input arguments can be in the following formats:
         `[x, y]'
         `x, y`
        '''
        if y is None:
            x, y = x
        if (not self.curve_segments or
            self.curve_segment_types[-1] != 'L'):
            self._add_curve_segment('L')

        self.curve_segments[-1].append([x,y])

    def curve_vertex(self, x, y=None):
        ''' Add a curved vertex to current contour
        Args:
        Input arguments can be in the following formats:
         `[x, y]'
         `x, y`
        '''
        if y is None:
            x, y = x
        if (not self.curve_segments or
            self.curve_segment_types[-1] != 'C'):
            self._add_curve_segment('C')
        self.curve_segments[-1].append([x,y])

    # def vertex(self, x, y=None):
    #     ''' Add a vertex to current contour
    #     Args:
    #     Input arguments can be in the following formats:
    #      `[x, y]'
    #      `x, y`
    #     '''
    #     if y is None:
    #         x, y = x
    #     if not self._cur_point:
    #         self.ctx.move_to(x, y)
    #     else:
    #         self.ctx.line_to(x, y)
    #     self._cur_point = [x, y]

    # def cubic(self, *args):
    #     ''' Draw a cubic bezier curve
    #     Args:
    #     Input arguments can be in the following formats:
    #      `[x1, y1], [x2, y2], [x3, y3]`
    #      `x1, y1, x2, y2, x3, y3`
    #     '''
    #     if len(args) == 3:
    #         p1, p2, p3 = args
    #     else:
    #         p1 = args[:2]
    #         p2 = args[2:4]
    #         p3 = args[4:6]
    #     self._cur_point = [*p3]
    #     self.ctx.curve_to(*p1, *p2, *p3)
    # cvertex = cubic

    # def quadratic(self, *args):
    #     ''' Draw a quadratic bezier curve
    #     Args:
    #     Input arguments can be in the following formats:
    #         `[x1, y1], [x2, y2]`
    #         `x1, y1, x2, y2`
    #     '''
    #     if len(args) == 2:
    #         (x1, y1), (x2, y2) = args
    #     else:
    #         x1, y1, x2, y2 = args

    #     if not self._cur_point:
    #         print("Need an inital point to construct quadratic bezier curve")
    #         raise ValueError

    #     x0, y0 = self._cur_point
    #     self.ctx.curve_to(
    #         (2 * x1 + x0) / 3,
    #         (2 * y1 + y0) / 3,
    #         (2 * x1 + x2) / 3,
    #         (2 * y1 + y2) / 3,
    #         x2, y2)

    #     self._cur_point = [x2, y2]
    # qvertex = quadratic

    # def quadratic_to_cubic(self, x1, y1, x2, y2):
    #     ''' Convert a quadratic bezier curve to a cubic bezier curve
    #     Args:
    #     Input arguments can be in the following formats:
    #         `x1, y1, x2, y2`
    #     '''
    #     x0, y0 = self._cur_point
    #     self.ctx.curve_to(
    #                         2.0 / 3.0 * x1 + 1.0 / 3.0 * x0,
    #                         2.0 / 3.0 * y1 + 1.0 / 3.0 * y0,
    #                         2.0 / 3.0 * x1 + 1.0 / 3.0 * x2,
    #                         2.0 / 3.0 * y1 + 1.0 / 3.0 * y2,
    #                         y1, y2)

    # def bezier(self, *args):
    #     ''' Draws a bezier curve segment from current point
    #         The degree of the curve (2 or 3) depends on the input arguments
    #     Args:
    #     Input arguments can be in the following formats:
    #         `[x1, y1], [x2, y2], [x3, y3]` is cubic
    #         `x1, y1, x2, y2, x3, y3` is cubic
    #         `[x1, y1], [x2, y2]` is quadratic
    #         `x1, y1, x2, y2` is quadratic
    #     '''
    #     if len(args) == 3 or len(args)==6:
    #         self.cubic(*args)
    #     else:
    #         self.quadratic(*args)

    def load_image(self, path):
        '''Load an image from disk. Currently only supports png! Use external
        loading into NumPy instead'''
        if not 'png' in path:
            print ("Load image only supports PNG files!!!")
            assert(0)
        surf = cairo.ImageSurface.create_from_png(path)
        return surf

    def image(self, img, *args, opacity=1.0):
        """Draw an image at position with (optional) size and (optional) opacity

        Args:
        img: The input image. Can be either a numpy array or a pyCairo surface (e.g. another canvas).
        *args: position and size can be specified with the following formats:
            `x, y`:  position only
            `x, y, w, h`: position and size
            `[x, y]`: position only (also a numpy array or tuple are valid)
            `[x, y], [w, h]`: position and size
        if the position is not specified, the original image dimensions will be used

        `opacity`: a value between 0 and 1 specifying image opacity.

        """
        if isinstance(img, Image.Image):
            img = np.array(img)
        if type(img) == np.ndarray:
            img = numpy_to_surface(img)
        self.ctx.save()
        if len(args) == 0:
            pos = np.zeros(2)
            size = [img.get_width(), img.get_height()]
        elif len(args) == 1: #[x, y]
            pos = args[0]
            size = [img.get_width(), img.get_height()]
        elif len(args) == 2: 
            if is_number(args[0]): # x, y
                pos = args
                size = [img.get_width(), img.get_height()]
            else: # [x, y], [w, h]
                pos, size = args
        elif len(args) == 4: # x, y, w, h
            pos = args[:2] 
            size = args[2:]
        else:
            print("Unexpected number of arguments for image")
            raise ValueError

        pos = np.array(pos).astype(float)
        size = np.array(size).astype(float)

        # Disabling rect mode for images
        # if self._rect_mode == 'center':
        #     pos -= size/2
        # elif self._rect_mode == 'radius':
        #     pos -= size
        #     size *= 2

        self.ctx.translate(pos[0], pos[1])

        if size is not None:
            sx = size[0]/img.get_width()
            sy = size[1]/img.get_height()
            self.ctx.scale(sx, sy)

        self.ctx.set_source_surface(img)
        self.ctx.paint_with_alpha(opacity)
        self.ctx.restore()

    def shape(self, poly_list, closed=False):
        '''Draw a shape represented as a list of polylines, see the ~polyline~
        method for the format of each polyline
        '''

        self.begin_shape()
        for P in poly_list:
            self.polyline(P, closed=closed)
        self.end_shape()

    def text(self, pos, text, center=False):
        ''' Draw text at a given position

        Args:
            if center=True the text will be horizontally centered
        '''

        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)
        if center:
            (x, y, w, h, dx, dy) = self.ctx.text_extents(text)
            self.ctx.move_to(pos[0]-w/2-x, pos[1])
        else:
            self.ctx.move_to(*pos)
        self.ctx.text_path(text)
        self.ctx.fill()

    def polygon(self, *args):
        ''' Draw a *closed* polygon
        The polyline is specified as either:
        - a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
        - a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)'''
        self.polyline(*args, closed=True)

    def polyline(self, *args, closed=False):
        ''' Draw a polyline. 
        The polyline is specified as either:
        - a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
        - a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)
        
        To close the polyline set the named closed argument to `True`, e.g. `c.polyline(points, closed=True)`.
        '''
        self.ctx.new_sub_path()
        #self.ctx.new_path()
        if len(args)==1:
            points = args[0]
        else:
            points = args
        self.ctx.move_to(*points[0])
        for p in points[1:]:
            self.ctx.line_to(*p)
        if closed:
            self.ctx.close_path()

        self._fillstroke()

    def identity(self):
        self.ctx.identity_matrix()

    def background(self, *args):
        ''' Clear the canvas with a given color '''
        # self.clear_callback()
        self.ctx.identity_matrix()
        self.ctx.set_source_rgba(*self._apply_colormode(self._convert_rgba(args)))
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()

    def get_buffer(self):
        return self.surf.get_data()

    def get_image(self):
        ''' Get canvas image as a numpy array '''
        img = np.ndarray (shape=(self.height, self.width, 4), dtype=np.uint8, buffer=self.surf.get_data())[:,:,:3].copy()
        img = img[:,:,::-1]
        return img

    def get_image_grayscale(self):
        ''' Returns the canvas image as a grayscale numpy array (in 0-1 range)'''
        img = self.get_image()
        img = np.sum(img, axis=-1)/3
        return img/255

    def save_image(self, path):
        ''' Save the canvas to an image'''
        self.surf.write_to_png(path)

    def save_svg(self, path):
        ''' Save the canvas to an svg file'''
        if self.recording_surface is None:
            raise ValueError('No recording surface in canvas')
        surf = cairo.SVGSurface(path, self.width, self.height)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.recording_surface)
        ctx.paint()
        surf.finish()
        fix_clip_path(path, path)
        

    def save_pdf(self, path):
        ''' Save the canvas to an svg file'''
        if self.recording_surface is None:
            raise ValueError('No recording surface in canvas')
        surf = cairo.PDFSurface(path, self.width, self.height)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.recording_surface)
        ctx.paint()
        surf.finish()
        
    def Image(self):
        return Image.fromarray(self.get_image())

    # def save(self):
    #     ''' Save the canvas to an image'''
    #     if not self.output_file:
    #         print('No output file specified')
    #         return
    #     if '.svg' in self.output_file:
    #         svg_surf = cairo.SVGSurface(self.output_file, self.width, self.height)
    #         svg_ctx = cairo.Context(svg_surf)
    #         svg_ctx.set_source_surface(self.surf)
    #         svg_ctx.paint()
    #         svg_ctx.set_source_surface(self.recording_surface)
    #         svg_ctx.paint()
    #         svg_surf.finish()
    #     else:
    #         self.surf.write_to_png(self.output_file)

    def save(self, path):
        ''' Save the canvas to an image'''
        if '.svg' in path:
            self.save_svg(path)
        elif '.pdf' in path:
            self.save_pdf(path)
        elif '.png' in path:
            # TODO use PIL
            self.save_image(path)

    def show(self, size=None, title='', axis=False):
        import matplotlib.pyplot as plt
        if size is not None:
            plt.figure(figsize=(size[0]/100, size[1]/100))
        else:
            plt.figure(figsize=(self.width/100, self.height/100))
        if title:
            plt.title(title)
        plt.imshow(self.get_image())
        if not axis:
            plt.gca().axis('off')
        plt.show()

    def _convert_html_color(self, html_color):
        # Remove '#' if present
        if html_color.startswith('#'):
            html_color = html_color[1:]

        # Extract RGB or RGBA components
        if len(html_color) == 6:
            r = int(html_color[:2], 16) / 255.0
            g = int(html_color[2:4], 16) / 255.0
            b = int(html_color[4:6], 16) / 255.0
            return np.array([r, g, b, 1.0])
        elif len(html_color) == 8:
            r = int(html_color[:2], 16) / 255.0
            g = int(html_color[2:4], 16) / 255.0
            b = int(html_color[4:6], 16) / 255.0
            a = int(html_color[6:8], 16) / 255.0
            return np.array([r, g, b, a])
        else:
            raise ValueError("Invalid HTML color format")


    def _convert_rgb(self, x):
        if len(x)==1:
            if not is_number(x[0]): # array like input
                return np.array(x[0])/self.color_scale
            return (x[0]/self.color_scale,
                    x[0]/self.color_scale,
                    x[0]/self.color_scale)
        return (x[0]/self.color_scale,
                x[1]/self.color_scale,
                x[2]/self.color_scale)

    def _convert_rgba(self, x):
        if len(x)==1:
            if type(x[0]) == str:
                return self._convert_html_color(x[0])
            elif not is_number(x[0]): # array like input
                return np.array(x[0])/self.color_scale
            return (x[0]/self.color_scale,
                    x[0]/self.color_scale,
                    x[0]/self.color_scale, 1.0)
        elif len(x) == 3:
            return (x[0]/self.color_scale,
                    x[1]/self.color_scale,
                    x[2]/self.color_scale, 1.0)
        elif len(x) == 2:
            return (x[0]/self.color_scale,
                    x[0]/self.color_scale,
                    x[0]/self.color_scale,
                    x[1]/self.color_scale)
        return (x[0]/self.color_scale,
                x[1]/self.color_scale,
                x[2]/self.color_scale,
                x[3]/self.color_scale)

def map(value, start1, stop1, start2, stop2, within_bounds=False):
    ''' Re-maps a number from one range to another. '''
    t = ((value - start1) / (stop1 - start1))
    if within_bounds:
        t = max(0.0, min(t, 1.0))
    return start2 + (stop2 - start2) * t

def radians(x):
    ''' Get radians given x degrees'''
    return np.pi/180*x

def degrees(x):
    ''' Get degrees given x radians'''
    return x * (180.0/np.pi)


def numpy_to_surface(arr):
    ''' Convert numpy array to a pycairo surface'''
    # Get the shape and data type of the numpy array
    if len(arr.shape) == 2:
        if arr.dtype == np.uint8:
            arr = np.dstack([arr, arr, arr, (np.ones(arr.shape)*255).astype(np.uint8)])
        else:
            # Assume grayscale 0-1 image
            arr = np.dstack([arr, arr, arr, np.ones(arr.shape)])
            arr = (arr * 255).astype(np.uint8)
    else:
        if arr.shape[2] == 3:
            #pdb.set_trace()
            if arr.dtype == np.uint8:
                arr = np.dstack([arr, np.ones(arr.shape[:2], dtype=np.uint8)*255])
            else:
                arr = np.dstack([arr, np.ones(arr.shape[:2])])
                arr = (arr * 255).astype(np.uint8)
        else:
            if arr.dtype != np.uint8:
                arr = (arr * 255).astype(np.uint8)

    arr = arr.copy(order='C') # must be "C-contiguous"
    arr[:, :, :3] = arr[:, :, ::-1][:,:,1:]
    surf = cairo.ImageSurface.create_for_data(
        arr, cairo.FORMAT_ARGB32, arr.shape[1], arr.shape[0])

    return surf


def show_image(im, size=None, title='', cmap='gray'):
    ''' Display a (numpy) image'''
    import matplotlib.pyplot as plt
    if size is not None:
        plt.figure(figsize=size)
    else:
        plt.figure()
    if title:
        plt.title(title)
    plt.imshow(im, cmap)
    plt.show()


def show_images(images, ncols, size=None, title='', cmap='gray'):
    ''' Display multiple images in a grid'''
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    n = len(images)
    nrows = int(np.ceil(n/ncols))
    print(nrows)
    if size is not None:
        plt.figure(figsize=size)
    else:
        plt.figure()
    if title:
        plt.title(title)
    gs = GridSpec(nrows, ncols)
    for i, img in enumerate(images):
        ax = plt.subplot(gs[i])
        plt.imshow(img, cmap)
        ax.axis('off')
    plt.tight_layout()
    plt.show()


def hsv_to_rgb(hsva):
    h, s, v = hsva[:3]
    a = 1
    if len(hsva) > 3:
        a = hsva[3]

    if s == 0.0:
        r = g = b = v
    else:
        h = fmod(h, 1) / (60.0 / 360.0)
        i = int(h)
        f = h - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

    return np.array([r,g,b,a])[:len(hsva)]


class VideoInput:
    '''
    Video Input utility (requires OpenCV to be installed).
    Allows for reading frames from a video file or camera.

    param name: Either an integer indicating the device number, or a string indicating the path of a video file
    param size: A tuple indicating the desired size of the video frames (width, height)
    param resize_mode: A string indicating the desired resize mode. Can be 'crop' or 'stretch'
    '''
    def __init__(self, name=0, size=None, resize_mode='crop'):
        ''' Constructor'''
        import cv2
        # define a video capture object
        self.vid = cv2.VideoCapture(name)
        self.size = size
        self.resize_mode = resize_mode
        self.name = name

    def read(self, loop_flag=False):
        import cv2
        # Capture video frame by frame
        success, img = self.vid.read()

        if not success:
            if type(self.name) == str and not loop_flag: # If a video loop automatically
                self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return self.read(True)
            else:
                print('No video')
                if self.size is not None:
                    return np.zeros((self.size[1], self.size[0], 3)).astype(np.uint8)
                else:
                    return np.zeros((16, 16, 3)).astype(np.uint8)

        if self.size is not None:
            src_w, src_h = img.shape[1], img.shape[0]
            dst_w, dst_h = self.size

            if self.resize_mode == 'crop':
                # Keep aspect ratio by cropping
                aspect = dst_w / dst_h

                # Check if aspect ratio match
                asrc_w = int(aspect*src_h)
                if asrc_w > src_w: # aspect ratio > 1
                    asrc_h = int(src_h/aspect)
                    d = (src_h - asrc_h)//2
                    img = img[d:d+asrc_h, :, :]
                elif asrc_w < src_w: # aspect ratio < 1
                    d = (src_w - asrc_w)//2
                    img = img[:, d:d+asrc_w, :]

            # Resize the image frames
            img = cv2.resize(img, self.size)

        img = img[:,:,::-1]
        return img

def cardinal_spline(Q, c, closed=False):
    ''' Returns a Bezier chain for a Cardinal spline interpolation for a sequence of values
    c is the tension parameter with 0.5 a Catmull-Rom spline
    '''
    Q = np.array(Q)
    if closed:
        Q = np.vstack([Q, Q[0]])
    n = len(Q)
    D = []
    for k in range(1, n-1):
        # Note that we do not take parametrisation into account here
        d = (1-c)*(Q[k+1] - Q[k-1])
        D.append(d)
    if closed:
        d1 =  (1-c)*(Q[1] - Q[-2])
        dn = d1
    else:
        d1 = (1-c)*(Q[1] - Q[0])
        dn = (1-c)*(Q[-1] - Q[-2])
    D = [d1] + D + [dn]
    P = [Q[0]]
    for k in range(1, n):
        p1 = Q[k-1] + D[k-1]/3
        p2 = Q[k] - D[k]/3
        p3 = Q[k]
        P += [p1, p2, p3]
    return np.array(P)

# Fix svg export clip path 
# RecordingSurface adds a clip-path attribute that breaks Illustrator import
def fix_namespace(xml_content):
    #return xml_content
    # Remove namespace prefixes from the XML content and replace ns1 with xlink (argh)
    xml_content = xml_content.replace('ns0:', '').replace(':ns0', '')
    return xml_content.replace('ns1:', 'xlink:').replace(':ns1', ':xlink')

def fix_clip_path(file_path, out_path):
    import xml.etree.ElementTree as ET

    # Load the SVG file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Define the namespace
    namespace = {'svg': 'http://www.w3.org/2000/svg'}

    # Find the first <g> tag
    g_tag = root.find('.//svg:g', namespace)

    # Remove the 'clip-path' attribute if it exists
    if 'clip-path' in g_tag.attrib:
        del g_tag.attrib['clip-path']
    res = ET.tostring(root, encoding='unicode')
    # Save and then apply fixes
    tree.write(out_path, encoding='UTF-8', xml_declaration=True, default_namespace='')
    with open(out_path, 'r') as f:
        # Fix namepace
        txt = fix_namespace(f.read())
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(txt)
