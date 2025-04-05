import streamlit as st
import os
from datetime import datetime
import glob
from flask import Flask, request
import threading
import requests
import time

IMGUR_CLIENT_ID = "482770ca658ef76"
UBIDOTS_TOKEN = "BBUS-cstt1Eo2ShorZrikxa0zy27es1vstF"
DEVICE_LABEL = "esp32"
VARIABLE_LABEL = "image"

# Folder to store images
UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Start Flask app in a background thread only once
if "flask_started" not in st.session_state:
    st.session_state.flask_started = True

    app = Flask(__name__)

    @app.route("/upload", methods=["POST"])
    def upload():
        image = request.data  # Receive raw image data from ESP32-CAM
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as f:
            f.write(image)

        cleanup_images()
        return "Image received", 200

    def start_flask():
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    threading.Thread(target=start_flask, daemon=True).start()

def cleanup_images():
    """Keep only the latest 5 images."""
    images = sorted(glob.glob(os.path.join(UPLOAD_FOLDER, "*.jpg")), key=os.path.getmtime, reverse=True)
    if len(images) > 5:
        for img in images[5:]:  # Keep the latest 5 images, delete the rest
            os.remove(img)

def upload_to_imgur(image_path):
    """Uploads an image to Imgur and returns the direct URL."""
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    with open(image_path, "rb") as img:
        response = requests.post("https://api.imgur.com/3/image", headers=headers, files={"image": img})
    
    if response.status_code == 200:
        return response.json()["data"]["link"]  # Direct image URL
    else:
        st.error(f"Imgur Upload Failed: {response.text}")
        return None

def send_to_ubidots(image_url):
    """Sends the image URL to Ubidots."""
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    data = {
        VARIABLE_LABEL: {
            "value": 1,  # Dummy value (Ubidots requires a number)
            "context": {"url": image_url}  # Store the image URL here
        }
    }

    response = requests.post(url, json=data, headers=headers)
    # st.write("Ubidots Response:", response.json())

def get_latest_image():
    """Returns the latest image file path."""
    images = sorted(glob.glob(os.path.join(UPLOAD_FOLDER, "*.jpg")), key=os.path.getmtime, reverse=True)
    return images[0] if images else None

st.title("ESP32-CAM Image Receiver")
placeholder = st.empty()

if st.button("Check for New Image"):
    latest_image = get_latest_image()
    
    if latest_image:
        image_url = upload_to_imgur(latest_image)
        
        if image_url:
            send_to_ubidots(image_url)
            placeholder.image(latest_image, caption="Latest Received Image", use_container_width=True)
    else:
        st.warning("No images received yet!")