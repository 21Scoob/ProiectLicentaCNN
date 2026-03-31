import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL
import webbrowser

st.set_page_config(page_title="Credits")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()


query_params = st.query_params
if "success" in query_params and "session_id" in query_params:
    session_id = query_params["session_id"]
    amount = int(query_params.get("amount", 0))
    
    with st.spinner("Se verifică plata..."):
        try:
            res = requests.get(f"{API_URL}/verify-payment/?session_id={session_id}&email={st.session_state['user']}&amount={amount}")
            if res.status_code == 200 and res.json().get("status") == "success":
                st.success(f"Plată confirmată! Ai primit {amount} credite.")
                st.session_state['credits'] = res.json()["new_credits"]
                
                st.query_params.clear()
            else:
                st.error("Nu am putut verifica plata. Contactează suportul.")
        except Exception as e:
            st.error(f"Eroare la verificarea plății: {e}")

if "canceled" in query_params:
    st.warning("Plata a fost anulată.")
    st.query_params.clear()


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
        st.subheader(f"{pkg['amount']} Credite")
        st.write(f"Preț: {pkg['price']} €")
        
        if st.button(f"Cumpără {pkg['amount']}", key=f"buy_{pkg['amount']}", use_container_width=True):
            try:
                payload = {
                    "email": st.session_state['user'],
                    "amount": pkg['amount'],
                    "price_eur": pkg['price']
                }
                response = requests.post(f"{API_URL}/create-checkout-session/", params=payload)
                if response.status_code == 200:
                    checkout_url = response.json().get("url")
                    st.info("Te redirecționăm către Stripe...")
                    
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                    st.link_button("Mergi la Plată", checkout_url)
                else:
                    st.error("Eroare la generarea sesiunii de plată.")
            except Exception as e:
                st.error(f"Eroare de conexiune: {e}")
