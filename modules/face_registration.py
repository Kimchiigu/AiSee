import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import base64
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import cloudinary
import cloudinary.uploader
import time
import json
import requests
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open('./ubidots-config.json', 'r') as f:
    config = json.load(f)
UBIDOTS_TOKEN = config["UBIDOTS_TOKEN"]
DEVICE_LABEL = config["DEVICE_LABEL"]
REGISTRATION_IMAGE = config["registration_image"]


if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["FIREBASE_SERVICE_ACCOUNT"].to_dict())
    initialize_app(cred)
db = firestore.client()

cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"],
    secure=True
)

face_cascade = cv2.CascadeClassifier('model/absensi/haarcascade_frontalface_default.xml')

### Helper Functions ###
@st.cache_data(ttl=1) 
def get_latest_image_path():
    images = glob.glob("./uploaded_images/*.jpg")
    if not images:
        return None
    return max(images, key=os.path.getmtime)

def fetch_latest_image_from_flask():
    try:
        latest_image_path = get_latest_image_path()
        if not latest_image_path:
            st.error("No images found.")
            return None
        image = cv2.imread(latest_image_path)
        return image
    except Exception as e:
        st.error(f"Error fetching image: {e}")
        return None

def send_to_ubidots(image_url):
    """Sends the image URL to Ubidots."""
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    data = {
        REGISTRATION_IMAGE: {
            "value": 1,  # Dummy value (Ubidots requires a number)
            "context": {"url": image_url}
        }
    }
    response = requests.post(url, json=data, headers=headers)


def detect_and_draw_faces(frame):
    """Detect faces and draw rectangles on the frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame, faces

def simulate_live_feed(placeholder):
    """Display a single frame for live feed."""
    frame = fetch_latest_image_from_flask()
    if frame is None:
        return
    frame, _ = detect_and_draw_faces(frame)
    placeholder.image(frame, channels="RGB", use_container_width=True)
    time.sleep(0.2) 

def capture_faces(placeholder, num_images=50, delay=0.1):
    """Capture multiple face images with a delay, showing live feed."""
    captured_faces = []
    for _ in range(num_images):
        frame = fetch_latest_image_from_flask()
        if frame is None:
            continue
        frame_with_faces, faces = detect_and_draw_faces(frame)
        placeholder.image(frame_with_faces, channels="RGB", use_container_width=True)
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_rgb = frame[y:y+h, x:x+w]
            face_gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
            captured_faces.append(face_gray)
        time.sleep(delay)
    return captured_faces

def upload_to_cloudinary(image_np, name, idx):
    """Upload a grayscale image to Cloudinary and return its URL."""
    if len(image_np.shape) == 3:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
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

    if "camera_active" not in st.session_state:
        st.session_state.camera_active = False
    if "capturing" not in st.session_state:
        st.session_state.capturing = False

    preview_placeholder = st.empty()
    cap = None

    if not st.session_state.camera_active:
        if st.button("Start Camera"):
            st.session_state.camera_active = True
            st.rerun()

    if st.session_state.camera_active:
        st.info("Camera is on. Adjust your position and click 'Capture Face' when ready.")
        
        cap = fetch_latest_image_from_flask()
        if cap is None:
            return

        if not st.session_state.capturing:
            simulate_live_feed(preview_placeholder)

        capture_button = st.button("Capture Face")
        if capture_button:
            st.session_state.capturing = True
            st.info("Capturing 50 images... please hold still for 5 seconds.")
            faces = capture_faces(preview_placeholder, num_images=50, delay=0.1)
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

            st.session_state.camera_active = False
            st.session_state.capturing = False
            st.rerun()

        if st.button("Stop Camera"):
            st.session_state.camera_active = False
            st.session_state.capturing = False
            st.rerun()

        if cap is not None:
            simulate_live_feed(preview_placeholder)

def render():
    st.title("Face Registration")
    register_user()