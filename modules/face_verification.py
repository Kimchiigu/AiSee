import streamlit as st
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
import time
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ESP32_IP = "http://192.168.1.8" # Replace with your ESP32 IP address

with open('./ubidots-config.json', 'r') as f:
    config = json.load(f)
UBIDOTS_TOKEN = config["UBIDOTS_TOKEN"]
DEVICE_LABEL = config["DEVICE_LABEL"]
attendance_name = config["attendant_names"]
attendance_subject = config["attendant_subjects"]
attendance_time = config["attendant_times"]

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
face_recognizer = cv2.face.LBPHFaceRecognizer_create()
model_path = 'model/absensi/face_recognizer.yml'
TRAINED_FOLDERS_FILE = 'model/absensi/trained_folders.json'
LABEL_MAPPING_FILE = 'model/absensi/label_mapping.json'

### Helper Functions ###
def fetch_latest_image_from_flask():
    try:
        images = sorted(glob.glob("./uploaded_images/*.jpg"), key=os.path.getmtime, reverse=True)

        if not images:
            st.error("No images found in the 'uploaded_images' folder.")
            return None

        latest_image_path = images[0] 
        image = cv2.imread(latest_image_path)
        return image

    except Exception as e:
        st.error(f"Error fetching image: {e}")
        return None


def send_to_ubidots(name, subject, time):
    """Sends the data to Ubidots."""
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    data = {
        attendance_name: {
            "value": 1,  # Dummy value (Ubidots requires a number)
            "context" : {"name": name}
        },
        attendance_subject: {
            "value": 1,
            "context" : {"subject": subject}
        }, 
        attendance_time: {
            "value": 1,
            "context" : {"time": time}
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
    frame = fetch_latest_image_from_flask()
    
    if frame is None:
        st.error("No image found.")
        return None
    
    _, faces = detect_and_draw_faces(frame)
    
    st.image(frame, channels="RGB", use_container_width=True)
    
    if len(faces) > 0:
        x, y, w, h = faces[0]
        face = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_RGB2GRAY)
        return face
    
    st.warning("No face detected.")
    return None

def get_user_id_by_name(name):
    """Get user ID by name from the users collection."""
    users_ref = db.collection("users").where("name", "==", name).stream()
    for user in users_ref:
        return user.id
    return None

def get_semester_by_name(name):
    """Get semester by name from the users collection."""
    users_ref = db.collection("users").where("name", "==", name).stream()
    for user in users_ref:
        return user.to_dict().get("semester")
    return None

def get_attendance_id(userId, subject, semester):
    """Get attendance ID from the attendance collection."""
    attendance_ref = db.collection("attendance").where("userId", "==", userId).where("subject", "==", subject).where("semester", "==", semester).stream()
    for attendance in attendance_ref:
        return attendance.id

    # No attendance found, create a new one
    new_attendance = {
        "userId": userId,
        "subject": subject,
        "semester": semester,
        "attendTimes": 0,
        "isPass":False,
        "maximum": 12,
        "minimum": 10
    }
    doc_ref = db.collection("attendance").add(new_attendance)
    return doc_ref[1].id

### Main Function ###
def verify_user():
    st.subheader("Verify Face")
    name = st.text_input("Name")
    subject = st.text_input("Subject")
    session = st.number_input("Session", min_value=1, value=1)

    if st.button("Scan Face"):
        status = 0
        verified_success = False
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
            if confidence < 100:
                folder_name = next((folder for folder, id in label_mapping.items() if id == label_id), None)
                if folder_name:
                    if folder_name.lower() == name.lower():
                        st.success(f"✅ Welcome back, {folder_name}! Confidence: {confidence:.2f}")
                        
                        user_id = get_user_id_by_name(name)
                        if not user_id:
                            st.error("User not found in database.")
                            return

                        semester = get_semester_by_name(name)
                        attendance_id = get_attendance_id(user_id, subject, semester)
                        if not attendance_id:
                            st.error(f"No attendance record found for {name} in subject {subject}.")
                            
                            response = requests.post(ESP32_IP, data={"verify": "success" if status else "fail"})
                            return

                        session_id = f"session{session}"
                        timestamp = datetime.now().isoformat()
                        db.collection("attendanceLogs").add({
                            "attendanceId": attendance_id,
                            "sessionId": session_id,
                            "timestamp": timestamp,
                            "isVerified": True
                        })
                        
                        db.collection("attendance").document(attendance_id).update({
                            "attendTimes": firestore.Increment(1)
                        })
                        # Send data to Ubidots
                        send_to_ubidots(name, subject, timestamp)
                        
                        # Send data to ESP32
                        status = 1
                        
                        response = requests.post(ESP32_IP, data={"verify": "success" if status else "fail"})
                        
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