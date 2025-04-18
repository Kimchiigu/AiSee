import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import cv2
import numpy as np
import os
import time
import csv
from ultralytics import YOLO
from datetime import datetime
from io import StringIO
import av

@st.cache_resource
def load_model():
    model_path = "model/monitoring/yolov9m.pt"
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
            if seat_data.get("occupied", False) and seat_data.get("start_time") is not None:
                current_duration = time.time() - seat_data["start_time"]
                total_duration = seat_data.get("accumulated_time", 0.0) + current_duration
            else:
                total_duration = seat_data.get("accumulated_time", 0.0)
            mm = int(total_duration // 60)
            ss = int(total_duration % 60)
            duration_text = f"{mm}:{ss:02d}"
            cv2.putText(frame_copy, duration_text, (sx, sy + sh + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame_copy

def is_person_in_seat(person_box, seat_region):
    px, py, pw, ph = person_box
    cx = px + pw / 2.0
    cy = py + ph / 2.0
    sx, sy, sw, sh = seat_region
    return (sx <= cx <= sx + sw) and (sy <= cy <= sy + sh)

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

class SeatMonitoringTransformer(VideoTransformerBase):
    def __init__(self):
        self.model = load_model()
        self.frame_count = 0
        self.last_frame = None
        self.last_processed_frame = None
        self.person_count = 0  # Track number of detected persons

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.last_frame = rgb_img

        # Always draw seats on the frame
        seats = st.session_state.get("seats", {})
        frame_with_seats = draw_seats(rgb_img, seats)

        # Process every 5th frame to reduce CPU load, unless monitoring
        self.frame_count += 1
        if self.frame_count % 5 != 0 and not st.session_state.get("monitoring", False):
            return cv2.cvtColor(frame_with_seats, cv2.COLOR_RGB2BGR)

        # Run person detection in monitoring mode
        if st.session_state.get("monitoring", False):
            results = self.model(rgb_img, conf=0.3)  # Lowered confidence for better detection
            person_detections = []

            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    x_min, y_min, x_max, y_max = xyxy
                    w = x_max - x_min
                    h = y_max - y_min
                    if cls == 0:  # Person class
                        person_detections.append({
                            "box": (int(x_min), int(y_min), int(w), int(h)),
                            "conf": conf
                        })

            self.person_count = len(person_detections)  # Update person count

            # Update seat occupancy
            for seat_label, seat_data in seats.items():
                seat_region = seat_data["region"]
                seat_occupied_now = False
                for det in person_detections:
                    if is_person_in_seat(det["box"], seat_region):
                        seat_occupied_now = True
                        break

                if seat_occupied_now and not seat_data["occupied"]:
                    seat_data["occupied"] = True
                    seat_data["start_time"] = time.time()
                elif not seat_occupied_now and seat_data["occupied"]:
                    elapsed = time.time() - seat_data["start_time"]
                    seat_data["accumulated_time"] = seat_data.get("accumulated_time", 0.0) + elapsed
                    seat_data["start_time"] = None
                    seat_data["occupied"] = False

            # Draw all elements on the frame
            final_frame = frame_with_seats.copy()

            # Draw person detections
            for det in person_detections:
                x_min, y_min, w_box, h_box = det["box"]
                x_max = x_min + w_box
                y_max = y_min + h_box
                cv2.rectangle(final_frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)),
                             (0, 0, 255), 2)
                label = f"person [{det['conf']:.2f}]"
                cv2.putText(final_frame, label, (int(x_min), int(y_min) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            self.last_processed_frame = final_frame
            return cv2.cvtColor(final_frame, cv2.COLOR_RGB2BGR)

        return cv2.cvtColor(frame_with_seats, cv2.COLOR_RGB2BGR)

def monitor_attendance():
    st.title("Seat Occupancy Monitoring")
    st.write("Configure seat regions and monitor student presence.")
    st.info("When start camera, click the play button to avoid connection error")

    if "seats" not in st.session_state:
        st.session_state.seats = {}
    if "snapshot" not in st.session_state:
        st.session_state.snapshot = None
    if "monitoring" not in st.session_state:
        st.session_state.monitoring = False

    if st.session_state.snapshot is None:
        st.subheader("Step 1: Capture Snapshot")
        
        ctx = webrtc_streamer(
            key="snapshot-capture",
            video_transformer_factory=SeatMonitoringTransformer,
            async_transform=True,
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480}}, "audio": False},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

        if st.button("Capture Snapshot"):
            if ctx.video_transformer and ctx.video_transformer.last_frame is not None:
                st.session_state.snapshot = ctx.video_transformer.last_frame
                st.success("Snapshot captured! Proceed to configure seats.")
                st.rerun()
            else:
                st.error("No frame available to capture. Please ensure the camera is working.")

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
        
        # Display current seat configuration
        st.write("Current Seat Configuration:")
        for label, seat_data in st.session_state.seats.items():
            x, y, w, h = seat_data["region"]
            st.write(f"Seat {label}: (x={x}, y={y}, width={w}, height={h})")
            
        ctx = webrtc_streamer(
            key="seat-monitoring",
            video_transformer_factory=SeatMonitoringTransformer,
            async_transform=True,
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480}}, "audio": False},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

        # Display debugging info
        if ctx.video_transformer:
            st.write(f"Number of Persons Detected: {ctx.video_transformer.person_count}")

        # Show current seat status
        if st.session_state.seats:
            st.write("### Current Seat Status")
            for label, seat_data in st.session_state.seats.items():
                status = "Occupied" if seat_data.get("occupied", False) else "Empty"
                total_time = seat_data.get("accumulated_time", 0.0)
                if seat_data.get("occupied", False) and seat_data.get("start_time") is not None:
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
            reset_button = st.button("Reset All Timers")
            if reset_button:
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