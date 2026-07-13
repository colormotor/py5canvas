# Naive SVG loader
from importlib import reload
import svgpathtools as svg
import xml.etree.ElementTree as ET
import numpy as np
import pdb
import re
import matplotlib.colors as mcolors

def v2(x,y): return np.array([x, y])

# Elliptic arc code borrowed from https://github.com/dbrnz/flatmap-ol-maker
def svg_angle(u, v):
    dot = np.dot(u, v)
    length = np.linalg.norm(u)*np.linalg.norm(v)
    angle = np.arccos(np.clip(dot/length, -1, 1))
    if u[0]*v[1] - u[1]*v[0] < 0:
        angle = -angle
    return angle

def elliptic_arc_point(c, r, phi, eta):
    return v2(c[0] + r[0]*np.cos(phi)*np.cos(eta) - r.imag*np.sin(phi)*np.sin(eta),
                    c[1] + r[0]*np.sin(phi)*np.cos(eta) + r[1]*np.cos(phi)*np.sin(eta))

def w(r, phi, eta):
    return v2(-r[0]*np.cos(phi)*np.sin(eta) - r[1]*np.sin(phi)*np.cos(eta),
              -r[0]*np.sin(phi)*np.sin(eta) + r[1]*np.cos(phi)*np.cos(eta))

def cubic_bezier_control_points(c, r, phi, eta1, eta2):
    alpha = np.sin(eta2 - eta1)*(np.sqrt(4 + 3*np.power(np.tan((eta2 - eta1)/2), 2)) - 1)/3
    P1 = elliptic_arc_point(c, r, phi, eta1)
    d1 = elliptic_arc_derivative(r, phi, eta1)
    Q1 = v2(P1[0] + alpha*d1[0], P1[1] + alpha*d1[1])
    P2 = elliptic_arc_point(c, r, phi, eta2)
    d2 = elliptic_arc_derivative(r, phi, eta2)
    Q2 = v2(P2[0] - alpha*d2[0], P2[1] - alpha*d2[1])
    return (P1, Q1, Q2, P2)

def cubic_beziers_from_arc(arc):#r, phi, flagA, flagS, p1, p2):
    r = arc.radius
    p1 = arc.start
    p2 = arc.end
    phi = np.radians(arc.rotation)
    flagA = False #arc.large_arc
    flagS = True #arc.sweep
    # irint(arc)
    r_abs = v2(abs(r[0]), abs(r[1]))
    d = v2((p1[0] - p2[0]), (p1[1] - p2[1]))
    p = v2(np.cos(phi)*d[0]/2 + np.sin(phi)*d[1]/2,
              -np.sin(phi)*d[0]/2 + np.cos(phi)*d[1]/2)
    p_sq = v2(p[0]**2, p[1]**2)
    r_sq = v2(r_abs[0]**2, r_abs[1]**2)

    ratio = p_sq[0]/r_sq[0] + p_sq[1]/r_sq[1]
    if ratio > 1:
        scale = np.sqrt(ratio)
        r_abs = v2(scale*r_abs[0], scale*r_abs[1])
        r_sq = v2(r_abs[0]**2, r_abs[1]**2)

    dq = r_sq[0]*p_sq[1] + r_sq[1]*p_sq[0]
    pq = (r_sq[0]*r_sq[1] - dq)/dq
    q = np.sqrt(max(0, pq))
    if flagA == flagS:
        q = -q

    cp = v2(q * r_abs[0]*p[1]/r_abs[1],
               -q * r_abs[1]*p[0]/r_abs[0])
    c = v2(cp[0]*np.cos(phi) - cp[1]*np.sin(phi) + (p1[0] + p2[0])/2.0,
               cp[0]*np.sin(phi) + cp[1]*np.cos(phi) + (p1[1] + p2[1])/2.0)

    lambda1 = svg_angle(v2(                   1,                     0),
                        v2((p[0] - cp[0])/r_abs[0], ( p[1] - cp[1])/r_abs[1]))
    delta = svg_angle(v2(( p[0] - cp[0])/r_abs[0], ( p[1] - cp[1])/r_abs[1]),
                      v2((-p[0] - cp[0])/r_abs[0], (-p[1] - cp[1])/r_abs[1]))
    delta = delta - 2*np.pi*np.floor(delta/(2*np.pi))
    if not flagS:
        delta -= 2*np.pi
    lambda2 = lambda1 + delta

    t = lambda1
    dt = np.pi/4
    curves = []
    while (t + dt) < lambda2:
        control_points = (cp for cp in cubic_bezier_control_points(c, r_abs, phi, t, t + dt))
        curves.append(svg.CubicBezier(*control_points))
        t += dt
    control_points = (cp for cp in cubic_bezier_control_points(c, r_abs, phi, t, lambda2))
    curves.append(svg.CubicBezier(*(tuple(control_points)[:3]), p2))
    return curves

def to_bezier(piece):
    ''' convert a line or Bezier segment to control points'''
    one3d = 1./3
    if type(piece)==svg.path.Line:
        a, b = piece.start, piece.end
        return [[a, a+(b-a)*one3d, b+(a-b)*one3d, b]]
    elif type(piece)==svg.path.CubicBezier:
        return [[piece.start,
                piece.control1,
                piece.control2,
                piece.end]]
    elif type(piece)==svg.path.QuadraticBezier:
        QP0 = piece.start
        QP1 = piece.control
        QP2 = piece.end
        CP1 = QP0 + 2/3 *(QP1-QP0)
        CP2 = QP2 + 2/3 *(QP1-QP2)
        return [[QP0, CP1, CP2, QP2]]
    elif type(piece)==svg.path.Arc:
        bezs = sum([to_bezier(ap) for ap in cubic_beziers_from_arc(piece)], [])
        # print(bezs)
        return bezs

    raise ValueError

def path_to_bezier(path):
    ''' convert SVG path to a Bezier control points'''
    pieces = sum([to_bezier(piece) for piece in path], [])
    try:
        bezier = [pieces[0][0]] + sum([piece[1:] for piece in pieces],[])
    except IndexError as e:
        print(e)
        breakpoint()
    return np.vstack(bezier)

def to_segment(piece):
    ''' convert a line or Bezier segment to control points'''
    return [piece.start, piece.end]

def path_to_polyline(path):
    ''' convert SVG path to a Bezier control points'''
    pieces = [to_segment(piece) for piece in path]
    try:
        bezier = [pieces[0][0]] + sum([piece[1:] for piece in pieces],[])
    except IndexError:
        import pdb; pdb.set_trace()
    return np.vstack(bezier)


from functools import reduce

def split_compound_paths(paths, data=[]):
    ''' Split compound paths, since svgpathtools does not do that by default'''
    import re
    split_paths = []
    if data:
        split_data = []
        if len(paths) != len(data):
            raise ValueError("Data and path length mismatch")

    groups = []
    out_data = []
    for i, path in enumerate(paths):
        if not path:
            continue
        if data:
            try:
                out_data.append(data[i])
            except IndexError as e:
                breakpoint()
        s = path.d()
        # split at occurrences of moveto commands
        sub_d = filter(None, re.split('[Mm]', s))
        # indices (without moveto) of splits
        lens = [len(list(filter(None, re.split('[A-z]', d))))-1 for d in sub_d]
        # cum sum
        split_inds = [0] + reduce(lambda c, x: c + [c[-1] + x], lens, [0])[1:]
        chunk = [svg.Path(*path[a:b]) for a, b in zip(split_inds, split_inds[1:])]
        if data:
            groups.append(chunk)
            #split_data += [data[i]]*len(chunk)
        else:
            split_paths += chunk
    if data:
        return groups, out_data
        #return split_paths, split_data
    return split_paths

def hex_to_rgb(hex_color):
    """ Convert hex color (#RRGGBB) to an RGB array in range [0,1] """
    try:
        return np.array(mcolors.hex2color(hex_color))  # Normalize 0-1
    except ValueError:
        return None  # Invalid hex

def rgb_string_to_array(rgb_str):
    """ Convert 'rgb(r,g,b)' string to normalized [0,1] RGB array """
    try:
        values = re.findall(r'\d+', rgb_str)  # Extract numbers
        if len(values) == 3:  # Ensure it's an RGB triplet
            return np.array([int(values[0])/255, int(values[1])/255, int(values[2])/255])
    except Exception as e:
        print(e)
        pass
    return None

def parse_color(color_str):
    """ Convert color string (hex, rgb, or named) to a 3D numpy array in range [0,1] """
    if not color_str or color_str.lower() == 'none':
        print(color_str)
        return None  # No color

    color_str = color_str.strip().lower()

    if color_str.startswith('#'):  # Hex format
        return hex_to_rgb(color_str)
    elif color_str.startswith('rgb'):  # RGB format
        return rgb_string_to_array(color_str)
    elif color_str in mcolors.CSS4_COLORS:  # Named colors (e.g., "red")
        return hex_to_rgb(mcolors.CSS4_COLORS[color_str])
    print('unrecognized', color_str)
    return None  # Unrecognized color


def extract_path_colors(svg_path):
    def local_name(tag):
        return tag.rsplit('}', 1)[-1] if '}' in tag else tag

    def parse_style(style_str):
        out = {}
        if not style_str:
            return out
        for part in style_str.split(';'):
            part = part.strip()
            if not part or ':' not in part:
                continue
            k, v = part.split(':', 1)
            out[k.strip()] = v.strip()
        return out

    def parse_css_classes(css_text):
        css_text = css_text or ""
        css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
        class_map = {}
        for selector, body in re.findall(r"([^{}]+)\{([^{}]+)\}", css_text):
            decls = parse_style(body.strip())
            for sel in selector.split(','):
                sel = sel.strip()
                if sel.startswith('.'):
                    cls = sel[1:].strip()
                    if cls:
                        class_map.setdefault(cls, {}).update(decls)
        return class_map

    NAMED = {
        'black': '#000000', 'white': '#ffffff', 'red': '#ff0000',
        'green': '#008000', 'blue': '#0000ff', 'gray': '#808080',
        'grey': '#808080', 'yellow': '#ffff00', 'cyan': '#00ffff',
        'magenta': '#ff00ff'
    }

    def color_to_rgb01(paint_value):
        if paint_value is None:
            return None
        v = str(paint_value).strip()
        if not v:
            return None
        low = v.lower()

        if low in ('none', 'transparent', 'currentcolor'):
            return None
        if low.startswith('url('):
            return None

        if low in NAMED:
            low = NAMED[low]

        if low.startswith('#'):
            h = low[1:]
            if len(h) in (3, 4):
                r = int(h[0]*2, 16)
                g = int(h[1]*2, 16)
                b = int(h[2]*2, 16)
            elif len(h) in (6, 8):
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
            else:
                return None
            return np.array([r/255.0, g/255.0, b/255.0], dtype=float)

        m = re.match(r'^rgba?\(\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)\s*,\s*([0-9.]+%?)', low)
        if m:
            def chan(x):
                if x.endswith('%'):
                    return max(0, min(255, int(round(float(x[:-1]) * 2.55))))
                return max(0, min(255, int(round(float(x)))))
            r = chan(m.group(1))
            g = chan(m.group(2))
            b = chan(m.group(3))
            return np.array([r/255.0, g/255.0, b/255.0], dtype=float)

        return None

    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Collect CSS from all <style> blocks
    css_chunks = []
    for el in root.iter():
        if local_name(el.tag) == 'style':
            css_chunks.append(el.text or "")
    class_styles = parse_css_classes("\n".join(css_chunks))

    def cascaded_value(elem, prop):
        # class rules first
        cls_attr = elem.attrib.get('class', '')
        if cls_attr:
            for cls in cls_attr.split():
                rules = class_styles.get(cls)
                if rules and prop in rules:
                    return rules.get(prop)

        # inline style
        style = parse_style(elem.attrib.get('style', ''))
        if prop in style:
            return style.get(prop)

        # direct attribute
        if prop in elem.attrib:
            return elem.attrib.get(prop)

        return None

    # Include common SVG shape elements (your example uses polygon + line)
    shape_tags = set(['path', 'polygon', 'polyline', 'line', 'rect', 'circle', 'ellipse'])

    results = []
    for elem in root.iter():
        tag = local_name(elem.tag)
        if tag not in shape_tags:
            continue

        fill_paint = cascaded_value(elem, 'fill')
        stroke_paint = cascaded_value(elem, 'stroke')

        results.append({
            'tag': tag,
            'fill': color_to_rgb01(fill_paint),
            'stroke': color_to_rgb01(stroke_paint),
        })

    return results


def svg_to_beziers(path, get_colors=False):
    ''' Load Bezier curves from a SVG file'''
    #pdb.set_trace()
    doc = svg.Document(path)
    paths = doc.paths()
    if get_colors:
        colors = extract_path_colors(path)  # Get colors
        if not colors:
            colors = [dict(fill=np.zeros(3), stroke=None)]*len(paths)
        groups, colors = split_compound_paths(paths, colors) # Actually groups
        if len(colors) != len(groups):
            breakpoint()
    else:
        paths = split_compound_paths(paths)
        colors = []
    #paths, attributes = svg.svg2paths(path)
    #pdb.set_trace()

    if get_colors:
        beziers = [[path_to_bezier(path) for path in paths if len(path)] for paths in groups]
        return beziers, colors
    beziers = [path_to_bezier(path) for path in paths if len(path)]
    return beziers

    
def load_svg(file_path, subd=40, get_colors=False):
    if get_colors:
        groups, colors = svg_to_beziers(file_path, get_colors=True)
    else:
        paths = svg_to_beziers(file_path)
    if get_colors:
        G = [[bezier.bezier_piecewise(path, subd) for path in paths] for paths in groups]
        return G, colors
    S = [bezier.bezier_piecewise(path, subd) for path in paths]
    return S

def load_svg_polylines(path):
    ''' Load Bezier curves from a SVG file'''
    #paths, attributes = svg.svg2paths(path)
    doc = svg.Document(path)
    paths = doc.paths()
    print('Num paths', len(paths))
    paths = split_compound_paths(paths)
    print('Num split paths', len(paths))
    polylines = [path_to_polyline(path) for path in paths if len(path) > 0]
    return polylines

def load_svg_bezier_chains(file_path, subd=40):
    paths = svg_to_beziers(file_path)
    return [path for path in paths]

