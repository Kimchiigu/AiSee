# flask_server.py
from flask import Flask, request
from datetime import datetime
import os
import glob

UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    image = request.data
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        f.write(image)

    cleanup_images()
    return "Image received", 200

def cleanup_images():
    images = sorted(glob.glob(os.path.join(UPLOAD_FOLDER, "*.jpg")), key=os.path.getmtime, reverse=True)
    if len(images) > 5:
        for img in images[5:]:
            os.remove(img)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)