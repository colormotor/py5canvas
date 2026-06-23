#!/usr/bin/env python3
import numpy as np

def array_like(obj):
    return isinstance(obj, (np.ndarray, list, tuple))

class FillRule:
    EVENODD = 'evenodd'
    NONZERO = 'nonzero'
    WINDING = 'nonzero'   # alias for nonzero

class BlendMode:
    CLEAR = 'clear'
    SOURCE = 'source'
    OVER = 'over'
    IN = 'in'
    OUT = 'out'
    ATOP = 'atop'
    DEST = 'dest'
    DEST_OVER = 'dest_over'
    DEST_IN = 'dest_in'
    DEST_OUT = 'dest_out'
    DEST_ATOP = 'dest_atop'
    XOR = 'xor'
    ADD = 'add'
    SATURATE = 'saturate'
    MULTIPLY = 'multiply'
    SCREEN = 'screen'
    OVERLAY = 'overlay'
    DARKEN = 'darken'
    LIGHTEN = 'lighten'
    COLOR_DODGE = 'color_dodge'
    COLOR_BURN = 'color_burn'
    HARD_LIGHT = 'hard_light'
    SOFT_LIGHT = 'soft_light'
    DIFFERENCE = 'difference'
    EXCLUSION = 'exclusion'
    HSL_HUE = 'hsl_hue'
    HSL_SATURATION = 'hsl_saturation'
    HSL_COLOR = 'hsl_color'
    HSL_LUMINOSITY = 'hsl_luminosity'

class LineCap:
    BUTT = 'butt'
    ROUND = 'round'
    SQUARE = 'square'

class LineJoin:
    MITER = 'miter'
    ROUND = 'round'
    BEVEL = 'bevel'

class FontSlant:
    NORMAL = 'normal'
    ITALIC = 'italic'
    OBLIQUE = 'oblique'

class FontWeight:
    NORMAL = 'normal'
    BOLD = 'bold'

class ExtendMode:
    PAD = 'pad'
    REPEAT = 'repeat'
    REFLECT = 'reflect'
        
class Renderer:
    """Abstract base class for all drawing backends."""

    # These will be overridden by subclasses
    def move_to(self, x: float, y: float): pass
    def line_to(self, x: float, y: float): pass
    def curve_to(self, cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float): pass
    def close_path(self): pass
    def new_sub_path(self): pass
    def arc(self, xc: float, yc: float, radius: float, angle1: float, angle2: float): pass
    def rectangle(self, x: float, y: float, width: float, height: float, radius: float): pass
    def ellipse(self, x, y, rw, rh): pass
    
    def fill(self): pass
    def stroke(self): pass
    def fillstroke(self): pass
    def fill_preserve(self): fill()  # default: no preserve, will be overridden by Cairo
    def stroke_preserve(self): stroke()

    def get_line_width(self): pass
    def set_fill(self, fill): pass
    def set_stroke(self, stroke): pass
    
    def set_source_gradient(self, gradient):
        raise NotImplementedError
    
    #def set_source_rgba(self, r: float, g: float, b: float, a: float): pass
    #
    def set_line_width(self, w: float): pass
    def set_dash(self, dashes): pass
    def set_line_cap(self, cap: str): pass
    def set_line_join(self, join: str): pass
    def set_fill_rule(self, rule: str): pass
    def set_blend_mode(self, mode: str): pass
    def get_blend_mode(self): pass
    def set_font_size(self, size: float): pass
    def select_font_face(self, family: str, slant: str = FontSlant.NORMAL,
                         weight: str = FontWeight.NORMAL): pass
    def text_extents(self, text): pass   # returns TextExtents namedtuple

    def save(self): pass
    def restore(self): pass
    def translate(self, tx: float, ty: float): pass
    def scale(self, sx: float, sy: float): pass
    def rotate(self, angle_rad: float): pass
    def set_matrix(self, matrix): pass
    def transform(self, matrix): pass
    
    def get_matrix(self): pass
    def get_origin(self): pass
    def paint(self): pass   # fill whole canvas with current color
    def paint_with_alpha(self, alpha: float): pass
    def mask_surface(self, surface, dx, dy): pass

    def get_surface(self): return None
    
    # For raster backends only
    def get_image_array(self) -> np.ndarray: return None
    def create_image_surface(self, width, height): return None

    # For vector backends
    def get_svg_string(self) -> str: return None
    def save_svg(self, path): pass

    # Optional: drawing images (will raise NotImplementedError for SVG)
    def set_source_surface(self, surface, x=0, y=0): pass
    def paint_image(self, img_surface, opacity=1.0): pass

try:
    import cairo


    class MultiContext:
        """Workaround for TeeSurface not working on Mac (at least)
        This should enable rendering to multiple surfaces (each with their own context)
        """
        def __init__(self, surf):
            self.surface = surf
            self.dirty = False
            self.ctxs = [cairo.Context(surf)]
            for key, value in cairo.Context.__dict__.items():
                if hasattr(value, "__call__"):
                    self.__dict__[key] = wrapper(self, key)

        def push_context(self, ctx):
            self.ctxs.append(ctx)

        def pop_context(self):
            self.ctxs.pop()

            
    def wrapper(self, fn):
        def result(*args, **kwargs):
            res = None
            self.dirty = True
            for ctx in self.ctxs:  # [::-1]:
                res = getattr(ctx, fn)(*args, **kwargs)
            return res
        return result


    class CairoRenderer(Renderer):
        """Wraps a Cairo context (with MultiContext support) and implements the Renderer API."""

        def __init__(self, width, height, recording=False):
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            self._surf = surf
            self._ctx = MultiContext(surf)        
            self.width = width
            self.height = height
            self._fill = (0,0,0,1)
            self._stroke = (0,0,0,1)
            self._line_width = 1
            self._dash = []
            self._fill_rule = FillRule.NONZERO
            self._blend_mode = BlendMode.OVER
            self._ctx.set_fill_rule(_cairo_fill_rule_map[self._fill_rule])
            self.recording_surface = None
            if recording:
                self.recording_surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
                self._recording_ctx = cairo.Context(self.recording_surface)
                self._ctx.push_context(self._recording_ctx)

        def get_origin(self):
            """Get the origin in canvas coordinates for the current transformation.
            Returns a 2d numpy array"""
            return np.array([self._ctx.get_matrix().x0,
                            self._ctx.get_matrix().y0])
        def get_line_width(self): return self._ctx.get_line_width()
        
        def move_to(self, x, y): self._ctx.move_to(x, y)
        def line_to(self, x, y): self._ctx.line_to(x, y)
        def curve_to(self, cx1, cy1, cx2, cy2, x, y):
            self._ctx.curve_to(cx1, cy1, cx2, cy2, x, y)
        def close_path(self): self._ctx.close_path()
        def new_sub_path(self): self._ctx.new_sub_path()
        def arc(self, xc, yc, radius, angle1, angle2):
            self._ctx.arc(xc, yc, radius, angle1, angle2)
            
        def rectangle(self, x, y, width, height, radius=None):
            self.new_sub_path()
            if radius is not None:
                radius = min(radius, min(width, height) / 2)
                self._roundrect(x, y, width, height, radius)
            else:
                self._ctx.rectangle(x, y, width, height)
            
        def ellipse(self, x, y, rw, rh):
            self.save()
            self.translate(x, y)
            self.scale(rw*2, rh*2)
            self.new_sub_path()
            self.arc(0, 0, 1, 0, np.pi * 2.0)
            self.restore()
            
        def _roundrect(self, x, y, w, h, r):
            # https://www.geeksforgeeks.org/python/pycairo-drawing-the-roundrect/
            self.arc(x + r, y + r, r, np.pi, 3 * np.pi / 2)
            self.arc(x + w - r, y + r, r, 3 * np.pi / 2, 0)
            self.arc(x + w - r, y + h - r, r, 0, np.pi / 2)
            self.arc(x + r, y + h - r, r, np.pi / 2, np.pi)
            self.close_path()

        def _set_fill(self):
            if array_like(self._fill):
                self._ctx.set_source_rgba(*self._fill) 
            else:
                # Assume gradient
                self._ctx.set_source(self._fill.gradient)
                
        def fill(self):
            self._set_fill()
            self._ctx.fill()
            
        def stroke(self):
            self._ctx.set_source_rgba(*self._stroke)
            self._ctx.stroke()
            
        def fill_preserve(self):
            self._set_fill()
            self._ctx.fill_preserve()
            
        def stroke_preserve(self):
            self._ctx.set_source_rgba(*self._stroke)
            self._ctx.stroke_preserve()

        def fillstroke(self):
            if self._fill is not None:
                if array_like(self._fill):
                    self._ctx.set_source_rgba(*self._fill) 
                else:
                    # Assume gradient
                    self._ctx.set_source(self._fill.gradient)
                
                if self._stroke is not None:
                    self._ctx.fill_preserve()
                else:
                    self._ctx.fill()
            if self._stroke is not None:
                self._ctx.set_source_rgba(*self._stroke)
                self._ctx.stroke()

        def background(self, rgba, first=False, save=True):
            if first:
                cur_op = self.get_blend_mode()
                self.set_blend_mode('source')
            
            if save:
                self.set_fill(rgba)
                self.rectangle(0, 0, self.width, self.height)
                self.fill()
            else:
                self.set_source_rgba(*rgba)
                self.paint()

            if first:
                self.set_blend_mode(cur_op)
                
        # Styling
        def set_fill(self, fill):
            self._fill = fill
            
        def set_stroke(self, stroke):
            self._stroke = stroke

        
        # def set_fill_gradient(self, gradient):
        #     self._fill = gradient.gradient
            
        def set_source_rgba(self, r, g, b, a):
            self._ctx.set_source_rgba(r, g, b, a)

        # def set_source_gradient(self, gradient):
        #     self._ctx.set_source(gradient.gradient)   # gradient.gradient is the Cairo object
            
        def set_line_width(self, w): self._ctx.set_line_width(w)
        def set_dash(self, dashes): self._ctx.set_dash(dashes)
        def set_line_cap(self, cap: str):
            self._ctx.set_line_cap(_cairo_line_cap_map[cap])
        def set_line_join(self, join: str):
            self._ctx.set_line_join(_cairo_line_join_map[join])
        def set_fill_rule(self, rule: str):
            self._fill_rule = rule
            self._ctx.set_fill_rule(_cairo_fill_rule_map[rule])
        def set_blend_mode(self, mode: str):
            self._blend_mode = mode
            self._ctx.set_operator(_cairo_blend_map[mode])
        def get_blend_mode(self):
            return self._blend_mode
        def set_font_size(self, size: float):
            self._ctx.set_font_size(size)
        def select_font_face(self, family: str, slant: str = FontSlant.NORMAL,
                            weight: str = FontWeight.NORMAL):
            self._ctx.select_font_face(family, _cairo_slant_map.get(slant, cairo.FontSlant.NORMAL),
                                    _cairo_weight_map.get(weight, cairo.FontWeight.NORMAL))
        def text_extents(self, text):
            return self._ctx.get_scaled_font().text_extents(text)

        def save(self): self._ctx.save()
        def restore(self): self._ctx.restore()
        def translate(self, tx, ty): self._ctx.translate(tx, ty)
        def scale(self, sx, sy): self._ctx.scale(sx, sy)
        def rotate(self, angle_rad): self._ctx.rotate(angle_rad)
        def transform(self, mat): 
            if isinstance(mat, np.ndarray):
                mat = cairo.Matrix(mat[0][0], mat[1][0], mat[0][1], mat[1][1], mat[0][2], mat[1][2])
            self._ctx.transform(mat)
        def set_matrix(self, mat):
            if isinstance(mat, np.ndarray):
                mat = cairo.Matrix(mat[0][0], mat[1][0], mat[0][1], mat[1][1], mat[0][2], mat[1][2])
            self._ctx.set_matrix(mat)
        def get_matrix(self):
            return self._ctx.get_matrix()
        def get_origin(self):
            mat = self.get_matrix()
            return np.array([mat.x0, mat.y0])

        def get_surface(self): return self._surf
        
        def paint(self):
            self._ctx.paint()
        def paint_with_alpha(self, alpha):
            self._ctx.paint_with_alpha(alpha)
        def mask_surface(self, surface, dx, dy):
            self._ctx.mask_surface(surface, dx, dy)

        def get_image_array(self) -> np.ndarray:
            img = np.ndarray(shape=(self.height, self.width, 4), dtype=np.uint8,
                            buffer=self._surf.get_data())[:, :, :3].copy()
            img = img[:, :, ::-1]
            return img

        def save_svg(self, path):
            surf = cairo.SVGSurface(path, self.width, self.height)
            ctx = cairo.Context(surf)
            ctx.set_source_surface(self.recording_surface)
            ctx.paint()
            surf.finish()
            fix_svg(path)
            #fix_clip_path(path, path)

        def get_svg_string(self):
            raise NotImplementedError("CairoRenderer does not produce raw SVG string")

        def set_source_surface(self, surface, x=0, y=0):
            self._ctx.set_source_surface(surface, x, y)

        # For gradient support
        def set_source_gradient(self, gradient):
            self._ctx.set_source(gradient.gradient)

        # Additional Cairo-specific helpers
        def push_group(self):
            self._ctx.push_group()

        def pop_group_to_source(self):
            self._ctx.pop_group_to_source()

        def set_font_face(self, face):
            self._ctx.set_font_face(face)

        def get_scaled_font(self):
            return self._ctx.get_scaled_font()

        def text_path(self, text):
            self._ctx.text_path(text)

        def copy_path(self):
            return self._ctx.copy_path()

    
    # Maps from generic enums to cairo
    _cairo_fill_rule_map = {
        FillRule.EVENODD: cairo.FILL_RULE_EVEN_ODD,
        FillRule.NONZERO: cairo.FILL_RULE_WINDING,
    }
    _cairo_blend_map = {
        BlendMode.CLEAR: cairo.OPERATOR_CLEAR,
        BlendMode.SOURCE: cairo.OPERATOR_SOURCE,
        BlendMode.OVER: cairo.OPERATOR_OVER,
        BlendMode.IN: cairo.OPERATOR_IN,
        BlendMode.OUT: cairo.OPERATOR_OUT,
        BlendMode.ATOP: cairo.OPERATOR_ATOP,
        BlendMode.DEST: cairo.OPERATOR_DEST,
        BlendMode.DEST_OVER: cairo.OPERATOR_DEST_OVER,
        BlendMode.DEST_IN: cairo.OPERATOR_DEST_IN,
        BlendMode.DEST_OUT: cairo.OPERATOR_DEST_OUT,
        BlendMode.DEST_ATOP: cairo.OPERATOR_DEST_ATOP,
        BlendMode.XOR: cairo.OPERATOR_XOR,
        BlendMode.ADD: cairo.OPERATOR_ADD,
        BlendMode.SATURATE: cairo.OPERATOR_SATURATE,
        BlendMode.MULTIPLY: cairo.OPERATOR_MULTIPLY,
        BlendMode.SCREEN: cairo.OPERATOR_SCREEN,
        BlendMode.OVERLAY: cairo.OPERATOR_OVERLAY,
        BlendMode.DARKEN: cairo.OPERATOR_DARKEN,
        BlendMode.LIGHTEN: cairo.OPERATOR_LIGHTEN,
        BlendMode.COLOR_DODGE: cairo.OPERATOR_COLOR_DODGE,
        BlendMode.COLOR_BURN: cairo.OPERATOR_COLOR_BURN,
        BlendMode.HARD_LIGHT: cairo.OPERATOR_HARD_LIGHT,
        BlendMode.SOFT_LIGHT: cairo.OPERATOR_SOFT_LIGHT,
        BlendMode.DIFFERENCE: cairo.OPERATOR_DIFFERENCE,
        BlendMode.EXCLUSION: cairo.OPERATOR_EXCLUSION,
        BlendMode.HSL_HUE: cairo.OPERATOR_HSL_HUE,
        BlendMode.HSL_SATURATION: cairo.OPERATOR_HSL_SATURATION,
        BlendMode.HSL_COLOR: cairo.OPERATOR_HSL_COLOR,
        BlendMode.HSL_LUMINOSITY: cairo.OPERATOR_HSL_LUMINOSITY,
    }
    _cairo_line_cap_map = {
        LineCap.BUTT: cairo.LINE_CAP_BUTT,
        LineCap.ROUND: cairo.LINE_CAP_ROUND,
        LineCap.SQUARE: cairo.LINE_CAP_SQUARE,
    }
    _cairo_line_join_map = {
        LineJoin.MITER: cairo.LINE_JOIN_MITER,
        LineJoin.ROUND: cairo.LINE_JOIN_ROUND,
        LineJoin.BEVEL: cairo.LINE_JOIN_BEVEL,
    }
    _cairo_slant_map = {
        FontSlant.NORMAL: cairo.FontSlant.NORMAL,
        FontSlant.ITALIC: cairo.FontSlant.ITALIC,
        FontSlant.OBLIQUE: cairo.FontSlant.OBLIQUE,
    }
    _cairo_weight_map = {
        FontWeight.NORMAL: cairo.FontWeight.NORMAL,
        FontWeight.BOLD: cairo.FontWeight.BOLD,
    }


except ImportError:
    CairoRenderer = None
    

class SVGRenderer(Renderer):
    """Generates SVG elements directly, suitable for Pyodide/Marimo."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._path_parts = []          # list of SVG path commands (strings)
        self._elements = []            # list of SVG elements (<path>, <circle>, etc.)
        self._current_element = None
        self._fill = (0, 0, 0, 1)
        self._stroke = (0, 0, 0, 1)
        self._line_width = 1
        self._dash = []
        self._cap = LineCap.BUTT
        self._join = LineJoin.MITER
        self._fill_rule = FillRule.NONZERO
        self._blend_mode = BlendMode.OVER
        self._matrix_stack = [np.eye(3)]
        self._font_size = 10
        self._font_family = "sans-serif"
        self._font_slant = FontSlant.NORMAL
        self._font_weight = FontWeight.NORMAL
        # recording of background (we'll draw a rect for background)
        self._background = None
        self._gradients = {}        # id -> Gradient object
        self._gradient_id_counter = 0
        self._current_gradient = None
        
    def _add_path_command(self, cmd):
        self._path_parts.append(cmd)

        
    def _emit_path(self, close=False):
        if not self._path_parts:
            return
        d = ' '.join(self._path_parts)
        if close:
            d += ' Z'
        
        tag = f'<path d="{d}" style="{self._svg_style()}" transform="{self._svg_transform()}" />'
        self._elements.append(tag)
        self._path_parts = []

    def _svg_transform(self):
        m = self._matrix_stack[-1]
        # matrix is 3x3 affine, we need a, b, c, d, e, f for SVG matrix()
        # Cairo matrix: xx, yx, xy, yy, x0, y0  -> a=xx, b=yx, c=xy, d=yy, e=x0, f=y0
        # Our numpy matrix is standard: [[a, c, e], [b, d, f], [0,0,1]]
        # So a=m[0,0], b=m[1,0], c=m[0,1], d=m[1,1], e=m[0,2], f=m[1,2]
        a, c, e = m[0,0], m[0,1], m[0,2]
        b, d, f = m[1,0], m[1,1], m[1,2]
        return f'matrix({a:.6g},{b:.6g},{c:.6g},{d:.6g},{e:.6g},{f:.6g})'

    def _svg_style(self):
        style_parts = []
        style_parts = []
        f = self._fill
        if f is not None and f[3] > 0:
            style_parts.append(f'fill:rgba({int(f[0]*255)},{int(f[1]*255)},{int(f[2]*255)},{int(f[3]*255)})')
        else:
            style_parts.append('fill:none')
        s = self._stroke
        if s is not None and s[3] > 0:
            style_parts.append(f'stroke:rgba({int(s[0]*255)},{int(s[1]*255)},{int(s[2]*255)},{int(s[3]*255)})')
            style_parts.append(f'stroke-width:{self._line_width}')
            if self._dash:
                dashes = ', '.join(str(x) for x in self._dash)
                style_parts.append(f'stroke-dasharray:{dashes}')
            cap_map = {LineCap.BUTT:'butt', LineCap.ROUND:'round', LineCap.SQUARE:'square'}
            style_parts.append(f'stroke-linecap:{cap_map[self._cap]}')
            join_map = {LineJoin.MITER:'miter', LineJoin.ROUND:'round', LineJoin.BEVEL:'bevel'}
            style_parts.append(f'stroke-linejoin:{join_map[self._join]}')
        else:
            style_parts.append('stroke:none')

        if self._current_gradient:
            self._style_parts.append(f'fill:url(#{self._current_gradient})')
            
        fill_rule = 'nonzero' if self._fill_rule == FillRule.NONZERO else 'evenodd'
        style_parts.append(f'fill-rule:{fill_rule}')
        if self._blend_mode != BlendMode.OVER:
            style_parts.append(f'mix-blend-mode:{self._blend_mode}')
        style = '; '.join(style_parts)
        return style
    
    def move_to(self, x, y):
        self._add_path_command(f'M {x:.4f} {y:.4f}')

    def line_to(self, x, y):
        self._add_path_command(f'L {x:.4f} {y:.4f}')

    def curve_to(self, cx1, cy1, cx2, cy2, x, y):
        self._add_path_command(f'C {cx1:.4f} {cy1:.4f} {cx2:.4f} {cy2:.4f} {x:.4f} {y:.4f}')

    def close_path(self):
        self._add_path_command('Z')

    def new_sub_path(self):
        # Not needed for SVG as new_path starts a new d= string if we call move_to
        pass

    def arc(self, xc, yc, radius, angle1, angle2):
        # TODO broken
        # Ensure angles are counter‑clockwise and within [0, 2π) for consistency
        a1 = angle1 % (2 * np.pi)
        a2 = angle2 % (2 * np.pi)
        if a2 <= a1:
            a2 += 2 * np.pi

        # Full circle?
        full = (a2 - a1) >= (2 * np.pi - 1e-12)
        if full:
            # Split into two semi‑circles
            self.arc(xc, yc, radius, a1, a1 + np.pi)
            self.arc(xc, yc, radius, a1 + np.pi, a1 + 2 * np.pi)
            return

        # Start point of the arc
        sx = xc + radius * np.cos(a1)
        sy = yc + radius * np.sin(a1)

        # If the path buffer is empty, we must start a new sub‑path (like Cairo)
        if not self._path_parts:
            self.move_to(sx, sy)               # append 'M' command

        # End point of the arc
        ex = xc + radius * np.cos(a2)
        ey = yc + radius * np.sin(a2)

        # Determine large‑arc and sweep flags
        sweep_angle = a2 - a1
        large = 1 if sweep_angle > np.pi else 0
        sweep = 1  # clockwise orientation (matches Cairo's increasing‑angle direction)

        self._path_parts.append(
            f'A {radius:.4f} {radius:.4f} 0 {large} {sweep} {ex:.4f} {ey:.4f}'
        )

        
    def rectangle(self, x, y, w, h, r=None):
        # TODO broken
        if r is None:
            r = 0
        style = self._svg_style()
        self._elements.append(f'<rect x="{x:.4f}" y="{y:.4f}" '
                               f'width="{w:.4f}" height="{h:.4f}" rx="{r:.4f}" ry="{r:.4f}" '
                               f'style="{style}" '
                               f'transform="{self._svg_transform()}"/>')
        
    
    def fill(self):
        if self._fill is not None and self._fill[3] > 0:
            self._emit_path()

    def stroke(self):
        if self._stroke is not None and self._stroke[3] > 0:
            self._emit_path()

    def fillstroke(self):
        if self._fill is not None or self._stroke is not None:
            self._emit_path()
        
                
    def fill_preserve(self):
        # SVG doesn't have fill_preserve, we'll just fill and not clear path so it can be stroked.
        self.fill()
        # keep path_parts?

    def stroke_preserve(self):
        self.stroke()
        # keep path_parts?

    def background(self, rgba, first=False, save=True):
        old_fill = self._fill
        self.set_fill(rgba)
        self.rectangle(0, 0, self.width, self.height)
        self.fill()
        self._fill = old_fill
        
    def set_source_rgba(self, r, g, b, a):
        # store for later fill/stroke
        self._fill = (r, g, b, a)
        self._stroke = (r, g, b, a)  # will be set separately by canvas

    # Styling
    def set_fill(self, fill):
        self._fill = fill

    def set_stroke(self, stroke):
        self._stroke = stroke

    def set_source_gradient(self, gradient):
        # Generate a unique ID and store the gradient info
        grad_id = f'grad{self._gradient_id_counter}'
        self._gradient_id_counter += 1
        self._gradients[grad_id] = gradient
        # Set fill/stroke to use this gradient (will be used in _emit_path)
        self._current_gradient = grad_id

    def _generate_gradient_defs(self):
        defs = []
        for grad_id, grad in self._gradients.items():
            stops_xml = []
            for stop in grad.stops_data:
                offset, *rgba = stop
                r, g, b, a = rgba if len(rgba)==4 else (*rgba, 1.0)
                stops_xml.append(
                    f'<stop offset="{offset}" stop-color="rgba({int(r*255)},{int(g*255)},{int(b*255)},{a})" />'
                )
            spread = grad.extend_mode   # 'pad', 'repeat', 'reflect'
            if grad.kind == 'linear':
                x1, y1 = grad.start
                x2, y2 = grad.end
                defs.append(
                    f'<linearGradient id="{grad_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'gradientUnits="userSpaceOnUse" spreadMethod="{spread}">'
                    + ''.join(stops_xml) +
                    '</linearGradient>'
                )
            else:  # radial
                cx0, cy0, r0 = grad.inner
                cx1, cy1, r1 = grad.outer
                defs.append(
                    f'<radialGradient id="{grad_id}" cx="{cx1}" cy="{cy1}" r="{r1}" '
                    f'fx="{cx0}" fy="{cy0}" gradientUnits="userSpaceOnUse" spreadMethod="{spread}">'
                    + ''.join(stops_xml) +
                    '</radialGradient>'
                )
        return ''.join(defs)

    def set_line_width(self, w): self._line_width = w
    def set_dash(self, dashes): self._dash = list(dashes)
    def set_line_cap(self, cap): self._cap = cap
    def set_line_join(self, join): self._join = join
    def set_fill_rule(self, rule): self._fill_rule = rule
    def set_blend_mode(self, mode): self._blend_mode = mode
    def get_blend_mode(self): return self._blend_mode
    def set_font_size(self, size): self._font_size = size
    def select_font_face(self, family, slant=FontSlant.NORMAL, weight=FontWeight.NORMAL):
        self._font_family = family
        self._font_slant = slant
        self._font_weight = weight

    def text_extents(self, text):
        # Rough extents without actual font metrics; return dummy
        from collections import namedtuple
        TextExtents = namedtuple('TextExtents', 'x_bearing y_bearing width height x_advance y_advance')
        return TextExtents(0, -self._font_size*0.8, self._font_size*0.6*len(text), self._font_size,
                           self._font_size*0.6*len(text), 0)

    def save(self):
        self._matrix_stack.append(np.array(self._matrix_stack[-1]))

    def restore(self):
        self._matrix_stack.pop()

    def translate(self, tx, ty):
        m = self._matrix_stack[-1]
        self._matrix_stack[-1] = m @ np.array([[1,0,tx],[0,1,ty],[0,0,1]])

    def scale(self, sx, sy):
        m = self._matrix_stack[-1]
        self._matrix_stack[-1] = m @ np.array([[sx,0,0],[0,sy,0],[0,0,1]])

    def rotate(self, angle_rad):
        c = np.cos(angle_rad)
        s = np.sin(angle_rad)
        m = self._matrix_stack[-1]
        self._matrix_stack[-1] = m @ np.array([[c, -s, 0],[s, c, 0],[0,0,1]])

    def set_matrix(self, matrix):
        self._matrix_stack[-1] = matrix

    def apply_matrix(self, matrix):
        self._matrix_stack[-1] *= matrix
        
    def get_matrix(self):
        return self._matrix_stack[-1]

    def get_origin(self):
        return self._matrix_stack[-1][:2,2]

    def paint(self):
        if self._background is not None:
            self._elements.insert(0, f'<rect width="100%" height="100%" fill="{self._background}" />')

    def paint_with_alpha(self, alpha):
        pass  # not needed

    def mask_surface(self, surface, dx, dy):
        raise NotImplementedError("SVG renderer does not support mask_surface")

    def set_source_surface(self, surface, x=0, y=0):
        raise NotImplementedError("SVG renderer does not support image drawing")

    def get_image_array(self):
        return None

    def save_svg(self, path):
        with open(path, 'w') as f:
            f.write(self.get_svg_string())

    def get_svg_string(self):
        # Assemble all elements into a full SVG document
        defs = self._generate_gradient_defs()
        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}">')
        if defs:
            svg.append(f'<defs>{defs}</defs>')
        for elem in self._elements:
            svg.append(elem)
        svg.append('</svg>')
        return '\n'.join(svg)


# Fix svg export clip path
# RecordingSurface adds a clip-path attribute that breaks Illustrator import
def fix_namespace(xml_content):
    # return xml_content
    # Remove namespace prefixes from the XML content and replace ns1 with xlink (argh)
    xml_content = xml_content.replace("ns0:", "").replace(":ns0", "")
    xml_content = xml_content.replace("ns1:", "xlink:").replace(":ns1", ":xlink")
    # Remove defs as svgpathtools cannot load these
    # TODO this might bite us back
    xml_content = xml_content.replace("<svg:defs>", "").replace("</svg:defs>", "")
    return xml_content


def fix_clip_path(file_path, out_path):
    import xml.etree.ElementTree as ET

    # Load the SVG file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Define the namespace
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    # Find the first <g> tag
    g_tag = root.find(".//svg:g", namespace)

    # Remove the 'clip-path' attribute if it exists
    if "clip-path" in g_tag.attrib:
        del g_tag.attrib["clip-path"]
    res = ET.tostring(root, encoding="unicode")
    # Save and then apply fixes
    tree.write(out_path, encoding="UTF-8", xml_declaration=True, default_namespace="")
    with open(out_path, "r") as f:
        # Fix namepace
        txt = fix_namespace(f.read())
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(txt)


def fix_svg(path, out_path=None):
    import xml.etree.ElementTree as ET
    if out_path is None:
        out_path = path

    SVG_NS = "http://www.w3.org/2000/svg"
    XLINK_NS = "http://www.w3.org/1999/xlink"

    # Preserve the prefixes Cairo writes
    ET.register_namespace("svg", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)

    tree = ET.parse(path)
    root = tree.getroot()

    svg_g = f"{{{SVG_NS}}}g"
    svg_use = f"{{{SVG_NS}}}use"

    # Old fix_clip_path behavior
    g_tag = root.find(f".//{svg_g}")
    if g_tag is not None and "clip-path" in g_tag.attrib:
        del g_tag.attrib["clip-path"]

    # Remove the duplicate-rendering <use> element
    for use in list(root.iter(svg_use)):
        href = use.get("href") or use.get(f"{{{XLINK_NS}}}href")
        if href and href.startswith("#"):
            parent = next((p for p in root.iter() if use in list(p)), None)
            if parent is not None:
                parent.remove(use)

    tree.write(out_path, encoding="UTF-8", xml_declaration=True)

    # Existing namespace cleanup
    with open(out_path, "r", encoding="utf-8") as f:
        txt = fix_namespace(f.read())
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(txt)
