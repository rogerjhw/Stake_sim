import streamlit as st
import pdfplumber

st.set_page_config(page_title="Privacy Policy", layout="wide")

st.title("Stakeholder Privacy Policy")

pdf_path = "/Users/rogerwhite/Downloads/PrivacyPolicy.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            st.markdown(f"<pre>{text}</pre>", unsafe_allow_html=True)

