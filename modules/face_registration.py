import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import requests
import base64
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase-service-account.json"))
    initialize_app(cred)
db = firestore.client()

# Initialize Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

face_cascade = cv2.CascadeClassifier('model/absensi/haarcascade_frontalface_default.xml')

### Helper Functions ###
def get_camera_indices():
    """Detect available camera indices."""
    camera_indices = [] 
    for i in range(50):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            camera_indices.append(i)
            cap.release()
    return camera_indices

def get_camera():
    """Open the first available camera."""
    camera_indices = get_camera_indices()
    if not camera_indices:
        st.error("No camera available.")
        return None
    return cv2.VideoCapture(camera_indices[0])

def release_camera(cap):
    """Release the camera resource."""
    if cap is not None and cap.isOpened():
        cap.release()

def capture_frame(cap):
    """Capture a single frame from the camera."""
    ret, frame = cap.read()
    if not ret:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def detect_and_draw_faces(frame):
    """Detect faces and draw rectangles on the frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame, faces

def simulate_live_feed(placeholder, cap):
    """Display a single frame for live feed."""
    frame = capture_frame(cap)
    if frame is None:
        return
    frame, _ = detect_and_draw_faces(frame)
    placeholder.image(frame, channels="RGB", use_container_width=True)

def capture_faces(cap, placeholder, num_images=50, delay=0.1):
    """Capture multiple face images with a delay, showing live feed."""
    captured_faces = []
    for _ in range(num_images):
        frame = capture_frame(cap)
        if frame is None:
            continue
        frame_with_faces, faces = detect_and_draw_faces(frame)
        placeholder.image(frame_with_faces, channels="RGB", use_container_width=True)
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_rgb = frame[y:y+h, x:x+w]
            # Convert to grayscale
            face_gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
            captured_faces.append(face_gray)
        time.sleep(delay)
    return captured_faces

def upload_to_cloudinary(image_np, name, idx):
    """Upload a grayscale image to Cloudinary and return its URL."""
    # Ensure image is in grayscale (single channel)
    if len(image_np.shape) == 3:  # If still RGB
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    # Convert grayscale to 3-channel for JPEG compatibility
    image_np_3ch = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    _, buffer = cv2.imencode('.jpg', image_np_3ch)
    b64_img = base64.b64encode(buffer).decode()
    upload_result = cloudinary.uploader.upload(
        "data:image/jpeg;base64," + b64_img,
        folder=f"AiSee/{name}",
        public_id=f"{name}_{idx}"
    )
    return upload_result['secure_url']

### Main Function ###
def register_user():
    st.subheader("Register New Face")
    name = st.text_input("Name")
    email = st.text_input("Email")
    role = st.selectbox("Role", ["Student", "Teacher", "Admin"])
    
    if role not in ("Teacher", "Admin"):
        kelas = st.text_input("Class")
        type = st.selectbox("Type", ["School", "University"])
        
        if type == "School":
            grade = st.number_input("Grade", min_value=1, max_value=12)
        elif type == "University":
            semester = st.number_input("Semester", min_value=1, max_value=15)

    # Initialize session state
    if "camera_active" not in st.session_state:
        st.session_state.camera_active = False
    if "capturing" not in st.session_state:
        st.session_state.capturing = False

    # Camera handling
    preview_placeholder = st.empty()
    cap = None

    if not st.session_state.camera_active:
        if st.button("Start Camera"):
            st.session_state.camera_active = True
            st.rerun()

    if st.session_state.camera_active:
        st.info("Camera is on. Adjust your position and click 'Capture Face' when ready.")
        
        cap = get_camera()
        if cap is None:
            return

        # Show live feed
        if not st.session_state.capturing:
            simulate_live_feed(preview_placeholder, cap)

        # Capture Face button
        capture_button = st.button("Capture Face")
        if capture_button:
            st.session_state.capturing = True
            st.info("Capturing 50 images... please hold still for 5 seconds.")
            faces = capture_faces(cap, preview_placeholder, num_images=50, delay=0.1)
            st.session_state.capturing = False

            if faces:
                urls = []
                for idx, face in enumerate(faces):
                    url = upload_to_cloudinary(face, name, idx)
                    urls.append(url)

                if role in ("Teacher", "Admin"):
                    db.collection("users").add({
                        "name": name,
                        "email": email,
                        "images": urls,
                        "role": role.lower()
                    })
                else:
                    if type == "School":
                        db.collection("users").add({
                            "name": name,
                            "email": email,
                            "images": urls,
                            "class": kelas,
                            "role": role.lower(),
                            "type": type.lower(),
                            "grade": grade
                        })
                    elif type == "University":
                        db.collection("users").add({
                            "name": name,
                            "email": email,
                            "images": urls,
                            "class": kelas,
                            "role": role.lower(),
                            "type": type.lower(),
                            "semester": semester
                        })
                st.success(f"{len(urls)} face images uploaded and user registered!")
            else:
                st.error("No faces captured. Please try again and ensure your face is visible.")

            release_camera(cap)
            st.session_state.camera_active = False
            st.session_state.capturing = False
            st.rerun()

        # Stop Camera button
        if st.button("Stop Camera"):
            release_camera(cap)
            st.session_state.camera_active = False
            st.session_state.capturing = False
            st.rerun()

        # Ensure camera is released if page is closed
        if cap is not None:
            simulate_live_feed(preview_placeholder, cap)  # Keep feed alive

def render():
    st.title("Face Registration")
    register_user()