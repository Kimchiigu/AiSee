import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import time
import csv
from ultralytics import YOLO
from PIL import Image, ImageTk

class SeatOccupancyApp:
    def __init__(self, root, model_path="yolov9m.pt", camera_index=0):
        self.root = root
        self.root.title("Seat Occupancy Tracking")
        self.model = YOLO(model_path)
        print("Model class names:", self.model.names)
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera or video source!")
            self.root.destroy()
            return
        self.seats = {
            "A": {"region": (25, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
            "B": {"region": (175, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
            "C": {"region": (325, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0},
            "D": {"region": (475, 150, 100, 100), "occupied": False, "start_time": None, "accumulated_time": 0.0}
        }
        self.create_widgets()
        self.update_frame()

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack()
        self.right_frame = tk.Frame(self.main_frame, width=200)
        self.right_frame.pack(side="right", fill="y")
        self.reset_button = ttk.Button(self.right_frame, text="Reset All Timer", command=self.reset_all_timers)
        self.reset_button.pack(pady=10, fill="x")
        self.csv_button = ttk.Button(self.right_frame, text="Download CSV", command=self.download_csv)
        self.csv_button.pack(pady=10, fill="x")
        self.change_region_button = ttk.Button(self.right_frame, text="Change Region", command=self.open_region_popup)
        self.change_region_button.pack(pady=10, fill="x")

    def reset_all_timers(self):
        for seat_data in self.seats.values():
            seat_data["accumulated_time"] = 0.0
            seat_data["start_time"] = None
            seat_data["occupied"] = False

    def download_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Seat Data"
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Seat Label,Accumulated Time (s)\n")
            for label, seat_data in self.seats.items():
                total_time = seat_data["accumulated_time"]
                if seat_data["occupied"] and seat_data["start_time"]:
                    total_time += time.time() - seat_data["start_time"]
                f.write(f"{label},{total_time:.2f}\n")
        messagebox.showinfo("CSV Downloaded", f"Data saved to {file_path}.")

    def open_region_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add/Change Seat Region")
        tk.Label(popup, text="Seat Label:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        label_entry = tk.Entry(popup)
        label_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(popup, text="X:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        x_entry = tk.Entry(popup)
        x_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(popup, text="Y:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        y_entry = tk.Entry(popup)
        y_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(popup, text="Width:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        w_entry = tk.Entry(popup)
        w_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(popup, text="Height:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        h_entry = tk.Entry(popup)
        h_entry.grid(row=4, column=1, padx=5, pady=5)

        def add_seat():
            seat_label = label_entry.get().strip()
            if not seat_label:
                messagebox.showerror("Error", "Seat label cannot be empty.")
                return
            try:
                sx = int(x_entry.get())
                sy = int(y_entry.get())
                sw = int(w_entry.get())
                sh = int(h_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Coordinates must be integers.")
                return
            if seat_label in self.seats:
                messagebox.showwarning("Warning", f"Seat '{seat_label}' already exists. Overwriting it.")
            self.seats[seat_label] = {
                "region": (sx, sy, sw, sh),
                "occupied": False,
                "start_time": None,
                "accumulated_time": 0.0
            }
            messagebox.showinfo("Success", f"Seat '{seat_label}' added/updated.")
            popup.destroy()

        add_btn = ttk.Button(popup, text="Add/Update Seat", command=add_seat)
        add_btn.grid(row=5, column=0, columnspan=2, pady=10)
        tk.Label(popup, text="Seat Label to Delete:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        delete_label_entry = tk.Entry(popup)
        delete_label_entry.grid(row=6, column=1, padx=5, pady=5)

        def delete_seat():
            seat_label_to_delete = delete_label_entry.get().strip()
            if not seat_label_to_delete:
                messagebox.showerror("Error", "Please enter a seat label to delete.")
                return
            if seat_label_to_delete in self.seats:
                del self.seats[seat_label_to_delete]
                messagebox.showinfo("Success", f"Seat '{seat_label_to_delete}' deleted.")
                popup.destroy()
            else:
                messagebox.showerror("Error", f"No seat found with label '{seat_label_to_delete}'.")

        delete_btn = ttk.Button(popup, text="Delete Seat", command=delete_seat)
        delete_btn.grid(row=7, column=0, columnspan=2, pady=10)

    def is_person_in_seat(self, person_box, seat_region):
        px, py, pw, ph = person_box
        cx = px + pw / 2.0
        cy = py + ph / 2.0
        sx, sy, sw, sh = seat_region
        return (sx <= cx <= sx + sw) and (sy <= cy <= sy + sh)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.video_label.config(text="No video frame available.")
            return
        results = self.model(frame)
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
                if cls == 0 and conf > 0.7:
                    person_detections.append({
                        "box": (x_min, y_min, w, h),
                        "conf": conf
                    })
                else:
                    print(f"Ignored detection: class={self.model.names[cls]}, conf={conf}")
        for seat_label, seat_data in self.seats.items():
            seat_region = seat_data["region"]
            seat_occupied_now = False
            for det in person_detections:
                if self.is_person_in_seat(det["box"], seat_region):
                    seat_occupied_now = True
                    break
            if seat_occupied_now and not seat_data["occupied"]:
                seat_data["occupied"] = True
                seat_data["start_time"] = time.time()
            elif not seat_occupied_now and seat_data["occupied"]:
                elapsed = time.time() - seat_data["start_time"]
                seat_data["accumulated_time"] += elapsed
                seat_data["start_time"] = None
                seat_data["occupied"] = False
        for seat_label, seat_data in self.seats.items():
            sx, sy, sw, sh = seat_data["region"]
            color = (0, 255, 0) if seat_data["occupied"] else (0, 0, 255)
            cv2.rectangle(frame, (int(sx), int(sy)), (int(sx + sw), int(sy + sh)), color, 2)
            cv2.putText(frame, seat_label, (int(sx), int(sy) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            if seat_data["occupied"] and seat_data["start_time"] is not None:
                current_duration = time.time() - seat_data["start_time"]
                total_duration = seat_data["accumulated_time"] + current_duration
            else:
                total_duration = seat_data["accumulated_time"]
            mm = int(total_duration // 60)
            ss = int(total_duration % 60)
            duration_text = f"{mm}:{ss:02d}"
            cv2.putText(frame, duration_text, (int(sx), int(sy + sh + 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        persons_inside_seats = []
        for det in person_detections:
            for seat_data in self.seats.values():
                if self.is_person_in_seat(det["box"], seat_data["region"]):
                    persons_inside_seats.append(det)
                    break
        for idx, det in enumerate(persons_inside_seats, start=1):
            print(f"Drawing person_{idx} at {det['box']}")
            (x_min, y_min, w_box, h_box) = det["box"]
            conf = det["conf"]
            x_max = x_min + w_box
            y_max = y_min + h_box
            cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (255, 0, 0), 2)
            label = f"person_{idx} [{conf:.2f}]"
            cv2.putText(frame, label, (int(x_min), int(y_min) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        print("Frame shape:", rgb_frame.shape, "Sample pixel:", rgb_frame[0, 0])
        pil_img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=pil_img)
        self.video_label.imgtk = imgtk 
        self.video_label.configure(image=imgtk)
        self.root.after(10, self.update_frame)

def main():
    root = tk.Tk()
    app = SeatOccupancyApp(root, model_path="yolov9m.pt", camera_index=0)
    root.mainloop()

if __name__ == "__main__":
    main()