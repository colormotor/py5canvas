# Face landmark detection using: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker

from py5canvas import *
import numpy as np

import time
import pathlib
import urllib.request

import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options as base_options_module

# Path to the model file
model_path = pathlib.Path("face_landmarker.task")

# Check if the model file exists, if not, download it
if not model_path.exists():
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
    print()
    print(f"Downloading model from {url}...")
    with urllib.request.urlopen(url) as r, model_path.open("wb") as o:
        while chunk := r.read(1024):
            o.write(chunk)
    print(f"Model downloaded and saved as {model_path}")

# Initialize MediaPipe FaceLandmarker
base_options = base_options_module.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=1,
)
model = vision.FaceLandmarker.create_from_options(options)

video_size = 160
video = VideoInput(size=(video_size, video_size))


def setup():
    create_canvas(512, 512)


def draw():
    background(0)

    # Video frame
    frame = video.read()
    # Convert to numpy 8 bit
    frame = np.array(frame)

    push()
    scale(width / video_size)
    image(frame)

    # Convert the frame to RGB and create MediaPipe Image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

    # # Detect face landmarks in the frame
    result = model.detect(mp_image)

    if result and result.face_landmarks:
        # Convenience aliases to MediaPipe Face Mesh connection sets
        FM = mp.solutions.face_mesh
        TESSELLATION = FM.FACEMESH_TESSELATION
        CONTOURS = FM.FACEMESH_CONTOURS
        IRISES = getattr(FM, "FACEMESH_IRISES", set())
        LIPS = getattr(FM, "FACEMESH_LIPS", set())
        LEFT_EYE = getattr(FM, "FACEMESH_LEFT_EYE", set())
        RIGHT_EYE = getattr(FM, "FACEMESH_RIGHT_EYE", set())
        LEFT_EB = getattr(FM, "FACEMESH_LEFT_EYEBROW", set())
        RIGHT_EB = getattr(FM, "FACEMESH_RIGHT_EYEBROW", set())
        FACE_OVAL = getattr(FM, "FACEMESH_FACE_OVAL", set())

        # Draw each detected face
        for lms in result.face_landmarks:
            pts = landmarks_to_px(lms)

            no_fill()

            # 1) Light tessellation (cyan)
            stroke(0, 255, 255)
            stroke_weight(0.2)
            draw_connections(pts, TESSELLATION)

            # 2) Accented contours (thicker) — different colors for readability
            stroke_weight(0.8)

            # Eyebrows
            stroke(255, 105, 180)  # pink
            draw_connections(pts, LEFT_EB)
            stroke(186, 85, 211)  # purple
            draw_connections(pts, RIGHT_EB)

            # Eyes
            stroke(65, 105, 225)  # blue
            draw_connections(pts, LEFT_EYE)
            stroke(147, 112, 219)  # blue-purple
            draw_connections(pts, RIGHT_EYE)
            if IRISES:
                stroke(70, 130, 180)
                draw_connections(pts, IRISES)

            # Lips
            stroke(0, 255, 255)  # cyan
            draw_connections(pts, LIPS)

            # Face oval
            stroke(64, 224, 208)  # teal
            draw_connections(pts, FACE_OVAL)

    pop()


# helpers ------------------------------------------------------------------------


# convert one face's landmarks to pixel coordinates
def landmarks_to_px(lms):
    return np.array([[lm.x * video_size, lm.y * video_size] for lm in lms], dtype=float)


# Helper: draw a set of connections
def draw_connections(pts, connections):
    for i, j in connections:
        line(pts[i], pts[j])


run()
