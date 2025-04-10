import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import pandas as pd
import plotly.express as px  # Optional for interactive charts
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# --- Initialize Firebase with your existing configuration ---
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase-service-account.json"))
    initialize_app(cred)
db = firestore.client()

def render():

    # --- Fetch and Display Student Users ---
    st.subheader("Student Users")
    users_ref = db.collection("users")
    students = []
    try:
        docs = users_ref.where("role", "==", "student").get()
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            students.append(user_data)
    except Exception as e:
        st.error(f"Error fetching users: {e}")

    if students:
        df_students = pd.DataFrame(students)
        st.dataframe(df_students)
    else:
        st.info("No student users found.")

    # --- Fetch Data for Graphs ---
    st.subheader("Data Visualization")

    reports_data = []
    try:
        reports_ref = db.collection("reports").get()
        for doc in reports_ref:
            report = doc.to_dict()
            report['id'] = doc.id
            reports_data.append(report)
    except Exception as e:
        st.error(f"Error fetching reports: {e}")

    if reports_data:
        df_reports = pd.DataFrame(reports_data)
        # Example Graph: Distribution of Overall Scores
        fig_scores = px.histogram(df_reports, x="overallScore", title="Distribution of Overall Scores")
        st.plotly_chart(fig_scores)
    else:
        st.info("No report data available for visualization.")

    # --- CRUD Forms ---
    st.subheader("Insert New Data")

    with st.expander("Add New Report"):
        with st.form("add_report"):
            user_id = st.text_input("User ID")
            semester = st.text_input("Semester")
            overall_weight = st.number_input("Overall Weight", min_value=0)
            overall_score = st.number_input("Overall Score", min_value=0, max_value=100)
            submitted = st.form_submit_button("Add Report")
            if submitted:
                try:
                    db.collection("reports").document(f"{user_id}_{semester}").set({
                        "userId": user_id,
                        "semester": semester,
                        "overallWeight": overall_weight,
                        "overallScore": overall_score,
                    })
                    st.success("Report added successfully!")
                except Exception as e:
                    st.error(f"Error adding report: {e}")

    with st.expander("Add New Subject"):
        with st.form("add_subject"):
            report_id = st.text_input("Report ID (e.g., user123_semester-1)")
            subject_name = st.text_input("Subject Name")
            passing_score = st.number_input("Passing Score", min_value=0, max_value=100)
            weight = st.number_input("Weight", min_value=0)
            is_pass = st.checkbox("Is Passing")
            submitted = st.form_submit_button("Add Subject")
            if submitted:
                try:
                    db.collection("subjects").document(f"{report_id}_{subject_name.lower().replace(' ', '_')}").set({
                        "reportId": report_id,
                        "name": subject_name,
                        "passingScore": passing_score,
                        "weight": weight,
                        "isPass": is_pass,
                    })
                    st.success("Subject added successfully!")
                except Exception as e:
                    st.error(f"Error adding subject: {e}")

    with st.expander("Add New Assignment"):
        with st.form("add_assignment"):
            subject_id = st.text_input("Subject ID (e.g., user123_semester-1_math)")
            weight = st.number_input("Weight", min_value=0)
            scores_str = st.text_input("Scores (comma-separated)")
            submitted = st.form_submit_button("Add Assignment")
            if submitted:
                try:
                    scores = [int(s.strip()) for s in scores_str.split(',')]
                    db.collection("assignments").document(f"{subject_id}_assignment{len(scores)}").set({
                        "subjectId": subject_id,
                        "weight": weight,
                        "scores": scores,
                    })
                    st.success("Assignment added successfully!")
                except Exception as e:
                    st.error(f"Error adding assignment: {e}")

    with st.expander("Add New Mid-Exam"):
        with st.form("add_mid_exam"):
            subject_id = st.text_input("Subject ID (e.g., user123_semester-1_math)")
            weight = st.number_input("Weight", min_value=0)
            score = st.number_input("Score", min_value=0, max_value=100)
            submitted = st.form_submit_button("Add Mid-Exam")
            if submitted:
                try:
                    db.collection("midExams").document(f"{subject_id}_midterm").set({
                        "subjectId": subject_id,
                        "weight": weight,
                        "score": score,
                    })
                    st.success("Mid-Exam added successfully!")
                except Exception as e:
                    st.error(f"Error adding mid-exam: {e}")

    with st.expander("Add New Final Exam"):
        with st.form("add_final_exam"):
            subject_id = st.text_input("Subject ID (e.g., user123_semester-1_math)")
            weight = st.number_input("Weight", min_value=0)
            score = st.number_input("Score", min_value=0, max_value=100)
            submitted = st.form_submit_button("Add Final Exam")
            if submitted:
                try:
                    db.collection("finalExams").document(f"{subject_id}_final").set({
                        "subjectId": subject_id,
                        "weight": weight,
                        "score": score,
                    })
                    st.success("Final Exam added successfully!")
                except Exception as e:
                    st.error(f"Error adding final exam: {e}")

    with st.expander("Add New Attendance"):
        with st.form("add_attendance"):
            user_id = st.text_input("User ID")
            semester = st.text_input("Semester")
            subject = st.text_input("Subject Name")
            minimum = st.number_input("Minimum Attendance", min_value=0)
            maximum = st.number_input("Maximum Attendance", min_value=0)
            is_pass = st.checkbox("Is Attendance Passing")
            submitted = st.form_submit_button("Add Attendance")
            if submitted:
                try:
                    db.collection("attendance").document(f"{user_id}_{semester}_{subject.lower().replace(' ', '_')}").set({
                        "userId": user_id,
                        "semester": semester,
                        "subject": subject,
                        "minimum": minimum,
                        "maximum": maximum,
                        "isPass": is_pass,
                    })
                    st.success("Attendance details added successfully!")
                except Exception as e:
                    st.error(f"Error adding attendance details: {e}")