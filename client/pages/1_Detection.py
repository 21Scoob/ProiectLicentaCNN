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

# ── Clear previous results when page loads fresh (no scan yet) ─────
if "scan_done" not in st.session_state:
    st.session_state["scan_done"] = False
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

st.title("Deepfake Detection System")
st.markdown("---")

headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}

# ── Fetch existing sources for dropdown ────────────────────────────
existing_sources = []
try:
    src_res = requests.get(f"{API_URL}/source-stats/", headers=headers)
    if src_res.status_code == 200:
        existing_sources = [s["display_name"] for s in src_res.json()]
except Exception:
    pass

# ── Image Upload ───────────────────────────────────────────────────
st.header("Upload an image for analysis")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key=f"uploader_{st.session_state['uploader_key']}")

if uploaded_file is not None:
    st.image(uploaded_file, caption='Uploaded image.', use_container_width=True)
    
    # ── Source Selection ───────────────────────────────────────────
    st.markdown("**Source**")
    
    if existing_sources:
        options = existing_sources + ["+ Create new..."]
        selected = st.selectbox("Select a source", options, label_visibility="collapsed")
        
        if selected == "+ Create new...":
            source_input = st.text_input("New source name", placeholder="e.g. ProTV, CNN, BBC...")
        else:
            source_input = selected
    else:
        options = ["+ Create one"]
        selected = st.selectbox("Select a source", options, label_visibility="collapsed")
        source_input = st.text_input("New source name", placeholder="e.g. ProTV, CNN, BBC...")
    
    if st.button("Start Scan", use_container_width=True):
        if st.session_state['credits'] > 0:
            with st.spinner('ResNet50 and ViT models are analyzing the image...'):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    response = requests.post(f"{API_URL}/predict/", files=files, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['last_prediction'] = data['prediction']
                        st.session_state['last_label'] = data['label']
                        st.session_state['last_threshold'] = data['threshold']
                        st.session_state['last_scan_id'] = data['scan_id']
                        st.session_state['credits'] = data['new_credits']
                        st.session_state['show_feedback'] = True
                        st.session_state['scan_done'] = True
                        
                        # ── Submit source if provided ──────────────
                        if source_input and source_input.strip():
                            try:
                                requests.post(
                                    f"{API_URL}/source/",
                                    json={
                                        "scan_id": data['scan_id'],
                                        "display_name": source_input.strip()
                                    },
                                    headers=headers
                                )
                            except Exception:
                                pass
                        
                        st.rerun()
                    elif response.status_code == 402:
                        st.error("You don't have enough credits!")
                    else:
                        st.error(f"Processing error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.error("You don't have enough credits! Please recharge your account.")

# ── Analysis Result (only shown after a scan) ──────────────────────
if st.session_state.get("scan_done") and 'last_prediction' in st.session_state:
    val = st.session_state['last_prediction']
    label = st.session_state.get('last_label', 'Unknown')
    threshold = st.session_state.get('last_threshold', 50.0)
    scan_id = st.session_state.get('last_scan_id')
    
    st.markdown("---")
    st.subheader("Analysis Result")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Model veridicity score:** {val}%")
        st.markdown(f"**Your threshold:** {threshold}%")
        
        if label == "Real":
            st.success(
                f"**REAL** — The veridicity score ({val}%) is equal to or above "
                f"your threshold ({threshold}%), so this scan is classified as authentic."
            )
        else:
            st.error(
                f"**DEEPFAKE** — The veridicity score ({val}%) is below "
                f"your threshold ({threshold}%), so this scan is classified as manipulated."
            )
    
    with col2:
        st.metric("Veridicity", f"{val}%")
        st.metric("Threshold", f"{threshold}%")
        if label == "Real":
            st.metric("Verdict", "Real")
        else:
            st.metric("Verdict", "Deepfake")

    # ── Feedback ───────────────────────────────────────────────────
    if st.session_state.get('show_feedback'):
        st.write("---")
        st.markdown("##### Help us improve!")
        st.write("Was the result correct?")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, it's correct", use_container_width=True):
                requests.post(f"{API_URL}/feedback/", json={
                    "scan_id": scan_id,
                    "is_correct": True,
                    "comment": "User confirmed result"
                }, headers=headers)
                st.session_state['show_feedback'] = False
                st.success("Thank you for your feedback!")
                st.rerun()
        with c2:
            if st.button("No, it's wrong", use_container_width=True):
                st.session_state['feedback_negative'] = True

        if st.session_state.get('feedback_negative'):
            comment = st.text_area("Tell us more (optional):", placeholder="Ex: The image is real, but it was detected as fake...")
            if st.button("Submit Negative Feedback"):
                requests.post(f"{API_URL}/feedback/", json={
                    "scan_id": scan_id,
                    "is_correct": False,
                    "comment": comment
                }, headers=headers)
                st.session_state['show_feedback'] = False
                st.session_state['feedback_negative'] = False
                st.success("Thank you! We will analyze this error.")
                st.rerun()

    # ── Reset button ──────────────────────────────────────────────
    st.markdown("---")
    if st.button("New Scan", use_container_width=True):
        for key in ['last_prediction', 'last_label', 'last_threshold', 'last_scan_id', 'show_feedback', 'feedback_negative', 'scan_done']:
            st.session_state.pop(key, None)
        st.session_state["uploader_key"] += 1
        st.rerun()
