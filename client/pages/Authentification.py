import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from datetime import datetime, timedelta
import time
from utils import init_session, handle_auth, render_sidebar, API_URL

st.set_page_config(page_title="Authentication")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)

st.title("Deepfake Detection System")

if st.session_state['user'] is None:
    tab_login, tab_register = st.tabs(["Login", "Register"])
    
    with tab_login:
        email_login = st.text_input("Email", key="login_email").strip().lower()
        pass_login = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/login/", json={"email": email_login, "password": pass_login})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['user'] = data['user']['email']
                    st.session_state['username'] = data['user']['username']
                    st.session_state['credits'] = data['user']['credits']
                    st.session_state['auth_token'] = data['access_token']
                    
                    expiry = datetime.now() + timedelta(days=7)
                    cookie_manager.set("auth_token", data['access_token'], expires_at=expiry)
                    
                    st.success("Succesful Login")
                    time.sleep(0.5)
                    st.switch_page("pages/1_Detection.py")
                else:
                    st.error("Incorrect Email or password!")
            except:
                st.error("Error connecting to the server.")
                
    with tab_register:
        user_reg = st.text_input("Username", key="reg_user")
        email_reg = st.text_input("Email", key="reg_email").strip().lower()
        pass_reg = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Register",use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/register/?email={email_reg}&password={pass_reg}&username={user_reg}")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.update({"user": data['user']['email'], "username": data['user']['username'], "credits": data['user']['credits'], "auth_token": data['access_token']})
                    
                    expiry = datetime.now() + timedelta(days=7)
                    cookie_manager.set("auth_token", data['access_token'], expires_at=expiry)
                    
                    st.success("Account created with success!")
                    time.sleep(0.5)
                    st.switch_page("pages/1_Detection.py")
                else:
                    st.error(response.json().get("detail", "Eroare la înregistrare"))
            except:
                st.error("Error connecting to the server.")
else:
    st.success(f"You are already connected as {st.session_state['username']}!")
    if st.button("Go to detector", use_container_width=True):
        st.switch_page("pages/1_Detection.py")
