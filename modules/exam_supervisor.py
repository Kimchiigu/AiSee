import streamlit as st
import cv2
import numpy as np
import time
import pandas as pd
from PIL import Image
from model.exam.exam import load_model

model = load_model()

# Global seat config
if "seats" not in st.session_state:
    st.session_state.seats = {
        "A": {"region": (25, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
        "B": {"region": (175, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
        "C": {"region": (325, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
        "D": {"region": (475, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
    }

if "stop_monitor" not in st.session_state:
    st.session_state.stop_monitor = False

def is_person_in_seat(person_box, seat_region):
    px, py, pw, ph = person_box
    cx = px + pw / 2.0
    cy = py + ph / 2.0
    sx, sy, sw, sh = seat_region
    return (sx <= cx <= sx + sw) and (sy <= cy <= sy + sh)

def show_camera_for_seat_setup():
    st.subheader("🎥 Live Camera (No Detection)")
    cap = cv2.VideoCapture(0)
    placeholder = st.empty()

    if not cap.isOpened():
        st.error("Unable to access camera")
        return

    stop_cam = st.button("⏹️ Stop Camera", key="stop_camera_btn")
    while cap.isOpened() and not st.session_state.stop_monitor:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw seat boxes
        for label, seat in st.session_state.seats.items():
            sx, sy, sw, sh = seat["region"]
            cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh), (0, 255, 255), 2)
            cv2.putText(frame, label, (sx, sy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        placeholder.image(frame_rgb, channels="RGB")

        if stop_cam:
            st.session_state.stop_monitor = True
            break

    cap.release()
    st.session_state.stop_monitor = False

def start_monitoring():
    st.subheader("📹 Monitoring Started")
    cap = cv2.VideoCapture(0)
    placeholder = st.empty()

    if not cap.isOpened():
        st.error("Unable to access camera")
        return

    stop_button = st.button("⏹️ Stop Monitoring", key="stop_button")
    while cap.isOpened() and not st.session_state.stop_monitor:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        persons = []
        if len(results) > 0:
            for box in results[0].boxes:
                if int(box.cls[0]) == 0:  # person
                    xyxy = box.xyxy[0].cpu().numpy()
                    x_min, y_min, x_max, y_max = map(int, xyxy)
                    persons.append((x_min, y_min, x_max - x_min, y_max - y_min))

        for label, seat in st.session_state.seats.items():
            sx, sy, sw, sh = seat["region"]
            occupied_now = any(is_person_in_seat(p, (sx, sy, sw, sh)) for p in persons)

            if occupied_now and not seat["occupied"]:
                seat["start_time"] = time.time()
                seat["occupied"] = True
            elif not occupied_now and seat["occupied"]:
                elapsed = time.time() - seat["start_time"]
                seat["accumulated_time"] += elapsed
                seat["start_time"] = None
                seat["occupied"] = False

            color = (0, 255, 0) if seat["occupied"] else (0, 0, 255)
            cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh), color, 2)
            cv2.putText(frame, f"{label} {int(seat['accumulated_time'])}s", (sx, sy - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        placeholder.image(frame_rgb, channels="RGB")

        if stop_button:
            st.session_state.stop_monitor = True
            break

    cap.release()
    st.success("Monitoring stopped.")
    st.session_state.stop_monitor = False

def render():
    st.title("🪑 Exam Seat Monitoring")

    # ---- SEAT CONFIGURATION ----
    with st.expander("🛠️ Configure Seats"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ➕ Add/Update Seat")
            label = st.text_input("Seat Label")
            x = st.number_input("X", value=0)
            y = st.number_input("Y", value=0)
            w = st.number_input("Width", value=100)
            h = st.number_input("Height", value=100)
            if st.button("Add / Update Seat", key="add_seat"):
                st.session_state.seats[label] = {
                    "region": (int(x), int(y), int(w), int(h)),
                    "occupied": False, "start_time": None, "accumulated_time": 0.0
                }
                st.success(f"Seat '{label}' added or updated")

        with col2:
            st.markdown("### ❌ Delete Seat")
            if st.session_state.seats:
                to_delete = st.selectbox("Select seat to delete", list(st.session_state.seats.keys()))
                if st.button("Delete Seat", key="delete_seat"):
                    st.session_state.seats.pop(to_delete, None)
                    st.success(f"Seat '{to_delete}' deleted")
            else:
                st.info("No seat to delete.")

    st.markdown("---")

    # ---- BUTTONS ----
    cam_only = st.button("📷 Show Camera Only (for seat setting)")
    monitor = st.button("▶️ Start Monitoring")

    if cam_only:
        show_camera_for_seat_setup()

    if monitor:
        start_monitoring()

    # ---- EXPORT ----
    st.markdown("---")
    if st.button("📄 Export to CSV"):
        data = []
        for label, seat in st.session_state.seats.items():
            total_time = seat["accumulated_time"]
            if seat["occupied"] and seat["start_time"]:
                total_time += time.time() - seat["start_time"]
            data.append({"Seat": label, "Accumulated Time (s)": round(total_time, 2)})
        df = pd.DataFrame(data)
        st.download_button("⬇️ Download CSV", data=df.to_csv(index=False),
                           file_name="seat_occupancy.csv", mime="text/csv")
