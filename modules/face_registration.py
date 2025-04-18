import streamlit as st
import cv2
import numpy as np
import base64
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import cloudinary
import cloudinary.uploader
import time
from streamlit_webrtc import WebRtcMode, webrtc_streamer, VideoProcessorBase
import av
from collections import deque

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

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

class FaceCaptureProcessor(VideoProcessorBase):
    def __init__(self, name):
        self.detected_faces = deque(maxlen=50)
        self.uploaded_urls = []
        self.last_capture_time = 0
        self.capture_interval = 0.1
        self.capturing = False
        self.capture_complete = False
        self.last_detected_count = 0
        self.name = name
    
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05, 
            minNeighbors=5, 
            minSize=(50, 50), 
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        print(f"Detected faces: {len(faces)}, Coordinates: {faces}")
        self.last_detected_count = len(faces)
        
        current_time = time.time()
        
        if self.capturing and not self.capture_complete and len(faces) > 0:
            (x, y, w, h) = faces[0]
            if (len(self.detected_faces) < 50 and 
                current_time - self.last_capture_time >= self.capture_interval):
                print(f"Capturing face #{len(self.detected_faces) + 1}")
                face_img = gray[y:y+h, x:x+w]
                if face_img.size > 0:
                    self.detected_faces.append(face_img)
                    self.last_capture_time = current_time
                    try:
                        url = upload_to_cloudinary(face_img, self.name, len(self.detected_faces) - 1)
                        self.uploaded_urls.append(url)
                        print(f"Uploaded face #{len(self.uploaded_urls)} to Cloudinary: {url}")
                    except Exception as e:
                        print(f"Cloudinary upload failed: {str(e)}")
                if len(self.detected_faces) >= 50:
                    print("50 faces captured and uploaded, stopping")
                    self.capture_complete = True
                    self.capturing = False
        
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def upload_to_cloudinary(image_np, name, idx):
    try:
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
    except Exception as e:
        st.error(f"Cloudinary upload failed for image {idx}: {str(e)}")
        raise

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

    if "registration_complete" not in st.session_state:
        st.session_state.registration_complete = False
    if "capture_started" not in st.session_state:
        st.session_state.capture_started = False
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "face_processor" not in st.session_state:
        st.session_state.face_processor = None

    st.write("Please position your face in the center of the camera frame with good lighting.")

    if not st.session_state.capture_started and not st.session_state.registration_complete:
        if st.button("Start Capture Face"):
            st.session_state.capture_started = True
            st.session_state.processing = False
            st.rerun()

    if st.session_state.capture_started:
        ctx = webrtc_streamer(
            key="face-registration",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=lambda: FaceCaptureProcessor(name),
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

        if ctx.video_processor:
            st.session_state.face_processor = ctx.video_processor
            st.session_state.face_processor.capturing = True

            debug_placeholder = st.empty()
            progress_placeholder = st.empty()

            if st.session_state.face_processor:
                capture_count = len(st.session_state.face_processor.detected_faces)
                upload_count = len(st.session_state.face_processor.uploaded_urls)
                debug_placeholder.write(f"Detected faces in last frame: {st.session_state.face_processor.last_detected_count}")
                progress_placeholder.progress(min(capture_count / 50, 1.0), text=f"Capturing: {capture_count}/50 faces, Uploaded: {upload_count}/50")
                
                if not st.session_state.face_processor.capture_complete:
                    time.sleep(0.1) 
                    st.rerun()

            if st.button("Stop Capture"):
                st.session_state.capture_started = False
                st.session_state.face_processor.capturing = False
                st.rerun()

    if (st.session_state.face_processor and 
        st.session_state.face_processor.capture_complete and 
        len(st.session_state.face_processor.uploaded_urls) >= 50 and 
        not st.session_state.registration_complete and 
        not st.session_state.processing):
        st.session_state.processing = True
        try:
            with st.spinner("Saving to Firebase..."):
                user_data = {
                    "name": name,
                    "email": email,
                    "images": st.session_state.face_processor.uploaded_urls,
                    "role": role.lower()
                }
                if role not in ("Teacher", "Admin"):
                    user_data["class"] = kelas
                    user_data["type"] = type.lower()
                    if type == "School":
                        user_data["grade"] = grade
                    elif type == "University":
                        user_data["semester"] = semester
                db.collection("users").add(user_data)
                print("User data saved to Firebase")

            st.session_state.registration_complete = True
            st.session_state.processing = False
            st.session_state.capture_started = False
            st.success("Registration complete! User successfully created with 50 face images.")
            st.balloons()
        except Exception as e:
            st.error(f"Firebase save failed: {str(e)}")
            st.session_state.processing = False

def render():
    st.title("Face Registration")
    register_user()
