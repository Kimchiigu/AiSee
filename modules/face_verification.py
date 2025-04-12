import streamlit as st
import cv2
import numpy as np
import os
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime
import time

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
    global face_recognizer
    
    user_folders = list_user_folders()
    trained_folders = load_trained_folders()
    new_folders = [folder for folder in user_folders if folder not in trained_folders]

    if not new_folders and os.path.exists(model_path):
        return

    if os.path.exists(model_path):
        face_recognizer.read(model_path)
    else:
        face_recognizer = cv2.face.LBPHFaceRecognizer_create()

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
                labels.append(label_mapping[folder])
        if faces:
            face_recognizer.update(faces, np.array(labels, dtype=np.int32))
            trained_folders.append(folder)

    face_recognizer.write(model_path)
    save_trained_folders(trained_folders)
    save_label_mapping(label_mapping)

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

def get_user_id_by_name(name):
    """Get user ID by name from the users collection."""
    users_ref = db.collection("users").where("name", "==", name).stream()
    for user in users_ref:
        return user.id
    return None

def get_attendance_id(user_id, subject, semester="semester-1"):
    """Get attendance ID from the attendance collection."""
    attendance_ref = db.collection("attendance").where("userId", "==", user_id).where("subject", "==", subject).where("semester", "==", semester).stream()
    for attendance in attendance_ref:
        return attendance.id
    return None

### Main Function ###
def verify_user():
    st.subheader("Verify Face")
    name = st.text_input("Name")
    subject = st.text_input("Subject")
    session = st.number_input("Session", min_value=1, value=1)

    if st.button("Scan Face"):
        if not name or not subject or not session:
            st.error("Please fill in all fields: Name, Subject, and Session.")
            return

        train_model()

        if os.path.exists(model_path):
            face_recognizer.read(model_path)
        else:
            st.error("No trained model found. Please register users first.")
            return

        label_mapping = load_label_mapping()
        if not label_mapping:
            st.error("No label mapping found. Please register users first.")
            return

        face = capture_face_for_verification(timeout=5)
        if face is not None and isinstance(face, np.ndarray):
            label_id, confidence = face_recognizer.predict(face)
            if confidence < 100:  # Adjust threshold as needed
                folder_name = next((folder for folder, id in label_mapping.items() if id == label_id), None)
                if folder_name:
                    # Check if predicted name matches input name
                    if folder_name.lower() == name.lower():
                        st.success(f"✅ Welcome back, {folder_name}! Confidence: {confidence:.2f}")
                        
                        # Get user ID
                        user_id = get_user_id_by_name(name)
                        if not user_id:
                            st.error("User not found in database.")
                            return

                        # Get attendance ID
                        attendance_id = get_attendance_id(user_id, subject)
                        if not attendance_id:
                            st.error(f"No attendance record found for {name} in subject {subject}.")
                            return

                        # Save to attendanceLogs
                        session_id = f"session{session}"
                        timestamp = datetime.now().isoformat()
                        db.collection("attendanceLogs").add({
                            "attendanceId": attendance_id,
                            "sessionId": session_id,
                            "timestamp": timestamp,
                            "isVerified": True
                        })
                        st.success(f"Attendance logged for {name} in {subject}, session {session}.")
                    else:
                        st.error(f"❌ Name mismatch: Predicted {folder_name}, but you entered {name}.")
                else:
                    st.warning("❌ Face not recognized.")
            else:
                st.warning("❌ Face not recognized.")
        else:
            st.error("No face detected or invalid format.")

def render():
    st.title("Face Verification")
    verify_user()