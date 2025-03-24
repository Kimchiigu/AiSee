import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import requests
import tempfile
import base64
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import cloudinary
import cloudinary.uploader
import os
from model.absensi.absen import detect_faces_from_camera

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase-service-account.json"))
    initialize_app(cred)
db = firestore.client()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

face_cascade = cv2.CascadeClassifier('model/absensi/haarcascade_frontalface_default.xml')
face_recognizer = cv2.face.LBPHFaceRecognizer_create()
model_path = 'face_recognizer.yml'
if os.path.exists(model_path):
    face_recognizer.read(model_path)
    model_loaded = True
else:
    model_loaded = False


def capture_face(timeout=5, num_images=10, st_placeholder=None):
    return detect_faces_from_camera(timeout, num_images, st_placeholder)

def upload_to_cloudinary(image_np, name, idx):
    _, buffer = cv2.imencode('.jpg', image_np)
    b64_img = base64.b64encode(buffer).decode()
    upload_result = cloudinary.uploader.upload(
        "data:image/jpeg;base64," + b64_img,
        folder=f"AiSee/{name}",
        public_id=f"{name}_{idx}"
    )
    return upload_result['secure_url']

def register_user():
    st.subheader("Register New Face")
    name = st.text_input("Name")
    email = st.text_input("Email")

    if st.button("Capture Face"):
        st.info("Get ready... capturing 10 images!")

        video_placeholder = st.empty()

        faces = capture_face(timeout=5, num_images=10, st_placeholder=video_placeholder)

        if faces:
            urls = []
            for idx, face in enumerate(faces):
                url = upload_to_cloudinary(face, name, idx)
                urls.append(url)

            db.collection("users").add({
                "name": name,
                "email": email,
                "images": urls
            })
            st.success(f"{len(urls)} face images uploaded and user registered!")
        else:
            st.error("No face detected.")

def capture_face_for_verification(timeout=5):
    faces = detect_faces_from_camera(timeout, num_images=1)
    if faces and len(faces) > 0:
        return faces[0]
    return None

def verify_user():
    st.subheader("Verify Face")
    name = st.text_input("Enter your name for verification")

    if st.button("Scan Face"):
        users = db.collection("users").where("name", "==", name).get()
        if not users:
            st.error("User not found.")
            return

        user = users[0].to_dict()
        image_urls = user.get("images", [])

        training_data = []
        labels = []

        for idx, url in enumerate(image_urls):
            resp = requests.get(url, stream=True)
            img = np.asarray(bytearray(resp.raw.read()), dtype=np.uint8)
            frame = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)

            faces = face_cascade.detectMultiScale(frame, scaleFactor=1.2, minNeighbors=5)
            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                training_data.append(face)
                labels.append(0)

        if not training_data:
            st.warning("No face found in images.")
            return

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(training_data, np.array(labels))

        face = capture_face_for_verification(timeout=5)
        if face is not None and isinstance(face, np.ndarray):
            label, confidence = recognizer.predict(face)
            if label == 0:
                st.success(f"✅ Welcome back, {name}! Confidence: {confidence:.2f}")
            else:
                st.warning("❌ Face not recognized.")
        else:
            st.error("No face detected or invalid format.")

def render():
    st.title("Face Attendance App")
    col1, col2 = st.columns(2)
    with col1:
        register_user()
    with col2:
        verify_user()
