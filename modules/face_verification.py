import streamlit as st
import cv2
import numpy as np
import os
import requests
import cloudinary
import cloudinary.api
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime
from deepface import DeepFace
import tempfile

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

face_cascade = cv2.CascadeClassifier(os.path.join(BASE_DIR, 'model/absensi/haarcascade_frontalface_default.xml'))

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
            face = frame[y:y+h, x:x+w]
            release_camera(cap)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                cv2.imwrite(tmp.name, cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
                return tmp.name
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

        face_file = capture_face_for_verification(timeout=5)
        if face_file is None:
            st.error("No face detected or camera error.")
            return

        user_folders = list_user_folders()
        if name.lower() not in [folder.lower() for folder in user_folders]:
            st.error(f"No images found for {name} in Cloudinary.")
            os.remove(face_file)
            return

        images = cloudinary.api.resources(type='upload', prefix=f"AiSee/{name}/")['resources']
        if not images:
            st.error(f"No images found for {name} in Cloudinary.")
            os.remove(face_file)
            return

        verified = False
        for img in images:
            url = img['secure_url']
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                resp = requests.get(url, stream=True)
                tmp.write(resp.content)
                tmp_path = tmp.name

            try:
                result = DeepFace.verify(face_file, tmp_path, model_name="Facenet", detector_backend="opencv")
                if result["verified"] and result["distance"] < 0.4:
                    verified = True
                    break
            except Exception as e:
                st.warning(f"Error verifying image: {str(e)}")
            finally:
                os.remove(tmp_path)

        os.remove(face_file)

        if verified:
            st.success(f"✅ Welcome back, {name}!")
            
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
            st.error(f"❌ Face not recognized or does not match {name}.")

def render():
    st.title("Face Verification")
    verify_user()