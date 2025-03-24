import streamlit as st
from utils.auth import login_form
from modules import dashboard, face_attendance, camera_feeds, access_control, incident_reports, settings

st.set_page_config(
    page_title="AIsee",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load styles
with open("static/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.sidebar.markdown("# AIsee")
st.sidebar.markdown("---")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_form()
else:
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Face Attendance", "Camera Feeds", "Access Control", "Incident Reports", "Settings"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "Dashboard":
        dashboard.render()
    elif page == "Face Attendance":
        face_attendance.render()
    elif page == "Camera Feeds":
        camera_feeds.render()
    elif page == "Access Control":
        access_control.render()
    elif page == "Incident Reports":
        incident_reports.render()
    elif page == "Settings":
        settings.render()
