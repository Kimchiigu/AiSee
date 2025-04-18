import streamlit as st
from utils.auth import login_form
from modules import face_registration, face_verification, attendance_monitoring, exam_supervisor

st.set_page_config(
    page_title="AIsee - Intelligent Student Monitoring",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/youraisseproject',
        'Report a bug': "https://github.com/youraisseproject/issues",
        'About': "# AIsee\nAn intelligent student monitoring system"
    }
)

def load_css():
    with open("static/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        /* Main content area */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Sidebar improvements */
        [data-testid="stSidebar"] {
            color: white;
        }
        
        /* Sidebar header */
        .sidebar .sidebar-content {
            background: transparent;
        }
        
        /* Button styling */
        .stButton>button {
            border: 1px solid #4b6cb7;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
            width: 100%;
            margin-bottom: 0.5rem;
        }
        
        .stButton>button:hover {
            background-color: #4b6cb7;
            color: white;
        }
        
        /* Active button */
        .stButton>button:focus:not(:active) {
            background-color: #3a56a5;
            color: white;
        }
        
        /* Logout button */
        .logout-btn>button {
            background-color: #ff4b4b;
            color: white;
            border: none;
        }
        
        .logout-btn>button:hover {
            background-color: #ff3030;
        }
        
        /* Divider */
        .sidebar-divider {
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            margin: 1rem 0;
        }
        
        /* Navigation header */
        .nav-header {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def render_sidebar():
    st.sidebar.markdown("# 👁️ AIsee")
    st.sidebar.markdown("**Intelligent Student Monitoring System**")
    st.sidebar.markdown("**Login With admin:admin1234**")
    st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.sidebar.markdown(f"### Welcome, {st.session_state.get('username', 'Admin')}")
        st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.sidebar.markdown('<p class="nav-header">Navigation</p>', unsafe_allow_html=True)
        
        nav_options = {
            "Face Registration": "📸",
            "Face Verification": "👤",
            "Attendance Monitoring": "✅",
            "Exam Supervisor": "📝",
        }
        
        for page_name, icon in nav_options.items():
            if st.sidebar.button(f"{icon} {page_name}"):
                st.session_state.page = page_name
        
        st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.sidebar.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "Dashboard" 
            st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

def render_main():
    if not st.session_state.logged_in:
        login_form()
    else:
        page = st.session_state.page
        if page == "Face Registration":
            face_registration.render()
        elif page == "Face Verification":
            face_verification.render()
        elif page == "Attendance Monitoring":
            attendance_monitoring.render()
        elif page == "Exam Supervisor":
            exam_supervisor.render()

render_sidebar()
render_main()
