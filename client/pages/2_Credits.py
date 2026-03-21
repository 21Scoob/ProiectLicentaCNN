import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Cumpără Credite", page_icon="💰")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

# --- CONTINUT PAGINA ---
st.title("Reîncarcă-ți Contul")
st.write("Alege pachetul de credite care ți se potrivește.")

credit_packages = [
    {"amount": 10, "price": 5},
    {"amount": 50, "price": 20},
    {"amount": 100, "price": 35}
]

cols = st.columns(3)

for i, pkg in enumerate(credit_packages):
    with cols[i]:
        st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px">
                <h3>{pkg['amount']} Credite</h3>
                <p style="font-size: 1.5em; color: #B843C4;">{pkg['price']} €</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Cumpără {pkg['amount']}", key=f"buy_{pkg['amount']}", type="primary", use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/add-credits/?email={st.session_state['user']}&amount={pkg['amount']}")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['credits'] = data['new_credits']
                    st.success(f"Ai cumpărat {pkg['amount']} credite!")
                    st.rerun()
                else:
                    st.error("Eroare la procesarea plății.")
            except:
                st.error("Eroare la conectarea cu serverul.")
