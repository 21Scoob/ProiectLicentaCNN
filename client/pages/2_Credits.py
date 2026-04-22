import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL
import webbrowser

st.set_page_config(page_title="Credits", initial_sidebar_state="collapsed")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()


query_params = st.query_params
if "success" in query_params and "session_id" in query_params:
    session_id = query_params["session_id"]
    amount = int(query_params.get("amount", 0))
    
    with st.spinner("Verifying payment..."):
        try:
            res = requests.get(f"{API_URL}/verify-payment/?session_id={session_id}&email={st.session_state['user']}&amount={amount}")
            if res.status_code == 200 and res.json().get("status") == "success":
                st.success(f"Payment confirmed! You received {amount} credits.")
                st.session_state['credits'] = res.json()["new_credits"]
                
                st.query_params.clear()
            else:
                st.error("Could not verify payment. Contact support.")
        except Exception as e:
            st.error(f"Error verifying payment: {e}")

if "canceled" in query_params:
    st.warning("Payment was canceled.")
    st.query_params.clear()
    
st.title("Recharge Your Account")
st.write("Choose the credit package that suits you.")

credit_packages = [
    {"amount": 10, "price": 5},
    {"amount": 50, "price": 20},
    {"amount": 100, "price": 35}
]

cols = st.columns(3)

for i, pkg in enumerate(credit_packages):
    with cols[i]:
        st.subheader(f"{pkg['amount']} Credits")
        st.write(f"Price: {pkg['price']} €")
        
        if st.button(f"Buy {pkg['amount']}", key=f"buy_{pkg['amount']}", use_container_width=True):
            try:
                headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
                params = {
                    "amount": pkg['amount'],
                    "price_eur": pkg['price']
                }
                response = requests.post(f"{API_URL}/create-checkout-session/", params=params, headers=headers)
                if response.status_code == 200:
                    checkout_url = response.json().get("url")
                    st.info("Redirecting you to Stripe...")
                    
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                    st.link_button("Go to Payment", checkout_url)
                else:
                    st.error("Error generating checkout session.")
            except Exception as e:
                st.error(f"Connection error: {e}")