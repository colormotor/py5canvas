'''
Using py5sketch with differentiable rasterization to approximate an image.
Uses diffvg https://github.com/BachiLi/diffvg and pytorch
'''
from importlib import reload
from py5canvas import canvas
reload(canvas)

from skimage import io
import numpy as np
import pydiffvg, torch
import imgui
from array import array

img = None

# Load grayscale image
img = io.imread('images/frida128.png')
img = img[:, :, 0]
img = img / 255.0
w, h = img.shape[1], img.shape[0]

# setup diffvg
pydiffvg.set_use_gpu(torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def to_tensor(v, dtype=torch.float32):
    return torch.tensor(v, dtype=dtype).contiguous()

def rearrange_image(img):
    img = np.rot90(img.T, 3)
    img = np.fliplr(img)
    return img

def numpy_image(img):
    return rearrange_image(img.detach().cpu().numpy()[0])

# Setup diffvg primitives
img = to_tensor(img)
n = 5
degree = 2
num_control_points = to_tensor([degree-1 for _ in range(n-1)], torch.int32)
num_points = (n-1) * degree + 1
primitives = []
num_samples = 2
losses = []

stroke_color = to_tensor(np.array([0.0, 0.0, 0.0, 1.0]))
fill_color = None
num_primitives = 20

for i in range(num_primitives):
    points = np.vstack([np.random.uniform(0, img.shape[1], num_points),
                        np.random.uniform(0, img.shape[0], num_points)]).T
    points = to_tensor(points)
    print(points.shape)

    points.requires_grad = True
    path = pydiffvg.Path(num_control_points=num_control_points,
                         points=points,
                         stroke_width=to_tensor(np.ones(num_points))*1,
                         is_closed=False,
                         use_distance_approx=False)
    primitives.append(path)
group = pydiffvg.ShapeGroup(shape_ids=torch.tensor(list(range(num_primitives))),
                            fill_color=fill_color,
                            stroke_color=stroke_color)

background_image = torch.ones(w, h, 3, device=device)


def render(seed=0):
    scene_args = pydiffvg.RenderFunction.serialize_scene(w, h, primitives, [group],
                                                         use_prefiltering=False)
    img = pydiffvg.RenderFunction.apply(w, h, num_samples, num_samples, seed, None, *scene_args)
    img = img[:, :, 3:4] * img[:, :, :3] + background_image * (1 - img[:, :, 3:4])
    img = img[:, :, :3]
    img = img.unsqueeze(0)
    img = img.permute(0, 3, 1, 2) # NHWC -> NCHW
    return img


# Setup optimizer
parameters = [path.points for path in primitives]
opt = torch.optim.Adam(parameters, lr=3.0)


def setup():
    create_canvas(512, 512)
    # Here we tell the UI that we build a custom UI
    sketch.set_gui_callback(gui)


def gui():
    # Visualize losses
    if losses:
        if imgui.tree_node("Loss", imgui.TREE_NODE_DEFAULT_OPEN):
            imgui.plot_lines("Losses", array('f', losses), graph_size=(300, 100))
            imgui.text('Loss: %.4f' % losses[-1])
            imgui.tree_pop()


def draw():
    c.background(255)

    # Optimize
    im = render()
    opt.zero_grad()
    loss = torch.nn.functional.mse_loss(im[0][0], img)
    loss.backward()
    opt.step()
    im = numpy_image(im)
    #im = (im[:,:,0] + img.cpu().numpy())/2

    # Clamp points to image size (assuming square)
    for points in parameters:
        points.data.clamp_(0, img.shape[0])

    # Anneal learning rate
    for g in opt.param_groups:
        g['lr'] = g['lr']*0.999
        print(g['lr'])
    # Keep track of them losses
    losses.append(loss.item())

    # Draw
    c.background(255)
    c.push()
    scale_amt = c.width/im.shape[1]
    c.scale(scale_amt)


    c.image((img.cpu().numpy() + np.ones(img.shape))/2)
    c.no_fill()
    c.stroke(0)
    c.stroke_weight(1.5)
    for path in primitives:
        pts = path.points.detach().cpu().numpy()
        c.begin_contour()
        c.vertex(pts[0])
        for i in range(1, len(pts), degree):
            c.bezier(*pts[i:i+degree])
        c.end_contour()
    c.pop()
