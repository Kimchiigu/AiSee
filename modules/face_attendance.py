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
model_path = 'model/absensi/face_recognizer.yml'
TRAINED_FOLDERS_FILE = 'model/absensi/trained_folders.json'
LABEL_MAPPING_FILE = 'model/absensi/label_mapping.json'

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

def simulate_live_feed(placeholder, cap, duration=50):
    """Simulate a live camera feed for a given duration."""
    start_time = time.time()
    while time.time() - start_time < duration:
        frame = capture_frame(cap)
        if frame is None:
            continue
        frame, _ = detect_and_draw_faces(frame)
        placeholder.image(frame, channels="RGB", use_container_width=True)
        time.sleep(0.1)  # Adjust this delay to control frame rate

def capture_faces(cap, num_images=50, delay=0.5):
    """Capture multiple face images with a delay between captures."""
    captured_faces = []
    for _ in range(num_images):
        frame = capture_frame(cap)
        if frame is None:
            continue
        _, faces = detect_and_draw_faces(frame)
        if len(faces) > 0:
            x, y, w, h = faces[0]  # Take the first detected face
            captured_faces.append(frame[y:y+h, x:x+w])
        time.sleep(delay)
    return captured_faces

def upload_to_cloudinary(image_np, name, idx):
    """Upload an image to Cloudinary and return its URL."""
    _, buffer = cv2.imencode('.jpg', image_np)
    b64_img = base64.b64encode(buffer).decode()
    upload_result = cloudinary.uploader.upload(
        "data:image/jpeg;base64," + b64_img,
        folder=f"AiSee/{name}",
        public_id=f"{name}_{idx}"
    )
    return upload_result['secure_url']

def list_user_folders():
    """List all subfolders in the 'AiSee' folder on Cloudinary."""
    result = cloudinary.api.subfolders("AiSee")
    folders = [folder['name'] for folder in result['folders']]
    return folders

def load_trained_folders():
    """Load the list of trained folders from a local JSON file."""
    if os.path.exists(TRAINED_FOLDERS_FILE):
        with open(TRAINED_FOLDERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trained_folders(folders):
    """Save the list of trained folders to a local JSON file."""
    with open(TRAINED_FOLDERS_FILE, 'w') as f:
        json.dump(folders, f)

def load_label_mapping():
    """Load the label mapping from a local JSON file."""
    if os.path.exists(LABEL_MAPPING_FILE):
        with open(LABEL_MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_label_mapping(mapping):
    """Save the label mapping to a local JSON file."""
    with open(LABEL_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)

def train_model():
    """Train or update the face recognition model with new folders using integer labels."""
    global face_recognizer  # Add this line to access the global variable
    
    user_folders = list_user_folders()
    trained_folders = load_trained_folders()
    new_folders = [folder for folder in user_folders if folder not in trained_folders]

    if not new_folders and os.path.exists(model_path):
        # No new folders and model exists, nothing to do
        return

    # Load existing model or create a new one
    if os.path.exists(model_path):
        face_recognizer.read(model_path)
    else:
        face_recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Rest of the function remains the same...
    label_mapping = load_label_mapping()
    next_label_id = max(label_mapping.values(), default=-1) + 1

    for folder in new_folders:
        if folder not in label_mapping:
            label_mapping[folder] = next_label_id
            next_label_id += 1

        images = cloudinary.api.resources(type='upload', prefix=f"AiSee/{folder}/")['resources']
        faces = []
        labels = []
        for img in images:
            url = img['secure_url']
            resp = requests.get(url, stream=True)
            img_array = np.asarray(bytearray(resp.raw.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            detected_faces = face_cascade.detectMultiScale(frame, scaleFactor=1.2, minNeighbors=5)
            for (x, y, w, h) in detected_faces:
                face = frame[y:y+h, x:x+w]
                faces.append(face)
                labels.append(label_mapping[folder])  # Use integer label
        if faces:
            face_recognizer.update(faces, np.array(labels, dtype=np.int32))
            trained_folders.append(folder)

    # Save the updated model, trained folders, and label mapping
    face_recognizer.write(model_path)
    save_trained_folders(trained_folders)
    save_label_mapping(label_mapping)

### Main Functions ###

def register_user():
    st.subheader("Register New Face")
    name = st.text_input("Name")
    email = st.text_input("Email")
    role = st.selectbox("Role", ["Student", "Teacher", "Admin"])
    
    if role not in ("Teacher", "Admin"):
        type = st.selectbox("Type", ["School", "University"])
        grade = st.number_input("Grade/Semester", min_value=1, max_value=15)

    # Initialize session state
    if "camera_active" not in st.session_state:
        st.session_state.camera_active = False

    # "Start Camera" button
    if not st.session_state.camera_active:
        if st.button("Start Camera"):
            st.session_state.camera_active = True
            st.rerun()

    # When camera is active
    if st.session_state.camera_active:
        st.info("Camera is on. Adjust your position and click 'Capture Face' when ready.")
        preview_placeholder = st.empty()

        cap = get_camera()
        if cap is None:
            return

        # Show live feed for a short duration
        simulate_live_feed(preview_placeholder, cap, duration=5)

        # "Capture Face" button
        if st.button("Capture Face"):
            st.info("Capturing 50 images... please hold still for 5 seconds.")
            faces = capture_faces(cap, num_images=50, delay=0.5)
            release_camera(cap)

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
                    db.collection("users").add({
                        "name": name,
                        "email": email,
                        "images": urls,
                        "role": role.lower(),
                        "type": type.lower(),
                        "grade": grade
                    })
                st.success(f"{len(urls)} face images uploaded and user registered!")
            else:
                st.error("No faces captured. Please try again and ensure your face is visible.")

            # Reset state
            st.session_state.camera_active = False
            st.rerun()

        # "Stop Camera" button
        if st.button("Stop Camera"):
            release_camera(cap)
            st.session_state.camera_active = False
            st.rerun()

def capture_face_for_verification(timeout=5):
    """Capture a single face for verification."""
    cap = get_camera()
    if cap is None:
        return None
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        frame = capture_frame(cap)
        if frame is None:
            continue
        _, faces = detect_and_draw_faces(frame)
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_RGB2GRAY)
            release_camera(cap)
            return face
    release_camera(cap)
    return None

def verify_user():
    st.subheader("Verify Face")

    if st.button("Scan Face"):
        train_model()

        # Load the trained model
        if os.path.exists(model_path):
            face_recognizer.read(model_path)
        else:
            st.error("No trained model found. Please register users first.")
            return

        # Load label mapping
        label_mapping = load_label_mapping()
        if not label_mapping:
            st.error("No label mapping found. Please register users first.")
            return

        face = capture_face_for_verification(timeout=5)
        if face is not None and isinstance(face, np.ndarray):
            label_id, confidence = face_recognizer.predict(face)
            if confidence < 100:  # Adjust threshold as needed
                # Map integer label back to folder name
                folder_name = next((folder for folder, id in label_mapping.items() if id == label_id), None)
                if folder_name:
                    st.success(f"✅ Welcome back, {folder_name}! Confidence: {confidence:.2f}")
                else:
                    st.warning("❌ Face not recognized.")
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