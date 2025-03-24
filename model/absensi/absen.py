import cv2
import time
import numpy as np

face_cascade = cv2.CascadeClassifier('model/absensi/haarcascade_frontalface_default.xml')

def detect_faces_from_camera(timeout=5, num_images=10, streamlit_placeholder=None):
    cap = cv2.VideoCapture(0)
    collected_faces = []
    start_time = time.time()

    while time.time() - start_time < timeout and len(collected_faces) < num_images:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            face = gray[y:y + h, x:x + w]
            collected_faces.append(face)
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if streamlit_placeholder:
            streamlit_placeholder.image(rgb_frame, channels="RGB")

        cv2.waitKey(100)

    cap.release()
    return collected_faces
