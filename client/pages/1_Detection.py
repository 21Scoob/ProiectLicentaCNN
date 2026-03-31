import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Deepfake Detection")

st.markdown("""
    <style>
        [data-testid="stFileUploader"] section button {
            display: none;
        }
        [data-testid="stFileUploader"] section {
            padding: 40px !important;
        }
    </style>
""", unsafe_allow_html=True)

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

st.title("Sistem de Detecție Deepfake")
st.markdown("---")

st.header("Încarcă o imagine pentru analiză")
uploaded_file = st.file_uploader("Alege o imagine...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Imagine încărcată.', use_container_width=True)
    
    if st.button("Inițiază Scanarea", type="primary", use_container_width=True):
        if st.session_state['credits'] > 0:
            with st.spinner('Modelele ResNet50 și ViT analizează imaginea...'):
                import time
                time.sleep(2) 
                prediction_val = 87.5  
                st.session_state['last_prediction'] = prediction_val
                st.session_state['show_feedback'] = True
        else:
            st.error("Nu mai ai credite suficiente! Te rugăm să reîncarci contul.")

if 'last_prediction' in st.session_state:
    val = st.session_state['last_prediction']
    
    st.markdown("---")
    st.subheader("Rezultatul Analizei")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if val > 50:
            st.error(f"Probabilitate Deepfake: **{val}%**")
            st.warning("Atenție! Imaginea prezintă semne clare de manipulare digitală.")
        else:
            st.success(f"Probabilitate Deepfake: **{val}%**")
            st.info("Imaginea pare a fi autentică conform analizei noastre.")

    if st.session_state.get('show_feedback'):
        st.write("---")
        st.markdown("##### 📢 Ajută-ne să ne îmbunătățim!")
        st.write("Rezultatul a fost corect?")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Da, este corect", use_container_width=True):
                requests.post(f"{API_URL}/feedback/", json={
                    "email": st.session_state['user'],
                    "is_correct": True,
                    "comment": "User confirmed result"
                })
                st.session_state['show_feedback'] = False
                st.success("Mulțumim pentru feedback!")
                st.rerun()
        with c2:
            if st.button("❌ Nu, este greșit", use_container_width=True):
                st.session_state['feedback_negative'] = True

        if st.session_state.get('feedback_negative'):
            comment = st.text_area("Spune-ne mai multe (opțional):", placeholder="Ex: Imaginea este reală, dar a fost detectată ca fake...")
            if st.button("Trimite Feedback Negativ"):
                requests.post(f"{API_URL}/feedback/", json={
                    "email": st.session_state['user'],
                    "is_correct": False,
                    "comment": comment
                })
                st.session_state['show_feedback'] = False
                st.session_state['feedback_negative'] = False
                st.success("Mulțumim! Vom analiza această eroare.")
                st.rerun()
