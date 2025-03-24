import streamlit as st

def render():
    st.markdown("<h1 class='main-header'>Camera Feeds</h1>", unsafe_allow_html=True)

    camera_areas = ["Main Entrance", "Hallways", "Classrooms", "Gymnasium", "Cafeteria", "Parking Lot"]
    selected_area = st.selectbox("Select Area", camera_areas)

    st.markdown("<h2 class='sub-header'>Live Feeds</h2>", unsafe_allow_html=True)
        
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {selected_area} - Camera 1")
        st.image("https://via.placeholder.com/640x360.png?text=Camera+Feed+1", use_column_width=True)
        st.markdown("Status: **Online**")
            
        st.markdown(f"### {selected_area} - Camera 3")
        st.image("https://via.placeholder.com/640x360.png?text=Camera+Feed+3", use_column_width=True)
        st.markdown("Status: **Online**")
        
    with col2:
        st.markdown(f"### {selected_area} - Camera 2")
        st.image("https://via.placeholder.com/640x360.png?text=Camera+Feed+2", use_column_width=True)
        st.markdown("Status: **Online**")
            
        st.markdown(f"### {selected_area} - Camera 4")
        st.image("https://via.placeholder.com/640x360.png?text=Camera+Feed+4", use_column_width=True)
        st.markdown("Status: **Online**")

    st.markdown("<h2 class='sub-header'>Camera Controls</h2>", unsafe_allow_html=True)
        
    col1, col2, col3 = st.columns(3)
        
    with col1:
        st.markdown("### Pan/Tilt/Zoom")
        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            st.button("←")
        with col_mid:
            st.button("↑")
            st.button("↓")
        with col_right:
            st.button("→")
            
        st.slider("Zoom", 1, 10, 1)
        
    with col2:
        st.markdown("### Settings")
        st.checkbox("Enable Motion Detection")
        st.checkbox("Enable Recording")
        st.selectbox("Resolution", ["Low (480p)", "Medium (720p)", "High (1080p)"])
        
    with col3:
        st.markdown("### Presets")
        st.button("Default Position")
        st.button("Entrance Focus")
        st.button("Wide Angle")