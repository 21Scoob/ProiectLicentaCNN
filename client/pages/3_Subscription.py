import streamlit as st
import requests
from extra_streamlit_components import CookieManager
import time

st.set_page_config(page_title="Abonamente", page_icon="💳")

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

# Verificare autentificare
if st.session_state['user'] is None:
    st.warning("Te rugăm să te autentifici.")
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
st.title("Alege Abonamentul Potrivit")
st.write("Deblochează mai multe scanări.")

try:
    response = requests.get("http://localhost:8000/plans/")
    if response.status_code == 200:
        plans = response.json()
        cols = st.columns(len(plans))
        for i, plan in enumerate(plans):
            with cols[i]:
                st.markdown(f"""
                    <div style="border: 2px solid #B843C4; padding: 20px; border-radius: 15px; text-align: center; margin-bottom:10px;">
                        <h2 style="color: #B843C4;">{plan['name']}</h2>
                        <p style="font-size: 1.5em; font-weight: bold;">{plan['price']} €</p>
                        <p>✅ {plan['monthly_credits']} Credite</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Alege {plan['name']}", key=f"btn_{plan['name']}", type="primary", use_container_width=True):
                    up_res = requests.post(f"http://localhost:8000/upgrade-plan/?email={st.session_state['user']}&plan_name={plan['name']}")
                    if up_res.status_code == 200:
                        st.session_state['credits'] = up_res.json()['new_credits']
                        st.success(f"Te-ai abonat la {plan['name']}!")
                        st.rerun()
except:
    st.error("Eroare la încărcarea planurilor.")
