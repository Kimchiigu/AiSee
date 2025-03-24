<h1 align="center"> AiSee 🎓🤖 </h1>

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
5. [How to Run Locally](#how-to-run-locally)
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

---

## 🔥 Features

- 📷 **Face Registration & Recognition**
- ✅ **Live Attendance Verification**
- 🎯 **Cheating Detection via Boundary Box**
- ☁️ **Cloud Storage for Images**
- 🔐 **Firebase Integration for User Management**
- 🌐 **Streamlit Web Interface**

---

## ⚙️ Technology Stack

### 💡 Core Technologies

- **Python** — Backend logic and CV model integration
- **Streamlit** — Interactive web-based UI
- **OpenCV** — Face detection and cheating detection
- **Firebase** — Cloud database for user metadata
- **Cloudinary** — Cloud image storage

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

## 🚀 How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/YourUsername/aisee.git
cd aisee
```

### 2. Setup `.env` File

Create a `.env` by copy the `.env.example` file at the root of the project with the following:

```env
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_STORAGE_BUCKET=
FIREBASE_MESSAGING_SENDER_ID=
FIREBASE_APP_ID=
FIREBASE_MEASUREMENT_ID=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### 3. Run the Streamlit App

```bash
streamlit run main.py
```

---

## ☁️ Firebase & Cloudinary Setup

### Firebase (Firestore + Auth)

- Go to [Firebase Console](https://console.firebase.google.com/)
- Create a project and enable Firestore Database
- Add a web app and get the configuration keys
- Enable Authentication → Email/Password

### Cloudinary

- Go to [Cloudinary](https://cloudinary.com/)
- Create an account and get your API Key, Secret, and Cloud Name
- Set them in the `.env` file as `CLOUDINARY_URL`

---

## 📬 Contact

Feel free to open issues or contact me if you need help setting it up!

> Made with 💙 for the Samsung Innovation Campus Batch 6
