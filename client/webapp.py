import streamlit as st
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, API_URL

st.set_page_config(page_title="Sistem Detecție Deepfake", layout="centered", initial_sidebar_state="expanded")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)

# --- CONTINUT PAGINA ---
st.title("Sistem de Detecție Deepfake")

st.markdown("""
### Despre acest site

Într-o eră digitală unde imaginile pot fi modificate rapid, acest instrument vine în ajutorul tău pentru a te asigura că descoperi mereu realitatea. Platforma noastră îți va permite să încarci o fotografie cu privire la care ai suspiciuni — poate nu ești sigur dacă este o imagine autentică, o creație în totalitate generată prin Inteligență Artificială (AI), sau un fals (deepfake / alterare).

---

### Cum funcționează?

Procesarea și verificarea imaginilor sunt asigurate prin combinarea performanțelor a două arhitecturi avansate de **Machine Learning**: 
1. **Modelul ViT (Vision Transformer):** Capabil să analizeze atent legăturile vizuale sub-regionale ale imaginii.
2. **Modelul CNN (Convolutional Neural Network):** Recunoscut istoric pentru recunoașterea extraordinară a texturilor.

La momentul încărcării pozei, aceste două modele lucrează împreună și calculează probabilitatea exactă de modificare a fotografiei. **Rezultatul afișat va reprezenta cât la sută (%) sunt șanse ca fotografia respectivă să fie alterată sau generată AI.**

---

### Începe analiza

Ești pregătit? Ai nevoie de un cont pentru a putea iniția procesul de analiză.
""")

st.write("")

if not st.session_state["user"]:
    if st.button("Mergi la sistemul de Autentificare / Înregistrare", use_container_width=True):
        st.switch_page("pages/Authentification.py")
else:
    if st.button("Mergi la Detector",  use_container_width=True):
        st.switch_page("pages/1_Detection.py")
