import streamlit as st
import requests
import time
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def init_session():
    """Initializare variabile session_state"""
    defaults = {
        "user": None,
        "username": None,
        "credits": 0,
        "auth_token": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def handle_auth(cookie_manager):
    """Logica de auto-login folosind JWT din cookie-uri"""
    # Așteptăm puțin ca managerul de cookie să fie gata
    time.sleep(0.1) 
    jwt_token = cookie_manager.get("auth_token")

    if jwt_token and st.session_state["user"] is None:
        try:
            response = requests.get(f"{API_URL}/validate-token/?token={jwt_token}")
            if response.status_code == 200:
                user_data = response.json()
                st.session_state["user"] = user_data["email"]
                st.session_state["username"] = user_data["username"]
                st.session_state["credits"] = user_data["credits"]
                st.session_state["auth_token"] = jwt_token
                st.rerun()
        except Exception:
            pass
    return jwt_token

def render_sidebar(cookie_manager):
    """Randare sidebar consistent si stilizat"""
    # Ascunde navigatia implicita Streamlit
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none; }
            .sidebar-user-card {
                background-color: #B843C4; 
                padding: 15px; 
                border-radius: 10px; 
                color: white; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state["username"]:
            st.markdown(f"""
                <div class="sidebar-user-card">
                    <h3 style="margin: 0; color: white;">{st.session_state['username']}</h3>
                    <p style="margin: 2px 0 0 0; font-size: 0.8em; opacity: 0.8;">{st.session_state['user']}</p>
                    <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold;">💰 Credite:</span>
                        <span style="font-size: 1.2em; font-weight: bold;">{st.session_state['credits']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.write("### Navigare")
        if st.button("🏠 Acasă", use_container_width=True):
            st.switch_page("webapp.py")
        
        if not st.session_state["user"]:
            if st.button("🔒 Autentificare", use_container_width=True):
                st.switch_page("pages/Authentification.py")
        else:
            if st.button("🔍 Detecție", use_container_width=True):
                st.switch_page("pages/1_Detection.py")
            if st.button("💰 Credite", use_container_width=True):
                st.switch_page("pages/2_Credits.py")
            if st.button("💳 Abonamente", use_container_width=True):
                st.switch_page("pages/3_Subscription.py")
            
            st.write("---")
            if st.button("Deconectare", use_container_width=True):
                cookie_manager.delete("auth_token")
                st.session_state["user"] = None
                st.session_state["username"] = None
                st.session_state["credits"] = 0
                st.session_state["auth_token"] = None
                st.rerun()

def require_auth():
    """Blocheaza accesul paginii daca userul nu e logat"""
    if st.session_state['user'] is None:
        st.warning("Te rugăm să te autentifici pentru a accesa această pagină.")
        if st.button("Mergi la Autentificare"):
            st.switch_page("pages/Authentification.py")
        st.stop()
