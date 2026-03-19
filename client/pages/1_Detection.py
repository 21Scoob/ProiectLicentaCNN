import streamlit as st
import requests
from extra_streamlit_components import CookieManager
import time

st.set_page_config(page_title="Detecție Deepfake", page_icon="🔍")

cookie_manager = CookieManager()

# Ascunde meniul implicit de pagini
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

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

# Verificare autentificare (după încercarea de auto-login)
if st.session_state['user'] is None:
    st.warning("Te rugăm să te autentifici pentru a accesa această pagină.")
    if st.button("Mergi la Autentificare"):
        st.switch_page("pages/Authentification.py")
    st.stop()

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
st.markdown("---")

st.header("Încarcă o imagine pentru analiză")
uploaded_file = st.file_uploader("Alege o imagine...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Imagine încărcată.', use_container_width=True)
    
    if st.button("Inițiază Scanarea", type="primary"):
        if st.session_state['credits'] > 0:
            st.info("Scanarea este în curs de procesare...")
        else:
            st.error("Nu mai ai credite suficiente!")
