import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Subscriptions", initial_sidebar_state="collapsed")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

# --- CONTINUT PAGINA ---
st.title("Choose the Right Subscription")
st.write(f"Your current plan: **{st.session_state.get('plan', 'Free')}**")
st.write("Unlock more scans.")

# Încercăm să luăm planurile de la server
all_plans = []
try:
    response = requests.get(f"{API_URL}/plans/")
    if response.status_code == 200:
        all_plans = response.json()
    else:
        st.error("Too many requests, come back later.")
except requests.exceptions.RequestException:
    st.error("Cannot connect to the server to load plans.")

if all_plans:
    current_plan = st.session_state.get('plan', 'Free')
    plans = [p for p in all_plans if p['name'] != current_plan]
    
    if not plans:
        st.info("You are already on the highest plan (Gold)!")
    else:
        cols = st.columns(len(plans))
        for i, plan in enumerate(plans):
            with cols[i]:
                label = f"{plan['name']}\n\n{plan['price']} €\n\n✅ {plan['monthly_credits']} Credits\n\nChoose Plan"
                if st.button(label, key=f"btn_{plan['name']}", use_container_width=True):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
                        up_res = requests.post(f"{API_URL}/upgrade-plan/?plan_name={plan['name']}", headers=headers)
                        if up_res.status_code == 200:
                            st.session_state['credits'] = up_res.json()['new_credits']
                            st.session_state['plan'] = plan['name']
                            st.success(f"You subscribed to {plan['name']}!")
                            st.rerun()
                        else:
                            st.error("Error processing subscription.")
                    except requests.exceptions.RequestException:
                        st.error("Connection error while processing payment.")
                        
            
                        
                        
                        
                        
                        