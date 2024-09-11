
# Table of Contents

1.  [`Canvas` class](#org75849f3)
    1.  [`set_color_scale(...)`](#org192e246)
    2.  [`rect_mode(...)`](#org5a10562)
    3.  [`center` (property)](#org8b54155)
    4.  [`width` (property)](#org362d502)
    5.  [`height` (property)](#org7fecd31)
    6.  [`no_fill()`](#org17e8e42)
    7.  [`no_stroke()`](#orge4c47c8)
    8.  [`color_mode(...)`](#org137ab9a)
    9.  [`fill()`](#org3c78a57)
    10. [`stroke()`](#orgc456a45)
    11. [`stroke_weight(...)`](#org2096992)
    12. [`line_join(...)`](#org08add77)
    13. [`blend_mode(...)`](#orgabae718)
    14. [`line_cap(...)`](#orga6b531b)
    15. [`text_size(...)`](#orgd532a0b)
    16. [`text_font(...)`](#orgadb6a33)
    17. [`push()`](#orgbf317e8)
    18. [`pop()`](#org70a9d5a)
    19. [`translate()`](#org958fc20)
    20. [`scale()`](#org39cdb9d)
    21. [`rotate(...)`](#org672e8f0)
    22. [`apply_matrix(...)`](#orgb048bb3)
    23. [`rotate_deg(...)`](#org875ed24)
    24. [`rectangle()`](#orgd79f7ab)
    25. [`rect()`](#org154fb73)
    26. [`quad()`](#org383a042)
    27. [`arrow(...)`](#orgd0f7b16)
    28. [`triangle()`](#org438c9bc)
    29. [`circle()`](#org622f91a)
    30. [`ellipse()`](#org484e542)
    31. [`arc()`](#orgf60ad2f)
    32. [`begin_shape()`](#org1764557)
    33. [`end_shape(...)`](#org4dadc05)
    34. [`begin_contour()`](#orgc315c00)
    35. [`end_contour(...)`](#org0b6b499)
    36. [`vertex(...)`](#orgddfeb91)
    37. [`curve_vertex(...)`](#org276d1ae)
    38. [`load_image(...)`](#org5b1b921)
    39. [`image(...)`](#orgb9dffc5)
    40. [`shape(...)`](#org018731f)
    41. [`text(...)`](#org71c3619)
    42. [`polygon()`](#org43d74b5)
    43. [`polyline()`](#orgbbf328e)
    44. [`background()`](#org97fa5c4)
    45. [`get_image()`](#orgbb08f96)
    46. [`get_image_grayscale()`](#orgd656aba)
    47. [`save_image(...)`](#orgfa5b3d9)
    48. [`save_svg(...)`](#org4076288)
    49. [`save_pdf(...)`](#org218e825)
    50. [`save(...)`](#orgf327d6e)
    51. [`show()`](#orgfd4610d)
    52. [`show_plt(...)`](#org912bf87)



<a id="org75849f3"></a>

# `Canvas` class

Creates a drawing canvas (pyCairo) that behaves similarly to p5js

Constructor arguments:

-   `width` : (`int`), width of the canvas in pixels
-   `height` : (`int`), height of the canvas in pixels
-   `clear_callback` (optional): function, a callback to be called when the canvas is cleared (for internal use mostly)


<a id="org192e246"></a>

## `set_color_scale(...)`

Set color scale:

Arguments:

-   `scale` (float): the color scale. if we want to specify colors in the `0...255` range,

`scale` will be `255`. If we want to specify colors in the `0...1` range, `scale` will be `1`


<a id="org5a10562"></a>

## `rect_mode(...)`

Set the &ldquo;mode&rdquo; for drawing rectangles.

Arguments:

-   `mode` (string): can be one of &rsquo;corner&rsquo;, &rsquo;center&rsquo;, &rsquo;radius&rsquo;


<a id="org8b54155"></a>

## `center` (property)

The center of the canvas (as a 2d numpy array)


<a id="org362d502"></a>

## `width` (property)

The width of canvas


<a id="org7fecd31"></a>

## `height` (property)

The height of canvas


<a id="org17e8e42"></a>

## `no_fill()`

Do not fill subsequent shapes


<a id="orge4c47c8"></a>

## `no_stroke()`

Do not stroke subsequent shapes


<a id="org137ab9a"></a>

## `color_mode(...)`

Set the color mode for the canvas

Arguments:

-   `mode` (string): can be one of &rsquo;rgb&rsquo;, &rsquo;hsv&rsquo; depending on the desired color mode
-   `scale` (float): the scale for the color values (e.g. 255 for 0&#x2026;255 range, 1 for 0&#x2026;1 range)


<a id="org3c78a57"></a>

## `fill()`

Set the color of the current fill

Arguments:

-   A single argument specifies a grayscale value, e.g `c.fill(128)` will fill with 50% gray.
-   Two arguments specify grayscale with opacity, e.g. `c.fill(255, 128)` will fill with transparent white.
-   Three arguments specify a color depending on the color mode (rgb or hsv)
-   Four arguments specify a color with opacity


<a id="orgc456a45"></a>

## `stroke()`

Set the color of the current stroke

Arguments:

-   A single argument specifies a grayscale value.
-   Two arguments specify grayscale with opacity.
-   Three arguments specify a color depending on the color mode (rgb or hsv)
-   Four arguments specify a color with opacity


<a id="org2096992"></a>

## `stroke_weight(...)`

Set the line width


<a id="org08add77"></a>

## `line_join(...)`

Specify the &rsquo;join&rsquo; mode for polylines.

Arguments:

-   `join` (string): can be one of &ldquo;miter&rdquo;, &ldquo;bevel&rdquo; or &ldquo;round&rdquo;


<a id="orgabae718"></a>

## `blend_mode(...)`

Specify the blending mode

Arguments:

-   `mode` (string) can be one of: &ldquo;clear&rdquo;, &ldquo;source&rdquo;, &ldquo;over&rdquo;, &ldquo;in&rdquo;, &ldquo;out&rdquo;, &ldquo;atop&rdquo;,
    &ldquo;dest&rdquo;, &ldquo;dest<sub>over</sub>&rdquo;, &ldquo;dest<sub>in</sub>&rdquo;, &ldquo;dest<sub>out</sub>&rdquo;, &ldquo;dest<sub>atop</sub>&rdquo;, &ldquo;xor&rdquo;, &ldquo;add&rdquo;, &ldquo;saturate&rdquo;, &ldquo;multiply&rdquo;, &ldquo;screen&rdquo;, &ldquo;overlay&rdquo;, &ldquo;darken&rdquo;, &ldquo;lighten&rdquo;, &ldquo;color<sub>dodge</sub>&rdquo;, &ldquo;color<sub>burn</sub>&rdquo;, &ldquo;hard<sub>light</sub>&rdquo;, &ldquo;soft<sub>light</sub>&rdquo;, &ldquo;difference&rdquo;, &ldquo;exclusion&rdquo;, &ldquo;hsl<sub>hue</sub>&rdquo;, &ldquo;hsl<sub>saturation</sub>&rdquo;, &ldquo;hsl<sub>color</sub>&rdquo;, &ldquo;hsl<sub>luminosity</sub>&rdquo;
    See <https://www.cairographics.org/operators/> for a discussion on the different operators.


<a id="orga6b531b"></a>

## `line_cap(...)`

Specify the &rsquo;cap&rsquo; for lines.

Arguments:

-   `cap` (string): can be one of &ldquo;butt&rdquo;, &ldquo;round&rdquo; or &ldquo;square&rdquo;


<a id="orgd532a0b"></a>

## `text_size(...)`

Specify the text size

Arguments:

-   `size` (int): the text size


<a id="orgadb6a33"></a>

## `text_font(...)`

Specify the font to use for text rendering
Arguments:

-   `font` (string): the name of a system font


<a id="orgbf317e8"></a>

## `push()`

Save the current drawing state and transformations


<a id="org70a9d5a"></a>

## `pop()`

Restore the previously pushed drawing state and transformations


<a id="org958fc20"></a>

## `translate()`

Translate by specifying `x` and `y` offset.

Arguments:

-   The offset can be specified as an array/list (e.g `c.translate([x,y])`
    or as single arguments (e.g. `c.translate(x, y)`)


<a id="org39cdb9d"></a>

## `scale()`

Apply a scaling transformation.

Arguments:

-   Providing a single number will apply a uniform transformation.
-   Providing a pair of number will scale in the x and y directions.
-   The scale can be specified as an array/list (e.g `c.scale([x,y])`

or as single arguments (e.g. `c.scale(x, y)`)&rsquo;&rsquo;&rsquo;


<a id="org672e8f0"></a>

## `rotate(...)`

Rotate by `theta` radians


<a id="orgb048bb3"></a>

## `apply_matrix(...)`

Apply an affine (3x3) transformation matrix


<a id="org875ed24"></a>

## `rotate_deg(...)`

Rotate using degrees


<a id="orgd79f7ab"></a>

## `rectangle()`

Draw a rectangle given top-left corner, width and heght.

Arguments:

-   `[topleft_x, topleft_y], [width, height]`,
-   `[topleft_x, topleft_y], width, height`,
-   `topleft_x, topleft_y, width, height`
-   &rsquo;[[topleft<sub>x</sub>, topleft<sub>y</sub>], [bottomright<sub>x</sub>, bottomright<sub>y</sub>]]&rsquo;


<a id="org154fb73"></a>

## `rect()`

Draw a rectangle given top-left corner, width and heght.

Input arguments can be in the following formats:

-   `[topleft_x, topleft_y], [width, height]`,
-   `[topleft_x, topleft_y], width, height`,
-   `topleft_x, topleft_y, width, height`


<a id="org383a042"></a>

## `quad()`

Draws a quadrangle given four points

Input arguments can be in the following formats:

-   `a, b, c, d` (Four points specified as lists/tuples/numpy arrays
-   `x1, y1, x2, y2, x3, y3, x4, y4`, a sequence of numbers, one for each coordinate


<a id="orgd0f7b16"></a>

## `arrow(...)`

Draw an arrow between two points `a` and `b`


<a id="org438c9bc"></a>

## `triangle()`

Draws a triangle given three points

Input arguments can be in the following formats:

-   `a, b, c` (Four points specified as lists/tuples/numpy arrays
-   `x1, y1, x2, y2, x3, y3`


<a id="org622f91a"></a>

## `circle()`

Draw a circle given center and radius

Input arguments can be in the following formats:

-   `[center_x, center_y], radius`,
-   `center_x, center_y, raidus`


<a id="org484e542"></a>

## `ellipse()`

Draw an ellipse with center, width and height.

Input arguments can be in the following formats:

-   `[center_x, center_y], [width, height]`,
-   `[center_x, center_y], width, height`,
-   `center_x, center_y, width, height`


<a id="orgf60ad2f"></a>

## `arc()`

Draw an arc given the center of the ellipse `x, y`
the size of the ellipse `w, h` and the initial and final angles
in radians  `start, stop`.

Input arguments can be in the following formats:

-`x, y, w, h, start, stop`
-`[x, y]', '[w, h]', '[start, stop]'
  -`[x, y]&rsquo;, w, h, start, stop~


<a id="org1764557"></a>

## `begin_shape()`

Begin drawing a compound shape


<a id="org4dadc05"></a>

## `end_shape(...)`

End drawing a compound shape


<a id="orgc315c00"></a>

## `begin_contour()`

Begin drawing a contour


<a id="org0b6b499"></a>

## `end_contour(...)`

End drawing a contour


<a id="orgddfeb91"></a>

## `vertex(...)`

Add a vertex to current contour

Input arguments can be in the following formats:

`[x, y]'
 ~x, y`


<a id="org276d1ae"></a>

## `curve_vertex(...)`

Add a curved vertex to current contour

Input arguments can be in the following formats:

`[x, y]'
 ~x, y`


<a id="org5b1b921"></a>

## `load_image(...)`

Load an image from disk. Actually returns a PIL image


<a id="orgb9dffc5"></a>

## `image(...)`

Draw an image at position with (optional) size and (optional) opacity

Arguments:

-   `img`: The input image. Can be either a PIL image, a numpy array or a pyCairo surface (e.g. another canvas).
-   optional arguments: position and size can be specified with the following formats:
    -   `x, y`:  position only
    -   `x, y, w, h`: position and size
    -   `[x, y]`: position only (also a numpy array or tuple are valid)
    -   `[x, y], [w, h]`: position and size

if the position is not specified, the original image dimensions will be used

-   `opacity`: a value between 0 and 1 specifying image opacity.


<a id="org018731f"></a>

## `shape(...)`

Draw a shape represented as a list of polylines, see the `polyline`
method for the format of each polyline


<a id="org71c3619"></a>

## `text(...)`

Draw text at a given position

Arguments:
    if center=True the text will be horizontally centered


<a id="org43d74b5"></a>

## `polygon()`

Draw a **closed** polygon
The polyline is specified as either:

-   a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
-   a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)


<a id="orgbbf328e"></a>

## `polyline()`

Draw a polyline.
The polyline is specified as either:

-   a list of `[x,y]` pairs (e.g. `[[0, 100], [200, 100], [200, 200]]`)
-   a numpy array with shape `(n, 2)`, representing `n` points (a point for each row and a coordinate for each column)

To close the polyline set the named closed argument to `True`, e.g. `c.polyline(points, closed=True)`.


<a id="org97fa5c4"></a>

## `background()`

Clear the canvas with a given color


<a id="orgbb08f96"></a>

## `get_image()`

Get canvas image as a numpy array


<a id="orgd656aba"></a>

## `get_image_grayscale()`

Returns the canvas image as a grayscale numpy array (in 0-1 range)


<a id="orgfa5b3d9"></a>

## `save_image(...)`

Save the canvas to an image


<a id="org4076288"></a>

## `save_svg(...)`

Save the canvas to an svg file


<a id="org218e825"></a>

## `save_pdf(...)`

Save the canvas to an svg file


<a id="orgf327d6e"></a>

## `save(...)`

Save the canvas to an image


<a id="orgfd4610d"></a>

## `show()`

Display the canvas in a notebook


<a id="org912bf87"></a>

## `show_plt(...)`

Show the canvas in a notebook with matplotlib

Arguments:
size (tuple, optional): The size of the displayed image, by default this is the size of the canvas
title (string, optional): A title for the figure
axis (bool, optional): If `True` shows the coordinate axes

