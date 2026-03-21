import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Abonamente", page_icon="💳")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

# --- CONTINUT PAGINA ---
st.title("Alege Abonamentul Potrivit")
st.write("Deblochează mai multe scanări.")

try:
    response = requests.get(f"{API_URL}/plans/")
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
                    up_res = requests.post(f"{API_URL}/upgrade-plan/?email={st.session_state['user']}&plan_name={plan['name']}")
                    if up_res.status_code == 200:
                        st.session_state['credits'] = up_res.json()['new_credits']
                        st.success(f"Te-ai abonat la {plan['name']}!")
                        st.rerun()
except:
    st.error("Eroare la încărcarea planurilor.")
