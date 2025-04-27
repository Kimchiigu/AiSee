import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoTransformerBase
import cv2
import numpy as np
import os
import time
import csv
from ultralytics import YOLO
from datetime import datetime
from io import StringIO
import av
import queue
import threading
import time

global_seats = {}
seats_lock = threading.Lock()
seat_updates_queue = queue.Queue()

class SnapshotTransformer(VideoTransformerBase):
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=1)
    
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        try:
            self.frame_queue.put(img, timeout=1)
        except queue.Full:
            pass
        return img

@st.cache_resource
def load_model():
    model_path = "model/emotion/yolov11_finetuned.pt"
    if not os.path.exists(model_path):
        st.error(f"Model file not found at {model_path}.")
        st.stop()
    return YOLO(model_path)

def draw_seats(frame, seats):
    frame_copy = frame.copy()
    for label, seat_data in seats.items():
        sx, sy, sw, sh = seat_data["region"]
        color = (0, 255, 0) if seat_data.get("occupied", False) else (255, 0, 0)
        cv2.rectangle(frame_copy, (sx, sy), (sx + sw, sy + sh), color, 2)
        cv2.putText(frame_copy, label, (sx, sy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        if st.session_state.get("monitoring", False):
            total_duration = seat_data.get("accumulated_time", 0.0)
            if seat_data.get("occupied", False) and seat_data.get("start_time"):
                total_duration += time.time() - seat_data["start_time"]
            mm = int(total_duration // 60)
            ss = int(total_duration % 60)
            duration_text = f"{mm}:{ss:02d}"
            cv2.putText(frame_copy, duration_text, (sx, sy + sh + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame_copy

def is_person_in_seat(person_box, seat_region):
    px, py, pw, ph = person_box
    cx = px + pw / 2
    cy = py + ph / 2
    sx, sy, sw, sh = seat_region
    return (sx <= cx <= sx + sw) and (sy <= cy <= sy + sh)

def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    model = load_model()
    with seats_lock:
        seats = global_seats.copy()
    
    img = frame.to_ndarray(format="bgr24")
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = model.predict(rgb_img, conf=0.3)
    person_detections = []
    if len(results) > 0:
        boxes = results[0].boxes
        for box in boxes:
            if int(box.cls[0]) == 0:
                x_min, y_min, x_max, y_max = box.xyxy[0].cpu().numpy()
                person_detections.append((x_min, y_min, x_max - x_min, y_max - y_min))
    
    for label, seat_data in seats.items():
        seat_region = seat_data["region"]
        occupied = any(is_person_in_seat(person_box, seat_region) for person_box in person_detections)
        
        if occupied != seat_data["occupied"]:
            if occupied:
                seat_data["start_time"] = time.time()
            else:
                if seat_data["start_time"]:
                    elapsed = time.time() - seat_data["start_time"]
                    seat_data["accumulated_time"] += elapsed
                    seat_data["start_time"] = None
            seat_data["occupied"] = occupied
    
    frame_with_seats = draw_seats(rgb_img, seats)
    
    for (x, y, w, h) in person_detections:
        cv2.rectangle(frame_with_seats, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 2)
        cv2.putText(frame_with_seats, "Person", (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    seat_updates = {label: {"occupied": seat_data["occupied"], "start_time": seat_data["start_time"], "accumulated_time": seat_data["accumulated_time"]} for label, seat_data in seats.items()}
    seat_updates_queue.put(seat_updates)
    
    return av.VideoFrame.from_ndarray(cv2.cvtColor(frame_with_seats, cv2.COLOR_RGB2BGR), format="bgr24")

def process_seat_updates():
    try:
        while True:
            seat_updates = seat_updates_queue.get_nowait()
            for label, occupied in seat_updates.items():
                if label in st.session_state.seats:
                    seat_data = st.session_state.seats[label]
                    
                    if occupied:
                        if not seat_data["occupied"]:
                            seat_data["occupied"] = True
                            seat_data["start_time"] = time.time()
                    else:
                        if seat_data["occupied"]:
                            elapsed = time.time() - seat_data["start_time"]
                            seat_data["accumulated_time"] += elapsed
                            seat_data["occupied"] = False
                            seat_data["start_time"] = None
                    
                    with seats_lock:
                        if label in global_seats:
                            global_seats[label].update({
                                "occupied": seat_data["occupied"],
                                "start_time": seat_data["start_time"],
                                "accumulated_time": seat_data["accumulated_time"]
                            })
    except queue.Empty:
        pass

def download_csv(seats):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Seat Label", "Accumulated Time (s)"])
    for label, seat_data in seats.items():
        total_time = seat_data.get("accumulated_time", 0.0)
        if seat_data.get("occupied", False) and seat_data.get("start_time"):
            total_time += time.time() - seat_data["start_time"]
        writer.writerow([label, f"{total_time:.2f}"])
    csv_data = output.getvalue()
    output.close()
    return csv_data.encode('utf-8')

def capture_snapshot_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    if not hasattr(st.session_state, "snapshot_frame"):
        st.session_state.snapshot_frame = None
    st.session_state.snapshot_frame = img.copy()
    return av.VideoFrame.from_ndarray(img, format="bgr24")

def monitor_attendance():
    global global_seats
    st.title("Seat Occupancy Monitoring")
    st.write("Configure seat regions and monitor student presence.")
    st.info("When starting camera, click the play button and wait for video feed before capturing snapshot")

    if "seats" not in st.session_state:
        st.session_state.seats = {}
    if "snapshot" not in st.session_state:
        st.session_state.snapshot = None
    if "monitoring" not in st.session_state:
        st.session_state.monitoring = False

    with seats_lock:
        global_seats = st.session_state.seats.copy()

    if st.session_state.snapshot is None:
        st.subheader("Step 1: Capture Snapshot")
        
        ctx = webrtc_streamer(
            key="snapshot-capture",
            video_transformer_factory=SnapshotTransformer,
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                "video": {"width": 640, "height": 480},
                "audio": False
            },
            async_processing=True,
        )

        if st.button("Capture Snapshot"):
            if ctx.video_transformer:
                try:
                    latest_frame = ctx.video_transformer.frame_queue.get(timeout=5)
                    st.session_state.snapshot = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
                    st.success("Snapshot captured! Proceed to configure seats.")
                    st.rerun()
                except queue.Empty:
                    st.error("No frames received from camera. Please:")
                    st.markdown("1. Ensure camera permissions are granted")
                    st.markdown("2. Check camera connection")
                    st.markdown("3. Wait for video feed to appear before capturing")
            else:
                st.error("Camera not initialized. Please click the 'Start Camera' button first.")

    elif not st.session_state.monitoring:
        st.subheader("Step 2: Configure Seat Regions")
        
        if st.session_state.snapshot is not None:
            height, width, _ = st.session_state.snapshot.shape
            st.write(f"Snapshot Size: {width}x{height} pixels")
            frame_with_seats = draw_seats(st.session_state.snapshot, st.session_state.seats)
            st.image(frame_with_seats, channels="RGB", caption="Configure Seat Regions", use_container_width=True)

        with st.form("seat_form"):
            st.write("Add or Update Seat")
            seat_label = st.text_input("Seat Label (e.g., A, B)", key="seat_label")
            x = st.number_input("X Coordinate", min_value=0, value=25, key="x_coord")
            y = st.number_input("Y Coordinate", min_value=0, value=150, key="y_coord")
            width = st.number_input("Width", min_value=1, value=100, key="width")
            height = st.number_input("Height", min_value=1, value=100, key="height")
            submit_seat = st.form_submit_button("Add/Update Seat")

            if submit_seat:
                if not seat_label:
                    st.error("Seat label cannot be empty.")
                else:
                    st.session_state.seats[seat_label] = {
                        "region": (int(x), int(y), int(width), int(height)),
                        "occupied": False,
                        "start_time": None,
                        "accumulated_time": 0.0
                    }
                    st.success(f"Seat '{seat_label}' added/updated.")
                    st.rerun()

        with st.form("delete_seat_form"):
            st.write("Delete Seat")
            delete_label = st.text_input("Seat Label to Delete", key="delete_label")
            delete_seat = st.form_submit_button("Delete Seat")

            if delete_seat:
                if not delete_label:
                    st.error("Please enter a seat label to delete.")
                elif delete_label not in st.session_state.seats:
                    st.error(f"No seat found with label '{delete_label}'.")
                else:
                    del st.session_state.seats[delete_label]
                    st.success(f"Seat '{delete_label}' deleted.")
                    st.rerun()

        if st.session_state.seats:
            st.write("Current Seats:")
            for label, seat_data in st.session_state.seats.items():
                x, y, w, h = seat_data["region"]
                st.write(f"Seat {label}: (x={x}, y={y}, width={w}, height={h})")

        if st.session_state.seats:
            if st.button("Start Monitoring"):
                st.session_state.monitoring = True
                st.rerun()
        else:
            st.warning("Please add at least one seat before starting monitoring.")

    else:
        st.subheader("Step 3: Monitoring Seats")
        process_seat_updates()
        
        st.write("Current Seat Configuration:")
        for label, seat_data in st.session_state.seats.items():
            x, y, w, h = seat_data["region"]
            st.write(f"Seat {label}: (x={x}, y={y}, width={w}, height={h})")
            
        webrtc_ctx = webrtc_streamer(
            key="seat-monitoring",
            video_frame_callback=video_frame_callback,
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
            async_processing=True,
        )

        if st.session_state.seats:
            st.write("### Current Seat Status")
            for label, seat_data in st.session_state.seats.items():
                status = "Occupied" if seat_data.get("occupied", False) else "Empty"
                total_time = seat_data.get("accumulated_time", 0.0)
                if seat_data.get("occupied", False) and seat_data.get("start_time"):
                    total_time += time.time() - seat_data["start_time"]
                mm = int(total_time // 60)
                ss = int(total_time % 60)
                st.write(f"Seat {label}: {status} - Total time: {mm}:{ss:02d}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Stop Monitoring"):
                st.session_state.monitoring = False
                st.rerun()
        
        with col2:
            if st.button("Reset All Timers"):
                for seat_data in st.session_state.seats.values():
                    seat_data["accumulated_time"] = 0.0
                    seat_data["start_time"] = None
                    seat_data["occupied"] = False
                st.success("All timers reset.")
                st.rerun()
        
        with col3:
            csv_data = download_csv(st.session_state.seats)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"seat_occupancy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

def render():
    monitor_attendance()