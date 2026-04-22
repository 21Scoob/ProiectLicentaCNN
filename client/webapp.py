import streamlit as st
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, API_URL

st.set_page_config(page_title="Deepfake Detection System", layout="centered", initial_sidebar_state="expanded")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)

# --- CONTINUT PAGINA ---
st.title("Deepfake Detection System")

st.markdown("""
### About this site

In a digital era where images can be quickly modified, this tool comes to your aid to ensure you always discover reality. Our platform will allow you to upload a photo you are suspicious about — maybe you are not sure if it is an authentic image, an entirely Artificial Intelligence (AI) generated creation, or a fake (deepfake / alteration).

---

### How does it work?

Image processing and verification are ensured by combining the performances of two advanced **Machine Learning** architectures: 
1. **ViT (Vision Transformer) Model:** Capable of carefully analyzing the sub-regional visual links of the image.
2. **CNN (Convolutional Neural Network) Model:** Historically recognized for its extraordinary texture recognition.

Upon uploading the photo, these two models work together and calculate the exact probability of the photo's modification. **The displayed result will represent the percentage (%) chance that the respective photo is altered or AI generated.**

---

### Start analysis

Are you ready? You need an account to be able to initiate the analysis process.
""")

st.write("")

if not st.session_state["user"]:
    if st.button("Go to Authentication / Registration system", use_container_width=True):
        st.switch_page("pages/Authentification.py")
else:
    if st.button("Go to Detector",  use_container_width=True):
        st.switch_page("pages/1_Detection.py")
