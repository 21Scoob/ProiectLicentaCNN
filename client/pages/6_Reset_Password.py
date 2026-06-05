import streamlit as st
import requests
import time
from utils import API_URL

st.set_page_config(page_title="Reset Password", initial_sidebar_state="collapsed")

st.title("Reset Password")

query_params = st.query_params
token = query_params.get("token")

if not token:
    st.markdown("Enter your email address to receive a password reset link.")
    email = st.text_input("Email").strip().lower()

    if st.button("Send Reset Link", use_container_width=True):
        if not email:
            st.error("Please enter your email.")
        else:
            try:
                response = requests.post(f"{API_URL}/forgot-password/", json={"email": email})
                if response.status_code == 200:
                    st.success("If an account exists with that email, a reset link has been sent.")
                else:
                    st.error(response.json().get("detail", "Error sending email"))
            except Exception as e:
                st.error("Error connecting to the server.")
else:
    st.markdown("Enter your new password below.")
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm New Password", type="password")

    if st.button("Reset Password", use_container_width=True):
        if new_pass != confirm_pass:
            st.error("Passwords do not match.")
        elif len(new_pass) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            try:
                response = requests.post(f"{API_URL}/reset-password/", json={
                    "token": token,
                    "new_password": new_pass
                })
                if response.status_code == 200:
                    st.success("Password reset successfully. Redirecting to login...")
                    time.sleep(1.5)
                    st.switch_page("pages/Authentification.py")
                else:
                    st.error(response.json().get("detail", "Error resetting password"))
            except Exception as e:
                st.error("Error connecting to the server.")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Back to Login", use_container_width=True, type="secondary"):
    st.switch_page("pages/Authentification.py")
