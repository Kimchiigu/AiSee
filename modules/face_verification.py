import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import cv2
import numpy as np
import os
import requests
import cloudinary
import cloudinary.api
import json
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_recognizer = cv2.face.LBPHFaceRecognizer_create()
model_path = 'model/absensi/face_recognizer.yml'
TRAINED_FOLDERS_FILE = 'model/absensi/trained_folders.json'
LABEL_MAPPING_FILE = 'model/absensi/label_mapping.json'

### Helper Functions ###
def list_user_folders():
    """List all subfolders in the 'AiSee' folder on Cloudinary."""
    try:
        result = cloudinary.api.subfolders("AiSee")
        folders = [folder['name'] for folder in result['folders']]
        return folders
    except Exception as e:
        st.error(f"Error accessing Cloudinary: {e}")
        return []

def load_trained_folders():
    """Load the list of trained folders from a local JSON file."""
    if os.path.exists(TRAINED_FOLDERS_FILE):
        with open(TRAINED_FOLDERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trained_folders(folders):
    """Save the list of trained folders to a local JSON file."""
    os.makedirs(os.path.dirname(TRAINED_FOLDERS_FILE), exist_ok=True)
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
    os.makedirs(os.path.dirname(LABEL_MAPPING_FILE), exist_ok=True)
    with open(LABEL_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)

def train_model():
    """Train or update the face recognition model with new folders using integer labels."""
    global face_recognizer
    
    user_folders = list_user_folders()
    if not user_folders:
        st.warning("No user folders found in Cloudinary.")
        return False

    trained_folders = load_trained_folders()
    new_folders = [folder for folder in user_folders if folder not in trained_folders]

    if not new_folders and os.path.exists(model_path):
        return True

    face_recognizer = cv2.face.LBPHFaceRecognizer_create()

    label_mapping = load_label_mapping()
    next_label_id = max(label_mapping.values(), default=-1) + 1

    faces = []
    labels = []

    for folder in user_folders:
        if folder not in label_mapping:
            label_mapping[folder] = next_label_id
            next_label_id += 1

        images = cloudinary.api.resources(type='upload', prefix=f"AiSee/{folder}/")['resources']
        for img in images:
            try:
                url = img['secure_url']
                resp = requests.get(url, stream=True)
                img_array = np.asarray(bytearray(resp.raw.read()), dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
                detected_faces = face_cascade.detectMultiScale(frame, scaleFactor=1.2, minNeighbors=5)
                for (x, y, w, h) in detected_faces:
                    face = frame[y:y+h, x:x+w]
                    faces.append(face)
                    labels.append(label_mapping[folder])
            except Exception as e:
                st.warning(f"Error processing image {img['public_id']}: {e}")

    if faces:
        face_recognizer.train(faces, np.array(labels, dtype=np.int32))
        face_recognizer.write(model_path)
        save_trained_folders(user_folders)
        save_label_mapping(label_mapping)
        return True
    else:
        st.error("No faces found for training.")
        return False

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

### WebRTC Video Transformer ###
class FaceVerificationTransformer(VideoTransformerBase):
    def __init__(self):
        self.last_face = None
        self.face_detected = False
        self.model_loaded = False
        
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(rgb_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if not self.face_detected:
                self.last_face = gray[y:y+h, x:x+w]
                self.face_detected = True
                
        return cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

### Main Function ###
def verify_user():
    st.subheader("Verify Face")
    name = st.text_input("Name")
    subject = st.text_input("Subject")
    session = st.number_input("Session", min_value=1, value=1)

    if not name or not subject or not session:
        st.warning("Please fill in all fields: Name, Subject, and Session.")
        return

    if not os.path.exists(model_path):
        st.info("Training face recognition model...")
        if not train_model():
            st.error("Failed to train the face recognition model.")
            return
    else:
        try:
            face_recognizer.read(model_path)
        except:
            st.info("Existing model appears invalid, retraining...")
            if not train_model():
                st.error("Failed to train the face recognition model.")
                return

    label_mapping = load_label_mapping()
    if not label_mapping:
        st.error("No label mapping found. Please register users first.")
        return

    ctx = webrtc_streamer(
        key="face-verification",
        video_transformer_factory=FaceVerificationTransformer,
        async_transform=True,
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    if ctx.video_transformer:
        if st.button("Verify Face"):
            if not ctx.video_transformer.face_detected:
                st.error("No face detected. Please position your face in the camera.")
                return

            face = ctx.video_transformer.last_face
            if face is not None and isinstance(face, np.ndarray):
                try:
                    label_id, confidence = face_recognizer.predict(face)
                    if confidence < 100:
                        folder_name = next((folder for folder, id in label_mapping.items() if id == label_id), None)
                        if folder_name:
                            if folder_name.lower() == name.lower():
                                st.success(f"✅ Welcome back, {folder_name}! Confidence: {confidence:.2f}")
                                
                                user_id = get_user_id_by_name(name)
                                if not user_id:
                                    st.error("User not found in database.")
                                    return

                                attendance_id = get_attendance_id(user_id, subject)
                                if not attendance_id:
                                    st.error(f"No attendance record found for {name} in subject {subject}.")
                                    return

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
                            st.warning("❌ Face not recognized in database.")
                    else:
                        st.warning(f"❌ Face not recognized (confidence too low: {confidence:.2f})")
                except Exception as e:
                    st.error(f"Error during face prediction: {e}")

def render():
    st.title("Face Verification")
    verify_user()
