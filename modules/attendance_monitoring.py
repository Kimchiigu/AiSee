import streamlit as st
import cv2
import numpy as np
import os
import time
import csv
from ultralytics import YOLO
from datetime import datetime
from io import BytesIO

# Cache model seperti exam_supervisor.py
@st.cache_resource
def load_model():
    model_path = "model/monitoring/yolov9m.pt"  # Ganti dengan path model YOLO Anda
    if not os.path.exists(model_path):
        st.error(f"Model file not found at {model_path}.")
        st.stop()
    return YOLO(model_path)

### Helper Functions (Disesuaikan dengan exam_supervisor.py) ###
def open_camera():
    """Open the default webcam, mirip exam_supervisor.py."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Error: Could not open webcam. Ensure your webcam is connected.")
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def read_frame(cap):
    """Read a frame from the camera, mirip exam_supervisor.py."""
    if cap is None or not cap.isOpened():
        return False, None
    ret, frame = cap.read()
    if not ret:
        return False, None
    return True, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def release_camera(cap):
    """Release the camera, mirip exam_supervisor.py."""
    if cap is not None and cap.isOpened():
        cap.release()

def draw_seats(frame, seats):
    """Draw seat bounding boxes and labels, tambahan untuk attendance."""
    frame_copy = frame.copy()
    for label, seat_data in seats.items():
        sx, sy, sw, sh = seat_data["region"]
        color = (0, 255, 0) if seat_data.get("occupied", False) else (0, 0, 255)
        cv2.rectangle(frame_copy, (sx, sy), (sx + sw, sy + sh), color, 2)
        cv2.putText(frame_copy, label, (sx, sy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw duration if monitoring
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
    """Check if a person's center is within a seat region."""
    px, py, pw, ph = person_box
    cx = px + pw / 2.0
    cy = py + ph / 2.0
    sx, sy, sw, sh = seat_region
    return (sx <= cx <= sx + sw) and (sy <= cy <= sy + sh)

def download_csv(seats):
    """Generate and download seat data as CSV."""
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(["Seat Label", "Accumulated Time (s)"])
    for label, seat_data in seats.items():
        total_time = seat_data.get("accumulated_time", 0.0)
        if seat_data.get("occupied", False) and seat_data.get("start_time"):
            total_time += time.time() - seat_data["start_time"]
        writer.writerow([label, f"{total_time:.2f}"])
    output.seek(0)
    return output

### Main Function ###
def monitor_attendance():
    st.title("Seat Occupancy Monitoring")
    st.write("Configure seat regions and monitor student presence.")

    model = load_model()

    # Inisialisasi session state
    if "seats" not in st.session_state:
        st.session_state.seats = {}
    if "snapshot" not in st.session_state:
        st.session_state.snapshot = None
    if "monitoring" not in st.session_state:
        st.session_state.monitoring = False
    if "run" not in st.session_state:
        st.session_state.run = False

    # Step 1: Capture Snapshot
    if st.session_state.snapshot is None:
        st.subheader("Step 1: Capture Snapshot")
        frame_placeholder = st.empty()

        start_button = st.button("Start Webcam")
        stop_button = st.button("Stop Webcam")
        capture_button = st.button("Capture Snapshot")

        if start_button:
            st.session_state.run = True

        if stop_button:
            st.session_state.run = False
            frame_placeholder.empty()

        if capture_button:
            cap = open_camera()
            if cap:
                ret, frame = read_frame(cap)
                if ret:
                    st.session_state.snapshot = frame
                    st.session_state.run = False
                    release_camera(cap)
                    st.success("Snapshot captured! Proceed to configure seats.")
                    st.rerun()
                release_camera(cap)
            else:
                st.error("Failed to capture snapshot.")

        if st.session_state.run:
            cap = open_camera()
            if cap:
                while st.session_state.run:
                    ret, frame = read_frame(cap)
                    if not ret:
                        st.error("Error: Could not read frame from webcam.")
                        break
                    frame_placeholder.image(frame, channels="RGB", caption="Live Feed", use_container_width=True)
                    time.sleep(0.05)  # Jeda seperti exam_supervisor.py
                    if not st.session_state.run:
                        break
                release_camera(cap)
            else:
                st.session_state.run = False

    # Step 2: Configure Seats
    elif not st.session_state.monitoring:
        st.subheader("Step 2: Configure Seat Regions")
        snapshot_placeholder = st.empty()
        
        if st.session_state.snapshot is not None:
            height, width, _ = st.session_state.snapshot.shape
            st.write(f"Snapshot Size: {width}x{height} pixels")
            frame_with_seats = draw_seats(st.session_state.snapshot, st.session_state.seats)
            snapshot_placeholder.image(frame_with_seats, channels="RGB", caption="Configure Seat Regions", use_container_width=True)

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
                st.session_state.run = False
                st.rerun()
        else:
            st.warning("Please add at least one seat before starting monitoring.")

    # Step 3: Monitor Seats
    else:
        st.subheader("Step 3: Monitoring Seats")
        frame_placeholder = st.empty()

        start_button = st.button("Start Webcam")
        stop_button = st.button("Stop Webcam")
        reset_button = st.button("Reset All Timers")
        download_button = st.button("Download CSV")

        if start_button:
            st.session_state.run = True

        if stop_button:
            st.session_state.run = False
            frame_placeholder.empty()

        if reset_button:
            for seat_data in st.session_state.seats.values():
                seat_data["accumulated_time"] = 0.0
                seat_data["start_time"] = None
                seat_data["occupied"] = False
            st.success("All timers reset.")
            st.rerun()

        if download_button:
            csv_data = download_csv(st.session_state.seats)
            st.download_button(
                label="Download Seat Data",
                data=csv_data,
                file_name=f"seat_occupancy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        if st.session_state.run:
            cap = open_camera()
            if cap:
                while st.session_state.run:
                    ret, frame = read_frame(cap)
                    if not ret:
                        st.error("Error: Could not read frame from webcam.")
                        break

                    # Run YOLO inference
                    results = model(frame, conf=0.5)  # Mirip exam_supervisor.py
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
                            if cls == 0:  # Class 0 => person
                                person_detections.append({
                                    "box": (x_min, y_min, w, h),
                                    "conf": conf
                                })

                    # Check occupancy
                    for seat_label, seat_data in st.session_state.seats.items():
                        seat_region = seat_data["region"]
                        seat_occupied_now = False
                        for det in person_detections:
                            if is_person_in_seat(det["box"], seat_region):
                                seat_occupied_now = True
                                break

                        # Time tracking
                        if seat_occupied_now and not seat_data["occupied"]:
                            seat_data["occupied"] = True
                            seat_data["start_time"] = time.time()
                        elif not seat_occupied_now and seat_data["occupied"]:
                            elapsed = time.time() - seat_data["start_time"]
                            seat_data["accumulated_time"] += elapsed
                            seat_data["start_time"] = None
                            seat_data["occupied"] = False

                    # Draw seats and YOLO boxes
                    frame_with_seats = draw_seats(frame, st.session_state.seats)
                    annotated_frame = results[0].plot()  # Gunakan YOLO plot seperti exam_supervisor.py
                    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    # Gabungkan seat boxes ke YOLO frame
                    final_frame = np.where(frame_with_seats != frame, frame_with_seats, annotated_frame_rgb)

                    frame_placeholder.image(final_frame, channels="RGB", caption="Monitoring Seats", use_container_width=True)
                    time.sleep(0.05)  # Jeda seperti exam_supervisor.py

                    if not st.session_state.run:
                        break
                release_camera(cap)
            else:
                st.session_state.run = False

### Render Function ###
def render():
    monitor_attendance()
