#!/usr/bin/env python3
"""Simplistic utilty to mimic [P5js](https://p5js.org) in Python/Jupyter notebooks.

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
from math import fmod, pi


def is_number(x):
    return isinstance(x, numbers.Number)


class Canvas:
    ''' Creates a a pycairo surface that behaves similarly to p5js'''
    def __init__(self, width, height):
        """Initialize Canvas with given `width` and `height`
        """
        # See https://pycairo.readthedocs.io/en/latest/reference/context.html
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surf)
        self.color_scale = 255.0

        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)

        ctx.set_source_rgba(0.0, 0.0, 0.0, 255.0)
        ctx.rectangle(0,0,width,height)
        ctx.fill()

        self._color_mode = 'rgb'
        self.width = width
        self.height = height
        self.surf = surf
        self.ctx = ctx
        self.cur_fill = self._convert_rgba([255.0])
        self.cur_stroke = None
        self.no_draw = False

        self.ctx.select_font_face("sans-serif")
        self.ctx.set_font_size(16)
        self.line_cap('round')

        # Constants
        self.PI = pi
        self.TWO_PI = pi*2

    def set_color_scale(self, scale):
        """Set color scale, e.g. if we want to specify colors in the `0`-`255` range, scale would be `255`,
        or if the colors are in the `0`-`1` range, scale will be `1`"""

        self.color_scale = scale

    @property
    def surface(self):
        return self.surf

    def no_fill(self):
        self.fill(None)

    def no_stroke(self):
        self.stroke(None)

    def color_mode(self, mode, scale=255):
        self._color_mode = mode
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

    def pop(self):
        self.ctx.restore()

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

        """

        if len(args) == 2:
            p, size = args
        elif len(args) == 3:
            p = args[0]
            size = args[1:]
        elif len(args) == 4:
            p = args[:2]
            size = args[2:]
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


    def line(self, *args):
        """Draw a line between given its end points.

        Args:
        Input arguments can be in the following formats:
         `[x1, y1], [x2, y2]`,
         `x1, y1, x2, y2`
        """

        if len(args) == 2:
            a, b = args
        if len(args) == 4:
            a = args[:2]
            b = args[2:]  
        self.ctx.new_path()
        self.ctx.move_to(*a)
        self.ctx.line_to(*b)
        self._fillstroke()

    def begin_shape(self):
        ''' Begin drawing a compound shape'''
        self.no_draw = True

    def end_shape(self):
        ''' End drawing a compound shape'''
        self.no_draw = False
        self._fillstroke()

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
        self.ctx.new_path()
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
        self.ctx.identity_matrix()
        self.ctx.set_source_rgba(*self._apply_colormode(self._convert_rgba(args)))
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()


    def get_buffer(self):
        return self.surf.get_data()


    def get_image(self):
        ''' Get canvas image as a numpy array '''
        img = np.ndarray (shape=(self.height, self.width,4), dtype=np.uint8, buffer=self.surf.get_data())[:,:,:3].copy()
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
            if not is_number(x[0]): # array like input
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
    '''Video Input utility (required OpenCV)'''
    def __init__(self, name=0, size=None, resize_mode='crop'):
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
    
if __name__ == '__main__':
    from skimage import io

    c = Canvas(26, 26)
    c.background(0, 0, 0)

    c.stroke(255)
    c.no_fill()
    c.stroke_weight(2)
    c.fill([255, 0, 0])
    c.text_size(26)
    c.text([13, 22], "B", center=True)
    im = np.vstack([np.linspace(0, 1, 26) for _ in range(26)]).T

    im = np.dstack([im, np.zeros_like(im), np.zeros_like(im), np.ones_like(im)])
    #im = io.imread('./images/test2.png')
    print(im.shape, im.dtype)
    c.image(im) #np.random.uniform(0, 1, (26, 26)))
    #c.polyline(np.random.uniform(0, 26, (10, 2)))
    c.show()

#%%



    c.no_fill()
    c.stroke_weight(13)
    c.line_cap('round')
    c.circle([20, 50], 10)
    c.stroke(255, 0, 255)
    img = c.load_image('images/test.png')
    c.image(img, [200, 100], [120, 20])
    c.line([0,0], [200,60])
    c.line([0,10], [200,90])
    c.stroke(255, 128)
    c.polygon([[10, 20], [100,30], [200,60], [50, 120]])
    c.polygon([[200 + np.cos(t)*100, 200 + np.sin(t)*100] for t in np.linspace(0, np.pi*2, 100)])
    c.fill(255, 0, 0)
    c.begin_shape()
    c.rectangle([20, 20], [200, 200])
    c.rectangle([40, 40], [100, 100])
    c.end_shape()

    im = c.get_image()
    plt.imshow(im)
    plt.show()
