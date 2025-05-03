import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import uuid

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["FIREBASE_SERVICE_ACCOUNT"].to_dict())
    initialize_app(cred)
db = firestore.client()

def render():
    role = st.session_state.get("role", "")
    if role not in ["admin", "teacher"]:
        st.warning("You do not have permission to access this page.")
        return

    st.header("📚 Create New Subject")

    # Form fields
    subject_name = st.text_input("Subject Name")
    semester = st.selectbox("Semester (optional)", ["", "1", "2", "3", "4", "5", "6", "7", "8"])
    grade = st.selectbox("Grade (optional)", ["", "10", "11", "12"])
    passing_score = st.number_input("Passing Score", min_value=0, max_value=100, value=75)
    weight = st.number_input("Subject Weight (e.g. 1.0, 2.5)", min_value=0.0, step=0.1, value=1.0)

    if st.button("Create Subject"):
        if not subject_name:
            st.warning("Please enter a subject name.")
            return

        if not semester and not grade:
            st.warning("Please select at least a semester or a grade.")
            return

        # Build data object
        subject_data = {
            "name": subject_name.lower(),
            "passingScore": passing_score,
            "weight": weight,
            "reportId": str(uuid.uuid4())
        }
        if semester:
            subject_data["semester"] = int(semester)
        if grade:
            subject_data["grade"] = int(grade)

        # Save to Firestore
        db.collection("subjects").add(subject_data)
        st.success(f"Subject '{subject_name}' added successfully!")
