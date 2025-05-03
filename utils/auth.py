import streamlit as st
from utils.role import get_user_info

def login_form():
    st.sidebar.markdown("## Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        stored_password, role = get_user_info(username)
        
        if stored_password:
            if password == stored_password:
                if role in ["admin", "teacher"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = role  # ✅ Save the user's role
                    st.rerun()
                else:
                    st.sidebar.error("You do not have permission to log in.")
            else:
                st.sidebar.error("Invalid password.")
        else:
            st.sidebar.error("User not found.")
