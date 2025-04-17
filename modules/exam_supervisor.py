import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import os
import glob

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

@st.cache_resource
def load_model():
    model_path = "model/cheating/yolov9m_finetuned.pt"
    if not os.path.exists(model_path):
        st.error(f"Model file not found at {model_path}. Please ensure the path is correct.")
        st.stop()
    return YOLO(model_path)

def render():
    model = load_model()

    st.title("Real-Time Exam Cheating Detection")
    st.write("This app uses a fine-tuned YOLOv9 model to detect 'Cheating', 'Mobile', or 'Normal' behaviors in real-time via Camera.")

    frame_placeholder = st.empty()

    if 'run' not in st.session_state:
        st.session_state.run = False

    start_button = st.button("Start Camera")
    stop_button = st.button("Stop Camera")

    if start_button:
        st.session_state.run = True
    if stop_button:
        st.session_state.run = False

    while st.session_state.run:
        frame = fetch_latest_image_from_flask()
        if frame is None:
            continue


        results = model.predict(frame, conf=0.5)
        annotated_frame = results[0].plot()
        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(annotated_frame_rgb, caption="Live Detection", use_container_width=True)

        for result in results[0].boxes:
            class_id = int(result.cls)
            class_name = model.names[class_id]
            confidence = float(result.conf)
            if "cheating" in class_name.lower():
                st.warning(f"Cheating Detected! Confidence: {confidence:.2f}")
            elif "mobile" in class_name.lower():
                st.warning(f"Mobile Device Detected! Confidence: {confidence:.2f}")
            elif "normal" in class_name.lower():
                st.success(f"Normal Behavior Detected! Confidence: {confidence:.2f}")

    st.write("Camera stopped.")