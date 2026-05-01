import streamlit as st
import requests
from datetime import datetime, timedelta


API_URL = "http://localhost:8000"

def init_session():
    """Initializare variabile session_state"""
    defaults = {
        "user": None,
        "username": None,
        "credits": 0,
        "auth_token": None,
        "logout_in_progress": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def handle_auth(cookie_manager):
    """Auto-Login logic"""
    if st.session_state.get("logout_in_progress"):                                              
      return None 
      
    if st.session_state.get("user") and st.session_state.get("auth_token"):
        return st.session_state["auth_token"]

    jwt_token = cookie_manager.get("auth_token") or st.session_state.get("auth_token")

    if jwt_token and st.session_state["user"] is None:
        try:
            response = requests.get(f"{API_URL}/validate-token/", headers={"Authorization": f"Bearer {jwt_token}"})
            if response.status_code == 200:
                user_data = response.json()
                st.session_state["user"] = user_data["email"]
                st.session_state["username"] = user_data["username"]
                st.session_state["credits"] = user_data["credits"]
                st.session_state["auth_token"] = jwt_token
                st.rerun()
            else:
                st.session_state["auth_token"] = None
        except Exception:
            pass
    return jwt_token

def render_sidebar(cookie_manager):
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none; }
            
            /* --- STIL SIDEBAR (MINIMALIST) --- */
            .sidebar-user-card {
                background-color: transparent; 
                padding: 15px; 
                border-radius: 10px; 
                color: white; 
                margin-bottom: 20px; 
            }

            /* Butoane Navigare: Transparente, Text Alb, Fara Hover */
            [data-testid="stSidebar"] div.stButton > button {
                background-color: transparent !important;
                color: white !important;
                border: none !important;
                min-height: 0px !important;
                height: auto !important;
                padding: 10px !important;
                width: 100% !important;
                text-align: left !important;
                justify-content: flex-start !important;
                transition: none !important; /* Elimina tranzitiile */
            }

            /* Elimina orice efect la hover pentru navigare */
            [data-testid="stSidebar"] div.stButton > button:hover,
            [data-testid="stSidebar"] div.stButton > button:active,
            [data-testid="stSidebar"] div.stButton > button:focus {
                background-color: transparent !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
                transform: none !important;
            }

            /* --- STIL CARDURI INTERACTIVE (ZONA PRINCIPALA) --- */
            [data-testid="stMainBlockContainer"] div.stButton > button {
                width: 100% !important;
                min-height: 45px !important;
                background-color:  transparent !important;
                color: white !important;
                padding: 25px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: pre-wrap !important;
                transition: all 0.3s ease !important;
                line-height: 1.6 !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
            }

            [data-testid="stMainBlockContainer"] div.stButton > button:hover {
         
                background-color: transparent !important;
                transform: translateY(-5px) !important;
                box-shadow: 0 12px 24px rgba(49, 27, 146, 0.15) !important;
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
                        <span style="font-weight: bold;">Credits:</span>
                        <span style="font-size: 1.2em; font-weight: bold;">{st.session_state['credits']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Home", key="nav_home", use_container_width=True):
            st.switch_page("webapp.py")
        
        if not st.session_state["user"]:
            if st.button("Authentication", key="nav_auth", use_container_width=True):
                st.switch_page("pages/Authentification.py")
        else:
            if st.button("Detection", key="nav_det", use_container_width=True):
                st.switch_page("pages/1_Detection.py")
            if st.button("Credits", key="nav_cred", use_container_width=True):
                st.switch_page("pages/2_Credits.py")
            
            st.write("---")
            if st.button("Logout", key="nav_logout", use_container_width=True):
                try:
                    cookie_manager.delete("auth_token")
                except (KeyError, Exception):
                    pass
                st.session_state["user"] = None
                st.session_state["username"] = None
                st.session_state["credits"] = 0
                st.session_state["auth_token"] = None
                st.session_state["logout_in_progress"] = True

def require_auth():
    """Blocheaza accesul paginii daca userul nu e logat"""
    if st.session_state["user"] is None:
        st.warning("Please go and authenticate to continue on this page.")
        if st.button("Go to Authentication", key="req_auth_btn"):
            st.switch_page("pages/Authentification.py")
        st.stop()
