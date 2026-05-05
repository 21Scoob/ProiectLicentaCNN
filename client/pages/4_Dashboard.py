import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Dashboard", initial_sidebar_state="collapsed")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

st.title("Dashboard")
st.markdown("---")

headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}

try:
    res = requests.get(f"{API_URL}/stats/", headers=headers)
    if res.status_code == 200:
        stats = res.json()
        
        # ── Top Metrics ──
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Scans", stats["total_scans"])
        m2.metric("Credits Left", stats["current_credits"])
        m3.metric("Credits Spent", stats["total_credits_spent"])
        m4.metric("Avg Confidence", f"{stats['avg_confidence']}%")
        
        st.markdown("---")
        
        # ── Detection Breakdown ──
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Detection Breakdown")
            total = stats["total_scans"]
            if total > 0:
                deepfake_pct = round(stats["deepfake_count"] / total * 100, 1)
                real_pct = round(stats["real_count"] / total * 100, 1)
                
                st.markdown(f"**Deepfake:** {stats['deepfake_count']} ({deepfake_pct}%)")
                st.progress(deepfake_pct / 100)
                
                st.markdown(f"**Real:** {stats['real_count']} ({real_pct}%)")
                st.progress(real_pct / 100)
            else:
                st.info("No scans yet.")
        
        with col2:
            st.subheader("Model Accuracy")
            if stats["accuracy_from_feedback"] is not None:
                acc = stats["accuracy_from_feedback"]
                st.markdown(f"Based on **{stats['feedback_total']}** user feedbacks:")
                st.markdown(f"### {'🟢' if acc >= 70 else '🟡' if acc >= 50 else '🔴'} {acc}%")
                st.progress(acc / 100)
                st.caption(f"{stats['feedback_correct']}/{stats['feedback_total']} confirmed correct")
            else:
                st.info("No feedback data yet. Rate scan results to see accuracy here.")
        
        st.markdown("---")
        
        # ── Scans Per Day Chart ──
        st.subheader("Scan Activity")
        spd = stats.get("scans_per_day", {})
        if spd:
            import pandas as pd
            df = pd.DataFrame(list(spd.items()), columns=["Date", "Scans"])
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            st.bar_chart(df)
        else:
            st.info("No scan activity data.")
        
        st.markdown("---")
        
        # ── Additional Info ──
        st.subheader("Account Info")
        c1, c2 = st.columns(2)
        c1.markdown(f"**Member since:** {stats['member_since'][:10]}")
        c2.markdown(f"**Avg processing time:** {stats['avg_processing_time_ms']}ms")
        
        # ── Source Veridicity ──
        st.markdown("---")
        st.subheader("Source Veridicity")
        try:
            src_res = requests.get(f"{API_URL}/source-stats/", headers=headers)
            if src_res.status_code == 200:
                src_stats = src_res.json()
                if src_stats:
                    for s in sorted(src_stats, key=lambda x: x["veridicity_percentage"], reverse=True):
                        v = s["veridicity_percentage"]
                        icon = "🟢" if v >= 70 else "🟡" if v >= 40 else "🔴"
                        st.markdown(f"{icon} **{s['display_name']}** — {v}% veridicity ({s['real_count']}/{s['total_scans']} real)")
                        st.progress(v / 100)
                else:
                    st.info("No source data yet. Add sources when scanning to see veridicity stats.")
        except Exception:
            st.warning("Could not load source stats.")

    else:
        st.error("Error loading dashboard data.")
except Exception as e:
    st.error(f"Connection error: {e}")
