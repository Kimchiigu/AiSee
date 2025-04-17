
# AiSee 🎓🤖

<p align="center">
  <img alt="AiSee Logo" title="AiSee" src="assets/aisee-logo.png" width="200">
</p>

<p align="center">
  AI-Powered Attendance & Cheating Detection System
</p>

---

# AiSee: Smart School System with AI + IoT 🎓🤖

AiSee is an intelligent school attendance system powered by **AI Computer Vision** and **IoT integration**, developed for **Samsung Innovation Campus Batch 6**. The application detects attendance through face recognition and verifies presence throughout the session, while also identifying potential **cheating behavior** through **object detection within boundary zones**.

---

## 🧭 Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Prerequisites](#prerequisites)
5. [How to Run the Full System (AI + IoT)](#how-to-run-the-full-system-ai--iot)
6. [Firebase & Cloudinary Setup](#firebase--cloudinary-setup)
7. [Contact](#contact)

---

## 📌 Project Overview

- **Name**: AiSee
- **Type**: AI + IoT Smart School System
- **Built For**: Samsung Innovation Campus Batch 6
- **Focus**: Facial recognition attendance, continuous verification, and cheating detection through object recognition
- **Modules**:
  - Real-time face registration and attendance verification
  - Object detection for cheating activity
  - Firebase integration for user data
  - Cloudinary for storing face image datasets
  - IoT camera integration for real-time exam surveillance

---

## 🔥 Features

- 📷 **Register Face**: Capture and store face images for user registration using real-time camera input.
- ✅ **Verify Face**: Authenticate users through facial recognition for secure attendance logging.
- 📊 **Attendance Monitoring**: Track and manage attendance records with continuous verification.
- 🕵️‍♂️ **Exam Supervisor**: Detect cheating behaviors using YOLO for object detection and HaarCascade for face detection within defined boundary zones.
- 🌐 **IoT Camera**: Upload images to Google Drive and send the link to the backend for cheating verification.

---

## ⚙️ Technology Stack

### 💡 Core Technologies

- **Python** — Backend logic and CV model integration
- **Streamlit** — Interactive web-based UI
- **OpenCV** — Face detection and cheating detection
- **Firebase** — Cloud database for user metadata
- **Cloudinary** — Cloud image storage
- **Flask** — Backend server for IoT camera to upload data
- **Arduino** — IoT firmware for image capture and HTTP POST

### 🧠 Computer Vision

- **Face Detection & Recognition**
- **YOLO / Haar Cascades / Custom Model** for cheating detection

---

## ✅ Prerequisites

Make sure these are installed on your machine:

- [Python 3.8+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Git](https://git-scm.com/)
- Cloudinary & Firebase credentials

Install required libraries:

```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run the Full System (AI + IoT)

### 1. Clone the Repository

```bash
git clone https://github.com/Kimchiigu/AiSee.git
cd aisee
```

### 2. Setup `secrets.toml`

Create a `.streamlit/secrets.toml` file and paste your credentials:

```toml
# Firebase configuration
FIREBASE_API_KEY = "your_firebase_api_key"
FIREBASE_AUTH_DOMAIN = "your_firebase_auth_domain"
FIREBASE_PROJECT_ID = "your_firebase_project_id"
FIREBASE_STORAGE_BUCKET = "your_firebase_storage_bucket"
FIREBASE_MESSAGING_SENDER_ID = "your_firebase_messaging_sender_id"
FIREBASE_APP_ID = "your_firebase_app_id"
FIREBASE_MEASUREMENT_ID = "your_firebase_measurement_id"

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = "your_cloudinary_cloud_name"
CLOUDINARY_API_KEY = "your_cloudinary_api_key"
CLOUDINARY_API_SECRET = "your_cloudinary_api_secret"

# Firebase service account
[FIREBASE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "your_project_id"
private_key_id = "your_private_key_id"
private_key = "your_private_key"
client_email = "your_client_email"
client_id = "your_client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your_client_x509_cert_url"
universe_domain = "googleapis.com"
```

### 3. Run the Streamlit Web App

```bash
streamlit run main.py
```

### 4. Run the Flask Server for IoT

In a separate terminal, run the Flask backend server to receive images from the IoT camera:

```bash
python flask-server.py
```

Make sure the endpoint in your `.ino` code matches this server IP.

### 5. Upload IoT Code to Microcontroller

- Open `iot_camera_uploader.ino` in Arduino IDE
- Plug in the ESP32-CAM or similar board
- Select the correct COM port
- Upload the sketch

You may need to install ESP32 board support via Arduino Board Manager.

### 6. Connect to Wi-Fi and Test

Once the IoT camera boots:

- It connects to Wi-Fi
- Takes snapshots at intervals
- Sends POST requests to your Flask server
- Flask server saves the image in uploaded_images

Done! 🎉

---

## ☁️ Firebase & Cloudinary Setup

### Firebase (Firestore + Auth)

- Go to [Firebase Console](https://console.firebase.google.com/)
- Create a project and enable Firestore Database
- Add a web app and get the configuration keys
- Enable Authentication → Email/Password
- Download the service account JSON and embed its contents in the `[FIREBASE_SERVICE_ACCOUNT]` section of `secrets.toml`

### Cloudinary

- Go to [Cloudinary](https://cloudinary.com/)
- Create an account and get your API Key, Secret, and Cloud Name
- Set them in the `secrets.toml` file as shown above

---

## 📬 Contact

Feel free to open issues or contact me if you need help setting it up!

> Made with 💙 for the Samsung Innovation Campus Batch 6
