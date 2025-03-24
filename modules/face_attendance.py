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


def capture_face(timeout=5):
    return detect_faces_from_camera(timeout)

def upload_to_cloudinary(image_np):
    _, buffer = cv2.imencode('.jpg', image_np)
    b64_img = base64.b64encode(buffer).decode()
    upload_result = cloudinary.uploader.upload("data:image/jpeg;base64," + b64_img)
    return upload_result['secure_url']

def register_user():
    st.subheader("Register New Face")
    name = st.text_input("Name")
    email = st.text_input("Email")
    if st.button("Capture Face"):
        st.info("Get ready... capturing in 5 seconds!")
        face = capture_face(timeout=5)
        if face is not None:
            st.success("Face captured!")
            url = upload_to_cloudinary(face)
            db.collection("users").add({
                "name": name,
                "email": email,
                "images": [url]
            })
            st.success("User registered to Firebase!")
        else:
            st.error("No face detected.")

def verify_user():
    st.subheader("Verify Face")
    if not model_loaded:
        st.warning("⚠️ No trained model found yet. Please register at least one face first.")
        return

    if st.button("Scan Face"):
        face = capture_face(timeout=5)
        if face is not None:
            label, confidence = face_recognizer.predict(face)
            users = db.collection("users").stream()
            user_list = list(users)
            if 0 <= label < len(user_list):
                matched_user = user_list[label].to_dict()
                st.success(f"Welcome, {matched_user['name']}! Confidence: {confidence:.2f}")
            else:
                st.warning("Face not recognized.")
        else:
            st.error("No face detected.")

def render():
    st.title("Face Attendance App")
    col1, col2 = st.columns(2)
    with col1:
        register_user()
    with col2:
        verify_user()
