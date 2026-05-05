import streamlit as st
import requests
import pandas as pd
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Scan History", initial_sidebar_state="collapsed")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

st.title("Scan History")
st.markdown("---")

headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}

try:
    res = requests.get(f"{API_URL}/scans/", headers=headers)
    if res.status_code == 200:
        scans = res.json()
        
        if not scans:
            st.info("No scans yet. Go to the Detection page to analyze your first image!")
        else:
            st.write(f"**Total scans:** {len(scans)}")
            
            # ── Filters ──
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_pred = st.selectbox("Filter by result", ["All", "Deepfake", "Real"])
            with col_f2:
                filter_source = st.selectbox("Filter by source", ["All"] + list(set(
                    s["source"]["display_name"] for s in scans if s["source"]
                )))
            
            filtered = scans
            if filter_pred != "All":
                filtered = [s for s in filtered if s["prediction"] == filter_pred]
            if filter_source != "All":
                filtered = [s for s in filtered if s["source"] and s["source"]["display_name"] == filter_source]
            
            st.write(f"Showing **{len(filtered)}** results")
            st.markdown("---")
            
            # ── Scan Cards ──
            for scan in filtered:
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 2])
                    
                    with c1:
                        st.markdown(f"** {scan['filename']}**")
                        st.caption(f"{scan['created_at'][:16].replace('T', ' ')}")
                    
                    with c2:
                        conf = scan['confidence']
                        if scan['prediction'] == "Deepfake":
                            st.markdown(f"**Deepfake** — {conf}%")
                        else:
                            st.markdown(f"**Real** — {conf}%")
                    
                    with c3:
                        if scan['source']:
                            st.markdown(f"{scan['source']['display_name']}")
                        else:
                            st.caption("No source")
                        
                        if scan['feedback']:
                            if scan['feedback']['is_correct']:
                                st.caption("✅ Confirmed correct")
                            else:
                                st.caption("❌ Marked incorrect")
                    
                    if scan.get('note'):
                        st.caption(f"{scan['note']}")
                    
                    st.markdown("---")
            
            # ── Export CSV ──
            if st.button("Export to CSV", use_container_width=True):
                rows = []
                for s in filtered:
                    rows.append({
                        "Filename": s["filename"],
                        "Prediction": s["prediction"],
                        "Confidence (%)": s["confidence"],
                        "Processing Time (ms)": s["processing_time_ms"],
                        "Source": s["source"]["display_name"] if s["source"] else "",
                        "Feedback": ("Correct" if s["feedback"]["is_correct"] else "Incorrect") if s["feedback"] else "",
                        "Date": s["created_at"][:16].replace("T", " ")
                    })
                df = pd.DataFrame(rows)
                csv = df.to_csv(index=False)
                st.download_button("⬇Download CSV", csv, "scan_history.csv", "text/csv", use_container_width=True)
    else:
        st.error("Error loading scan history.")
except Exception as e:
    st.error(f"Connection error: {e}")
