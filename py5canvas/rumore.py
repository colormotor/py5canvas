#!/usr/bin/env python3
import numpy as np
import numbers

cfg = lambda: None
cfg.seed = 0xF00D
cfg.shift = 131.2322
cfg.lacunarity = 2.0
cfg.falloff = 0.5

state = lambda: None
state.sphere = None
state.circle = None
state.fractal_bounding = {}

def is_number(x):
    return isinstance(x, numbers.Number)

def splitmix64_mix(x):
    x = np.array(x)
    x ^= x >> 30
    x *= 0xBF58476D1CE4E5B9
    x ^= x >> 27
    x *= 0x94D049BB133111EB
    x ^= x >> 31
    return x.astype(np.uint64)

def splittable64(x, key=0):
    # Split64
    # Adapted from https://nullprogram.com/blog/2018/07/31/
    x = x ^ np.uint64(key)
    x ^= x >> np.uint64(30)
    x *= np.uint64(0xBF58476D1CE4E5B9)
    x ^= x >> np.uint64(27)
    x *= np.uint64(0x94D049BB133111EB)
    x ^= x >> np.uint64(31)
    return x

# Murmur hashing adapted from https://www.shadertoy.com/view/ttc3zr
M = np.uint64(0x5bd1e995)
H = np.uint64(1190494759)

def murmur11(x):
    x = x * M;
    x ^= x>>24; x *= M;
    h = H * M
    h ^= x;
    h ^= h>>13; h *= M; h ^= h>>15;
    return h

def fract(x):
    return x - np.floor(x) #np.modf(x)[1]

def uint64(x):
    x = np.asarray(np.floor(x)).astype(np.int64)
    x = x.view(np.uint64)
    return x

def to01(x):
    return (x >> np.uint64(11)).astype(np.float64) * (1.0 / (1 << 53))

# 2d and 3d hashes from Jarzynski and Olano (2019)
# https://www.jcgt.org/published/0009/03/02/
VA = np.uint64(1664525)
VB = np.uint64(1013904223)
s16 = np.uint64(16)

def pcg2d(v):
    v = v * VA + VB
    v[0] += v[1] * VA #1664525
    v[1] += v[0] * VA #1664525
    v = v ^ (v>>16)
    v[0] += v[1] * VA #1664525
    v[1] += v[0] * VA #1664525
    v = v ^ (v>>16)
    return v

def pcg3d(v):
    v = _u64(v)
    v = v * VA + VB
    v[0] += v[1]*v[2]
    v[1] += v[2]*v[0]
    v[2] += v[0]*v[1]
    v ^= v >> s16
    v[0] += v[1]*v[2]; v[1] += v[2]*v[0]; v[2] += v[0]*v[1];
    return v


hashf = murmur11 #
#hashf = splittable64
#hashf = splitmix64_mix # splitmix64_mix #fmix64
#hashf = fmix64 # Slow
#hashf = wyhash64
#hashf = elias

C1 = 0 #np.uint64(0x9E3779B97F4A7C15)
C2 = 0 #np.uint64(0xC2B2AE3D27D4EB4F)
C3 = 0 #np.uint64(0x165667B19E3779F9)

def _u64(a):
    return np.asarray(a, dtype=np.uint64)

# 1D combine (hash of x only)
def hash11(hx):
    hx = uint64(hx)
    C1 = np.uint64(0x9E3779B97F4A7C15)  # golden-ratio increment
    h  = np.uint64(cfg.seed)
    h  = hashf(h ^ (_u64(hx) + C1))
    return to01(h)*2 - 1

# 2D combine
def hash21(hx, hy):
    hx, hy = [uint64(v) for v in [hx, hy]]
    h  = np.uint64(cfg.seed)
    h  = hashf(h ^ (_u64(hx) + C1))
    h  = hashf(h ^ (_u64(hy) + C2))
    return to01(h)*2 - 1

# 3D combine
def hash31(hx, hy, hz):
    hx, hy, hz = [uint64(v) for v in [hx, hy, hz]]
    h  = np.uint64(cfg.seed)
    h  = hashf(h ^ (_u64(hx) + C1))
    h  = hashf(h ^ (_u64(hy) + C2))
    h  = hashf(h ^ (_u64(hz) + C3))
    return to01(h)*2 - 1

def hash31i(hx, hy, hz):
    hx, hy, hz = [uint64(v) for v in [hx, hy, hz]]
    h  = np.uint64(cfg.seed)
    h  = hashf(h ^ (_u64(hx) + C1))
    h  = hashf(h ^ (_u64(hy) + C2))
    h  = hashf(h ^ (_u64(hz) + C3))
    return h

def hash33(hx, hy, hz):
    hx, hy, hz = [uint64(v + cfg.seed) for v in [hx, hy, hz]]
    return to01(pcg3d(np.stack([hx, hy, hz])))*2 - 1

def hash22(hx, hy):
    hx, hy = [uint64(v + cfg.seed) for v in [hx, hy]]
    return to01(np.stack([hx, hy]))*2 - 1

def mix(a, b, t):
    return a + (b - a)*t

def fade(t):
    return t*t*(3.0-2.0*t)
    # return t * t * t * (t * (t * 6 - 15) + 10);

def stack(v):
    return np.stack(v, axis=0)

def value_noise1(x):
    i = np.floor(x)
    f = fract(x)
    u = fade(f)
    return mix(hash11(i), hash11(i + 1), u)

def value_noise2(x, y):
    v = stack([x, y])
    i = np.floor(v)
    f = fract(v)

    a = hash21(i[0], i[1])
    b = hash21(i[0] + 1.0, i[1] + 0.0)
    c = hash21(i[0] + 0.0, i[1] + 1.0)
    d = hash21(i[0] + 1.0, i[1] + 1.0)

    # Same code, with the clamps in smoothstep and common subexpressions
    # optimized away.
    u = fade(f)
    return mix(a, b, u[0]) + (c - a) * u[1] * (1.0 - u[0]) + (d - b) * u[0] * u[1]

def value_noise3(x, y, z):
    v = stack([x, y, z])
    i = np.floor(v)
    ff = fract(v)
    u = fade(ff)

    a = hash31(v[0] + 0.0, v[1] + 0.0, v[2] + 0.0)
    b = hash31(v[0] + 1.0, v[1] + 0.0, v[2] + 0.0)
    c = hash31(v[0] + 0.0, v[1] + 1.0, v[2] + 0.0)
    d = hash31(v[0] + 1.0, v[1] + 1.0, v[2] + 0.0)
    e = hash31(v[0] + 0.0, v[1] + 0.0, v[2] + 1.0)
    f = hash31(v[0] + 1.0, v[1] + 0.0, v[2] + 1.0)
    g = hash31(v[0] + 0.0, v[1] + 1.0, v[2] + 1.0)
    h = hash31(v[0] + 1.0, v[1] + 1.0, v[2] + 1.0)

    return mix(mix(mix(a, b, u[0]),
                   mix(c, d, u[0]), u[1]),
               mix(mix(e, f, u[0]),
                   mix(g, h, u[0]), u[1]), u[2])

def grad_noise1(x):
    i = np.floor(x)
    f = fract(x)
    u = fade(f)
    g0 = hash11(i)
    g1 = hash11(i + 1)
    # From https://www.shadertoy.com/view/3sd3Rs
    return 2*mix( g0*(f-0.0), g1*(f-1.0), u)
    #return mix(hash11(i), hash11(i + 1), u)

def grad21(x, y):
    theta = hash21(x, y)*np.pi
    return np.cos(theta), np.sin(theta)

def dotgrad21(x, y, ox, oy, f):
    gx, gy = grad21(x + ox, y + oy)
    return gx*(f[0]-ox) + gy*(f[1]-oy)

def grad_noise2(x, y):
    v = stack([x, y])
    i = np.floor(v)
    f = fract(v)
    u = fade(f)
    a = dotgrad21(i[0], i[1], 0.0, 0.0, f)
    b = dotgrad21(i[0], i[1], 1.0, 0.0, f)
    c = dotgrad21(i[0], i[1], 0.0, 1.0, f)
    d = dotgrad21(i[0], i[1], 1.0, 1.0, f)

    scale = 1.4142135623730950488 #1.0/sqrt(0.5)
    return mix(mix(a, b, u[0]),
               mix(c, d, u[0]), u[1])*scale

def fibonacci_sphere(samples=100):
    points = []
    phi = np.pi * (np.sqrt(5.) - 1.)  # golden angle in radians
    for i in range(samples):
        y = 1 - (i / float(samples - 1)) * 2  # y goes from 1 to -1
        radius = np.sqrt(1 - y * y)  # radius at y

        theta = phi * i  # golden angle increment

        x = np.cos(theta) * radius
        z = np.sin(theta) * radius

        points.append((x, y, z))
    return np.array(points)

def grad3(x, y, z):
    if state.sphere is None:
        state.sphere = fibonacci_sphere(256)
        np.random.shuffle(state.sphere)
        state.sphere = state.sphere.T
    # res = hash33(x, y, z)
    # print(res.shape)
    # return res

    i = hash31i(x, y, z)&255
    return state.sphere[:, i]

    # theta, phi, _ = hash33(x, y, z)*np.pi
    # costh = np.cos(theta)
    # sinphi = np.sin(phi)
    # sinth = np.sin(theta)
    # return costh*sinphi, sinth*sinphi, costh

    # https://mathworld.wolfram.com/SpherePointPicking.html
    # Probably slow can do better
    # u, v, _ = hash33(x, y, z)*0.5 + 0.5
    # #v = hash31(x, y, z)*0.5 + 0.5
    # theta = 2*np.pi*u
    # phi = np.arccos(2*v - 1)
    # costh = np.cos(theta)
    # sinphi = np.sin(phi)
    # sinth = np.sin(theta)
    # return costh*sinphi, sinth*sinphi, costh


def dotgrad31(x, y, z, ox, oy, oz, f):
    gx, gy, gz = grad3(x + ox, y + oy, z + oz)
    return gx*(f[0]-ox) + gy*(f[1]-oy) + gz*(f[2]-oz)

def grad_noise3(x, y, z):
    v = stack([x, y, z])
    i = np.floor(v)
    ff = fract(v)
    u = fade(ff)

    a = dotgrad31(i[0], i[1], i[2], 0.0, 0.0, 0.0, ff)
    b = dotgrad31(i[0], i[1], i[2], 1.0, 0.0, 0.0, ff)
    c = dotgrad31(i[0], i[1], i[2], 0.0, 1.0, 0.0, ff)
    d = dotgrad31(i[0], i[1], i[2], 1.0, 1.0, 0.0, ff)
    e = dotgrad31(i[0], i[1], i[2], 0.0, 0.0, 1.0, ff)
    f = dotgrad31(i[0], i[1], i[2], 1.0, 0.0, 1.0, ff)
    g = dotgrad31(i[0], i[1], i[2], 0.0, 1.0, 1.0, ff)
    h = dotgrad31(i[0], i[1], i[2], 1.0, 1.0, 1.0, ff)

    scale = 1.15470053837925152901829 # 1.0/sqrt(0.75)
    return mix(mix(mix(a, b, u[0]),
                   mix(c, d, u[0]), u[1]),
               mix(mix(e, f, u[0]),
                   mix(g, h, u[0]), u[1]), u[2])*scale

def calc_fractal_bounding(octaves):
    '''Helper to scale the sum of octaves'''
    if octaves in state.fractal_bounding:
        return state.fractal_bounding[(octaves, cfg.falloff)]
    falloff = cfg.falloff
    amp = falloff;
    amp_fractal = 1.0
    for i in range(octaves):
        amp_fractal += amp
        amp *= falloff
    fractal_bounding = 1 / amp_fractal
    state.fractal_bounding[(octaves, cfg.falloff)] = fractal_bounding
    return fractal_bounding

def make_fbm(func):
    def fbm(*args, octaves=8):
        v = 0.0
        a = calc_fractal_bounding(octaves)
        shift = cfg.shift
        x = np.stack(args, axis=0)
        for i in range(octaves):
            v += a * func(*x)
            x = x * 2.0 + shift
            a *= cfg.falloff
        return v
    return fbm

value_fbm1 = make_fbm(value_noise1)
value_fbm2 = make_fbm(value_noise2)
value_fbm3 = make_fbm(value_noise3)
grad_fbm1 = make_fbm(grad_noise1)
grad_fbm2 = make_fbm(grad_noise2)
grad_fbm3 = make_fbm(grad_noise3)

def value_fbm_grid(x, y, octaves=8):
    ''' Generate fractal value noise over a 2d grid defined by two 1d numpy arrays x, y'''
    v = 0.0
    a = calc_fractal_bounding(octaves)
    shift = cfg.shift
    xx, yy = np.meshgrid(x, y)
    for i in range(octaves):
        v += a * value_noise2(xx, yy)
        xx = xx * cfg.lacunarity + shift
        yy = yy * 2.0 + shift
        a *= cfg.falloff
    return v

def grad_fbm_grid(x, y, octaves=8):
    ''' Generate fractal gradient noise over a 2d grid defined by two 1d numpy arrays x, y'''
    v = 0.0
    a = calc_fractal_bounding(octaves)
    xx, yy = np.meshgrid(x, y)
    for i in range(octaves):
        v += a * grad_noise2(xx, yy)
        xx = xx * cfg.lacunarity + cfg.shift
        yy = yy * cfg.lacunarity + cfg.shift
        a *= cfg.falloff
    return v

def value_fbm_grid3(x, y, z, octaves=8):
    ''' Generate fractal value noise over a 2d grid as a slice of a 3d volume defined by two 1d numpy arrays x, y and a scalar z'''
    v = 0.0
    a = calc_fractal_bounding(octaves)
    if is_number(z):
        xx, yy = np.meshgrid(x, y)
        zz = np.ones_like(xx)*z
    else:
        xx, yy, zz = np.meshgrid(x, y, z)

    for i in range(octaves):
        v += a * value_noise3(xx, yy, zz)
        xx = xx * cfg.lacunarity + cfg.shift
        yy = yy * cfg.lacunarity + cfg.shift
        a *= cfg.falloff
    return v

def grad_fbm_grid3(x, y, z, octaves=8):
    ''' Generate fractal gradient noise over a 2d grid defined by two 1d numpy arrays x, y'''
    v = 0.0
    a = calc_fractal_bounding(octaves)
    if is_number(z):
        xx, yy = np.meshgrid(x, y)
        zz = np.ones_like(xx)*z
    else:
        xx, yy, zz = np.meshgrid(x, y, z)

    for i in range(octaves):
        v += a * grad_noise3(xx, yy, zz)
        xx = xx * cfg.lacunarity + cfg.shift
        yy = yy * cfg.lacunarity + cfg.shift
        a *= cfg.falloff
    return v
