import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Deepfake Detection", initial_sidebar_state="collapsed")

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

st.title("Deepfake Detection System")
st.markdown("---")

st.header("Upload an image for analysis")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Uploaded image.', use_container_width=True)
    
    if st.button("Start Scan", type="primary", use_container_width=True):
        if st.session_state['credits'] > 0:
            with st.spinner('ResNet50 and ViT models are analyzing the image...'):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
                    
                    response = requests.post(f"{API_URL}/predict/", files=files, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['last_prediction'] = data['prediction']
                        st.session_state['last_scan_id'] = data['scan_id']
                        st.session_state['credits'] = data['new_credits']
                        st.session_state['show_feedback'] = True
                    elif response.status_code == 402:
                        st.error("You don't have enough credits!")
                    else:
                        st.error(f"Processing error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.error("You don't have enough credits! Please recharge your account.")

if 'last_prediction' in st.session_state:
    val = st.session_state['last_prediction']
    scan_id = st.session_state.get('last_scan_id')
    
    st.markdown("---")
    st.subheader("Analysis Result")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if val > 50:
            st.error(f"Deepfake Probability: **{val}%**")
            st.warning("Attention! The image shows clear signs of digital manipulation.")
        else:
            st.success(f"Deepfake Probability: **{val}%**")
            st.info("The image appears to be authentic according to our analysis.")

    if st.session_state.get('show_feedback'):
        st.write("---")
        st.markdown("##### 📢 Help us improve!")
        st.write("Was the result correct?")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, it's correct", use_container_width=True):
                headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
                requests.post(f"{API_URL}/feedback/", json={
                    "scan_id": scan_id,
                    "is_correct": True,
                    "comment": "User confirmed result"
                }, headers=headers)
                st.session_state['show_feedback'] = False
                st.success("Thank you for your feedback!")
                st.rerun()
        with c2:
            if st.button("❌ No, it's wrong", use_container_width=True):
                st.session_state['feedback_negative'] = True

        if st.session_state.get('feedback_negative'):
            comment = st.text_area("Tell us more (optional):", placeholder="Ex: The image is real, but it was detected as fake...")
            if st.button("Submit Negative Feedback"):
                headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
                requests.post(f"{API_URL}/feedback/", json={
                    "scan_id": scan_id,
                    "is_correct": False,
                    "comment": comment
                }, headers=headers)
                st.session_state['show_feedback'] = False
                st.session_state['feedback_negative'] = False
                st.success("Thank you! We will analyze this error.")
                st.rerun()
