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
import os
import numpy as np
import numbers
import copy, sys, types
import ctypes as ct
from math import fmod, pi, comb
from PIL import Image
import importlib
import importlib.util
from contextlib import contextmanager
from easydict import EasyDict as edict
import rumore  # Noise utils
from dataclasses import dataclass
from typing import Union, Optional
from fontTools.ttLib import TTFont
from . import renderer as rend
import pdb


class Shape:
    """
    Holds a list of contours, each contour being a sequence of drawing commands.
    Mirrors Processing's PShape: use begin_shape()/end_shape() to construct.
    """
    def __init__(self, tension=0.5):
        self.tension = tension
        self.contours = []           # list of contour command lists
        self._current_contour = None # list of commands for the contour being built
        self._curve_points = []      # pending Catmull‑Rom points for curve_vertex
        self._spline_start = None    # first point of the current spline (move-to)
        self._active = False         # True between begin_shape()/end_shape()
        self.style = {}

    def no_fill(self):
        self.fill(None)

    def no_stroke(self):
        self.stroke(None)
        return self
    
    def fill(self, *args):
        self.style['fill'] = args
        return self
    
    def stroke(self, *args):
        self.style['stroke'] = args
        return self
    
    def stroke_weight(self, w):
        self.style['stroke_weight'] = w
        return self
    
    def begin_shape(self):
        """Start building the shape. Clears any previous geometry."""
        self._active = True
        self.contours = []
        self._current_contour = None
        self._curve_points = []
        self._spline_start = None
        return self
    
    def end_shape(self, close=False):
        """
        Finish building the shape.
        If close is True, the last contour is closed before finalising.
        """
        if self._active:
            if self._current_contour is not None:
                self.end_contour(close)
            self._active = False
        return self
    
    def begin_contour(self):
        """Start a new contour. Must be called after begin_shape()."""
        if not self._active:
            raise RuntimeError("begin_shape() must be called before add_contour()")
        self._flush_spline()
        self._current_contour = []
        self.contours.append(self._current_contour)
        self._curve_points = []
        self._spline_start = None
        return self
    
    def vertex(self, x, y=None):
        """Add a straight vertex ."""
        if y is None:
            x, y = x

        self._start_contour_if_needed()
        self._flush_spline()
        if not self._current_contour:
            self._current_contour.append(('M', (x, y)))
        else:
            self._current_contour.append(('L', (x, y)))
        return self
    
    def curve_vertex(self, x, y=None):
        """Add a curved vertex (Catmull Rom spline)."""
        if y is None:
            x, y = x

        self._start_contour_if_needed()
        if not self._curve_points:
            if self._current_contour and self._current_contour[-1][0] in ('M', 'L'):
                self._spline_start = self._current_contour[-1][1]
            else:
                self._spline_start = None
        self._curve_points.append((x, y))
        return self
    
    def bezier_vertex(self, *args):
        """Add a cubic Bézier vertex; three control points."""
        if len(args) == 3:
            p1, p2, p3 = args
        else:
            p1 = np.array(args[:2])
            p2 = np.array(args[2:4])
            p3 = np.array(args[4:6])
        self._start_contour_if_needed()
        self._flush_spline()
        self._current_contour.append(
            ('C', (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]))
        )
        return self
    
    def polyline(self, points, closed=False):
        """Add a contour of straight line segments from a sequence of (x,y) points."""
        if not self._active:
            self.begin_shape()          # temporary activation for standalone use
        self.begin_contour()
        for i, p in enumerate(points):
            self.vertex(*p)         # line-to
        self.end_contour(closed)
        return self
    
    def end_contour(self, close=False):
        """Finish the current contour. If close=True, the contour is closed."""
        self._flush_spline(close=close)
        if close and self._current_contour:
            self._current_contour.append(('Z',))
        self._current_contour = None
        self._curve_points = []
        self._spline_start = None
        return self
    
    def polyline(self, points, closed=False):
        """Add a contour of straight line segments from a sequence of (x,y) points."""
        if not self._active:
            self.begin_shape()          # temporary activation for standalone use
        self.begin_contour()
        for i, p in enumerate(points):
            if i == 0:
                self.vertex(*p)         # move-to
            else:
                self.vertex(*p)         # line-to
        self.end_contour(closed)
        return self

    def multibezier(self, points, closed=False):
        """
        Add a contour of cubic Bézier segments.
        points: flat list of (x,y) pairs; first is move‑to, then triples are Bézier
                control points (p1, p2, p3), p1 being the first control point, etc.
        """
        if not self._active:
            self.begin_shape()
        self.begin_contour()
        # first point is move-to
        self.vertex(*points[0])
        for i in range(1, len(points)-2, 3):
            p1 = points[i]
            p2 = points[i+1]
            p3 = points[i+2]
            self._current_contour.append(
                ('C', (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])))
        self.end_contour(closed)
        return self

    def curve(self, points, close=False):
        """
        Add a contour of smooth Cardinal spline segments.
        points: sequence of (x,y) knots.
        """
        if not self._active:
            self.begin_shape()
        self.begin_contour()
        for i, p in enumerate(points):
            self.curve_vertex(*p)
        self.end_contour(close)
        return self

    def _start_contour_if_needed(self):
        if self._current_contour is None:
            self.begin_contour()

    def _flush_spline(self, close=False):
        if not self._curve_points or len(self._curve_points) < 2:
            self._curve_points = []
            self._spline_start = None
            return

        # Build full points list: include previous anchor if available
        pts = list(self._curve_points)
        if self._spline_start is not None:
            pts = [self._spline_start] + pts
        pts = np.array(pts)

        cp = cardinal_spline(pts, self.tension, closed=close)
        n_seg = len(pts) - 1 if not close else len(pts)

        self._current_contour.append(('M', cp[0]))
        for si in range(n_seg):
            c1 = cp[1 + 3*si]
            c2 = cp[2 + 3*si]
            end = cp[3 + 3*si]
            self._current_contour.append(
                ('C', (c1[0], c1[1], c2[0], c2[1], end[0], end[1]))
            )

        self._curve_points = []
        self._spline_start = None

    def apply(self, renderer):
        """Replay all contours onto a Cairo context (does not fill/stroke)."""
        for contour in self.contours:
            if not contour:
                continue
            first = contour[0]
            renderer.new_sub_path()
            if first[0] != 'M':
                raise ValueError("Contour must start with a move-to command")
            renderer.move_to(*first[1])
            for cmd in contour[1:]:
                if cmd[0] == 'L':
                    renderer.line_to(*cmd[1])
                elif cmd[0] == 'C':
                    c1x, c1y, c2x, c2y, ex, ey = cmd[1]
                    renderer.curve_to(c1x, c1y, c2x, c2y, ex, ey)
                elif cmd[0] == 'Z':
                    renderer.close_path()

                    
def is_number(x):
    return isinstance(x, numbers.Number)

        
class CanvasState:
    def __init__(self, c):
        self.c = c
        self.cur_fill = c._scale_color([255.0])
        self.cur_stroke = c._scale_color([0.0])
        self.cur_tint = c._scale_color([255.0])
        self._stroke_cap = "round"
        self._stroke_join = "miter"
        self._text_halign = "left"
        self._text_valign = "baseline"
        self._rect_mode = "corner"
        self._ellipse_mode = "center"
        self._font = "sans-serif"
        self._text_size = 16
        self._text_leading = 16
        self._line_width = 1.0
        self._angle_mode = 'radians'
        self._dash = []

    def set(self, prev=None):
        ''' Called if calling pop'''
        def should_set(prev, name):
            if prev is None:
                return True
            return prev.__dict__[name] != self.__dict__[name]

        if should_set(prev, "_stroke_cap"):
            self.c.stroke_cap(self._stroke_cap)
        if should_set(prev, "_stroke_join"):
            self.c.stroke_join(self._stroke_join)
        if should_set(prev, "_line_width"):
            self.c.stroke_weight(self._line_width)
        if should_set(prev, "_text_size"):
            self.c.text_size(self._text_size)
        if should_set(prev, "_dash"):
            self.c.stroke_dash(self._dash)

            
def draw_states_properties(*names):
    def decorator(cls):
        for name in names:
            def getter(self, n=name):
                return getattr(self.draw_states[-1], n)
            def setter(self, value, n=name):
                setattr(self.draw_states[-1], n, value)
            setattr(cls, name, property(getter, setter))
        return cls
    return decorator


@dataclass
class Font:
    obj: Union[str, object]
    size: int = None
    style: str = None

    
class Gradient:
    def __init__(self, kind, **kw):
        import cairo
        extend_modes = {
            'none': cairo.EXTEND_NONE,
            'pad': cairo.EXTEND_PAD,
            'repeat': cairo.EXTEND_REPEAT,
            'reflect': cairo.EXTEND_REFLECT,
        }
        stops = kw.pop('stops', [])
        extend = extend_modes.get(kw.pop('extend', 'pad'), cairo.EXTEND_PAD)

        if kind == 'linear':
            start = kw.get('start', (0, 0))
            end   = kw.get('end', (1, 0))
            grad = cairo.LinearGradient(*start, *end)
        elif kind == 'radial':
            inner = kw.get('inner', (0, 0, 0))
            outer = kw.get('outer', (0, 0, 1))
            grad = cairo.RadialGradient(*inner, *outer)
        else:
            raise ValueError("kind must be 'linear' or 'radial'")

        grad.set_extend(extend)

        for stop in stops:
            if len(stop) == 4:
                grad.add_color_stop_rgb(*stop)
            elif len(stop) == 5:
                grad.add_color_stop_rgba(*stop)
            else:
                raise ValueError("stops must be (offset,r,g,b) or (offset,r,g,b,a)")

        self.gradient = grad

    @classmethod
    def linear(cls, start, end, stops, extend='pad'):
        return cls('linear', start=start, end=end, stops=stops, extend=extend)

    @classmethod
    def radial(cls, inner, outer, stops, extend='pad'):
        return cls('radial', inner=inner, outer=outer, stops=stops, extend=extend)

    
@draw_states_properties(
    "cur_fill",
    "cur_stroke",
    "cur_tint",
    "_stroke_join",
    "_text_halign",
    "_text_valign",
    "_rect_mode",
    "_ellipse_mode",
    "_font",
    "_text_size",
    "_line_width",
    "_text_leading",
    "_angle_mode",
    "_dash",
)


class Canvas:
    """
    Defines a drawing canvas (pyCairo) that behaves similarly to p5js

    Constructor arguments:

    - =width= : (=int=), width of the canvas in pixels
    - =height= : (=int=), height of the canvas in pixels
    - =clear_callback= (optional): function, a callback to be called when the canvas is cleared (for internal use mostly)

    In a notebook you can create a canvas globally with either of:

    - =size(width, height)=
    - =create_canvas(width, height)=

    When using these functions all the canvas functionalities below will become globally available to the notebook.
    """
    def __init__(
        self,
        width,
        height,
        background=(200.0, 200.0, 200.0, 255.0),
        clear_callback=lambda: None,
        output_file="",
        recording=True,
        save_background=True,
        color_scale=255,
        backend='cairo',
        **kwargs
    ):
        """Constructor"""
        # # See https://pycairo.readthedocs.io/en/latest/reference/context.html
        # surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        # ctx = MultiContext(surf)
        if backend == 'cairo' and rend.CairoRenderer is not None:
            self.renderer = rend.CairoRenderer(width, height, recording=recording)
        else:
            self.renderer = rend.SVGRenderer(width, height)
        
        if 'cs' in kwargs:
            color_scale = kwargs['cs']

        # Create SVG surface for saving
        self.color_scale = np.ones(4) * color_scale

        # This is useful for py5sketch to reset SVG each time background is cleared
        self.clear_callback = clear_callback

        self._color_mode = "rgb"
        self._width = width
        self._height = height
        #self.surf = surf

        if save_background:
            self.renderer.set_source_rgba(*self._apply_colormode(background))
            self.renderer.paint()

        # ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        # #ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        # ctx.set_line_join(cairo.LINE_JOIN_MITER)
        # # ctx.set_antialias(cairo.ANTIALIAS_BEST)
        # ctx.set_source_rgba(*self._apply_colormode(background))
        # ctx.paint()  # rectangle(0, 0, width, height)

        self.last_background = background
        self._first_background = True

        # Keep track of draw states
        self.draw_states = [CanvasState(self)]
        self.draw_states[-1].set()

        self.no_draw = False

        self._save_background = save_background

        # Constants
        self.PI = pi
        self.TWO_PI = pi * 2
        self.HALF_PI = pi / 2
        self.QUARTER_PI = pi / 4
        self.CENTER = "center"
        self.TOP = "top"
        self.BOTTOM = "bottom"
        self.BASELINE = "baseline"
        self.CORNER = "corner"
        self.CORNERS = "corners"
        self.RADIUS = "radius"
        self.HSB = "hsv"
        self.HSV = "hsv"
        self.RGB = "rgb"
        self.CLOSE = "close"
        self.OPEN = "open"
        self.PIE = "pie"
        self.CHORD = "chord"
        self.MITER = "miter"
        self.BEVEL = "bevel"
        self.ROUND = "round"
        self.SQUARE = "square"
        self.PROJECT = "project"
        self.DEGREES = "degrees"
        self.RADIANS = "radians"

        # Shape building
        self.cur_shape = None      # current Shape being built
        self.tension = 0.5

        self.output_file = output_file
        # self.recording_surface = None
        # if output_file or recording:
        #     self.recording_surface = cairo.RecordingSurface(
        #         cairo.CONTENT_COLOR_ALPHA, None
        #     )
        #     recording_context = cairo.Context(self.recording_surface)
        #     self.ctx.push_context(recording_context)
        # else:
        #     print("Not creating recording context")

    def set_color_scale(self, scale):
        """Set color scale:

        Arguments:

        - `scale` (float): the color scale. if we want to specify colors in the `0...255` range,
         `scale` will be `255`. If we want to specify colors in the `0...1` range, `scale` will be `1`"""
        if is_number(scale):
            scale = np.ones(4) * scale
        self.color_scale[: len(scale)] = scale
        return self
    
    @property
    def cur_fill(self) -> np.ndarray:
        return self.draw_states[-1].cur_fill

    @cur_fill.setter
    def cur_fill(self, value):
        self.draw_states[-1].cur_fill = value

    @property
    def cur_stroke(self) -> np.ndarray:
        return self.draw_states[-1].cur_stroke

    @cur_stroke.setter
    def cur_stroke(self, value):
        self.draw_states[-1].cur_stroke = value

    def _get_stroke_or_fill_color(self):
        if self.cur_stroke is not None:
            return np.array(self.cur_stroke) * self.color_scale
        if self.cur_fill is not None:
            return np.array(self.cur_fill) * self.color_scale
        return None

    @property
    def center(self) -> np.ndarray:
        """The center of the canvas (as a 2d numpy array)"""
        return np.array([self._width / 2, self._height / 2])

    def get_width(self) -> int:
        """The width of canvas"""
        return self._width

    def get_height(self) -> int:
        """The height of canvas"""
        return self._height

    @property
    def width(self) -> int:
        """The width of canvas"""
        return self._width

    @property
    def height(self) -> int:
        """The height of canvas"""
        return self._height

    @property
    def surface(self):
        return self.renderer.get_surface()

    def no_fill(self):
        """Do not fill subsequent shapes"""
        self.fill(None)
        return self

    def no_stroke(self):
        """Do not stroke subsequent shapes"""
        self.stroke(None)
        return self

    def no_tint(self):
        """Do not tint images"""
        self.tint(None)
        return self

    def fill_rule(self, rule):
        """Sets the fill rule for complex shapes.

        Arguments:
        - One of `"evenodd"`, `"nonzero"`, or `"winding"`
        """
        self.renderer.set_fill_rule(rule)
        # rules = {
        #     "evenodd": cairo.FILL_RULE_EVEN_ODD,
        #     "nonzero": cairo.FILL_RULE_WINDING,
        #     "winding": cairo.FILL_RULE_WINDING,
        # }
        # if rule not in rules:
        #     print("Rule ", rule, " is not valid")
        #     print('Use either "nonzero" or "evenodd"')
        # self.ctx.set_fill_rule(rules[rule])
        return self

    def angle_mode(self, mode='degrees'):
        mode = mode.lower()
        if not mode in ['degrees', 'radians']:
            raise ValueError('invalid angle mode, use either RADIANS or DEGREES')
        self._angle_mode = mode
        return self

    def _to_radians(self, ang):
        if self._angle_mode == 'radians':
            return ang
        return radians(ang)

    def _to_degrees(self, ang):
        if self._angle_mode == 'degrees':
            return ang
        return degrees(ang)

    def color_mode(self, mode, *args):
        """Set the color mode for the canvas
        - `mode` (string): can be one of 'rgb', 'hsv' depending on the desired color mode
        - `scale` (float): the scale for the color values (e.g. 255 for 0...255 range, 1 for 0...1 range)
        - `*args`: color values in the current color mode

        Examples:

        - `color_mode('rgb', 1.0)` will set the color mode to RGB in the 0-1 range.

        Returns:

        - (float): red component value in the current color scale
         """
        self._color_mode = mode
        if len(args):
            if len(args) == 1:
                # Assume we set all scale to be equal
                self.set_color_scale(args[0])
            else:
                self.set_color_scale(args)
        return self

    def _is_hsv(self):
        mode = self._color_mode.lower()
        return mode == "hsv" or mode == "hsb"

    def _apply_colormode(self, clr):
        # Convert to 0,1 scale
        col = self._scale_color(clr)
        # If originally user provided a string return rgba
        if type(clr[0]) in [str, np.str_]:
            return col
        if self._is_hsv():
            return hsv_to_rgb(col)
        return col

    def red(self, *args) -> float:
        """Return the red component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): red component value in the current color scale
        """
        rgba = self._apply_colormode(args)*self.color_scale
        return rgba[0]

    def green(self, *args) -> float:
        """Return the green component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): green component value in the current color scale
        """
        rgba = self._apply_colormode(args)*self.color_scale
        return rgba[1]

    def blue(self, *args) -> float:
        """Return the blue component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): blue component value in the current color scale
        """
        rgba = self._apply_colormode(args)*self.color_scale
        return rgba[2]

    def hue(self, *args) -> float:
        """Return the hue component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): hue component value in the current color scale
        """
        rgba = self._apply_colormode(args)
        hsva = rgb_to_hsv(rgba)*self.color_scale
        return hsva[0]

    def saturation(self, *args) -> float:
        """Return the saturation component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): saturation component value in the current color scale
        """
        rgba = self._apply_colormode(args)
        hsva = rgb_to_hsv(rgba)*self.color_scale
        return hsva[1]

    def lightness(self, *args) -> float:
        """Return the lightness component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): lightness component value in the current color scale
        """
        rgba = self._apply_colormode(args)
        hsva = rgb_to_hsv(rgba)*self.color_scale
        return hsva[2]

    def brightness(self, *args) -> float:
        """Return the brightness component of a color.

        Arguments:

        - `*args`: color values in the current color mode

        Returns:

        - (float): brightness component value in the current color scale
        """
        rgba = self._apply_colormode(args)
        hsva = rgb_to_hsv(rgba)*self.color_scale
        return hsva[2]

    def linear_gradient_angle(self, *args, extend='pad'):
        """Create a linear gradient fill.

        Can be called in two ways:
            `linear_gradient(x1, y1, angle, length, stop1, stop2, ...)`
            `linear_gradient((x1, y1), angle, length, stop1, stop2, ...)`

        Each stop is a tuple:
           `(offset, color)`
        where:
            - offset is between 0 and 1
            - color is a tuple (r, g, b[, a]) in current color mode


        """
        if is_number(args[0]):
            x1, y1 = args[:2]
            angle, length = args[2:4]
            args = args[4:]
        else:
            x1, y1 = args[0]
            angle, length = args[1:3]
            args = args[3:]

        theta = self._to_radians(angle)
        x2, y2 = x1+np.cos(theta)*length, x1+np.sin(theta)*length

        if len(args) < 2:
            raise ValueError("You must provide at least 2 stops for creating a gradient")

        stops = [np.concatenate([[c[0]], self._apply_colormode(c[1])]) for c in args]

        return Gradient.linear(
            (x1, y1),
            (x2, y2),
            stops,
            extend=extend
        )

    def linear_gradient(self, *args, extend='pad'):
        """Create a linear gradient fill.

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
        """
        if is_number(args[0]):
            x1, y1, x2, y2 = args[:4]
            args = args[4:]
        else:
            (x1, y1), (x2, y2) = args[:2]
            args = args[2:]

        if len(args) < 2:
            raise ValueError("You must provide at least 2 stops for creating a gradient")

        stops = [np.concatenate([[c[0]], self._apply_colormode(c[1])]) for c in args]

        return Gradient.linear(
            (x1, y1),
            (x2, y2),
            stops,
            extend=extend
        )

    def radial_gradient(self, *args, extend='pad'):
        """Create a radial gradient fill.

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
        """
        if is_number(args[0]):
            cx0, cy0, r0, cx1, cy1, r1 = args[:6]
            args = args[6:]
        else:
            (cx0, cy0, r0), (cx1, cy1, r1) = args[:2]
            args = args[2:]

        if len(args) < 2:
            raise ValueError("You must provide at least 2 stops for creating a gradient")

        stops = [np.concatenate([[c[0]], self._apply_colormode(c[1])]) for c in args]

        return Gradient.radial(
            (cx0, cy0, r0),
            (cx1, cy1, r1),
            stops,
            extend=extend
        )

    def tint(self, *args):
        """Set the tint color for images

        Arguments:
        - A single argument specifies a grayscale value, e.g. `stroke(255)` will set the stroke to white.
        - Two arguments specify grayscale with opacity, e.g. `stroke(0, 128)` will set the stroke to black with 50% opacity.
        - Three arguments specify a color depending on the color mode (rgb or hsv), e.g. `stroke(255, 0, 0)` will set the stroke to red, when the color mode is RGB
        - Four arguments specify a color with opacity
        """

        if args[0] is None:
            self.cur_tint = None
        else:
            self.cur_tint = self._apply_colormode(args)
        return self
    
    def fill(self, *args):
        """Set the color of the current fill

        Arguments:

        - A single argument specifies a grayscale value, e.g `fill(128)` will fill with 50% gray.
        - Two arguments specify grayscale with opacity, e.g. `fill(255, 128)` will fill with transparent white.
        - Three arguments specify a color depending on the color mode (rgb or hsv)
        - Four arguments specify a color with opacity
        """
        if args[0] is None:
            self.cur_fill = None
        elif isinstance(args[0], Gradient):
            self.cur_fill = args[0]
        else:
            self.cur_fill = self._apply_colormode(args)
        return self

    def stroke(self, *args):
        """Set the color of the current stroke

        Arguments:
        - A single argument specifies a grayscale value, e.g. `stroke(255)` will set the stroke to white.
        - Two arguments specify grayscale with opacity, e.g. `stroke(0, 128)` will set the stroke to black with 50% opacity.
        - Three arguments specify a color depending on the color mode (rgb or hsv), e.g. `stroke(255, 0, 0)` will set the stroke to red, when the color mode is RGB
        - Four arguments specify a color with opacity
        """

        if args[0] is None:
            self.cur_stroke = None
        else:
            self.cur_stroke = self._apply_colormode(args)
        return self

    def stroke_dash(self, dash):
        """Set the line dash (stippling)

        Arguments:
        - A sequence of lengths, indicating alternating (on/off) dashed segments
        """
        self.renderer.set_dash(dash)
        return self

    def stroke_weight(self, w):
        """Set the line width

        Arguments:
        - The width in pixel of the stroke
        """
        self.renderer.set_line_width(w)
        return self

    def stroke_join(self, join):
        """Specify the 'join' mode for polylines.

        Arguments:

        - `join` (string): can be one of "miter", "bevel" or "round"
        """
        
        self.renderer.set_line_join(join)
        # join = join.lower()
        # joins = {
        #     "miter": cairo.LINE_JOIN_MITER,
        #     "bevel": cairo.LINE_JOIN_BEVEL,
        #     "round": cairo.LINE_JOIN_ROUND,
        # }
        # if join not in joins:
        #     print(str(join) + " not a valid line join")
        #     print("Choose one of " + str(joins.keys()))
        #     return
        # self.ctx.set_line_join(joins[join])
        return self

    line_join = stroke_join

    def stroke_cap(self, cap):
        """Specify the 'cap' mode for polylines.

        Arguments:

        - `join` (string): can be one of "round", "square" or "butt"
        """
        
        self.renderer.set_line_cap(join)
        return self
        
    line_cap = stroke_cap
    
    def blend_mode(self, mode="over"):
        """Specify the blending mode

        Arguments:

        - `mode` (string) can be a one of the blend mode constants:
            - `BLEND = "over"` (default) - Source overwrites canvas
            - `REPLACE = "source"` - Source completely replaces canvas
            - `ADD = "add"` - Source colors added to canvas
            - `MULTIPLY = "multiply"` - Colors multiplied (always darker)
            - `SCREEN = "screen"` - Colors inverted, multiplied, then inverted (always lighter)
            - `OVERLAY = "overlay"` - MULTIPLY for dark areas, SCREEN f
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
        """
        self.renderer.set_blend_mode(mode)
        return self

    def stroke_cap(self, cap):
        """Specify the 'cap' for lines.

        Arguments:

        - `cap` (string): can be one of "butt", "round" or "square"
        """
        self.renderer.set_line_cap(cap.lower())
        return self

    line_cap = stroke_cap

    def text_align(self, halign, valign="bottom"):
        """Specify the text alignment.

        Arguments:
        - `halign` (string): Horizontal alignment. One of "left", "center" or "right"
        - `valign` (string): Horizontal alignment. One of "baseline" (default), "top", "bottom", or "center"
        """
        self._text_halign = halign
        self._text_valign = valign
        return self

    def text_size(self, size):
        """Specify the text size

        N.B. this will also reset the text leading

        Arguments:

        - `size` (int): the text size
        """
        self._text_size = size
        self._text_leading = size
        self.renderer.set_font_size(self._text_size)
        #self.ctx.set_font_size(self._text_size)
        return self

    def text_leading(self, *args):
        """Specify the space between consecutive lines of text
        if no arguments are specified, returns the text leading values.

        Arguments:

        - `leading` (int, optional): the text leading
        """
        if len(args) == 0:
            return self._text_leading
        self._text_leading = args[0]
        return self

    def text_font(self, font):
        """Specify the font to use for text rendering.

        Arguments:

        - `font` (string or object): Either a string describing the font file path or system font name, or a font object (created with `create_font`)
        """
        if type(font) == str:
            # TODO fix API and redundancy here and in text_font
            if os.path.isfile(font):
                try:
                    info = read_font_names(font)
                    face = create_cairo_font_face_for_file(font)
                    # Only CairoRenderer supports set_font_face; SVG will ignore fine.
                    if hasattr(self.renderer, 'set_font_face'):
                        self.renderer.set_font_face(face)
                    self._font = f"{info['family']} {info['subfamily']}"
                except Exception as e:
                    print(f"Error loading font: {e}")
                return
            else:
                self._font = font
                self.renderer.select_font_face(font)
        else:
            self._font = font.obj
            if type(self._font) == str:
                # "Toy" case of a System font selected by name
                self.renderer.select_font_face(self._font)
            else:
                # Loaded font case
                self.renderer.set_font_face(self._font)
            if font.style is not None:
                self.text_style(font.style)
            if font.size is not None:
                self.text_size(font.size)
        return self

    def text_style(self, style):
        """Specify the style (normal, italic, bold, bolditalic) to use for text
        rendering.

        Arguments:
        - `style` (string): the name of a style ("normal", "italic", "bold",
        "bolditalic")
        """
        if style == 'bolditalic':
            self.renderer.select_font_face(self._font, 'bold', 'italic')
        if style == "normal":
            self.renderer.select_font_face(self._font, 'normal')
        elif style == "italic":
            self.renderer.select_font_face(self._font, 'normal', 'italic')
        elif style == "bold":
            self.renderer.select_font_face(self._font, 'bold')
        else:
            print(
                f"font style ={style}= not recognised (choose from: normal, italic, bold, bolditalic)"
            )
        return self

    def text_width(self, txt):
        # x_advance safer than width (works with spaces)
        info = self.renderer.text_extents()
        #info = self.ctx.get_scaled_font().text_extents(txt)
        return info.x_advance

    def text_height(self, txt):
        info = self.renderer.text_extents()
        #info = self.ctx.get_scaled_font().text_extents(txt)
        return info.height

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
        self.renderer.save()
        return popmanager()

    def pop_matrix(self):
        """
        Restore the previous transformation
        """
        self.renderer.restore()

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
        self.draw_states.append(copy.copy(self.draw_states[-1]))
        return popmanager()

    def pop_style(self):
        """
        Restore the previously pushed drawing state
        """
        old = self.draw_states.pop()
        self.draw_states[-1].set(old)

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
        self.renderer.save()
        self.draw_states.append(copy.copy(self.draw_states[-1]))
        return popmanager()

    def pop(self):
        """
        Restore the previously pushed drawing state and transformations
        """
        self.renderer.restore()
        old = self.draw_states.pop()
        self.draw_states[-1].set(old)

    def translate(self, *args):
        """Translate by specifying `x` and `y` offset.

        Arguments:

        - The offset can be specified as an array/list (e.g `translate([x,y])`
          or as single arguments (e.g. `translate(x, y)`)
        """
        if len(args) == 1:
            v = args[0]
        else:
            v = args
        self.renderer.translate(*v)
        return self

    def scale(self, *args):
        """Apply a scaling transformation.

        Arguments:

        - Providing a single number will apply a uniform transformation.
        - Providing a pair of number will scale in the x and y directions.
        - The scale can be specified as an array/list (e.g `scale([x,y])`
        or as single arguments (e.g. `scale(x, y)`)'''
        """

        if len(args) == 1:
            s = args[0]
            if is_number(s):
                s = [s, s]
        else:
            s = args
        self.renderer.scale(*s)
        return self

    def rotate(self, angle):
        """Rotate by `theta` radians (or degrees, depeending on the angle mode)"""
        self.renderer.rotate(self._to_radians(angle))
        return self

    rotate_rad = rotate

    def apply_matrix(self, mat):
        """Apply an affine (3x3) transformation matrix"""
        # matrix = cairo.Matrix(
        #     mat[0][0], mat[1][0], mat[0][1], mat[1][1], mat[0][2], mat[1][2]
        # )
        self.renderer.transform(mat) #matrix)
        return self

    def get_origin(self):
        """Get the origin in canvas coordinates for the current transformation.
        Returns a 2d numpy array"""
        return self.renderer.get_origin()
        
    def rotate_deg(self, deg):
        """Rotate using degrees"""
        self.renderer.rotate(radians(deg))
        return self

    def hsb(self, *args):
        """ Return RGB components for a color defined as HSB"""
        if len(args) > 1:
            return hsv_to_rgb(np.array(args)) * self.color_scale
        else:
            return hsv_to_rgb(np.array(args[0])) * self.color_scale

    hsv = hsb

    def rgb(self, *args):
        """Return HSV components for a color defined as RGB"""
        if len(args) > 1:
            return rgb_to_hsv(np.array(args)) * self.color_scale
        else:
            return rgb_to_hsv(np.array(args[0])) * self.color_scale

    def _setfill(self):
        self.renderer.set_fill(self.cur_fill)
        # if isinstance(self.cur_fill, Gradient):
        #     self.renderer.set_source_gradient(self.cur_fill) #.gradient)
        # else:
        #     self.renderer.set_source_rgba(*self.cur_fill)

    def _fillstroke(self):
        """Draw the current path with current fill/stroke attributes.
        This is only used by the old‑style path functions (polyline, circle, etc.)
        and is left unchanged for them."""
        if self.no_draw:
            return
        self.renderer.set_fill(self.cur_fill)
        self.renderer.set_stroke(self.cur_stroke)
        self.renderer.fillstroke()
         
        # self.renderer.fillstroke()
        
        # if self.cur_fill is not None:
        #     self._setfill()
        #     if self.cur_stroke is not None:
        #         self.renderer.fill_preserve()
        #     else:
        #         self.renderer.fill()
        # if self.cur_stroke is not None:
        #     self.renderer.set_source_rgba(*self.cur_stroke)
        #     self.renderer.stroke()

    def _draw_shape(self, shape_obj):
        """Draw a complete Shape object using current fill/stroke."""
        if shape_obj is None:
            return
        if shape_obj.style:
            self.push_style()
            if 'fill' in shape_obj.style:
                self.fill(*shape_obj.style['fill'])
            if 'stroke' in shape_obj.style:
                self.stroke(*shape_obj.style['stroke'])
            if 'stroke_weight' in shape_obj.style:
                self.stroke_weight(*shape_obj.style['stroke_weight'])
                
        shape_obj.apply(self.renderer)
        self._fillstroke()
        if shape_obj.style:
            self.pop_style()
        
    def begin_shape(self):
        """Start building a complex shape. Drawing is deferred until end_shape()."""
        self.no_draw = True
        self.cur_shape = Shape(tension=self.tension)
        self.cur_shape.begin_shape()        
        return self

    def end_shape(self, close=False):
        """Finish the shape and draw it."""
        if self.cur_shape is None:
            return
        self.cur_shape.end_shape(close)
        self.no_draw = False
        self._draw_shape(self.cur_shape)
        self.cur_shape = None
        return self
        
    def begin_contour(self):
        """Start a new contour within the currently built shape.
        If no shape is active, a new one is created automatically."""
        if self.cur_shape is None:
            self.cur_shape = Shape(tension=self.tension)
            self.cur_shape.begin_shape()
        self.cur_shape.begin_contour()
        return self

    def end_contour(self, close=False):
        """End the current contour. If not inside a begin_shape/end_shape block,
        the contour is drawn immediately.

        Arguments:

        - `close` (bool, optional): if `True` close the contour

        """
        if self.cur_shape is None:
            return
        self.cur_shape.end_contour(close)
        if not self.no_draw:
            # Called directly, so finalise and draw now
            self.cur_shape.end_shape(close=False)   # already closed contour
            self._draw_shape(self.cur_shape)
            self.cur_shape = None
        return self

    def vertex(self, x, y=None):
        """Add a vertex to current contour

        Input arguments can be in the following formats:

        - `[x, y]`
        - `x, y`
        """
        if self.cur_shape is None:
            raise RuntimeError("vertex() called without begin_shape()")
        self.cur_shape.vertex(x, y)
        return self

    def curve_vertex(self, x, y=None):
        """Add a curved vertex to current contour

        Input arguments can be in the following formats:

        - `[x, y]`
        - `x, y`
        """
        if self.cur_shape is None:
            raise RuntimeError("curve_vertex() called without begin_shape()")
        self.cur_shape.curve_vertex(x, y)
        return self

    def bezier_vertex(self, *args):
        """Draw a cubic Bezier segment from the current point
        requires a first control point to be already defined with `vertex`.


        Requires three points. Input arguments can be in the following formats:

        - `[x1, y1], [x2, y2], [x3, y3]`
        - `x1, y1, x2, y2, x3, y3`
        """
        if self.cur_shape is None:
            raise RuntimeError("bezier_vertex() called without begin_shape()")
        self.cur_shape.bezier_vertex(*args)
        return self

    def curve_tightness(self, val):
        """Sets the 'tension' parameter for the curve used when using `curve_vertex`"""
        self.tension = val
        if self.cur_shape is not None:
            self.cur_shape.tension = val
        return self

    def shape(self, obj, close=False):
        """Draw a pre‑built Shape object or a list of polylines (list of lists/arrays).
        For lists, each polyline becomes one contour (open or closed)."""
        if isinstance(obj, Shape):
            self._draw_shape(obj)
            return self

        # List of shapes 
        if isinstance(obj[0], Shape):
            for S in obj:
                self._draw_shape(S)
            return self
        
        # Convert legacy polyline lists into a temporary Shape
        if not is_compound(obj):
            obj = [obj]   # single polyline -> wrap in list
        tmp_shape = Shape()
        tmp_shape.begin_shape()                  # activate construction
        for poly in obj:
            pts = np.asarray(poly)
            if pts.ndim != 2 or pts.shape[1] != 2:
                raise ValueError("Each polyline must be an Nx2 array-like")
            tmp_shape.begin_contour()
            for i, p in enumerate(pts):
                if i == 0:
                    tmp_shape.vertex(*p)
                else:
                    tmp_shape.vertex(*p)   # moves to first point, lines to others
            if close:
                tmp_shape.end_contour(True)
            else:
                tmp_shape.end_contour(False)
        tmp_shape.end_shape(close=False)         # finalise
        self._draw_shape(tmp_shape)
        return self

    def rect_mode(self, mode):
        """Set the "mode" for drawing rectangles.

        Arguments:
        - `mode` (string): can be one of 'corner', 'corners', 'center', 'radius'

        """
        mode = mode.lower()
        if mode not in ["corner", "center", "radius", "corners"]:
            print("rect_mode: invalid mode")
            print("choose one among: corner, center, radius")
            return
        self._rect_mode = mode
        return self

    def ellipse_mode(self, mode):
        """Set the "mode" for drawing rectangles.

        Arguments:
        - `mode` (string): can be one of 'corner', 'center'
        """
        mode = mode.lower()
        if mode not in ["corner", "center", "radius", "corners"]:
            print("rect_mode: invalid mode")
            print("choose one among: corner, center")
            return
        self._ellipse_mode = mode
        return self

    
    def rectangle(self, *args, mode=None):
        """Draw a rectangle.
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

        """

        if mode is None:
            mode = self._rect_mode
        if len(args) == 1:
            radius = None
        elif len(args) % 2 == 1:
            if len(args) == 3:
                if not is_number(args[1]):
                    radius = args[-1]
                    args = args[:-1]
                else:
                    radius = None
            else:
                radius = args[-1]
                args = args[:-1]
        else:
            if len(args) == 2 and is_number(args[1]):
                radius = args[-1]
                args = args[:-1]
            else:
                radius = None

        if len(args) == 1:
            p = np.array(args[0][0])
            size = [args[0][1][0] - args[0][0][0], args[0][1][1] - args[0][0][1]]
            mode = "corner"  # Force the mode to corner since we explicitly defined the rect
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

        if mode.lower() == "center":
            p -= size / 2
        elif mode.lower() == "radius":
            p -= size
            size *= 2
        elif mode.lower() == "corners":
            # Interpret 'size' as the bottom right corner
            size = size - p

        self.renderer.rectangle(*p, *size, radius)
        self._fillstroke()
        return self

    rect = rectangle

    def square(self, *args, mode=None):
        """Draw a square.

        Arguments:

        The first sequence of arguments is one of
         - `[x, y], size`,
         - `x, y, size`

        The interpretation of `x` and `y` depends on the current rect mode. These indicate the
        center of the rectangle if the rect mode is `"center"` and the top left corner otherwise.
        """
        if mode is None:
            mode = self._rect_mode
        if mode == "corners":
            mode = "corner"
        if len(args) == 2:
            self.rectangle(args[0], [args[1], args[1]], mode=mode)
        elif len(args) == 3:
            self.rectangle(args[0], args[1], args[2], args[2], mode=mode)
        else:
            raise ValueError("square: wrong number of arguments")
        return self

    def rect(self, *args, mode=None):
        """Draws a rectangle.

        Input arguments can be in the following formats:

         - `[topleft_x, topleft_y], [width, height]`,
         - `[topleft_x, topleft_y], width, height`,
         - `topleft_x, topleft_y, width, height`

        Depending on
        """
        return self.rectangle(*args, mode=mode)

    def quad(self, *args):
        """Draws a quadrangle given four points

        Input arguments can be in the following formats:

         - `a, b, c, d` (Four points specified as lists/tuples/numpy arrays
         - `x1, y1, x2, y2, x3, y3, x4, y4`, a sequence of numbers, one for each coordinate
        """

        if len(args) == 4:
            self.polygon(args)
        else:
            self.polygon([[args[i * 2], args[i * 2 + 1]] for i in range(4)])
        return self

    def triangle(self, *args):
        """Draws a triangle given three points

        Input arguments can be in the following formats:

         - `a, b, c` (Four points specified as lists/tuples/numpy arrays
         - `x1, y1, x2, y2, x3, y3`
        """

        if len(args) == 3:
            self.polygon(args)
        else:
            self.polygon([[args[i * 2], args[i * 2 + 1]] for i in range(3)])
        return self

    def circle(self, *args, mode=""):
        """Draw a circle given center and radius

        Input arguments can be in the following formats:

        - `[center_x, center_y], radius`,
        - `center_x, center_y, raidus`
        """
        if not mode:
            mode = self._ellipse_mode.lower()
        else:
            mode = mode.lower()
        if len(args) == 3:
            center = args[:2]
            size = args[2]
        else:
            center, size = args
        x, y = center[:2]
        if mode == "radius":
            radius = size
        else:
            radius = size / 2
        if mode == "corner":
            x += radius
            y += radius
        self.renderer.ellipse(x, y, radius, radius)
        #self.renderer.new_sub_path()
        #self.renderer.arc(x, y, radius, 0, np.pi * 2.0)
        self._fillstroke()
        return self

    def ellipse(self, *args, mode=None):
        """Draw an ellipse with center, width and height.

        Input arguments can be in the following formats:

        - `[center_x, center_y], [width, height]`,
        - `[center_x, center_y], width, height`,
        - `center_x, center_y, width, height`
        - `[center_x, center_y], width`,
        - `center_x, center_y, width`,
        """

        if mode is None:
            mode = self._ellipse_mode
        if len(args) == 2:
            center = args[0]
            w = args[1]
            h = w
        elif len(args) == 3:
            if is_number(args[0]):
                center = args[:2]
                w = args[2]
                h = w
            else:
                center = args[0]
                w, h = args[1:]
        elif len(args) == 4:
            center = args[:2]
            w, h = args[2:]
        else:
            center = args[0]
            w, h = args[1]
        if mode.lower() == "corners":
            x1, y1 = center
            x2, y2 = w, h
            center = np.array([x1 + x2, y1 + y2]) / 2
            w, h = abs(x2 - x1), abs(y2 - y1)
        if not (w > 0 and h > 0):
            return
        self.push_matrix()
        if mode.lower() == "corner":
            center += [w/2, h/2]
        if mode.lower() == "radius":
            w = w * 2
            h = h * 2

        self.renderer.ellipse(center[0], center[1], w/2, h/2)
        self._fillstroke()
        
        # self.scale([w / 2, h / 2])
        # self.renderer.new_sub_path()
        # self.renderer.arc(0, 0, 1, 0, np.pi * 2.0)
        # self.pop_matrix()
        
        # if self.cur_fill is not None:
        #     self.set_fill(self.cur_fill)
        #     if self.cur_stroke is not None:
        #         self.renderer.fill_preserve()
        #     else:
        #         self.renderer.fill()
        # self.pop()
        # if self.cur_stroke is not None:
        #     self.renderer.set_stroke(self.cur_stroke)
        #     self.renderer.stroke()
        return self

    def line(self, *args):
        """Draws a line between two points

        Input arguments can be in the following formats:

         - `a, b` (Two points specified as lists/tuples/numpy arrays
         - `x1, y1, x2, y2`, a sequence of numbers, one for each coordinate
        """
        nostroke = False
        if self.cur_stroke is None:
            nostroke = True
            if self.cur_fill is not None:
                self.cur_stroke = self.cur_fill
            else:
                print("line: No color is set")
        if len(args) == 2:
            self.polyline([args[0], args[1]])
        if len(args) == 4:
            self.polyline([[args[0], args[1]], [args[2], args[3]]])
        if nostroke:
            self.cur_stroke = None
        return self

    def point(self, *args):
        """Draw a point at a given position

        Input arguments can be in the following formats:

         - `[x, y]`: a single point specified as a tuple/list/numpy array
         - `x1, y1`: two coordinates

        """
        nostroke = False
        if self.cur_stroke is None:
            nostroke = True
            if self.cur_fill is not None:
                self.cur_stroke = self.cur_fill
            else:
                print("point: No color is set")
        if len(args) == 1:
            self.polyline([args[0], args[0]])
        elif len(args) == 2:
            self.polyline([[args[0], args[1]], [args[0], args[1]]])
        else:
            raise ValueError("point: Illegal number of arguments")
        if nostroke:
            self.cur_stroke = None
        return self

    def arrow(self, *args, size=2.5, overhang=0.7, length=2.0):
        """Draw an arrow between two points

        Input arguments can be in the following formats:

        - `a, b` (Two points specified as lists/tuples/numpy arrays
        - `x1, y1, x2, y2`, a sequence of numbers, one for each coordinate
        """

        if len(args) == 2:
            a, b = args
        elif len(args) == 4:
            a = args[:2]
            b = args[2:]
        elif len(args) == 3:
            a = args[0]
            b = args[1]
            size = args[2]
        w = self.renderer.get_line_width() * size
        h = w * length
        a = np.array(a)
        b = np.array(b)
        d = b - a
        l = np.linalg.norm(d)
        d = d / (np.linalg.norm(d) + 1e-10)
        b = a + d * max(0.0, l - h)
        p = np.array([-d[1], d[0]])
        P = [b + p * w - d * w * overhang, b + d * h, b - p * w - d * w * overhang, b]
        self.line(a, b)
        self.push()
        self.fill(self._get_stroke_or_fill_color())
        self.no_stroke()
        self.polygon(P)
        self.pop()
        return self


    def arc(self, *args):
        """Draw an ellpitical arc, given the center of the ellipse `x, y`
        the size of the ellipse `w, h` and the initial and final angles
        in radians  `start, stop`.
        A last optional `mode` argument determines the arc's fill style.
        The fill modes are a semi-circle (`OPEN`), a closed semi-circle (`CHORD`),
        or a closed pie segment (`PIE`).

        Input arguments can be in the following formats:

          - `x, y, w, h, start, stop`
          - `[x, y]`, `[w, h]`, `[start, stop]`
          - `[x, y]`, `w, h, start, stop`

        """
        # Check if we specified a mode
        if type(args[-1]) == str:
            mode = args[-1].lower()
            args = args[:-1]
        else:
            mode = "open"
        if len(args) == 3:
            x, y = args[0]
            w, h = args[1]
            start, stop = args[2]
        elif len(args) == 6:
            x, y, w, h, start, stop = args
        else:
            x, y = args[0]
            w, h, start, stop = args[1:]
        if w == 0 or h == 0:
            return

        # Cairo expects degrees
        start, stop = (self._to_radians(start),
                       self._to_radians(stop))
        start = mod2pi(start)
        stop = mod2pi(stop)
        save_mat = self.renderer.get_matrix()
        self.renderer.translate(x, y)
        self.renderer.scale(w / 2, h / 2)
        if self.cur_fill is not None:
            self._setfill()
            self.renderer.new_sub_path()
            if mode != "chord":
                self.renderer.move_to(0, 0)
            self.renderer.arc(0, 0, 1, start, stop)
            self.renderer.fill()
        if self.cur_stroke is not None:
            self.renderer.set_stroke(self.cur_stroke)
            self.renderer.new_sub_path()
            if mode == "pie":
                self.renderer.move_to(0, 0)
            self.renderer.arc(0, 0, 1, start, stop)
            if mode != "open":
                self.renderer.close_path()
        self.renderer.set_matrix(save_mat)
        if self.cur_stroke is not None:
            self.renderer.stroke()
        return self

    def polygon(self, *args, close=True):
        """Draw a polygon (closed by default).

        The polyline is specified as either:

        - a list of =[x,y]= pairs (e.g. =[[0, 100], [200, 100], [200, 200]]=)
        - a numpy array with shape =(n, 2)=, representing =n= points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To create an opne polygon set the named =close= argument to =False=, e.g. =c.polygon(points, close=False)=.
        """
        return self.polyline(*args, close=close)

    def polyline(self, *args, close=False):
        """Draw a polyline (open by default).

        The polyline is specified as either:

        - a list of =[x,y]= pairs (e.g. =[[0, 100], [200, 100], [200, 200]]=)
        - a numpy array with shape =(n, 2)=, representing =n= points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To close the polyline set the named =close= argument to =True=, e.g. =c.polyline(points, close=True)=.
        """
        # Parse arguments into a list of (x,y) tuples
        if len(args) == 1:
            points = args[0]
        elif len(args) == 2:
            points = np.vstack(args).T
        else:
            raise ValueError("Wrong number of arguments")
        # Build a temporary Shape and draw it
        tmp = Shape()
        tmp.polyline(points, closed=close)
        self._draw_shape(tmp)
        return self

    def multibezier(self, *args, close=False):
        """
        Draw a sequence of connected cubic Bézier curves.

        Input can be:
        - a list of [x,y] pairs: first point is start, then triples of control points
          (c1, c2, end) for each segment.
        - two lists (or numpy arrays) of x, y coordinates, similarly arranged.
        - a flat list of coordinates.
        """
        # Parse arguments into a flat list of (x,y) pairs
        if len(args) == 1:
            points = args[0]
        elif len(args) == 2:
            points = np.vstack(args).T
        else:
            raise ValueError("Wrong number of arguments")
        tmp = Shape()
        tmp.multibezier(points, closed=close)
        self._draw_shape(tmp)
        return self

    def curve(self, *args, close=False):
        """Draw a curve (open by default) using Cardinal spline interpolation.

        The polyline is specified as either:

        - a list of =[x,y]= pairs (e.g. =[[0, 100], [200, 100], [200, 200]]=)
        - a numpy array with shape =(n, 2)=, representing =n= points (a point for each row and a coordinate for each column)
        - two lists (or numpy array) of numbers, one for each coordinate

        To close the curve set the named =close= argument to =True=, e.g. =c.curve(points, close=True)=.
        """
        if len(args) == 1:
            points = args[0]
        elif len(args) == 2:
            points = np.vstack(args).T
        else:
            raise ValueError("Wrong number of arguments")
        tmp = Shape()
        tmp.curve(points, close=close)
        self._draw_shape(tmp)
        return self

    def identity(self):
        """Resets the current matrix to the identity (no transformation)"""
        self.renderer.set_matrix(np.eye(3)) #identity_matrix()
        return self

    def reset_matrix(self):
        """Resets the current matrix to the identity (no transformation)"""
        self.renderer.set_matrix(np.eye(3)) #
        #self.renderer.identity_matrix()
        return self

    def copy(self, *args):
        """The first parameter can optionally be an image, if an image is not specified the funtion will use
        the canvas image, .
        The next four parameters, sx, sy, sw, and sh determine the region to copy from the source image.
        (sx, sy) is the top-left corner of the region. sw and sh are the region's width and height.
        The next four parameters, dx, dy, dw, and dh determine the region of the canvas to copy into.
        (dx, dy) is the top-left corner of the region. dw and dh are the region's width and height.

        `copy(src_image, sx, sy, sw, sh, dx, dy, dw, dh)`
        or
        `copy(sx, sy, sw, sh, dx, dy, dw, dh)`
        """

        if len(args) % 2 == 1:
            img = np.array(args[0])
            args = args[1:]
        else:
            img = self.get_image_array()
        if len(args) == 8:
            sx, sy, sw, sh, dx, dy, dw, dh = args
        else:
            ValueError("Unspported number of arguments for copy")
        img = img[sy : sy + sh, sx : sx + sw]
        self.image(img, dx, dy, dw, dh)
        return self

    def background(self, *args):
        """Clear the canvas with a given color
        Accepts either an array with the color components, or single color components (as in `fill`)
        """
        # self.clear_callback()
        # HACK Save background, this is needed for saving and no_loop in sketches
        # Since saving has to be done as a postprocess after the frame
        if not len(args):
            raise ValueError("background requires at least one argument")
        if len(args) == 1:
            self.last_background = args[0]
        else:
            self.last_background = args
        self.renderer.set_matrix(np.eye(3)) #identity_matrix()
        # HACK - we don't want to necessarily save the background when exporting SVG
        # Especially if we want to plot the output, so only draw the background to the
        # bitmap surface if that is the case.
        # if self._save_background:
        #     ctx = self.ctx
        # else:
        #     ctx = self.ctx.ctxs[0]

        # For the first clear, we use OPERATOR_SOURCE
        # Otherwise the background will not actually be transparent
        rgba = np.array(self._apply_colormode(args))
        self.renderer.background(rgba,
                                 self._first_background,
                                 self._save_background)
        
        self._first_background = False
        return self

    def get_buffer(self):
        surf = self.renderer.get_surface()
        if surf is None:
            return None
        return surf.get_data()

    def get_image_array(self):
        """Get canvas image as a numpy array"""
        img = np.ndarray(
            shape=(self.height, self.width, 4),
            dtype=np.uint8,
            buffer=self.get_buffer(),
        )[:, :, :3].copy()
        img = img[:, :, ::-1]
        return img

    def get_grayscale_array(self):
        """Get grayscale image of canvas contents as float numpy array (0 to 1 range)"""
        return np.mean(self.get_image_array() / 255, axis=-1)

    def get_image(self):
        """Get canvas as a PIL image"""
        return Image.fromarray(self.get_image_array())

    def get_image_grayscale(self):
        """Returns the canvas image as a grayscale numpy array (in 0-1 range)"""
        return self.get_image().convert("L")

    def save_image(self, path):
        """Save the canvas to an image

        Arguments:

        - The path where to save

        """
        self.renderer.write_to_png(path)

    def save_svg(self, path):
        """Save the canvas to an svg file

        Arguments:

        - The path where to save

        """
        self.renderer.save_svg(path)
        # if self.recording_surface is None:
        #     raise ValueError("No recording surface in canvas")
        # surf = cairo.SVGSurface(path, self.width, self.height)
        # ctx = cairo.Context(surf)
        # ctx.set_source_surface(self.recording_surface)
        # ctx.paint()
        # surf.finish()
        # fix_clip_path(path, path)

    def save_pdf(self, path):
        """Save the canvas to an svg file

        Arguments:

        - The path where to save

        """
        if not isinstance(self.renderer, rend.CairoRenderer):
            raise NotImplementedError("pdf saving is only implemented for CairoRenderer")
        if self.recording_surface is None:
            raise ValueError("No recording surface in canvas")
        import cairo
        surf = cairo.PDFSurface(path, self.width, self.height)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.renderer.recording_surface)
        ctx.paint()
        surf.finish()

    def Image(self):
        print("Image is deprected use =get_image()= instead")
        return self.get_image()

    def to_clipboard(self):
        """Copy canvas contents to clipboard (as SVG data)
        Requires pyperclip to be installed
        """
        import pyperclip, os
        name = 'py5canvas_clipboard.svg'
        self.save(name)
        with open(name, "r", encoding="utf-8") as f:
            data = f.read()
            pyperclip.copy(data)
            #os.remove(name)

    def save(self, path):
        """Save the canvas into a given file path
        The file format depends on the file extension
        """
        if ".svg" in path:
            self.save_svg(path)
        elif ".pdf" in path:
            self.save_pdf(path)
        elif ".png" in path:
            self.save_image(path)

    def show(self, size=None, resample="bicubic"):
        """Display the canvas in a notebook"""
        if isinstance(self.renderer, rend.SVGRenderer):
            svg_str = self.renderer.get_svg_string()
            try:
                # Jupyter / IPython environment
                from IPython.display import SVG, display
                return display(SVG(svg_str))
            except ImportError:
                from marimo import ui
                return ui.Html(f"<div>{svg_str}</div>")
        else:
            img = self.get_image()
            if size is not None:
                filter = {
                    "bicubic": Image.BICUBIC,
                    "nearest": Image.NEAREST,
                    "bilinear": Image.BILINEAR,
                    "lanczos": Image.LANCZOS,
                }
                img = img.resize(size, filter[resample])
            try:
                from IPython.display import display
                display(img)
            except (NameError, ImportError) as e:
                import marimo as mo
                mo.output.append(img)

    def show_plt(self, size=None, title="", axis=False):
        """Show the canvas in a notebook with matplotlib

        Arguments:

        - `size` (tuple, optional): The size of the displayed image, by default this is the size of the canvas
        - `title` (string, optional): A title for the figure
        - `axis` (bool, optional): If `True` shows the coordinate axes
        """
        import matplotlib.pyplot as plt
        if size is not None:
            plt.figure(figsize=(size[0] / 100, size[1] / 100))
        else:
            plt.figure(figsize=(self.width / 100, self.height / 100))
        if title:
            plt.title(title)
        plt.imshow(self.get_image())
        if not axis:
            plt.gca().axis("off")
        plt.show()

    def _convert_html_color(self, html_color):
        if html_color.startswith("#"):
            html_color = html_color[1:]
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

    def _scale_color(self, x):
        if len(x) == 1:
            if type(x[0]) == str:
                return self._convert_html_color(x[0])
            elif not is_number(x[0]):  # array like input
                return self._scale_color(*x)
                # return np.array(x[0])/self.color_scale[:len(x[0])]
            if self._is_hsv():
                # HSV sets value
                return (0, 0, x[0] / self.color_scale[2], 1.0)
            else:
                return (
                    x[0] / self.color_scale[0],
                    x[0] / self.color_scale[0],
                    x[0] / self.color_scale[0],
                    1.0,
                )
        elif len(x) == 3:
            return (
                x[0] / self.color_scale[0],
                x[1] / self.color_scale[1],
                x[2] / self.color_scale[2],
                1.0,
            )
        elif len(x) == 2:
            if type(x[0]) == str:
                clr = self._convert_html_color(x[0])
                clr[-1] = x[1] / self.color_scale[-1]
                return clr
            elif not is_number(x[0]):
                # (r, g, b), alpha case
                if len(x[0]) != 3:
                    raise ValueError("Need 3 components for color")
                clr = x[0]
                return (clr[0] / self.color_scale[0],
                        clr[1] / self.color_scale[1],
                        clr[2] / self.color_scale[2],
                        x[1] / self.color_scale[3])
            if self._is_hsv():
                return (0, 0, x[0] / self.color_scale[2], x[1] / self.color_scale[3])
            else:
                return (
                    x[0] / self.color_scale[0],
                    x[0] / self.color_scale[0],
                    x[0] / self.color_scale[0],
                    x[1] / self.color_scale[3],
                )
        return (
            x[0] / self.color_scale[0],
            x[1] / self.color_scale[1],
            x[2] / self.color_scale[2],
            x[3] / self.color_scale[3],
        )


    def create_turtle(self, *args, autodraw=True):
        """Create a turtle object at a given position (default is the origin)

        Arguments:
        - Optional, a pair of initial coordinates (either two values or a tuple/vector). The default is (0, 0)
        - `autodraw` (`bool`, default `True`): if `True` automatically draws the turtle path if the pen is down
        """
        from . import turtle
        if len(args)==1:
            pos = args[0]
        elif len(args)==2:
            pos = args
        else:
            pos = (0, 0)
        print("You created a turtle for the current canvas, it will not be valid if you create a new canvas!")
        return turtle.Turtle(pos, self, autodraw)

    def create_graphics(self, w, h):
        """Create a new canvas with the specified width and height
        E.g. `c = create_graphics(128, 128)` will put a new canvas into
        the variable `c`. You can draw the contents of the canvas with the `image` function.
        """
        return Canvas(w, h)

    def image(self, img, *args, opacity=1.0):
        """Draw an image at position with (optional) size and (optional) opacity

        Arguments:

        - `img`: The input image. Can be either a PIL image, a numpy array, a Canvas or a pyCairo surface.
        - optional arguments: position and size can be specified with the following formats:
            - `x, y`:  position only
            - `x, y, w, h`: position and size
            - `[x, y]`: position only (also a numpy array or tuple are valid)
            - `[x, y], [w, h]`: position and size
        if the position is not specified, the original image dimensions will be used

        - `opacity`: a value between 0 and 1 specifying image opacity.

        """
        if isinstance(self.renderer, rend.SVGRenderer):
            raise NotImplementedError('SVG renderer does not support image yet')
        if isinstance(img, Canvas):
            if isinstance(img, rend.SVGRenderer):
                raise NotImplementedError('SVG renderer does not support image yet')
            img = img.renderer._ctx.surface
        else:
            if not isinstance(img, np.ndarray):
                # This should take care of tensors and PIL Images
                if img.mode == 'P':
                    print("You are visualizing a quantized image, consider either converting it to 'L' or 'RGB' or 'RGBA' or using the indices")
                    print("Converting it to RGBA.")
                    img = img.convert('RGBA')
                img = np.array(img)
            img = numpy_to_surface(img)
        self.renderer.save()
        if len(args) == 0:
            pos = np.zeros(2)
            size = [img.get_width(), img.get_height()]
        elif len(args) == 1:  # [x, y]
            pos = args[0]
            size = [img.get_width(), img.get_height()]
        elif len(args) == 2:
            if is_number(args[0]):  # x, y
                pos = args
                size = [img.get_width(), img.get_height()]
            else:  # [x, y], [w, h]
                pos, size = args
        elif len(args) == 4:  # x, y, w, h
            pos = args[:2]
            size = args[2:]
        else:
            print("Unexpected number of arguments for image")
            raise ValueError

        pos = np.array(pos).astype(float)
        size = np.array(size).astype(float)
        self.renderer.translate(pos[0], pos[1])

        if size is not None:
            sx = size[0] / img.get_width()
            sy = size[1] / img.get_height()
            self.renderer.scale(sx, sy)

        # Apply tint if set
        if self.cur_tint is not None:
            r, g, b, a = self.cur_tint
            op = self.renderer.get_blend_mode()
            self.renderer.push_group()
            # base image
            self.renderer.set_source_surface(img, 0, 0)
            self.renderer.paint_with_alpha(1)
            # multiply tint 
            self.renderer.set_blend_mode('multiply')
            self.renderer.set_source_rgba(r, g, b, 1.0)
            self.renderer.mask_surface(img, 0, 0)
            # render group
            self.renderer.pop_group_to_source()
            self.renderer.set_blend_mode(op)
            self.renderer.paint_with_alpha(opacity*a)
        else:
        # Draw straight otherwise
            self.renderer.set_source_surface(img)
            self.renderer.paint_with_alpha(opacity)
        self.renderer.restore()
        return self

    def text(self, text, *args, align="", valign="", center=None, **kwargs):
        """Draw text at a given position

        Arguments:

            - `text`, the text to display
            - the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
            - `align`, horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
            - `valign`, vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`
            (Deprecated) if center=True the text will be horizontally centered
        """

        # Backwards compatibility since previous version has position first
        if type(text) not in [str, np.str_]:
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
            self._setfill()
            #self.ctx.set_source_rgba(*self.cur_fill)

        if not align:
            align = self._text_halign
        if not valign:
            valign = self._text_valign

        if center is not None:
            if center:
                align = "center"
            else:
                align = "left"

        x, y = pos

        lines = text.splitlines()

        if valign == "center":
            y -= (self._text_leading * (len(lines) - 1)) / 2
        elif valign == "bottom":
            y -= self._text_leading * (len(lines) - 1)

        for line in lines:
            ox, oy = self._text_offset(line, align, valign)
            self.renderer.move_to(x + ox, y + oy)
            self.renderer.text_path(line)
            self._fillstroke()
            y += self._text_leading
        return self

    def text_shapes(self, text, *args, dist=1, align="", valign=""):
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

        if not align:
            align = self._text_halign
        if not valign:
            valign = self._text_valign

        
        font = self.renderer.get_scaled_font()

        start_pos = np.array(pos, dtype=np.float32)

        lines = text.splitlines()

        if valign == "center":
            start_pos[1] -= (self._text_leading * (len(lines) - 1)) / 2
        elif valign == "bottom":
            start_pos[1] -= self._text_leading * (len(lines) - 1)

        all_shapes = []

        for line in lines:
            pos = start_pos + self._text_offset(line, align, valign)
            start_pos[1] += self._text_leading

            for char in line:
                extents = font.text_extents(char)

                # Extract path data
                self.renderer.text_path(char)
                path = self.renderer.copy_path()
                # Clear path so we don't draw
                self.renderer.new_path()

                shape = []

                def prev():
                    return shape[-1][-1][-1]

                def sample_line(points):
                    a = prev()
                    b = np.array(points)
                    s = np.linalg.norm(b - a)
                    n = max(int(s / dist) + 1, 2)
                    t = np.linspace(0, 1, n)[1:]
                    res = a + (b - a) * t.reshape(-1, 1)
                    return res

                def sample_cubic(points):
                    b, c, d = [
                        np.array(p) for p in [points[:2], points[2:4], points[4:6]]
                    ]
                    a = prev()
                    s = approx_arc_length_cubic(a, b, c, d)
                    n = max(int(s / dist) + 1, 2)
                    t = np.linspace(0, 1, n)[1:]
                    P = np.array([a, b, c, d])
                    return eval_bezier(P, t)

                for kind, points in path:
                    if kind == cairo.PATH_MOVE_TO:
                        shape.append([np.array([points])])
                    elif kind == cairo.PATH_LINE_TO:
                        shape[-1].append(sample_line(points))
                    elif kind == cairo.PATH_CURVE_TO:
                        shape[-1].append(sample_cubic(points))
                    elif kind == cairo.PATH_CLOSE_PATH:
                        shape[-1].append(sample_line(shape[-1][0][0]))

                res = [np.vstack(P) + pos for P in shape if len(P) > 1]
                all_shapes.append(res)
                pos += [extents.x_advance, 0]
        return all_shapes

    def text_shape(self, text, *args, dist=1, align="", valign=""):
        """Retrieves polylines for a given string of text in the current font

        Arguments:

        - `text`, the text to sample
        - the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
        - `dist`, approximate distance between samples
        - `align`, horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
        - `valign`, vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`
        """
        return sum(
            self.text_shapes(text, *args, dist=dist, align=align, valign=valign), []
        )

    def text_points(self, text, *args, dist=1, align="", valign=""):
        """Retrieves points for a given string of text in the current font

        Arguments:

        - `text`, the text to sample
        - the position of the text, either a pair of x, y arguments or a list like object (e.g. `[x, y]`)
        - `dist`, approximate distance between samples
        - `align` (named), horizontal alignment, etiher `'left'` (default), `'center'` or `'right'`
        - `valign` (named), vertical alignment, etiher `'bottom'` (default), `'center'` or `'top'`
        """
        return np.vstack(
            self.text_shape(text, *args, dist=dist, align=align, valign=valign)
        )

    def _text_offset(self, text, align, valign):
        (x_bearing, y_bearing, w, h, x_advance, y_advance) = self.renderer.text_extents(text)
        if not align:
            align = self._text_halign
        if not valign:
            valign = self._text_valign
        ox = 0
        oy = 0
        if align == "center":
            ox = -(w / 2 + x_bearing)
        elif align == "right":
            ox = -(w + x_bearing)
        if valign == "top":
            oy = -y_bearing
        elif valign == "center":
            oy = -(h / 2 + y_bearing)
        return ox, oy

    def text_bounds(self, text, *args, align="", valign=""):
        """Returns the bounding box of a string of text at a given position"""
        if len(args) == 2:
            pos = np.array(args)
        elif len(args) == 1:
            pos = np.array(args[0])
        else:
            pos = np.zeros(2)

        if not align:
            align = self._text_halign
        if not valign:
            valign = self._text_valign

        lines = text.splitlines()
        if valign == "center":
            pos[1] -= (self._text_leading * (len(lines) - 1)) / 2
        elif valign == "bottom":
            pos[1] -= self._text_leading * (len(lines) - 1)

        tl = []
        br = []
        for line in lines:
            (x_bearing, y_bearing, w, h, x_advance, y_advance) = self.renderer.text_extents(
                line
            )
            ox, oy = self._text_offset(line, align, valign)
            x, y = pos[0] + ox, pos[1] + oy - h
            tl.append((x, y))
            br.append((x + w, y + h))
            pos[1] += self._text_leading

        tl = np.min(tl, axis=0)
        br = np.max(br, axis=0)
        size = br - tl
        return edict(
            {
                "x": tl[0],
                "y": tl[1],
                "pos": tl,
                "w": size[0],
                "h": size[1],
                "size": size,
            }
        )

def radians(x):
    """Get radians given an angle in degrees"""
    return np.pi / 180 * x


def degrees(x):
    """Get degrees given an angle in radians"""
    return x * (180.0 / np.pi)


# def numpy_to_surface(arr):
#     """Convert numpy array to a pycairo surface"""
#     # Get the shape and data type of the numpy array
#     if len(arr.shape) == 2:
#         if arr.dtype == np.uint8:
#             arr = (
#                 np.dstack([arr, arr, arr, (np.ones(arr.shape) * 255).astype(np.uint8)])
#                 / 255
#             )
#         else:
#             # grayscale 0-1 image
#             arr = np.dstack([arr, arr, arr, np.ones(arr.shape)])
#     else:
#         if arr.shape[2] == 3:
#             if arr.dtype == np.uint8:
#                 arr = (
#                     np.dstack([arr, np.ones(arr.shape[:2], dtype=np.uint8) * 255]) / 255
#                 )
#             else:
#                 arr = np.dstack([arr, np.ones(arr.shape[:2])])
#         elif arr.shape[2] == 1:
#             if arr.dtype == np.uint8:
#                 arr = (
#                     np.dstack(
#                         [arr] * 3 + [np.ones(arr.shape[:2], dtype=np.uint8) * 255]
#                     )
#                     / 255
#                 )
#             else:
#                 arr = np.dstack([arr] * 3 + [np.ones(arr.shape[:2])])
#         else:
#             if arr.dtype == np.uint8:
#                 arr = arr / 255

#     arr[:, :, :3] *= arr[:, :, 3:4]  # premultiply alpha
#     arr = (arr * 255).astype(np.uint8)  # convert to uint8
#     arr = arr.copy(order="C")  # must be "C-contiguous"
#     arr[:, :, :3] = arr[:, :, :3][:, :, ::-1]  # Convert RGB to BGR
#     surf = cairo.ImageSurface.create_for_data(
#         arr, cairo.FORMAT_ARGB32, arr.shape[1], arr.shape[0]
#     )

#     return surf



def numpy_to_surface(arr):
    """
    LLM optimization
    Convert numpy array to a pycairo ImageSurface with fewer allocations.

    Supported inputs:
      - HxW uint8                  -> grayscale, opaque
      - HxWx3 uint8               -> RGB, opaque
      - HxWx4 uint8               -> RGBA, premultiplied into Cairo ARGB32 memory layout
    """
    import cairo
    if arr.dtype != np.uint8:
        arr = (arr*255).astype(np.uint8)
        #raise TypeError("Fast path expects uint8 input")

    h, w = arr.shape[:2]

    if arr.ndim == 2:
        # grayscale -> RGB24
        stride = cairo.Format.RGB24.stride_for_width(w)
        buf = np.empty((h, stride), dtype=np.uint8)
        pixels = buf[:, :w * 4].reshape(h, w, 4)

        pixels[..., 0] = arr   # B
        pixels[..., 1] = arr   # G
        pixels[..., 2] = arr   # R
        pixels[..., 3] = 0     # unused byte for RGB24

        surface = cairo.ImageSurface.create_for_data(
            buf, cairo.FORMAT_RGB24, w, h, stride
        )
        return surface

    if arr.ndim != 3:
        raise ValueError("Expected HxW, HxWx3, or HxWx4 array")

    c = arr.shape[2]

    if c == 3:
        # RGB -> RGB24, no premultiplication needed
        stride = cairo.Format.RGB24.stride_for_width(w)
        buf = np.empty((h, stride), dtype=np.uint8)
        pixels = buf[:, :w * 4].reshape(h, w, 4)

        pixels[..., 0] = arr[..., 2]  # B
        pixels[..., 1] = arr[..., 1]  # G
        pixels[..., 2] = arr[..., 0]  # R
        pixels[..., 3] = 0            # unused byte for RGB24

        surface = cairo.ImageSurface.create_for_data(
            buf, cairo.FORMAT_RGB24, w, h, stride
        )
        return surface

    if c == 4:
        # RGBA -> ARGB32, premultiplied, little-endian byte layout B,G,R,A
        stride = cairo.Format.ARGB32.stride_for_width(w)
        buf = np.empty((h, stride), dtype=np.uint8)
        pixels = buf[:, :w * 4].reshape(h, w, 4)

        a = arr[..., 3].astype(np.uint16)

        # Integer premultiply with rounding
        pixels[..., 0] = ((arr[..., 2].astype(np.uint16) * a + 127) // 255).astype(np.uint8)  # B
        pixels[..., 1] = ((arr[..., 1].astype(np.uint16) * a + 127) // 255).astype(np.uint8)  # G
        pixels[..., 2] = ((arr[..., 0].astype(np.uint16) * a + 127) // 255).astype(np.uint8)  # R
        pixels[..., 3] = arr[..., 3]  # A

        surface = cairo.ImageSurface.create_for_data(
            buf, cairo.FORMAT_ARGB32, w, h, stride
        )
        return surface

    raise ValueError("Expected 1, 3, or 4 channels")


def create_font(name, size=None, style=None):
    """Create a font from a file or from system fonts
    Arguments:

    - `font` (string or object): Either a string describing the font file path or system font name
    """
    # TODO fix API and redundancy here and in text_font
    if os.path.isfile(name):
        try:
            # info = read_font_names(name)
            # font = f"{info['family']} {info['subfamily']}"
            font = create_cairo_font_face_for_file(name)
        except Exception as e:
            print(f"Error: failed to load font {name}:")
            print(e)
    else:
        font = name
    return Font(font, size, style)


def show_image(im, size=None, title="", cmap="gray"):
    """Display a (numpy) image"""
    import matplotlib.pyplot as plt

    if size is not None:
        plt.figure(figsize=size)
    else:
        plt.figure()
    if title:
        plt.title(title)
    plt.imshow(im, cmap)
    plt.show()


def show_images(images, ncols, size=None, title="", cmap="gray"):
    """Display multiple images in a grid"""
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    n = len(images)
    nrows = int(np.ceil(n / ncols))
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
        ax.axis("off")
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

    return np.array([r, g, b, a])[: len(hsva)]


def rgb_to_hsv(rgba):
    r, g, b = rgba[:3]
    a = 1
    if len(rgba) > 3:
        a = rgba[-1]

    K = 0
    if g < b:
        g, b = b, g
        K = -1

    if r < g:
        r, g = g, r
        K = -2 / 6 - K

    chroma = r - g if g < b else r - b #r - (g < b ? g : b);
    h = abs(K + (g - b) / (6 * chroma + 1e-20))
    s = chroma / (r + 1e-20)
    v = r

    return np.array([h, s, v, a])[:len(rgba)]


def cardinal_spline(Q, c, closed=False):
    """Returns a Bezier chain for a Cardinal spline interpolation for a sequence of values
    c is the tension parameter with 0.5 a Catmull-Rom spline
    """
    Q = np.array(Q)
    if closed:
        Q = np.vstack([Q, Q[0]])
    n = len(Q)
    D = []
    for k in range(1, n - 1):
        # Note that we do not take parametrisation into account here
        d = (1 - c) * (Q[k + 1] - Q[k - 1])
        D.append(d)
    if closed:
        d1 = (1 - c) * (Q[1] - Q[-2])
        dn = d1
    else:
        d1 = (1 - c) * (Q[1] - Q[0])
        dn = (1 - c) * (Q[-1] - Q[-2])
    D = [d1] + D + [dn]
    P = [Q[0]]
    for k in range(1, n):
        p1 = Q[k - 1] + D[k - 1] / 3
        p2 = Q[k] - D[k] / 3
        p3 = Q[k]
        P += [p1, p2, p3]
    return np.array(P)


def bernstein(n, i):
    bi = comb(n, i)
    return lambda t, bi=bi, n=n, i=i: bi * t**i * (1 - t) ** (n - i)


def eval_bezier(P, t, d=0):
    """Bezier curve of degree len(P)-1. d is the derivative order (0 gives positions)"""
    n = len(P) - 1
    if d > 0:
        Q = np.diff(P, axis=0) * n
        return eval_bezier(Q, t, d - 1)
    B = np.vstack([bernstein(n, i)(t) for i, p in enumerate(P)])
    return (P.T @ B).T


def approx_arc_length_cubic(c0, c1, c2, c3):
    """Approximate length of a cubic Bezier curve"""
    v0 = np.linalg.norm(c1 - c0) * 0.15
    v1 = np.linalg.norm(
        -0.558983582205757 * c0
        + 0.325650248872424 * c1
        + 0.208983582205757 * c2
        + 0.024349751127576 * c3
    )
    v2 = np.linalg.norm(c3 - c0 + c2 - c1) * 0.26666666666666666
    v3 = np.linalg.norm(
        -0.024349751127576 * c0
        - 0.208983582205757 * c1
        - 0.325650248872424 * c2
        + 0.558983582205757 * c3
    )
    v4 = np.linalg.norm(c3 - c2) * 0.15
    return v0 + v1 + v2 + v3 + v4




def is_compound(S):
    """Returns True if S is a compound polyline,
    a polyline is represented as a list of points, or a numpy array with as many rows as points"""
    if type(S) != list:
        return False
    if type(S) == list:  # [0])==list:
        if not S:
            return True
        for P in S:
            try:
                if is_number(P[0]):
                    return False
            except IndexError:
                pass
        return True
    if type(S[0]) == np.ndarray and len(S[0].shape) > 1:
        return True
    return False



# Code adapted from https://www.cairographics.org/cookbook/freetypepython/

_ft_initialized = False


def create_cairo_font_face_for_file(filename, faceindex=0, loadoptions=0):
    "given the name of a font file, and optional faceindex to pass to FT_New_Face" " and loadoptions to pass to cairo_ft_font_face_create_for_ft_face, creates" " a cairo.FontFace object that may be used to render text with that font."
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
            # ft_lib = "freetype6.dll"
            # lc_lib = "libcairo-2.dll"
            ft_lib = "freetype.dll"
            lc_lib = "cairo.dll"
        elif sys.platform == "darwin":
            ft_lib = "libfreetype.dylib"
            lc_lib = "libcairo.2.dylib"
        else:
            ft_lib = "libfreetype.so.6"
            lc_lib = "libcairo.so.2"

        try:
            _freetype_so = ct.CDLL(ft_lib)
        except OSError as e:
            print(e)
            print("Freetype library missing")
            print("Possibly install with: mamba install freetype")

        _cairo_so = ct.CDLL(lc_lib)
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [
            ct.c_void_p,
            ct.c_int,
        ]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
        )
        _cairo_so.cairo_set_font_face.argtypes = [ct.c_void_p, ct.c_void_p]
        _cairo_so.cairo_font_face_status.argtypes = [ct.c_void_p]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ct.c_void_p]
        # initialize freetype
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d initializing FreeType library." % status)
        # end if

        class PycairoContext(ct.Structure):
            _fields_ = [
                ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                ("ctx", ct.c_void_p),
                ("base", ct.c_void_p),
            ]

        # end PycairoContext
        _PycairoContext = PycairoContext

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int()  # dummy address
        _ft_initialized = True
    # end if

    ft_face = ct.c_void_p()
    cr_face = None
    try:
        # load FreeType face
        status = _freetype_so.FT_New_Face(
            _ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face)
        )
        if status != FT_Err_Ok:
            raise RuntimeError(
                "Error %d creating FreeType font face for %s" % (status, filename)
            )
        # end if

        # create Cairo font face for freetype face
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename)
            )
        # end if
        # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
        # destroyed, so we have to do that for it, by attaching a cleanup callback to
        # the font_face. This only needs to be done once for each font face, while
        # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
        # twice with the same FT Face.
        # The following check for whether the cleanup has been attached or not is
        # actually unnecessary in our situation, because each call to FT_New_Face
        # will return a new FT Face, but we include it here to show how to handle the
        # general case.
        if (
            _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key))
            == None
        ):
            status = _cairo_so.cairo_font_face_set_user_data(
                cr_face, ct.byref(_ft_destroy_key), ft_face, _freetype_so.FT_Done_Face
            )
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError(
                    "Error %d doing user_data dance for %s" % (status, filename)
                )
            # end if
            ft_face = None  # Cairo has stolen my reference
        # end if

        # set Cairo font face into Cairo context
        cairo_ctx = cairo.Context(_surface)
        cairo_t = _PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError(
                "Error %d creating cairo font face for %s" % (status, filename)
            )
        # end if

    finally:
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)
    # end try

    # get back Cairo font face as a Python object
    face = cairo_ctx.get_font_face()
    return face


# Get font family name for file
# https://chatgpt.com/share/68a9d497-6b9c-8005-bff1-61a45501b1d9

# Preferred order for name records:
# 1) Windows/Unicode (platform 3) English (lang 0x0409) if available
# 2) Any Windows/Unicode
# 3) macOS Roman (platform 1) English (lang 0)
# 4) Any other non-empty record
PREFS = [
    (3, None, None, 0x0409),  # Win, any enc, English
    (3, None, None, None),  # Win, any lang
    (1, 0, None, 0),  # Mac Roman, English
    (None, None, None, None),
]


def _pick_name(name_table, name_id):
    # Try preferred platform/encoding/lang combos first
    for plat, enc, lang, lid in PREFS:
        rec = name_table.getName(name_id, plat, enc, lid)
        if rec:
            s = rec.toUnicode().strip()
            if s:
                return s
    # Last resort: first non-empty record of this nameID
    for rec in name_table.names:
        if rec.nameID == name_id:
            s = rec.toUnicode().strip()
            if s:
                return s
    return None


def read_font_names(path):
    """Return a dict with family, subfamily, full_name, postscript_name."""
    with TTFont(path, lazy=True) as f:
        name = f["name"]
        # Family: prefer Typographic Family (16) then legacy Family (1)
        family = _pick_name(name, 16) or _pick_name(name, 1)
        # Subfamily/Style: prefer Typographic Subfamily (17) then legacy Subfamily (2)
        subfamily = _pick_name(name, 17) or _pick_name(name, 2)
        # Full name and PostScript name if present
        full_name = _pick_name(name, 4)
        postscript_name = _pick_name(name, 6)

    return {
        "family": family,
        "subfamily": subfamily,
        "full_name": full_name
        or (f"{family} {subfamily}".strip() if family and subfamily else None),
        "postscript_name": postscript_name,
    }
    #     # end if
    #     # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
    #     # destroyed, so we have to do that for it, by attaching a cleanup callback to
    #     # the font_face. This only needs to be done once for each font face, while
    #     # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
    #     # twice with the same FT Face.
    #     # The following check for whether the cleanup has been attached or not is
    #     # actually unnecessary in our situation, because each call to FT_New_Face
    #     # will return a new FT Face, but we include it here to show how to handle the
    #     # general case.
    #     if (
    #         _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key))
    #         == None
    #     ):
    #         status = _cairo_so.cairo_font_face_set_user_data(
    #             cr_face, ct.byref(_ft_destroy_key), ft_face, _freetype_so.FT_Done_Face
    #         )
    #         if status != CAIRO_STATUS_SUCCESS:
    #             raise RuntimeError(
    #                 "Error %d doing user_data dance for %s" % (status, filename)
    #             )
    #         # end if
    #         ft_face = None  # Cairo has stolen my reference
    #     # end if

    #     # set Cairo font face into Cairo context
    #     cairo_ctx = cairo.Context(_surface)
    #     cairo_t = _PycairoContext.from_address(id(cairo_ctx)).ctx
    #     _cairo_so.cairo_set_font_face(cairo_t, cr_face)
    #     status = _cairo_so.cairo_font_face_status(cairo_t)
    #     if status != CAIRO_STATUS_SUCCESS:
    #         raise RuntimeError(
    #             "Error %d creating cairo font face for %s" % (status, filename)
    #         )
    #     # end if

    # finally:
    #     _cairo_so.cairo_font_face_destroy(cr_face)
    #     _freetype_so.FT_Done_Face(ft_face)
    # # end try

    # # get back Cairo font face as a Python object
    # face = cairo_ctx.get_font_face()
    # return face


# Get font family name for file
# https://chatgpt.com/share/68a9d497-6b9c-8005-bff1-61a45501b1d9

# Preferred order for name records:
# 1) Windows/Unicode (platform 3) English (lang 0x0409) if available
# 2) Any Windows/Unicode
# 3) macOS Roman (platform 1) English (lang 0)
# 4) Any other non-empty record
PREFS = [
    (3, None, None, 0x0409),  # Win, any enc, English
    (3, None, None, None),  # Win, any lang
    (1, 0, None, 0),  # Mac Roman, English
    (None, None, None, None),
]


def _pick_name(name_table, name_id):
    # Try preferred platform/encoding/lang combos first
    for plat, enc, lang, lid in PREFS:
        rec = name_table.getName(name_id, plat, enc, lid)
        if rec:
            s = rec.toUnicode().strip()
            if s:
                return s
    # Last resort: first non-empty record of this nameID
    for rec in name_table.names:
        if rec.nameID == name_id:
            s = rec.toUnicode().strip()
            if s:
                return s
    return None


def read_font_names(path):
    """Return a dict with family, subfamily, full_name, postscript_name."""
    with TTFont(path, lazy=True) as f:
        name = f["name"]
        # Family: prefer Typographic Family (16) then legacy Family (1)
        family = _pick_name(name, 16) or _pick_name(name, 1)
        # Subfamily/Style: prefer Typographic Subfamily (17) then legacy Subfamily (2)
        subfamily = _pick_name(name, 17) or _pick_name(name, 2)
        # Full name and PostScript name if present
        full_name = _pick_name(name, 4)
        postscript_name = _pick_name(name, 6)

    return {
        "family": family,
        "subfamily": subfamily,
        "full_name": full_name
        or (f"{family} {subfamily}".strip() if family and subfamily else None),
        "postscript_name": postscript_name,
    }

def mod2pi(theta):
    return theta - 2.0 * np.pi * np.floor(theta / 2.0 / np.pi)
