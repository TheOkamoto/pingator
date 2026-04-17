import base64
import os
import streamlit as st

def get_base64_image(file_path):
    """Reads an image and converts it to a base64 string for HTML embedding."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def load_local_css(file_name):
    """Loads a local CSS file and injects it into the Streamlit app."""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)