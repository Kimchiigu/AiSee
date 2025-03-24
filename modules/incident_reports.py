import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render():
    st.markdown("<h1 class='main-header'>Incident Reports</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["View Reports", "Create Report"])
        
    with tab1:
        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.date_input("Start Date", datetime.now() - timedelta(days=30))
            
        with col2:
            st.date_input("End Date", datetime.now())
            
        with col3:
            st.selectbox("Incident Type", ["All", "Security Breach", "Unauthorized Access", "Suspicious Activity", "Equipment Failure", "Other"])

        incidents = [
            {"id": "INC001", "date": "2023-06-10", "time": "15:45", "location": "Parking Lot", "type": "Suspicious Activity", "status": "Resolved", "reported_by": "John Smith"},
            {"id": "INC002", "date": "2023-06-05", "time": "09:30", "location": "Main Entrance", "type": "Unauthorized Access", "status": "Closed", "reported_by": "Security System"},
            {"id": "INC003", "date": "2023-05-28", "time": "14:15", "location": "Server Room", "type": "Equipment Failure", "status": "Resolved", "reported_by": "Sarah Johnson"},
            {"id": "INC004", "date": "2023-05-20", "time": "11:20", "location": "East Wing", "type": "Security Breach", "status": "Under Investigation", "reported_by": "David Wilson"},
        ]
            
        incident_df = pd.DataFrame(incidents)
        st.dataframe(incident_df, use_container_width=True)

        selected_incident = st.selectbox("Select Incident to View Details", [f"{inc['id']} - {inc['type']} ({inc['date']})" for inc in incidents])
            
        if st.button("View Details"):
            st.markdown("<h3>Incident Details</h3>", unsafe_allow_html=True)

            st.markdown(f"""
                **Incident ID:** INC001  
                **Date & Time:** 2023-06-10 15:45  
                **Location:** Parking Lot  
                **Type:** Suspicious Activity  
                **Status:** Resolved  
                **Reported By:** John Smith  
                
                **Description:**  
                Security camera detected an unknown individual loitering in the parking lot for an extended period. Security personnel was dispatched to investigate.
                
                **Actions Taken:**  
                1. Security guard approached the individual
                2. Individual identified as a parent waiting for student
                3. Identity verified through student records
                4. Incident closed as false alarm
                
                **Attachments:** [Camera Footage](#) | [Incident Report Form](#)
            """)
        
    with tab2:
        st.markdown("<h2 class='sub-header'>Create New Incident Report</h2>", unsafe_allow_html=True)

        with st.form("incident_report_form"):
            col1, col2 = st.columns(2)
                
            with col1:
                st.date_input("Incident Date", datetime.now())
                st.text_input("Location")
                st.selectbox("Incident Type", ["Security Breach", "Unauthorized Access", "Suspicious Activity", "Equipment Failure", "Other"])
                
            with col2:
                st.time_input("Incident Time", datetime.now().time())
                st.text_input("Reported By")
                st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
            st.text_area("Incident Description", height=150)
            st.text_area("Actions Taken", height=100)
                
            st.file_uploader("Attach Files (Images, Videos, Documents)", accept_multiple_files=True)

            submit_button = st.form_submit_button("Submit Report")
                
            if submit_button:
                st.success("Incident report submitted successfully!")