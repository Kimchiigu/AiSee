import logging
import queue
from pathlib import Path
from typing import List, NamedTuple

import av
import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO
import os
from streamlit_webrtc import WebRtcMode, webrtc_streamer

logger = logging.getLogger(__name__)

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray

@st.cache_resource
def load_model():
    model_path = "model/cheating/yolov9m_finetuned.pt"
    if not os.path.exists(model_path):
        st.error(f"Model file not found at {model_path}. Please ensure the path is correct.")
        st.stop()
    return YOLO(model_path)

result_queue: "queue.Queue[List[Detection]]" = queue.Queue()

def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    model = load_model()
    image = frame.to_ndarray(format="bgr24")
    
    results = model.predict(image, conf=0.5)
    annotated_frame = results[0].plot()
    
    detections = []
    for result in results[0].boxes:
        class_id = int(result.cls)
        label = model.names[class_id]
        score = float(result.conf)
        box = result.xyxy[0].cpu().numpy()
        
        detections.append(
            Detection(
                class_id=class_id,
                label=label,
                score=score,
                box=box,
            )
        )
    
    result_queue.put(detections)
    
    return av.VideoFrame.from_ndarray(annotated_frame, format="bgr24")

def render():
    st.title("Real-Time Exam Cheating Detection")
    st.write("This app uses a fine-tuned YOLOv9 model to detect 'Cheating', 'Mobile', or 'Normal' behaviors in real-time via webcam.")
    st.info("When start camera, click the play button to avoid connection error")

    webrtc_ctx = webrtc_streamer(
        key="exam-cheating-detection",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if st.checkbox("Show detection alerts", value=True):
        if webrtc_ctx.state.playing:
            alerts_placeholder = st.empty()
            
            while True:
                try:
                    detections = result_queue.get()
                    for detection in detections:
                        if "cheating" in detection.label.lower():
                            alerts_placeholder.warning(f"Cheating Detected! {detection.label} (Confidence: {detection.score:.2f})")
                        elif "mobile" in detection.label.lower():
                            alerts_placeholder.warning(f"Mobile Device Detected! {detection.label} (Confidence: {detection.score:.2f})")
                        elif "normal" in detection.label.lower():
                            alerts_placeholder.success(f"Normal Behavior Detected! {detection.label} (Confidence: {detection.score:.2f})")
                except queue.Empty:
                    continue
