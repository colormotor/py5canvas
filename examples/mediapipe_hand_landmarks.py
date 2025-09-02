# Hand landmarks and handedness label detection with https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker

from py5canvas import *
import numpy as np

import time
import pathlib
import urllib.request

import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options as base_options_module

# Path to the model file
model_path = pathlib.Path("hand_landmarker.task")

# Check if the model file exists, if not, download it
if not model_path.exists():
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    print()
    print(f"Downloading model from {url}...")
    with urllib.request.urlopen(url) as r, model_path.open("wb") as o:
        while chunk := r.read(1024):
            o.write(chunk)
    print(f"Model downloaded and saved as {model_path}")

# Initialize MediaPipe HandLandmarker
base_options = base_options_module.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
model = vision.HandLandmarker.create_from_options(options)

video_size = 512
video = VideoInput(size=(video_size, video_size))


def setup():
    create_canvas(512, 512)


def draw():
    background(0)

    # Video frame
    frame = video.read()
    frame = np.array(frame)  # uint8 (SRGB)

    push()
    scale(width / video_size)
    image(frame)

    # Detect hand landmarks
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = model.detect(mp_image)

    # Draw each detected hand
    if result and result.hand_landmarks:
        # Convenience alias to the canonical connection set
        HAND_CONNECTIONS = mp.solutions.hands.HAND_CONNECTIONS

        for i, lms in enumerate(result.hand_landmarks):
            pts = landmarks_to_px(lms)

            # 1) Connections (white)
            no_fill()
            stroke(255)
            stroke_weight(1.4)
            draw_connections(pts, HAND_CONNECTIONS)

            # 2) Joints (cyan dots)
            no_stroke()
            fill(0, 200, 255)
            for x, y in pts:
                circle((x, y), 3.8)

            # 3) Handedness label following index finger tip (landmark #8)
            idx_tip = pts[8]  # index finger tip
            label = handedness_label(result, i)
            if label:
                draw_floating_label(idx_tip, label)

    pop()


# helpers ------------------------------------------------------------------------


def landmarks_to_px(lms):
    """Convert one hand's landmarks to pixel coordinates in the video space."""
    return np.array([[lm.x * video_size, lm.y * video_size] for lm in lms], dtype=float)


def draw_connections(pts, connections):
    for a, b in connections:
        line(pts[a], pts[b])


def handedness_label(result, hand_index):
    """
    Extract 'Left' or 'Right' for a given hand index, handling both possible
    result.handedness container shapes.
    """
    try:
        hd = result.handedness[hand_index]
        # Either a list-like [Category, ...] or an object with .categories
        if hasattr(hd, "categories"):
            return hd.categories[0].category_name
        else:
            return hd[0].category_name
    except Exception:
        return None


def draw_floating_label(anchor_xy, text_str):
    x, y = anchor_xy
    # slight offset so we don't cover the fingertip
    x += 8
    y -= 8

    # Backing rounded rect
    push()
    rect_mode(CORNER)
    txt_pad_x, txt_pad_y = 6, 4
    text_size(10)
    tw = text_width(text_str)
    th = 12  # approximate line height for size 10
    no_stroke()
    fill(0, 0, 0, 180)
    rectangle(
        (x - txt_pad_x, y - th - txt_pad_y), (tw + 2 * txt_pad_x, th + 2 * txt_pad_y)
    )

    # Text
    fill(255)
    text(text_str, (x, y))
    pop()


run()
