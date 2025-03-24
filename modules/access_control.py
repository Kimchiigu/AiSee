import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render():
    st.markdown("<h1 class='main-header'>Access Control Management</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Access Points", "User Management", "Access Logs"])
        
    with tab1:
        st.markdown("<h2 class='sub-header'>Access Points Status</h2>", unsafe_allow_html=True)

        access_points = [
            {"id": "AP001", "name": "Main Entrance", "type": "Card Reader", "status": "Online", "last_activity": "14:32:05"},
            {"id": "AP002", "name": "Admin Office", "type": "Biometric", "status": "Online", "last_activity": "14:15:42"},
            {"id": "AP003", "name": "West Wing Door", "type": "Card Reader", "status": "Warning", "last_activity": "13:22:18"},
            {"id": "AP004", "name": "East Wing", "type": "Card Reader", "status": "Online", "last_activity": "14:28:17"},
            {"id": "AP005", "name": "Server Room", "type": "Biometric+PIN", "status": "Online", "last_activity": "11:45:30"},
            {"id": "AP006", "name": "Gymnasium", "type": "Card Reader", "status": "Online", "last_activity": "13:45:22"},
        ]
            
        ap_df = pd.DataFrame(access_points)
        st.dataframe(ap_df, use_container_width=True)

        st.markdown("<h3>Door Controls</h3>", unsafe_allow_html=True)
            
        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.selectbox("Select Door", [ap["name"] for ap in access_points])
            
        with col2:
            st.button("Lock Door")
            st.button("Unlock Door")
            
        with col3:
            st.checkbox("Emergency Unlock All")
            st.checkbox("Lockdown Mode")
        
    with tab2:
        st.markdown("<h2 class='sub-header'>User Management</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
            
        with col1:
            st.text_input("Search Users")
            
        with col2:
            st.selectbox("Filter By", ["All Users", "Staff", "Students", "Visitors", "Contractors"])

        users = [
            {"id": "S001", "name": "John Smith", "type": "Staff", "department": "Administration", "access_level": "Full"},
            {"id": "S002", "name": "Sarah Johnson", "type": "Staff", "department": "Faculty", "access_level": "Standard"},
            {"id": "T001", "name": "Emily Davis", "type": "Student", "department": "Grade 11", "access_level": "Limited"},
            {"id": "V001", "name": "Michael Brown", "type": "Visitor", "department": "N/A", "access_level": "Visitor"},
            {"id": "C001", "name": "David Wilson", "type": "Contractor", "department": "Maintenance", "access_level": "Restricted"},
        ]
            
        user_df = pd.DataFrame(users)
        st.dataframe(user_df, use_container_width=True)

        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.button("Add New User")
            
        with col2:
            st.button("Edit Selected User")
            
        with col3:
            st.button("Revoke Access")
        
    with tab3:
        st.markdown("<h2 class='sub-header'>Access Logs</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
            
        with col1:
            st.date_input("Start Date", datetime.now() - timedelta(days=7))
            
        with col2:
            st.date_input("End Date", datetime.now())

        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.selectbox("Access Point", ["All"] + [ap["name"] for ap in access_points])
            
        with col2:
            st.selectbox("User Type", ["All", "Staff", "Students", "Visitors", "Contractors"])
            
        with col3:
            st.selectbox("Status", ["All", "Authorized", "Denied", "Forced"])

        access_logs = [
            {"timestamp": "2023-06-15 14:32:05", "user_id": "S001", "name": "John Smith", "access_point": "Main Entrance", "status": "Authorized"},
            {"timestamp": "2023-06-15 14:15:42", "user_id": "S002", "name": "Sarah Johnson", "access_point": "Admin Office", "status": "Authorized"},
            {"timestamp": "2023-06-15 13:45:22", "user_id": "T001", "name": "Emily Davis", "access_point": "Gymnasium", "status": "Authorized"},
            {"timestamp": "2023-06-15 13:22:18", "user_id": "Unknown", "name": "Unknown", "access_point": "West Wing Door", "status": "Denied"},
            {"timestamp": "2023-06-15 11:45:30", "user_id": "C001", "name": "David Wilson", "access_point": "Server Room", "status": "Authorized"},
            {"timestamp": "2023-06-15 10:30:15", "user_id": "V001", "name": "Michael Brown", "access_point": "Main Entrance", "status": "Authorized"},
            {"timestamp": "2023-06-15 09:15:42", "user_id": "S002", "name": "Sarah Johnson", "access_point": "Admin Office", "status": "Authorized"},
            {"timestamp": "2023-06-15 08:45:03", "user_id": "S001", "name": "John Smith", "access_point": "Server Room", "status": "Authorized"},
        ]
            
        log_df = pd.DataFrame(access_logs)
        st.dataframe(log_df, use_container_width=True)

        col1, col2 = st.columns(2)
            
        with col1:
            st.download_button("Export to CSV", data="", file_name="access_logs.csv")
            
        with col2:
            st.download_button("Export to PDF", data="", file_name="access_logs.pdf")