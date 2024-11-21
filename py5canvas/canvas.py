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
"""

#%%
import numpy as np
import cairo
import numbers
import copy, sys, types
import ctypes as ct
from math import fmod, pi, comb
from PIL import Image
import importlib
import importlib.util
from contextlib import contextmanager
from easydict import EasyDict as edict

perlin_loader = importlib.util.find_spec('perlin_noise')
if perlin_loader is not None:
    from perlin_noise import PerlinNoise
    perlin = PerlinNoise()
else:
    print("Perlin noise not installed. Use `pip install perlin-noise` to install")
    perlin = None

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
        self.cur_stroke = c._convert_rgba([0.0])


class Canvas:
    """
    Defines a drawing canvas (pyCairo) that behaves similarly to p5js

    Constructor arguments:

    - ~width~ : (~int~), width of the canvas in pixels
    - ~height~ : (~int~), height of the canvas in pixels
    - ~clear_callback~ (optional): function, a callback to be called when the canvas is cleared (for internal use mostly)

    In a notebook you can create a canvas globally with either of:

    - ~size(width, height)~
    - ~create_canvas(width, height)~

    When using these functions all the canvas functionalities below will become globally available to the notebook.

    """

    def __init__(self, width, height, background=(128.0, 128.0, 128.0, 255.0),
                 clear_callback=lambda: None,
                 output_file='',
                 recording=True,
                 save_background=False):
        """Constructor"""
        # See https://pycairo.readthedocs.io/en/latest/reference/context.html
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = MultiContext(surf) #cairo.Context(surf)

        # Create SVG surface for saving
        self.color_scale = np.ones(4)*255.0

        # This is useful for py5sketch to reset SVG each time background is cleared
        self.clear_callback = clear_callback

        self._color_mode = 'rgb'
        self._width = width
        self._height = height
        self.surf = surf
        self.ctx = ctx

        #ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD) #FILL_RULE_WINDING) #EVEN_ODD)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING) #FILL_RULE_WINDING) #EVEN_ODD)
        ctx.set_line_join(cairo.LINE_JOIN_MITER)
        ctx.set_source_rgba(*self._apply_colormode(self._convert_rgba(background)))
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        self.last_background = background

        self.draw_states = [CanvasState(self)]

        # self.cur_fill = self._convert_rgba([255.0])
        # self.cur_stroke = None
        self._rect_mode = 'corner'
        self._ellipse_mode = 'center'

        self.no_draw = False

        self._save_background = save_background

        self.tension = 0.5

        # Constants
        self.PI = pi
        self.TWO_PI = pi*2
        self.HALF_PI = pi/2
        self.QUARTER_PI = pi/4
        self.CENTER = 'center'
        self.TOP = 'top'
        self.BOTTOM = 'bottom'
        self.CORNER = 'corner'
        self.CORNERS = 'corners'
        self.RADIUS = 'radius'
        self.HSB = 'hsv'
        self.HSV = 'hsv'
        self.RGB = 'rgb'
        self.CLOSE = 'close'
        self.OPEN = 'open'

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

        self.ctx.select_font_face("sans-serif")
        self.ctx.set_font_size(16)
        self.line_cap('round')
        self.text_halign = 'left'
        self.text_valign = 'bottom'

    def set_color_scale(self, scale):
        """Set color scale:

        Arguments:

        - ~scale~ (float): the color scale. if we want to specify colors in the ~0...255~ range,
         ~scale~ will be ~255~. If we want to specify colors in the ~0...1~ range, ~scale~ will be ~1~"""
        if is_number(scale):
            scale = np.ones(4)*scale
        self.color_scale[:len(scale)] = scale

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

    def _get_stroke_or_fill_color(self):
        """
        Returns the current stroke color if set, the fill color otherwise
        returns the current stroke or fill color as a numpy array, or ~None~ if no color is set
        """
        if self.cur_stroke is not None:
            return np.array(self.cur_stroke)*self.color_scale
        if self.cur_fill is not None:
            return np.array(self.cur_fill)*self.color_scale
        return None #self.cur_fill

    @property
    def center(self):
        """ The center of the canvas (as a 2d numpy array)"""
        return np.array([self._width/2,
                         self._height/2])

    def get_width(self):
        """ The width of canvas"""
        return self._width

    def get_height(self):
        """ The height of canvas"""
        return self._height

    @property
    def width(self):
        """ The width of canvas"""
        return self._width

    @property
    def height(self):
        """ The height of canvas"""
        return self._height

    @property
    def surface(self):
        return self.surf

    def no_fill(self):
        """ Do not fill subsequent shapes"""
        self.fill(None)

    def no_stroke(self):
        """ Do not stroke subsequent shapes"""
        self.stroke(None)

    def fill_rule(self, rule):
        """ Sets the fill rule

        """
        rules = {'evenodd':  cairo.FILL_RULE_EVEN_ODD,
                 'nonzero': cairo.FILL_RULE_WINDING,
                 'winding': cairo.FILL_RULE_WINDING}
        if rule not in rules:
            print('Rule ', rule, ' is not valid')
            print('Use either "nonzero" or "evenodd"')
        self.ctx.set_fill_rule(rules[rule])

    def color_mode(self, mode, *args):
        """ Set the color mode for the canvas

        Arguments:

        - ~mode~ (string): can be one of 'rgb', 'hsv' depending on the desired color mode
        - ~scale~ (float): the scale for the color values (e.g. 255 for 0...255 range, 1 for 0...1 range)

        Examples:

        - ~color_mode('rgb', 1.0)~ will set the color mode to RGB in the 0-1 range.
        """
        self._color_mode = mode
        if len(args):
            if len(args)==1:
                # Assume we set all scale to be equal
                self.set_color_scale(args[0])
            else:
                # Specify each component
                self.set_color_scale(args)

    def _apply_colormode(self, clr):
        mode = self._color_mode.lower()
        if mode == 'hsv' or mode == 'hsb':
            return hsv_to_rgb(clr)
        return clr

    def fill(self, *args):
        """ Set the color of the current fill

        Arguments:

        - A single argument specifies a grayscale value, e.g ~fill(128)~ will fill with 50% gray.
        - Two arguments specify grayscale with opacity, e.g. ~fill(255, 128)~ will fill with transparent white.
        - Three arguments specify a color depending on the color mode (rgb or hsv)
        - Four arguments specify a color with opacity
        """
        if args[0] is None:
            self.cur_fill = None
        else:
            self.cur_fill = self._apply_colormode(self._convert_rgba(args))

    def stroke(self, *args):
        """ Set the color of the current stroke

        Arguments:
        - A single argument specifies a grayscale value, e.g. ~stroke(255)~ will set the stroke to white.
        - Two arguments specify grayscale with opacity, e.g. ~stroke(0, 128)~ will set the stroke to black with 50% opacity.
        - Three arguments specify a color depending on the color mode (rgb or hsv), e.g. ~stroke(255, 0, 0)~ will set the stroke to red, when the color mode is RGB
        - Four arguments specify a color with opacity
        """

        if args[0] is None:
            self.cur_stroke = None
        else:
            self.cur_stroke = self._apply_colormode(self._convert_rgba(args))

    def stroke_weight(self, w):
        """Set the line width

        Arguments:
        - The width in pixel of the stroke
        """
        self.ctx.set_line_width(w)

    def line_join(self, join):
        """Specify the 'join' mode for polylines.

        Arguments:

        - ~join~ (string): can be one of "miter", "bevel" or "round"
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
        """Specify the blending mode

        Arguments:

        - ~mode~ (string) can be one of: "clear", "source", "over", "in", "out", "atop",
          "dest", "dest_over", "dest_in", "dest_out", "dest_atop", "xor", "add", "saturate", "multiply", "screen", "overlay", "darken", "lighten", "color_dodge", "color_burn", "hard_light", "soft_light", "difference", "exclusion", "hsl_hue", "hsl_saturation", "hsl_color", "hsl_luminosity"
          See [[https://www.cairographics.org/operators/]] for a discussion on the different operators.
        """
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

        Arguments:

        - ~cap~ (string): can be one of "butt", "round" or "square"
        """
        caps = {'butt': cairo.LINE_CAP_BUTT,
                'round': cairo.LINE_CAP_ROUND,
                'square': cairo.LINE_CAP_SQUARE}
        if cap not in caps:
            print(str(cap) + ' not a valid line cap')
            print('Choose one of ' + str(caps.keys()))
            return

        self.ctx.set_line_cap(caps[cap])

    def text_align(self, halign, valign='bottom'):
        """Specify the text alignment

        Arguments:
        - ~halign~ (string): Horizontal alignment. One of "left", "center" or "right"
        - ~valign~ (string): Horizontal alignment. One of "bottom" (default), "top" or "center"
        """
        self.text_halign = halign
        self.text_valign = valign

    def text_size(self, size):
        """Specify the text size

        Arguments:

        - ~size~ (int): the text size
        """
        self.ctx.set_font_size(size)

    def text_font(self, font):
        """Specify the font to use for text rendering
        Arguments:

        - ~font~ (string): the name of a system font
        """
        if '.ttf' in font:
            self.ctx.set_font_face(create_cairo_font_face_for_file(font))
        else:
            self.ctx.select_font_face(font)

    def push_matrix(self):
        """
        Save the current transformation
        """
        @contextmanager
        def popmanager():
            pass
            try:
                yield
            finally:
                self.pop_matrix()

        self.ctx.save()
        return popmanager()

    def pop_matrix(self):
        """
        Restore the previous transformation
        """
        self.ctx.restore()

    def push_style(self):
        """
        Save the current drawing state
        """
        @contextmanager
        def popmanager():
            pass
            try:
                yield
            finally:
                self.pop_style()

        self.draw_states.append(copy.deepcopy(self.draw_states[-1]))
        return popmanager()

    def pop_style(self):
        """
        Restore the previously pushed drawing state
        """
        self.draw_states.pop()

    def push(self):
        """
        Save the current drawing state and transformations
        """
        @contextmanager
        def popmanager():
            pass
            try:
                yield
            finally:
                self.pop()

        self.ctx.save()
        self.draw_states.append(copy.deepcopy(self.draw_states[-1]))
        return popmanager()

    def pop(self):
        """
        Restore the previously pushed drawing state and transformations
        """
        self.ctx.restore()
        self.draw_states.pop()

    def translate(self, *args):
        """Translate by specifying ~x~ and ~y~ offset.

        Arguments:

        - The offset can be specified as an array/list (e.g ~translate([x,y])~
          or as single arguments (e.g. ~translate(x, y)~)
        """
        if len(args)==1:
            v = args[0]
        else:
            v = args
        self.ctx.translate(*v)

    def scale(self, *args):
        """Apply a scaling transformation.

        Arguments:

        - Providing a single number will apply a uniform transformation.
        - Providing a pair of number will scale in the x and y directions.
        - The scale can be specified as an array/list (e.g ~scale([x,y])~
        or as single arguments (e.g. ~scale(x, y)~)'''
        """

        if len(args)==1:
            s = args[0]
            if is_number(s):
                s = [s, s]
        else:
            s = args
        self.ctx.scale(*s)

    def rotate(self, theta):
        ''' Rotate by ~theta~ radians'''
        self.ctx.rotate(theta)

    rotate_rad = rotate

    def apply_matrix(self, mat):
        ''' Apply an affine (3x3) transformation matrix'''
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

    hsb = hsv

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

    def rect_mode(self, mode):
        """ Set the "mode" for drawing rectangles.

        Arguments:
        - ~mode~ (string): can be one of 'corner', 'corners', 'center', 'radius'

        """
        if mode not in ['corner', 'center', 'radius']:
            print('rect_mode: invalid mode')
            print('choose one among: corner, center, radius')
            return
        self._rect_mode = mode

    def ellipse_mode(self, mode):
        """ Set the "mode" for drawing rectangles.

        Arguments:
        - ~mode~ (string): can be one of 'corner', 'center'
        """
        if mode not in ['corner', 'center']:
            print('rect_mode: invalid mode')
            print('choose one among: corner, center')
            return
        self._ellipse_mode = mode

    def rectangle(self, *args, mode=None):
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
        center of the rectangle if the rect mode is ~"center"~ and the top left corner otherwise.
        """

        if mode is None:
            mode = self._rect_mode

        if len(args) == 1:
            p = args[0][0]
            size = [args[0][1][0]-args[0][0][0], args[0][1][1]-args[0][0][1]]
            mode = 'corner' # Force the mode to corner since we explicitly defined the rect
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

        if mode.lower() == 'center':
            p -= size/2
        elif mode.lower() == 'radius':
            p -= size
            size *= 2
        elif mode.lower() == 'corners':
            # Interpret 'size' as the bottom right corner
            size = size - p

        self.ctx.rectangle(*p, *size)
        self._fillstroke()

    rect = rectangle

    def square(self, *args, mode=None):
        """Draw a square.

        Arguments:

        The first sequence of arguments is one of
         - ~[x, y], size~,
         - ~x, y, size~

        The interpretation of ~x~ and ~y~ depends on the current rect mode. These indicate the
        center of the rectangle if the rect mode is ~"center"~ and the top left corner otherwise.
        """
        if mode is None:
            mode = self._rect_mode
        if mode == 'corners':
            mode = 'corner'
        if len(args) == 2:
            self.rectangle(args[0], [args[1], args[1]], mode=mode)
        elif len(args) == 3:
            self.rectangle(args[0], args[1], args[2], args[2], mode=mode)
        else:
            raise ValueError('square: wrong number of arguments')


    def rect(self, *args, mode=None):
        """Draws a rectangle.

        Input arguments can be in the following formats:

         - ~[topleft_x, topleft_y], [width, height]~,
         - ~[topleft_x, topleft_y], width, height~,
         - ~topleft_x, topleft_y, width, height~

        Depending on
        """
        return self.rectangle(*args, mode=mode)

    def quad(self, *args):
        """Draws a quadrangle given four points

        Input arguments can be in the following formats:

         - ~a, b, c, d~ (Four points specified as lists/tuples/numpy arrays
         - ~x1, y1, x2, y2, x3, y3, x4, y4~, a sequence of numbers, one for each coordinate
        """

        if len(args)==4:
            self.polygon(args)
        else:
            self.polygon([[args[i*2], args[i*2+1]] for i in range(4)])


    def line(self, *args):
        """ Draws a line between two points

        Input arguments can be in the following formats:

         - ~a, b~ (Two points specified as lists/tuples/numpy arrays
         - ~x1, y1, x2, y2~, a sequence of numbers, one for each coordinate
        """
        nostroke = False
        if self.cur_stroke is None:
            nostroke = True
            if self.cur_fill is not None:
                self.cur_stroke = self.cur_fill
            else:
                print('line: No color is set')
        if len(args)==2:
            self.polyline(args[0], args[1])
        if len(args)==4:
            self.polyline([[args[0], args[1]], [args[2], args[3]]])
        if nostroke:
            self.cur_stroke = None

    def point(self, *args):
        ''' Draw a point at a given position

        Input arguments can be in the following formats:

         - ~[x, y]~: a single point specified as a tuple/list/numpy array
         - ~x1, y1~: two coordinates

        '''
        nostroke = False
        if self.cur_stroke is None:
            nostroke = True
            if self.cur_fill is not None:
                self.cur_stroke = self.cur_fill
            else:
                print('point: No color is set')
        if len(args)==1:
            self.polyline(args[0], args[0])
        elif len(args)==2:
            self.polyline([args[0], args[1]],
                          [args[0], args[1]])
        else:
            raise ValueError("point: Illegal number of arguments")
        if nostroke:
            self.cur_stroke = None


    def arrow(self, *args, size=2.5, overhang=0.7, length=2.0):
        ''' Draw an arrow between two points

        Input arguments can be in the following formats:

         - ~a, b~ (Two points specified as lists/tuples/numpy arrays
         - ~x1, y1, x2, y2~, a sequence of numbers, one for each coordinate
        '''

        if len(args) == 2:
            a, b = args
        elif len(args) == 4:
            a = args[:2]
            b = args[2:]
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
        self.fill(self._get_stroke_or_fill_color())
        self.no_stroke()
        self.polygon(P)
        self.pop()

    def triangle(self, *args):
        """Draws a triangle given three points

        Input arguments can be in the following formats:

         - ~a, b, c~ (Four points specified as lists/tuples/numpy arrays
         - ~x1, y1, x2, y2, x3, y3~
        """

        if len(args)==3:
            self.polygon(args)
        else:
            self.polygon([[args[i*2], args[i*2+1]] for i in range(3)])

    def circle(self, *args, mode='center'):
        """Draw a circle given center and radius

        Input arguments can be in the following formats:

        - ~[center_x, center_y], radius~,
        - ~center_x, center_y, raidus~
        """

        if len(args)==3:
            center = args[:2]
            radius = args[2]
        else:
            center, radius = args
        x, y = center
        if mode.lower() != 'center':
            x += radius
            y += radius
        self.ctx.new_sub_path()
        self.ctx.arc(*center, radius, 0, np.pi*2.)
        self._fillstroke()

    def ellipse(self, *args, mode=None):
        """Draw an ellipse with center, width and height.

        Input arguments can be in the following formats:

        - ~[center_x, center_y], [width, height]~,
        - ~[center_x, center_y], width, height~,
        - ~center_x, center_y, width, height~
        """

        if mode is None:
            mode = self._ellipse_mode

        if len(args) == 3:
            center = args[0]
            w, h = args[1:]
        elif len(args) == 4:
            center = args[:2]
            w, h = args[2:]
        else:
            center = args[0]
            w, h = args[1]

        if mode.lower() == 'corners':
            x1, y1 = center
            x2, y2 = w, h
            center = np.array([x1 + x2, y1 + y2])/2
            w, h = abs(x2 - x1), abs(y2 - y1)

        if not (w > 0 and h > 0):
            return

        self.push()
        self.translate(center)

        if mode.lower() == 'corner':
            self.translate(w/2, h/2)

        self.scale([w/2,h/2])

        self.ctx.new_sub_path()
        self.ctx.arc(0, 0, 1, 0, np.pi*2.)
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
        """Draw an arc given the center of the ellipse ~x, y~
        the size of the ellipse ~w, h~ and the initial and final angles
        in radians  ~start, stop~.
        NB. this differs from Processing/P5js as it always draws

        Input arguments can be in the following formats:

          - ~x, y, w, h, start, stop~
          - ~[x, y]~, ~[w, h]~, ~[start, stop]~
          - ~[x, y]~, ~w, h, start, stop~

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

        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)
            self.ctx.new_sub_path()
            self.ctx.move_to(0, 0)
            self.ctx.arc(0, 0, 1, start, stop)
            self.ctx.fill()
        if self.cur_stroke is not None:
            lw = self.ctx.get_line_width()
            self.ctx.set_line_width(lw*(2.0/min(w, h)))
            self.ctx.set_source_rgba(*self.cur_stroke)
            self.ctx.new_sub_path()
            self.ctx.arc(0, 0, 1, start, stop)
            self.ctx.stroke()
            self.ctx.set_line_width(lw)

            # if self.cur_stroke is not None:
            #     self.ctx.fill_preserve()
            # else:
            #     self.ctx.fill()
        self.pop()

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
        ''' End drawing a contour

        Arguments:

        - ~close~ (bool, optional): if ~True~ close the contour
        '''
        if isinstance(close, str):
            if close.lower() == 'close':
                close = True
            else:
                close = False
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
            self.ctx.move_to(*Cp[0])
            for i in range(0, len(Cp)-1, 3):
                self.ctx.curve_to(*Cp[i+1], *Cp[i+2], *Cp[i+3])
        else:
            cur = self.curve_segments[0].pop(0)

            self.ctx.move_to(*cur)
            for seg, type in zip(self.curve_segments, self.curve_segment_types):
                if not seg:
                    continue
                if type=='C':
                    P = [cur] + seg
                    Cp = cardinal_spline(P, self.tension, False)
                    for i in range(0, len(Cp)-1, 3):
                        self.ctx.curve_to(*Cp[i+1], *Cp[i+2], *Cp[i+3])
                elif type=='B':
                    # Cubic Bezier segment
                    for i in range(0, len(seg), 3):
                        self.ctx.curve_to(*seg[i], *seg[i+1], *seg[i+2])
                else:
                    for p in seg:
                        self.ctx.line_to(*p)
                cur = seg[-1]

        if close:
            self.ctx.close_path()
        self._fillstroke()

    def _add_curve_segment(self, type):
        self.curve_segments.append([])
        self.curve_segment_types.append(type)

    def vertex(self, x, y=None):
        ''' Add a vertex to current contour

        Input arguments can be in the following formats:

        - ~[x, y]~
        - ~x, y~
        '''
        if y is None:
            x, y = x
        if (not self.curve_segments or
            self.curve_segment_types[-1] != 'L'):
            self._add_curve_segment('L')

        self.curve_segments[-1].append([x, y])

    def curve_vertex(self, x, y=None):
        ''' Add a curved vertex to current contour

        Input arguments can be in the following formats:

        - ~[x, y]~
        - ~x, y~
        '''
        if y is None:
            x, y = x
        if (not self.curve_segments or
            self.curve_segment_types[-1] != 'C'):
            self._add_curve_segment('C')
        self.curve_segments[-1].append([x,y])

    def bezier_vertex(self, *args):
        ''' Draw a cubic Bezier segment from the current point
        requires a first control point to be already defined with ~vertex~.


        Requires three points. Input arguments can be in the following formats:

        - ~[x1, y1], [x2, y2], [x3, y3]~
        - ~x1, y1, x2, y2, x3, y3~
        '''
        if len(args) == 3:
            p1, p2, p3 = args
        else:
            p1 = args[:2]
            p2 = args[2:4]
            p3 = args[4:6]
        if not self.curve_segments:
            raise ValueError('bezier_vertex requires an initial vertex to work')
        if self.curve_segment_types[-1] != 'B':
            self._add_curve_segment('B')
        self.curve_segments[-1].append(p1)
        self.curve_segments[-1].append(p2)
        self.curve_segments[-1].append(p3)

    def curve_tightness(self, val):
        ''' Sets the 'tension' parameter for the curve used when using ~curve_vertex~
        '''
        self.tension = val

    # def vertex(self, x, y=None):
    #     ''' Add a vertex to current contour
    #     Arguments:
    #     Input arguments can be in the following formats:
    #      ~[x, y]'
    #      ~x, y~
    #     '''
    #     if y is None:
    #         x, y = x
    #     if not self._cur_point:
    #         self.ctx.move_to(x, y)
    #     else:
    #         self.ctx.line_to(x, y)
    #     self._cur_point = [x, y]

    def cubic(self, *args):
        ''' Draw a cubic bezier curve

        Input arguments can be in the following formats:

        - ~[x1, y1], [x2, y2], [x3, y3]~
        - ~x1, y1, x2, y2, x3, y3~
        '''
        if len(args) == 4:
            p0, p1, p2, p3 = args
        else:
            p0 = args[:2]
            p1 = args[2:4]
            p2 = args[4:6]
            p3 = args[6:8]
        self.ctx.move_to(*p0)
        self.ctx.curve_to(*p1, *p2, *p3)
        self._fillstroke()

    def quadratic(self, *args):
        ''' Draw a quadratic bezier curve

        Input arguments can be in the following formats:

        -    ~[x1, y1], [x2, y2]~
        -    ~x1, y1, x2, y2~
        '''
        if len(args) == 3:
            (x0, y0), (x1, y1), (x2, y2) = args
        else:
            x0, y0, x1, y1, x2, y2 = args

        self.ctx.move_to(*p0)
        self.ctx.curve_to(
            (2 * x1 + x0) / 3,
            (2 * y1 + y0) / 3,
            (2 * x1 + x2) / 3,
            (2 * y1 + y2) / 3,
            x2, y2)
        self._fillstroke()


    # def quadratic_to_cubic(self, x1, y1, x2, y2):
    #     ''' Convert a quadratic bezier curve to a cubic bezier curve
    #     Arguments:
    #     Input arguments can be in the following formats:
    #         ~x1, y1, x2, y2~
    #     '''
    #     x0, y0 = self._cur_point
    #     self.ctx.curve_to(
    #                         2.0 / 3.0 * x1 + 1.0 / 3.0 * x0,
    #                         2.0 / 3.0 * y1 + 1.0 / 3.0 * y0,
    #                         2.0 / 3.0 * x1 + 1.0 / 3.0 * x2,
    #                         2.0 / 3.0 * y1 + 1.0 / 3.0 * y2,
    #                         y1, y2)

    def bezier(self, *args):
        ''' Draws a bezier curve segment from current point
            The degree of the curve (2 or 3) depends on the input arguments
        Arguments:
        Input arguments can be in the following formats:
            ~[x1, y1], [x2, y2], [x3, y3]~ is cubic
            ~x1, y1, x2, y2, x3, y3~ is cubic
            ~[x1, y1], [x2, y2]~ is quadratic
            ~x1, y1, x2, y2~ is quadratic
        '''
        if len(args) == 4 or len(args)==8:
            self.cubic(*args)
        else:
            self.quadratic(*args)

    def create_graphics(self, w, h):
        ''' Create a new canvas with the specified width and height
            E.g. ~c = create_graphics(128, 128)~ will put a new canvas into
            the variable ~c~. You can draw the contents of the canvas with the ~image~ function.
        '''
        return Canvas(w, h)

    def image(self, img, *args, opacity=1.0):
        """Draw an image at position with (optional) size and (optional) opacity

        Arguments:

        - ~img~: The input image. Can be either a PIL image, a numpy array, a Canvas or a pyCairo surface.
        - optional arguments: position and size can be specified with the following formats:
            - ~x, y~:  position only
            - ~x, y, w, h~: position and size
            - ~[x, y]~: position only (also a numpy array or tuple are valid)
            - ~[x, y], [w, h]~: position and size
        if the position is not specified, the original image dimensions will be used

        - ~opacity~: a value between 0 and 1 specifying image opacity.

        """

        if isinstance(img, Canvas):
            img = img.surf
        else:
            if not isinstance(img, np.ndarray):
                # This should take care of tensors and PIL Images
                img = np.array(img)
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

    def shape(self, poly_list, close=False):
        '''Draw a shape represented as a list of polylines, see the ~polyline~
        method for the format of each polyline
        '''

        self.begin_shape()
        for P in poly_list:
            self.polyline(P, close=close)
        self.end_shape()

    def text(self, text, *args, align='', valign='', center=None, **kwargs):
        ''' Draw text at a given position

        Arguments:

            - ~text`, the text to display
            - the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
            - ~align~, horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
            - ~valign~, vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~
            (Deprecated) if center=True the text will be horizontally centered
        '''

        # Backwards compatibility since previous version has position first
        if type(text) != str:
            if len(args) != 1:
                raise ValueError("text: wrong number of args")
            print("Position before text is deprecated")
            print('Use text("text", pos) instead')
            pos, text = text, args[0]
        elif len(args) == 2:
            pos = args
        elif len(args) == 1:
            pos = args[0]
        else:
            raise ValueError("text: wrong number of args")

        if self.cur_fill is not None:
            self.ctx.set_source_rgba(*self.cur_fill)

        if center is not None:
            if center:
                align = 'center'
            else:
                align = 'left'

        ox, oy = self._text_offset(text, align, valign)

        self.ctx.move_to(pos[0]+ox, pos[1]+oy)
        self.ctx.text_path(text)
        self._fillstroke()

        #self.ctx.fill()

    # def text_bounds(self, text, *args):
    #     { x: 5.7, y: 12.1 , w: 9.9, h: 28.6 }.

    def text_shape(self, text, *args, dist=1, align='', valign=''):
        ''' Retrieves polylines for a given string of text in the current font

        Arguments:

        - ~text`, the text to sample
        - the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
        - ~dist~, approximate distance between samples
        - ~align~, horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
        - ~valign~, vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~
        '''

        if len(args) == 2:
            if is_number(args[0]):
                pos = args
            else:
                pos = args[0]
                dist = args[1]
        elif len(args) == 3:
            pos = args[:2]
            dist = args[2]
        elif len(args) == 1:
            pos = args[0]
        else:
            print(args, len(args))
            raise ValueError("text: wrong number of args")

        ctx = self.ctx
        pos = np.array(pos, dtype=np.float32)
        pos += self._text_offset(text, align, valign)
        # Extract path data
        ctx.text_path(text)
        path = ctx.copy_path()
        # Clear path so we don't draw
        ctx.new_path()
        shape = []

        def prev():
            return shape[-1][-1][-1]

        def sample_line(points):
            a = prev()
            b = np.array(points)
            s = np.linalg.norm(b - a)
            n = max(int(s / dist)+1, 2)
            t = np.linspace(0, 1, n)[1:]
            res = a + (b - a)*t.reshape(-1, 1)
            return res

        def sample_cubic(points):

            b, c, d = [np.array(p) for p in [points[:2], points[2:4], points[4:6]]]
            #return sample_line(d)
            a = prev()
            s = approx_arc_length_cubic(a, b, c, d)
            n = max(int(s / dist)+1, 2)
            t = np.linspace(0, 1, n)[1:]
            P = np.array([a, b, c, d])
            res = eval_bezier(P, t)
            #print('cubic', res.shape)
            return res


        for kind, points in path:
            if kind == cairo.PATH_MOVE_TO:
                shape.append([np.array([points])])
            elif kind == cairo.PATH_LINE_TO:
                shape[-1].append(sample_line(points))
            elif kind == cairo.PATH_CURVE_TO:
                shape[-1].append(sample_cubic(points))
            elif kind == cairo.PATH_CLOSE_PATH:
                shape[-1].append(sample_line(shape[-1][0][0]))
        res = [np.vstack(P)+pos for P in shape]
        #print(res)
        return [P for P in res if len(P) > 1]

    def text_points(self, text, *args, dist=1, align='', valign=''):
        ''' Retrieves points for a given string of text in the current font

        Arguments:

        - ~text`, the text to sample
        - the position of the text, either a pair of x, y arguments or a list like object (e.g. ~[x, y]~)
        - ~dist~, approximate distance between samples
        - ~align~ (named), horizontal alignment, etiher ~'left'~ (default), ~'center'~ or ~'right'~
        - ~valign~ (named), vertical alignment, etiher ~'bottom'~ (default), ~'center'~ or ~'top'~
        '''
        return np.vstack(self.text_shape(text, *args,
                                         dist=dist,
                                         align=align, valign=valign))

    def _text_offset(self, text, align, valign):
        (x_bearing, y_bearing, w, h, x_advance, y_advance) = self.ctx.text_extents(text)
        if not align:
            align = self.text_halign
        if not valign:
            valign = self.text_valign

        ox = 0
        oy = 0
        if align == 'center':
            ox = -(w/2 + x_bearing)
        elif align == 'right':
            ox = -(w + x_bearing)
        if valign == 'top':
            oy = -y_bearing
        elif valign == 'center':
            oy = -(h/2 + y_bearing)
        return ox, oy

    def text_bounds(self, text, *args, align='', valign=''):
        ''' Returns the bounding box of a string of text at a given position'''
        if len(args) == 2:
            pos = args
        elif len(args) == 1:
            pos = args[0]
        else:
            pos = np.zeros(2)

        (x_bearing, y_bearing, w, h, x_advance, y_advance) = self.ctx.text_extents(text)
        ox, oy = self._text_offset(text, align, valign)
        x, y = pos[0]+ox, pos[1]+oy-h
        return edict({'x':x, 'y':y,
                      'pos':np.array([x, y]),
                      'w':w, 'h':h,
                      'size': np.array([w, h])})

    def polygon(self, *args, close=True):
        ''' Draw a polygon (closed by default).

        The polyline is specified as either:

        - a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
        - a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To create an opne polygon set the named ~close~ argument to ~False~, e.g. ~c.polygon(points, close=False)~.
        '''
        self.polyline(*args, close=close)

    def curve(self, *args, close=True):
        ''' Draw a curve (open by default).

        The polyline is specified as either:

        - a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
        - a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To close the curve set the named ~close~ argument to ~True~, e.g. ~c.curve(points, close=True)~.
        '''
        if len(args)==1:
            points = args[0]
        elif len(args)==2:
            points = np.vstack(args).T
        else:
            raise ValueError("Wrong number of arguments")

        self.begin_contour()
        for p in points:
            self.curve_vertex(p)
        self.end_contour(close)

    def polyline(self, *args, close=False):
        ''' Draw a polyline (open by default).

        The polyline is specified as either:

        - a list of ~[x,y]~ pairs (e.g. ~[[0, 100], [200, 100], [200, 200]]~)
        - a numpy array with shape ~(n, 2)~, representing ~n~ points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To close the polyline set the named ~close~ argument to ~True~, e.g. ~c.polyline(points, close=True)~.
        '''
        self.ctx.new_sub_path()
        #self.ctx.new_path()
        if len(args)==1:
            points = args[0]
        elif len(args)==2:
            points = np.vstack(args).T
        else:
            raise ValueError("Wrong number of arguments")
        self.ctx.move_to(*points[0])
        for p in points[1:]:
            self.ctx.line_to(*p)
        if close:
            self.ctx.close_path()

        self._fillstroke()

    def identity(self):
        self.ctx.identity_matrix()

    def copy(self, *args):
        ''' The first parameter can optionally be an image, if an image is not specified the funtion will use
        the canvas image, .
        The next four parameters, sx, sy, sw, and sh determine the region to copy from the source image.
        (sx, sy) is the top-left corner of the region. sw and sh are the region's width and height.
        The next four parameters, dx, dy, dw, and dh determine the region of the canvas to copy into.
        (dx, dy) is the top-left corner of the region. dw and dh are the region's width and height.

        ~copy(src_image, sx, sy, sw, sh, dx, dy, dw, dh)~
        or
        ~copy(sx, sy, sw, sh, dx, dy, dw, dh)~
        '''

        if len(args) % 2 == 1:
            pdb.set_trace()
            img = np.array(args[0])
            args = args[1:]
        else:
            img = self.get_image()

        if len(args)==8:
            sx, sy, sw, sh, dx, dy, dw, dh = args
        else:
            ValueError("Unspported number of arguments for copy")

        img = img[sy:sy+sh,
                  sx:sx+sw]
        self.image(img, dx, dy, dw, dh)

    def background(self, *args):
        ''' Clear the canvas with a given color
            Accepts either an array with the color components, or single color components (as in ~fill~)
        '''
        # self.clear_callback()
        # HACK Save background, this is needed for saving and no_loop in sketches
        # Since saving has to be done as a postprocess after the frame
        if len(args)==1:
            self.last_background = args[0]
        else:
            self.last_background = args

        self.ctx.identity_matrix()
        # HACK - we don't want to necessarily save the background when exporting SVG
        # Especially if we want to plot the output, so only draw the background to the
        # bitmap surface if that is the case.
        if self._save_background:
            ctx = self.ctx
        else:
            ctx = self.ctx.ctxs[0]
        ctx.set_source_rgba(*self._apply_colormode(self._convert_rgba(args)))
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.fill()

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
        ''' Save the canvas to an image

        Arguments:

        - The path where to save

        '''
        self.surf.write_to_png(path)

    def save_svg(self, path):
        ''' Save the canvas to an svg file

        Arguments:

        - The path where to save

        '''
        if self.recording_surface is None:
            raise ValueError('No recording surface in canvas')
        surf = cairo.SVGSurface(path, self.width, self.height)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.recording_surface)
        ctx.paint()
        surf.finish()
        fix_clip_path(path, path)

    def save_pdf(self, path):
        ''' Save the canvas to an svg file

        Arguments:

        - The path where to save

        '''
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
        ''' Save the canvas into a given file path
            The file format depends on the file extension
        '''
        if '.svg' in path:
            self.save_svg(path)
        elif '.pdf' in path:
            self.save_pdf(path)
        elif '.png' in path:
            # TODO use PIL
            self.save_image(path)


    def show(self, size=None):
        ''' Display the canvas in a notebook'''
        if size is not None:
            display(Image.fromarray(self.get_image()).resize(size))
            return
        display(Image.fromarray(self.get_image()))


    def show_plt(self, size=None, title='', axis=False):
        ''' Show the canvas in a notebook with matplotlib

        Arguments:

        - ~size~ (tuple, optional): The size of the displayed image, by default this is the size of the canvas
        - ~title~ (string, optional): A title for the figure
        - ~axis~ (bool, optional): If ~True~ shows the coordinate axes
        '''
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
                return np.array(x[0])/self.color_scale[:len(x[0])]
            return (x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0])
        return (x[0]/self.color_scale[0],
                x[1]/self.color_scale[1],
                x[2]/self.color_scale[2])

    def _convert_rgba(self, x):
        if len(x)==1:
            if type(x[0]) == str:
                return self._convert_html_color(x[0])
            elif not is_number(x[0]): # array like input
                return self._convert_rgba(*x)
                #return np.array(x[0])/self.color_scale[:len(x[0])]
            return (x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0], 1.0)
        elif len(x) == 3:
            return (x[0]/self.color_scale[0],
                    x[1]/self.color_scale[1],
                    x[2]/self.color_scale[2], 1.0)
        elif len(x) == 2:
            if type(x[0]) == str:
                clr = self._convert_html_color(x[0])
                clr[-1] = x[1]/self.color_scale[-1]
                return clr
            return (x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0],
                    x[0]/self.color_scale[0],
                    x[1]/self.color_scale[3])
        return (x[0]/self.color_scale[0],
                x[1]/self.color_scale[1],
                x[2]/self.color_scale[2],
                x[3]/self.color_scale[3])

def radians(x):
    ''' Get radians given an angle in degrees'''
    return np.pi/180*x

def degrees(x):
    ''' Get degrees given an angle in radians'''
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
            if arr.dtype == np.uint8:
                arr = np.dstack([arr, np.ones(arr.shape[:2], dtype=np.uint8)*255])
            else:
                arr = np.dstack([arr, np.ones(arr.shape[:2])])
                arr = (arr * 255).astype(np.uint8)
        elif arr.shape[2] == 1:
            if arr.dtype == np.uint8:
                arr = np.dstack([arr]*3 + [np.ones(arr.shape[:2], dtype=np.uint8)*255])
            else:
                arr = np.dstack([arr]*3 + [np.ones(arr.shape[:2])])
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

    Arguments:

    - ~name~: Either an integer indicating the device number, or a string indicating the path of a video file
    - ~size~: A tuple indicating the desired size of the video frames (width, height)
    - ~resize_mode~: A string indicating the desired resize mode. Can be 'crop' or 'stretch'
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


def bernstein(n, i):
    bi = comb(n, i)
    return lambda t, bi=bi, n=n, i=i: bi * t**i * (1 - t)**(n - i)


def eval_bezier(P, t, d=0):
    '''Bezier curve of degree len(P)-1. d is the derivative order (0 gives positions)'''
    n = len(P) - 1
    if d > 0:
        Q = np.diff(P, axis=0)*n
        return eval_bezier(Q, t, d-1)
    B = np.vstack([bernstein(n, i)(t) for i, p in enumerate(P)])
    return (P.T @ B).T


def approx_arc_length_cubic(c0, c1, c2, c3):
    v0 = np.linalg.norm(c1-c0)*0.15
    v1 = np.linalg.norm(-0.558983582205757*c0 + 0.325650248872424*c1 + 0.208983582205757*c2 + 0.024349751127576*c3)
    v2 = np.linalg.norm(c3-c0+c2-c1)*0.26666666666666666
    v3 = np.linalg.norm(-0.024349751127576*c0 - 0.208983582205757*c1 - 0.325650248872424*c2 + 0.558983582205757*c3)
    v4 = np.linalg.norm(c3-c2)*.15
    return v0 + v1 + v2 + v3 + v4

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

# Optional perlin noise init
_perlin_octaves = 4
_perlin_falloff = 0.5

def noise_seed(seed):
    """ Sets the seed for the noise generator
    """
    global perlin

    if perlin is None:
        raise ValueError('Noise is not installed. use `pip install perlin-noise`')
    perlin = PerlinNoise(seed=seed)

def noise_detail(octaves, falloff=0.5):
    """ Adjusts the character and level of detail produced by the Perlin noise function.

    Arguments:

    - ~octaves~ (int): the number of noise 'octaves'. Each octave has double the frequency of the previous.
    - ~falloff~ (float, default 0.5): a number between 0 and 1 that multiplies the amplitude of each consectutive octave
    """
    global _perlin_falloff, _perlin_octaves

    if perlin is None:
        raise ValueError('Noise is not installed. use `pip install perlin-noise`')

    _perlin_falloff = falloff
    _perlin_octaves = octaves

def noise(*args):
    """ Returns a Perlin noise value (between 0 and 1) at a given coordinate.
    Noise is created by summing consecutive "octaves" with increasing level of detail.
    Each octave has double the frequency of the previous and an amplitude falls off for each octave. By default the falloff is 0.5.
    The default number of octaves is ~4~. Use `noise_detail~ to set the number of octaves and falloff.

    Arguments:

    - The arguments to this function can vary from 1 to 3, determining the "space" that is sampled to generate noise.
    The function also accepts a single array parameter with 1 to 3 elements.
    """
    if perlin is None:
        raise ValueError('Noise is not installed. use `pip install perlin-noise`')
    if len(args) > 1:
        x = np.array(args)
    else:
        if not is_number(args[0]):
            x = np.array(args[0]) #np.array(args[0])
        else:
            x = [args[0]]

    amp = 1.0
    ampsum = 0
    v = 0.0

    for i in range(_perlin_octaves):
        v += (perlin(tuple(x)))*amp
        x *= 2
        ampsum += amp
        amp *= _perlin_falloff
    v /= ampsum
    return v+0.5


# Code adapted from https://www.cairographics.org/cookbook/freetypepython/

_ft_initialized = False
def create_cairo_font_face_for_file (filename, faceindex=0, loadoptions=0):
    "given the name of a font file, and optional faceindex to pass to FT_New_Face" \
    " and loadoptions to pass to cairo_ft_font_face_create_for_ft_face, creates" \
    " a cairo.FontFace object that may be used to render text with that font."
    global _ft_initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface
    global _PycairoContext
    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _ft_initialized:
        # find shared objects
        if sys.platform == "win32":
            ft_lib = "freetype6.dll"
            lc_lib = "libcairo-2.dll"
        elif sys.platform == "darwin":
            ft_lib = "libfreetype.dylib"
            lc_lib = "libcairo.2.dylib"
        else:
            ft_lib = "libfreetype.so.6"
            lc_lib = "libcairo.so.2"

        try:
            _freetype_so = ct.CDLL (ft_lib)
        except OSError as e:
            print(e)
            print("Freetype library missing")
            print("Possibly install with: mamba install freetype")

        _cairo_so = ct.CDLL (lc_lib)
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ ct.c_void_p, ct.c_int ]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_set_font_face.argtypes = [ ct.c_void_p, ct.c_void_p ]
        _cairo_so.cairo_font_face_status.argtypes = [ ct.c_void_p ]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ ct.c_void_p ]
        # initialize freetype
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if  status != FT_Err_Ok :
            raise RuntimeError("Error %d initializing FreeType library." % status)
        #end if

        class PycairoContext(ct.Structure):
            _fields_ = \
                [
                    ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                    ("ctx", ct.c_void_p),
                    ("base", ct.c_void_p),
                ]
        #end PycairoContext
        _PycairoContext = PycairoContext

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int() # dummy address
        _ft_initialized = True
    #end if

    ft_face = ct.c_void_p()
    cr_face = None
    try :
        # load FreeType face
        status = _freetype_so.FT_New_Face(_ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face))
        if status != FT_Err_Ok :
            raise RuntimeError("Error %d creating FreeType font face for %s" % (status, filename))
        #end if

        # create Cairo font face for freetype face
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS :
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        #end if
        # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
        # destroyed, so we have to do that for it, by attaching a cleanup callback to
        # the font_face. This only needs to be done once for each font face, while
        # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
        # twice with the same FT Face.
        # The following check for whether the cleanup has been attached or not is
        # actually unnecessary in our situation, because each call to FT_New_Face
        # will return a new FT Face, but we include it here to show how to handle the
        # general case.
        if _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key)) == None :
            status = _cairo_so.cairo_font_face_set_user_data \
              (
                cr_face,
                ct.byref(_ft_destroy_key),
                ft_face,
                _freetype_so.FT_Done_Face
              )
            if status != CAIRO_STATUS_SUCCESS :
                raise RuntimeError("Error %d doing user_data dance for %s" % (status, filename))
            #end if
            ft_face = None # Cairo has stolen my reference
        #end if

        # set Cairo font face into Cairo context
        cairo_ctx = cairo.Context(_surface)
        cairo_t = _PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS :
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        #end if

    finally :
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)
    #end try

    # get back Cairo font face as a Python object
    face = cairo_ctx.get_font_face()
    return face
