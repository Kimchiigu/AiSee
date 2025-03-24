import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render():
    st.markdown("<h1 class='main-header'>Security Dashboard</h1>", unsafe_allow_html=True)
    
    current_time = datetime.now().strftime("%B %d, %Y %H:%M:%S")
    st.markdown(f"**Current Time:** {current_time}")

    st.markdown("<h2 class='sub-header'>System Status</h2>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Cameras")
        st.markdown("<span class='status-ok'>All Online (24/24)</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Access Points")
        st.markdown("<span class='status-warning'>Warning (1 issue)</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Alarms")
        st.markdown("<span class='status-ok'>Armed</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Network")
        st.markdown("<span class='status-ok'>Online</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h2 class='sub-header'>Recent Activity</h2>", unsafe_allow_html=True)

    activities = [
        {"time": "14:32:05", "location": "Main Entrance", "event": "Staff ID Scan", "person": "John Smith", "status": "Authorized"},
        {"time": "14:28:17", "location": "East Wing", "event": "Motion Detected", "person": "Unknown", "status": "Verified"},
    ]
    st.dataframe(pd.DataFrame(activities), use_container_width=True)

    st.markdown("<h2 class='sub-header'>Security Analytics</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        hours = list(range(24))
        access_counts = [5, 3, 1, 0, 0, 2, 15, 45, 80, 65, 40, 35, 50, 55, 45, 40, 60, 30, 15, 10, 8, 5, 3, 2]
        fig = px.bar(pd.DataFrame({"Hour": hours, "Access Count": access_counts}),
                     x="Hour", y="Access Count", title="Access Events by Hour")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        locations = ['Main Entrance', 'Admin Office', 'Classrooms']
        location_counts = [120, 85, 65]
        fig = px.pie(pd.DataFrame({"Location": locations, "Access Count": location_counts}),
                     names="Location", values="Access Count", title="Access by Location")
        st.plotly_chart(fig, use_container_width=True)
