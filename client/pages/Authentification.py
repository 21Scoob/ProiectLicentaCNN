import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Autentificare", page_icon="🔒")

# Manager pentru Cookie-uri
cookie_manager = CookieManager()

# Ascunde meniul implicit de pagini
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Initializare session_state
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'credits' not in st.session_state:
    st.session_state['credits'] = 0
if 'auth_token' not in st.session_state:
    st.session_state['auth_token'] = None

# --- LOGICA DE AUTO-LOGIN (JWT) ---
time.sleep(0.1)
jwt_token = cookie_manager.get("auth_token")
if jwt_token and st.session_state["user"] is None:
    try:
        response = requests.get(f"http://localhost:8000/validate-token/?token={jwt_token}")
        if response.status_code == 200:
            user_data = response.json()
            st.session_state["user"] = user_data["email"]
            st.session_state["username"] = user_data["username"]
            st.session_state["credits"] = user_data["credits"]
            st.session_state["auth_token"] = jwt_token
            st.rerun()
    except: pass

# --- SIDEBAR CONSISTENT ---
with st.sidebar:
    if st.session_state["username"]:
        st.markdown(f"""
            <div style="background-color: #B843C4; padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
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

# --- CONTINUT PAGINA ---
st.title("Sistem de Detecție Deepfake")

if st.session_state['user'] is None:
    tab_login, tab_register = st.tabs(["Login", "Register"])
    
    with tab_login:
        email_login = st.text_input("Email", key="login_email").strip().lower()
        pass_login = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary"):
            try:
                response = requests.post(
                    "http://localhost:8000/login/", 
                    json={"email": email_login, "password": pass_login}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['user'] = data['user']['email']
                    st.session_state['username'] = data['user']['username']
                    st.session_state['credits'] = data['user']['credits']
                    st.session_state['auth_token'] = data['access_token']
                    
                    # Salvam in cookie (7 zile)
                    expiry = datetime.now() + timedelta(days=7)
                    cookie_manager.set("auth_token", data['access_token'], expires_at=expiry)
                    
                    st.success("Logare reușită! Se procesează...")
                    time.sleep(0.5) # Așteptăm salvarea cookie-ului
                    st.switch_page("pages/1_Detection.py")
                else:
                    st.error("Email sau parolă incorectă!")
            except requests.exceptions.ConnectionError:
                st.error("Nu mă pot conecta la serverul backend. Asigură-te că FastAPI rulează!")
                
    with tab_register:
        user_reg = st.text_input("Nume Utilizator", key="reg_user")
        email_reg = st.text_input("Email", key="reg_email").strip().lower()
        pass_reg = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Register", type="primary"):
            if not user_reg:
                st.error("Te rugăm să introduci un nume de utilizator!")
            else:
                try:
                    response = requests.post(
                        f"http://localhost:8000/register/?email={email_reg}&password={pass_reg}&username={user_reg}"
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['user'] = data['user']['email']
                        st.session_state['username'] = data['user']['username']
                        st.session_state['credits'] = data['user']['credits']
                        st.session_state['auth_token'] = data['access_token']
                        
                        # Salvam in cookie
                        expiry = datetime.now() + timedelta(days=7)
                        cookie_manager.set("auth_token", data['access_token'], expires_at=expiry)
                        
                        st.success("Account created! Se procesează...")
                        time.sleep(0.5) # Așteptăm salvarea cookie-ului
                        st.switch_page("pages/1_Detection.py")
                    elif response.status_code == 400:
                        st.error(response.json().get("detail", "Eroare la creare"))
                    else:
                        st.error("A apărut o eroare necunoscută.")
                except requests.exceptions.ConnectionError:
                    st.error("Nu mă pot conecta la serverul backend. Asigură-te că FastAPI rulează!")

else:
    st.success(f"Ești conectat ca {st.session_state['username']}!")
    if st.button("Mergi la Detector", type="primary"):
        st.switch_page("pages/1_Detection.py")
