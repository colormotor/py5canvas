# Face recognition test using https://pypi.org/project/face-recognition/
from py5canvas import *
import numpy as np
import face_recognition
import time

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
    scale(width/video_size)
    image(frame)

    landmark_features = face_recognition.face_landmarks(frame)
    if landmark_features:
        landmark_features = landmark_features[0]
        # Draw eyes as circles at the average of the corresponding features
        left_eye_pos = np.mean(landmark_features['left_eye'], axis=0)
        right_eye_pos = np.mean(landmark_features['right_eye'], axis=0)
        mouth_pos = np.mean(landmark_features['top_lip'] + landmark_features['bottom_lip'], axis=0)
        stroke(0)
        stroke_weight(0.5)
        fill(255, 90)
        eye_size = 12
        circle(left_eye_pos+[0,2], eye_size)
        circle(right_eye_pos+[0,2], eye_size)
        fill(0)
        circle(left_eye_pos, eye_size/2)
        circle(right_eye_pos, eye_size/2)

        fill(255, 0, 0, 90)
        ellipse(mouth_pos, [20, 10])

run()