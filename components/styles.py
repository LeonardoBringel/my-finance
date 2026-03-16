import streamlit as st

def inject_global_css():
    st.markdown("""
    <style>
        [data-testid="stBaseButton-primary"] {
            background-color: #4CAF50 !important;
            border-color: #4CAF50 !important;
            color: white !important;
        }
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #43A047 !important;
            border-color: #43A047 !important;
        }
    </style>
    """, unsafe_allow_html=True)
