import streamlit as st
import cv2
import av
from streamlit_webrtc import VideoProcessorBase
from ultralytics import YOLO

@st.cache_resource
def load_model():
    return YOLO('./emotion-yolov11-model/yolov11_finetuned.pt')

class EmotionDetector(VideoProcessorBase):
    def __init__(self):
        self.model = load_model()
    
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = box.conf[0].item()
            cls = box.cls[0].item()
            label = self.model.names[cls]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{label} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")