import streamlit as st
import pandas as pd

def render():
    st.markdown("<h1 class='main-header'>System Settings</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["General", "Notifications", "Backup & Restore", "User Accounts"])
        
    with tab1:
        st.markdown("<h2 class='sub-header'>General Settings</h2>", unsafe_allow_html=True)

        st.text_input("System Name", "School Security System")
        st.text_input("Institution Name", "Springfield High School")
        st.text_area("System Description", "Comprehensive security management system for Springfield High School")

        st.selectbox("Time Zone", ["UTC", "EST (UTC-5)", "CST (UTC-6)", "MST (UTC-7)", "PST (UTC-8)"])
        st.checkbox("Use 24-hour format")

        st.selectbox("Default Dashboard View", ["Overview", "Camera Feeds", "Access Control"])
        st.slider("Data Refresh Rate (seconds)", 5, 60, 15)
            
        st.button("Save General Settings")
        
    with tab2:
        st.markdown("<h2 class='sub-header'>Notification Settings</h2>", unsafe_allow_html=True)

        st.markdown("### Email Notifications")
        st.text_input("Email Server")
        st.text_input("Email Username")
        st.text_input("Email Password", type="password")
        st.text_input("Sender Email")
        st.text_input("Recipients (comma separated)")

        st.markdown("### Notification Triggers")
        st.checkbox("Security Breaches")
        st.checkbox("Unauthorized Access Attempts")
        st.checkbox("System Failures")
        st.checkbox("Camera Offline Events")
        st.checkbox("Door Held Open Alerts")

        st.markdown("### SMS Notifications")
        st.checkbox("Enable SMS Notifications")
        st.text_input("SMS Gateway")
        st.text_input("SMS Recipients (comma separated)")

        st.button("Save Notification Settings")
        
    with tab3:
        st.markdown("<h2 class='sub-header'>Backup & Restore</h2>", unsafe_allow_html=True)

        st.markdown("### Backup Settings")
        st.checkbox("Enable Automatic Backups")
        st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
        st.text_input("Backup Location")
        st.slider("Retain Backups (days)", 7, 365, 30)

        st.markdown("### Manual Backup")
        col1, col2 = st.columns(2)
            
        with col1:
            st.button("Create Backup Now")
            
        with col2:
            st.download_button("Download Latest Backup", data="", file_name="security_backup.zip")

        st.markdown("### Restore System")
        st.file_uploader("Upload Backup File")
        st.button("Restore from Backup")
        
    with tab4:
        st.markdown("<h2 class='sub-header'>User Accounts</h2>", unsafe_allow_html=True)

        system_users = [
            {"username": "admin", "name": "System Administrator", "role": "Administrator", "last_login": "2023-06-15 10:30:22"},
            {"username": "security1", "name": "Security Officer 1", "role": "Security Staff", "last_login": "2023-06-15 08:15:45"},
            {"username": "principal", "name": "School Principal", "role": "Manager", "last_login": "2023-06-14 16:20:10"},
            {"username": "tech", "name": "IT Support", "role": "Technician", "last_login": "2023-06-13 11:45:30"},
        ]
            
        user_df = pd.DataFrame(system_users)
        st.dataframe(user_df, use_container_width=True)
            
        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.button("Add User")
            
        with col2:
            st.button("Edit Selected User")
            
        with col3:
            st.button("Delete User")

        st.markdown("### Password Policy")
        st.slider("Minimum Password Length", 6, 16, 8)
        st.checkbox("Require Special Characters")
        st.checkbox("Require Numbers")
        st.checkbox("Require Mixed Case")
        st.slider("Password Expiry (days)", 30, 365, 90)

        st.button("Save User Settings")