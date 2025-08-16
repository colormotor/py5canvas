#!/usr/bin/env python3

import numpy as np
from numpy import (sin, cos, tan)
from numpy.linalg import (norm, det, inv)
from scipy.interpolate import interp1d, splprep, splev
import numbers

def is_number(x):
    return isinstance(x, numbers.Number)

def is_compound(S):
    '''Returns True if S is a compound polyline,
    a polyline is represented as a list of points, or a numpy array with as many rows as points'''
    if type(S) != list:
        return False
    if type(S) == list: #[0])==list:
        if not S:
            return True
        for P in S:
            try:
                if is_number(P[0]):
                    return False
            except IndexError:
                pass
        return True
    if type(S[0])==np.ndarray and len(S[0].shape) > 1:
        return True
    return False


def is_polyline(P):
    '''A polyline can be represented as either a list of points or a NxDim array'''
    # TODO fixme
    if (type(P[0]) == np.ndarray and
        len(P[0].shape) < 2):
        return True
    if type(P) == list:
        if is_number(P[0]):
            return False
        else:
            return is_number(P[0][0])
    return False


def close_path(P):
    if type(P) == list:
        return P + [P[0]]
    return np.vstack([P, P[0]])


def close(S):
    if is_compound(S):
        return [close_path(P) for P in S]
    return close_path(S)


def is_empty(S):
    if type(S)==list and not S:
        return True
    return False


def vec(*args):
    return np.array(args)

def colvec(*args):
    return np.array(args).reshape(-1,1)

def radians(x):
    return np.pi/180*x


def degrees(x):
    return x * (180.0/np.pi)


def normalize(v):
    return v / np.linalg.norm(v)


def angle_between(*args):
    ''' Angle between two vectors (2d) [-pi,pi]'''
    if len(args)==2:
        a, b = args
    else:
        p1, p2, p3 = args
        a = p3 - p2 # TODO checkme
        b = p1 - p2
    return np.arctan2( a[0]*b[1] - a[1]*b[0], a[0]*b[0] + a[1]*b[1] )


def distance(a, b):
    return norm(b-a)


def distance_sq(a, b):
    return np.dot(b-a, b-a)


def point_line_distance(p, a, b):
    if np.array_equal(a,b):
        return distance(p, a)
    else:
        return abs(det(np.array([b-a, a-p]))) / norm(b-a)


def signed_point_line_distance(p, a, b):
    if np.array_equal(a,b):
        return distance(p, a)
    else:
        return (det(np.array([b-a, a-p]))) / norm(b-a)


def point_segment_distance(p, a, b):
    a, b = np.array(a), np.array(b)
    d = b - a
    # relative projection length
    u = np.dot( p - a, d ) / np.dot(d, d)
    u = np.clip(u, 0, 1)

    proj = a + u*d
    return np.linalg.norm(proj - p)


def perp(x):
    ''' 2d perpendicular vector'''
    return np.dot([[0,-1],[1, 0]], x)


def line_intersection_uv( a1, a2, b1, b2, aIsSegment=False, bIsSegment=False):
    ''' Returns True if the lines a1-a2 and b1-b2 intersect, intersection point and uv parameters.
        If aIsSegment or bIsSegment is True, the lines are treated as segments.
        If both are True, the intersection is only valid if both segments intersect.
        If both are False, the lines are treated as infinite lines.
    '''
    EPS = 0.00001
    intersection = np.zeros(2)
    uv = np.zeros(2)

    denom  = (b2[1]-b1[1]) * (a2[0]-a1[0]) - (b2[0]-b1[0]) * (a2[1]-a1[1])
    numera = (b2[0]-b1[0]) * (a1[1]-b1[1]) - (b2[1]-b1[1]) * (a1[0]-b1[0])
    numerb = (a2[0]-a1[0]) * (a1[1]-b1[1]) - (a2[1]-a1[1]) * (a1[0]-b1[0])

    if abs(denom) < EPS:
        return False, intersection, uv

    uv[0] = numera / denom
    uv[1] = numerb / denom

    intersection[0] = a1[0] + uv[0] * (a2[0] - a1[0])
    intersection[1] = a1[1] + uv[0] * (a2[1] - a1[1])

    isa = True
    if aIsSegment and (uv[0]  < 0 or uv[0]  > 1):
        isa = False
    isb = True
    if bIsSegment and (uv[1] < 0 or uv[1]  > 1):
        isb = False

    res = isa and isb
    return res, intersection, uv


def line_intersection( a1, a2, b1, b2, aIsSegment=False, bIsSegment=False ):
    ''' Returns True if the lines a1-a2 and b1-b2 intersect, intersection point.
        If aIsSegment or bIsSegment is True, the lines are treated as segments.
        If both are True, the intersection is only valid if both segments intersect.
        If both are False, the lines are treated as infinite lines.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,False)
    return res, intersection


def line_segment_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the line a1-a2 and the segment b1-b2 intersect, intersection point.
        The line is treated as infinite, the segment is treated as a segment.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,True)
    return res, intersection


def segment_line_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the segment a1-a2 and the line b1-b2 intersect, intersection point.
        The segment is treated as a segment, the line is treated as infinite.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,True,False)
    return res, intersection


def segment_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the segments a1-a2 and b1-b2 intersect, intersection point.
        Both segments are treated as segments.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,True,True)
    return res, intersection


def line_ray_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the line a1-a2 and the ray b1-b2 intersect, intersection point.
        The line is treated as infinite, the ray is treated as a ray starting at b1 and going in the direction of b2.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,False)
    return res and uv[1] > 0, intersection


def ray_line_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the ray a1-a2 and the line b1-b2 intersect, intersection point.
        The ray is treated as starting at a1 and going in the direction of a2, the line is treated as infinite.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,False)
    return res and uv[0] > 0, intersection


def ray_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the rays a1-a2 and b1-b2 intersect, intersection point.
        Both rays are treated as starting at their respective points and going in the direction of the second point.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,False)
    return res and uv[0] > 0 and uv[1] > 0, intersection


def ray_segment_intersection( a1, a2, b1, b2 ):
    ''' Returns True if the ray a1-a2 and the segment b1-b2 intersect, intersection point.
        The ray is treated as starting at a1 and going in the direction of a2, the segment is treated as a segment.
    '''
    res, intersection, uv = line_intersection_uv(a1,a2,b1,b2,False,True)
    return res and uv[0] > 0 and uv[1] > 0, intersection

# Rect utilities
def bounding_box(S, padding=0):
    ''' Axis ligned bounding box of one or more contours (any dimension)
        Returns [min,max] list'''
    if not is_compound(S):
        S = [S]
    if not S:
        return np.array([0, 0]), np.array([0, 0])

    bmin = np.min([np.min(V, axis=0) for V in S if len(V)], axis=0)
    bmax = np.max([np.max(V, axis=0) for V in S if len(V)], axis=0)
    return [bmin - padding, bmax + padding]

def rect_w(rect):
    return (np.array(rect[1]) - np.array(rect[0]))[0]

def rect_h(rect):
    return (np.array(rect[1]) - np.array(rect[0]))[1]

def rect_size(rect):
    return np.array(rect[1]) - np.array(rect[0])

def rect_aspect(rect):
    return rect_w(rect) / rect_h(rect)

def pad_rect(rect, pad):
    return np.array(rect[0])+pad, np.array(rect[1])-pad

def make_rect(x, y, w, h):
    return [np.array([x, y]), np.array([x+w, y+h])]

def make_centered_rect(p, size):
    return make_rect(p[0] - size[0]*0.5, p[1] - size[1]*0.5, size[0], size[1])

def rect_center(rect):
    return rect[0] + (rect[1]-rect[0])/2

def rect_corners(rect, close=False):
    w, h = rect_size(rect)
    rect = (np.array(rect[0]), np.array(rect[1]))
    P = [rect[0], rect[0] + [w, 0],
            rect[1], rect[0] + [0, h]]
    if close:
        P.append(P[0])
    return P

def rect_l(rect):
    return rect[0][0]

def rect_r(rect):
    return rect[1][0]

def rect_t(rect):
    return rect[0][1]

def rect_b(rect):
    return rect[1][1]

def random_point_in_rect(box):
    x = np.random.uniform( box[0][0], box[1][0] )
    y = np.random.uniform( box[0][1], box[1][1] )
    return np.array([x, y])

def scale_rect(rect, s, halign=0, valign=0):
    if is_number(s):
        s = [s, s]
    sx, sy = s
    r = [np.array(rect[0]), np.array(rect[1])]
    origin = rect_center(rect)
    if (halign == -1):
        origin[0] = rect_l(rect)
    if (halign == 1):
        origin[0] = rect_r(rect)
    if (valign == -1):
        origin[1] = rect_t(rect)
    if (valign == 1):
        origin[1] = rect_b(rect)
    A = trans_2d(origin)@scaling_2d([sx, sy])@trans_2d(-origin)

    return [affine_transform(A, r[0]), affine_transform(A, r[1])]


def rect_in_rect(src, dst, padding=0., axis=None):
    ''' Fit src rect into dst rect, preserving aspect ratio of src, with optional padding'''
    dst = pad_rect(dst, padding)

    dst_w, dst_h = dst[1] - dst[0]
    src_w, src_h = src[1] - src[0]

    ratiow = dst_w/src_w
    ratioh = dst_h/src_h
    if axis==None:
        if ratiow <= ratioh:
            axis = 1
        else:
            axis = 0
    if axis==1: # fit vertically [==]
        w = dst_w
        h = src_h*ratiow
        x = dst[0][0]
        y = dst[0][1] + dst_h*0.5 - h*0.5
    else: # fit horizontally [ || ]
        w = src_w*ratioh
        h = dst_h

        y = dst[0][1]
        x = dst[0][0] + dst_w*0.5 - w*0.5

    return make_rect(x, y, w, h)

def rect_to_rect_transform(src, dst):
    ''' Fit src rect into dst rect, without preserving aspect ratio'''
    m = np.eye(3,3)

    sw, sh = rect_size(src)
    dw, dh = rect_size(dst)

    m = trans_2d([dst[0][0],dst[0][1]])
    m = np.dot(m, scaling_2d([dw/sw,dh/sh]))
    m = np.dot(m, trans_2d([-src[0][0],-src[0][1]]))

    return m


def rect_in_rect_transform(src, dst, padding=0., axis=None):
    ''' Return homogeneous transformation matrix that fits src rect into dst'''
    fitted = rect_in_rect(src, dst, padding, axis)

    cenp_src = rect_center(src)
    cenp_dst = rect_center(fitted)

    M = np.eye(3)
    M = np.dot(M,
               trans_2d(cenp_dst - cenp_src))
    M = np.dot(M, trans_2d(cenp_src))
    M = np.dot(M, scaling_2d(rect_size(fitted)/rect_size(src)))
    M = np.dot(M, trans_2d(-cenp_src))
    return M


def transform_to_rect(shape, rect, padding=0., offset=[0,0], axis=None):
    ''' transform a shape or polyline to dest rect'''
    src_rect = bounding_box(shape)
    return affine_transform(trans_2d(offset)@rect_in_rect_transform(src_rect, rect, padding, axis), shape)



# 2d transformations (affine)
def det22(mat):
    return mat[0,0] * mat[1,1] - mat[0,1]*mat[1,0]

def rotate_vector_2d(v, ang):
    ''' 2d rotation matrix'''
    ca = np.cos(ang)
    sa = np.sin(ang)
    x, y = v
    return np.array([x*ca - y*sa,
                     x*sa + y*ca])

def rot_2d( theta, affine=True ):
    d = 3 if affine else 2
    m = np.eye(d)
    ct = np.cos(theta)
    st = np.sin(theta)
    m[0,0] = ct; m[0,1] = -st
    m[1,0] = st; m[1,1] = ct

    return m

def trans_2d( xy):
    m = np.eye(3)
    m[0,2] = xy[0]
    m[1,2] = xy[1]
    return m

def scaling_2d( xy, affine=True ):
    d = 3 if affine else 2

    if is_number(xy):
        xy = [xy, xy]

    m = np.eye(d)
    m[0,0] = xy[0]
    m[1,1] = xy[1]
    return m

def shear_2d(xy, affine=True):
    d = 3 if affine else 2
    m = np.eye(d)
    #return m
    m[0,1] = xy[0]
    m[1,0] = xy[1]
    return m

# 3d transformations (affine)
def rotx_3d (theta, affine=True):
    d = 4 if affine else 3
    m = np.eye(d)
    ct = cos(theta)
    st = sin(theta)
    m[1,1] = ct; m[1,2] = -st
    m[2,1] = st; m[2,2] = ct

    return m

def roty_3d (theta, affine=True):
    d = 4 if affine else 3
    m = np.eye(d)
    ct = cos(theta)
    st = sin(theta)
    m[0,0] = ct; m[0,2] = st
    m[2,0] = -st; m[2,2] = ct

    return m

def rotz_3d (theta, affine=True):
    d = 4 if affine else 3
    m = np.eye(d)
    ct = cos(theta)
    st = sin(theta)
    m[0,0] = ct; m[0,1] = -st
    m[1,0] = st; m[1,1] = ct

    return m

def trans_3d(xyz):
    m = np.eye(4)
    m[0,3] = xyz[0]
    m[1,3] = xyz[1]
    m[2,3] = xyz[2]
    return m

def scaling_3d(s, affine=True):
    d = 4 if affine else 3
    if not isinstance(s, (list, tuple, np.ndarray)):
        s = [s, s, s]

    m = np.eye(d)
    m[0,0] = s[0]
    m[1,1] = s[1]
    m[2,2] = s[2]
    return m

def _affine_transform_polyline(mat, P):
    dim = P[0].size
    P = np.vstack([np.array(P).T, np.ones(len(P))])
    P = mat@P
    return list(P[:dim,:].T)

def affine_transform(mat, data):
    if is_empty(data):
        # print('Empty data to affine_transform!')
        return data
    if is_polyline(data):
        P = np.array(data)
        dim = P[0].size
        P = np.vstack([np.array(P).T, np.ones(len(P))])
        P = mat@P
        return P[:dim,:].T
    elif is_compound(data):
        return [affine_transform(mat, P) for P in data]
    else: # assume a point
        dim = len(data)
        p = np.concatenate([data, [1]])
        return (mat@p)[:dim]

def affine_mul(mat, data):
    print('Use affine_transform instead')
    return affine_transform(mat, data) # For backwards compat

tsm = affine_transform


def projection(mat, data):
    if is_empty(data):
        return data
    if is_polyline(data):
        P = np.array(data)
        dim = P[0].size
        P = np.vstack([P.T, np.ones(len(P))])
        P = mat @ P
        P /= P[-1]
        return P[:dim].T
    elif is_compound(data):
        return [projection(mat, P) for P in data]
    else:
        dim = len(data)
        p = np.concatenate([data, [1]])
        p = mat @ p
        p /= p[-1]
        return p[:dim]


# Generates shapes (as polylines, 2d and 3d)
class shapes:
    def __init__(self):
        pass

    @staticmethod
    def box_3d(min, max):
        S = []
        # plotter-friendy version
        S.append(shapes.polygon(vec(min[0], min[1], min[2]),
                                vec(max[0], min[1], min[2]),
                                vec(max[0], max[1], min[2]),
                                vec(min[0], max[1], min[2])))
        S.append(shapes.polygon(vec(min[0], min[1], max[2]),
                                vec(max[0], min[1], max[2]),
                                vec(max[0], max[1], max[2]),
                                vec(min[0], max[1], max[2])))
        for i in range(4):
            S.append(np.array([S[0][i], S[1][i]]))
        # line segments only
        # S.append([vec(min[0], min[1], min[2]),  vec(max[0], min[1], min[2])])
        # S.append([vec(max[0], min[1], min[2]),  vec(max[0], max[1], min[2])])
        # S.append([vec(max[0], max[1], min[2]),  vec(min[0], max[1], min[2])])
        # S.append([vec(min[0], max[1], min[2]),  vec(min[0], min[1], min[2])])
        # S.append([vec(min[0], min[1], max[2]),  vec(max[0], min[1], max[2])])
        # S.append([vec(max[0], min[1], max[2]),  vec(max[0], max[1], max[2])])
        # S.append([vec(max[0], max[1], max[2]),  vec(min[0], max[1], max[2])])
        # S.append([vec(min[0], max[1], max[2]),  vec(min[0], min[1], max[2])])
        # S.append([vec(min[0], min[1], min[2]),  vec(min[0], min[1], max[2])])
        # S.append([vec(min[0], max[1], min[2]),  vec(min[0], max[1], max[2])])
        # S.append([vec(max[0], max[1], min[2]),  vec(max[0], max[1], max[2])])
        # S.append([vec(max[0], min[1], min[2]),  vec(max[0], min[1], max[2])])
        return S

    @staticmethod
    def cuboid(center=vec(0,0,0), halfsize=vec(1,1,1)):
        if is_number(halfsize):
            size = [halfsize, halfsize, halfsize]
        return shapes.box_3d(np.array(center) - np.array(halfsize),
                         np.array(center) + np.array(halfsize))


    @staticmethod
    def polygon(*args):
        ''' A closed polygon (joins last point to first)'''
        P = [np.array(p) for p in args]
        P.append(np.array(args[0]))
        return np.array(P)

    @staticmethod
    def regular_polygon(center, r, n):
        ang = ((n-2)*180)/(n*2)
        P = tsm(rot_2d(radians(ang)), shapes.circle([0,0], r, subd=n, close=False))+center
        return P

    @staticmethod
    def circle(center, r, subd=80, unit=1, close=True):
        if subd is None:
            subd = max(3, int(r*2*np.pi*(1/unit)))

        res = np.array([vec(np.cos(th), np.sin(th))*r + center
                                    for th in np.linspace(0, np.pi*2, subd+1)[:-1]])
        if close:
            res = close_path(res)
        return res

    @staticmethod
    def star(radius, ratio_inner=1.0, n=5, center=[0,0]):
        n = int(max(n, 3))
        th = np.linspace(0, np.pi*2, n*2+1)[:-1] - np.pi / (n*2)
        R = [radius, radius/(1.618033988749895+1)*ratio_inner]
        P = []
        for i, t in enumerate(th): #[::-1]):
            r = R[i%2]
            P.append(direction(t)*r + center)
        P = np.array(P)
        return P

    @staticmethod
    def random_radial_polygon(n, min_r=0.5, max_r=1., center=[0,0]):
        R = np.random.uniform(min_r, max_r, n)
        start = np.random.uniform(0., np.pi*2)
        Theta = randspace(start, start+np.pi*2, n+1)
        Theta = Theta[:-1] # skip last one
        V = np.zeros((n,2))
        V[:,0] = np.cos(Theta) * R + center[0]
        V[:,1] = np.sin(Theta) * R + center[1]
        return V

    @staticmethod
    def rectangle(*args):
        if len(args) == 2:
            rect = [*args]
        elif len(args) == 1:
            rect = args[0]
        elif len(args) == 4:
            rect = make_rect(*args)
        P = np.array(rect_corners(rect))
        return P


def randspace(a, b, n, minstep=0.1, maxstep=0.6):
    ''' Generate a sequence from a to b with random steps
        minstep and maxstep define the step magnitude
        '''
    v = minstep + np.random.uniform(size=(n-1))*(maxstep-minstep)
    v = np.hstack([[0.0], v])
    v = v / np.sum(v)
    v = np.cumsum(v)
    return a + v*(b-a)


def dp_simplify(P, eps, closed=False):
    ''' Douglas-Peucker simplification of a polyline (using OpenCV's implementation)'''
    import cv2
    P = np.array(P)
    dtype = P.dtype
    return cv2.approxPolyDP(P.astype(np.float32), eps, closed).astype(dtype)[:,0,:]


def uniform_sample( X, delta_s, closed=0, kind='slinear', data=None, inv_density=None, density_weight=0.5 ):
    ''' Uniformly samples a contour at a step dist'''
    if closed:
        X = np.vstack([X, X[0]])
        if data is not None:
            data = np.vstack([data, data[0]])

    D = np.diff(X[:,:2], axis=0)
    # chord lengths
    s = np.sqrt(D[:,0]**2 + D[:,1]**2)
    # Delete values in input with zero distance (due to a bug in interp1d)
    I = np.where(s==0)
    X = np.delete(X, I, axis=0)
    s = np.delete(s, I)
    # if inv_density is not None:
    #     inv_density = np.delete(inv_density, I)

    if data is not None:
        if type(data)==list or data.ndim==1:
            data = np.delete(data, I)
        else:
            data = np.delete(data, I, axis=0)

    #maxs = np.max(s)
    #s = s/maxs
    #delta_s = delta_s/maxs #np.max(s)

    # if inv_density is not None:
    #     inv_density = inv_density[:-1]
    #     inv_density = inv_density - np.min(inv_density)
    #     inv_density /= np.max(inv_density)
    #     density = density #1.0 - inv_density
    #     s = (1.0 - density_weight)*s + density_weight*density
    u = np.cumsum(np.concatenate([[0.], s]))
    u = u / u[-1]
    n = int(np.ceil(np.sum(s) / delta_s))
    t = np.linspace(u[0], u[-1], n)

    # if inv_density is not None:
    #     inv_density = inv_density - np.min(inv_density)
    #     inv_density /= np.max(inv_density)
    #     inv_density = np.clip(inv_density, 0.75, 1.0)
    #     param = np.cumsum(1-inv_density)
    #     param = param - np.min(param)
    #     param = param / np.max(param)

    #     u = u*param #(1.0 - density_weight) + param*density_weight
    #     u = u/u[-1]

    f = interp1d(u, X.T, kind=kind)
    Y = f(t)

    if data is not None:
        f = interp1d(u, data.T, kind=kind)
        data = f(t)
        if closed:
            if data.ndim>1:
                return Y.T[:-1,:], data.T[:-1,:]
            else:
                return Y.T[:-1,:], data.T[:-1]
        else:
            return Y.T, data.T
    if closed:
        return Y[:,:-1].T
    return Y.T


def smoothing_spline(n, pts, der=0, ds=0., dim=None, closed=False, w=None, smooth_k=0, degree=3, alpha=1.):
    ''' Computes a smoothing B-spline for a sequence of points.
    Input:
    n, number of interpolating points
    pts, sequence of points (dim X m)
    der, derivative order
    ds, if non-zero an approximate arc length parameterisation is used with distance ds between points,
    and the parameter n is ignored.
    closed, if True spline is periodic
    w, optional weights
    smooth_k, smoothing parameter,
    degree, spline degree,
    alpha, parameterisation (1, uniform, 0.5 centripetal)
    '''

    if closed:
        pts = np.vstack([pts, pts[0]])

    if w is None:
        w = np.ones(pts.shape[0])
    elif is_number(w):
        w = np.ones(pts.shape[0])*w

    if dim is None:
        dim = pts.shape[1]
    # D = np.diff(pts, axis=0)
    # # chord lengths
    # s = np.sqrt(np.sum([D[:,i]**2 for i in range(dim)], axis=0))
    # # I = np.where(s==0)
    # # pts = np.delete(pts, I, axis=0)
    # # s = np.delete(s, I)
    # # w = np.delete(w, I)

    # _, I = simplify.cleanup_contour(pts, closed=False, get_indices=True)
    # pts = pts[I]
    # #s = [s[i] for i in I]
    # w = [w[i] for i in I]


    degree = min(degree, pts.shape[0]-1)

    if pts.shape[0] < 2:
        print('Insufficient points for smoothing spline, returning original')
        return pts

    if ds != 0:
        D = np.diff(pts, axis=0)
        s = np.sqrt(np.sum([D[:,i]**2 for i in range(dim)], axis=0))+1e-5
        l = np.sum(s)
        s = s**(alpha)
        u = np.cumsum(np.concatenate([[0.], s]))
        u = u / u[-1]

        spl, u = splprep(pts.T, w=w, u=u, k=degree, per=closed, s=smooth_k)
        n = max(2, int(l / ds))
        t = np.linspace(u[0], u[-1], n)
    else:
        u = np.linspace(0, 1, pts.shape[0])
        spl, u = splprep(pts.T, u=u, w=w, k=degree, per=closed, s=smooth_k)
        t = np.linspace(0, 1, n)

    if type(der)==list:
        res = []
        for d in der:
            res.append(np.vstack(splev(t, spl, der=d)).T)
        return res
    res = splev(t, spl, der=der)
    return np.vstack(res).T


def chord_lengths( P, closed=0 ):
    ''' Chord lengths for each segment of a contour '''
    if closed:
        P = np.vstack([P, P[0]])
    D = np.diff(P, axis=0)
    L = np.sqrt( D[:,0]**2 + D[:,1]**2 )
    return L


def cum_chord_lengths( P, closed=0 ):
    ''' Cumulative chord lengths '''
    if len(P.shape)!=2:
        return []
    if P.shape[0] == 1:
        return np.zeros(1)
    L = chord_lengths(P, closed)
    return np.cumsum(np.concatenate([[0.0],L]))


def chord_length( P, closed=0 ):
    ''' Chord length of a contour '''
    if len(P.shape)!=2 or P.shape[0] < 2:
        return 0.
    L = chord_lengths(P, closed)
    return np.sum(L)


def polygon_area(P):
    '''(signed) area of a polygon'''
    if len(P.shape) < 2 or P.shape[0] < 3:
        return 0
    n = P.shape[0]
    area = 0.0
    P = P - np.mean(P, axis=0)
    for i in range(n):
        j = (i+1)%n
        area += 0.5 * (P[i,1]+P[j,1]) * (P[i,0]-P[j,0]) # trapezoid https://en.wikipedia.org/wiki/Shoelace_formula
        # The triangle version will run into numerical percision errors
        # if we have a small or thin polygon that is quite off center,
        # this can be solved by centering the polygon before comp. Maybe useful to do anyhow?
        #area += 0.5*(P[i,0] * P[j,1] - P[j,0] * P[i,1])

    return area

# O'Rourke's methods for robust geometric computations
def triangle_area( a, b, c ):
    da = a-b
    db = c-b
    return det(np.vstack([da, db]))*0.5

def collinear(a, b, p, eps=1e-5):
    return abs(triangle_area(a, b, p)) < eps

def segments_collinear(a, b, c, d, eps=1e-5):
    return collinear(a, b, c, eps) and collinear(a, b, d, eps)

def left_of(p, a, b, eps=1e-10):
    # Assumes coordinate system with y up so actually will be "right of" if visualizd y down
    p, a, b = [np.array(v) for v in [p, a, b]]
    return triangle_area(a, b, p) < eps

def is_point_in_triangle(p, tri, eps=1e-10):
    L = [left_of(p, tri[i], tri[(i+1)%3], eps) for i in range(3)]
    return L[0]==L[1] and L[1]==L[2]

def is_point_in_rect(p, rect):
    ''' return wether a point is in a rect'''
    l, t = rect[0]
    r, b = rect[1]
    w, h = rect[1] - rect[0]

    return ( p[0] >= l and p[1] >= t and
             p[0] <= r and p[1] <= b )

def is_point_in_poly(p, P):
    ''' Return true if point in polygon'''
    c = False
    n = P.shape[0]
    j = n-1
    for i in range(n):
        if ( ((P[i,1]>p[1]) != (P[j,1]>p[1])) and
             (p[0] < (P[j,0] - P[i,0])*(p[1] - P[i,1]) / (P[j,1] - P[i,1]) + P[i,0]) ):
                 c = not c
        j = i
    return c

def is_point_in_shape(p, S, get_flags=False):
    ''' Even odd point in shape test'''
    if p is None:
        return False
    c = 0
    flags = []
    for P in S:
        if len(P) < 3:
            flags.append(False)
        elif is_point_in_poly(p, P):
            flags.append(True)
            c = c+1
        else:
            flags.append(False)

    res = (c%2) == 1
    if get_flags:
        return res, flags
    return res
