import streamlit as st
import requests
from extra_streamlit_components import CookieManager
from utils import init_session, handle_auth, render_sidebar, require_auth, API_URL

st.set_page_config(page_title="Profile", initial_sidebar_state="collapsed")

cookie_manager = CookieManager()
init_session()
handle_auth(cookie_manager)
render_sidebar(cookie_manager)
require_auth()

st.title("Profile")
st.markdown("---")

headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}

try:
    res = requests.get(f"{API_URL}/profile/", headers=headers)
    if res.status_code == 200:
        profile = res.json()
        
        # ── Profile Card ──
        st.subheader(f"Hello, {profile['username']}!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Credits", profile["credits"])
        c2.metric("Total Scans", profile["total_scans"])
        c3.metric("Role", profile["role"].capitalize())
        
        st.markdown("---")
        st.caption(f"{profile['email']}")
        st.caption(f"Member since: {profile['member_since'][:10]}")
        st.caption(f"{'Verified' if profile['is_verified'] else 'Not verified'}")
        
        st.markdown("---")
        
        # ── Detection Threshold ──
        st.subheader("Detection Threshold")
        st.caption("Images with a deepfake probability above this value will be classified as Deepfake. Default: 50%.")
        
        current_threshold = profile.get("threshold", 50.0)
        
        with st.form("threshold_form"):
            new_threshold = st.slider(
                "Threshold (%)",
                min_value=0.0,
                max_value=100.0,
                value=current_threshold,
                step=1.0,
            )
            submitted = st.form_submit_button("Save Threshold", use_container_width=True)
        
        if submitted:
            try:
                r = requests.put(
                    f"{API_URL}/profile/",
                    json={"threshold": new_threshold},
                    headers=headers
                )
                if r.status_code == 200:
                    st.success("Threshold updated!")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Error updating threshold"))
            except Exception as e:
                st.error(f"Connection error: {e}")
        
        st.markdown("---")
        
        # ── Edit Username ──
        st.subheader("Edit Username")
        new_username = st.text_input("Username", value=profile["username"], key="edit_username")
        
        if st.button("Save Username", use_container_width=True):
            if new_username.strip() and new_username.strip() != profile["username"]:
                try:
                    r = requests.put(
                        f"{API_URL}/profile/",
                        json={"username": new_username.strip()},
                        headers=headers
                    )
                    if r.status_code == 200:
                        st.session_state["username"] = new_username.strip()
                        st.success("Username updated!")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Error updating username"))
                except Exception as e:
                    st.error(f"Connection error: {e}")
            else:
                st.warning("Please enter a different username.")
        
        st.markdown("---")
        
        # ── Personal Information ──
        st.subheader("Personal Information")
        
        new_name = st.text_input("Full Name", value=profile.get("name") or "", key="edit_name")
        new_address = st.text_input("Address", value=profile.get("address") or "", key="edit_address")
        new_company = st.text_input("Company Name", value=profile.get("company_name") or "", key="edit_company")
        
        if st.button("Save Personal Information", use_container_width=True):
            payload = {}
            if new_name.strip() != (profile.get("name") or ""):
                payload["name"] = new_name.strip()
            if new_address.strip() != (profile.get("address") or ""):
                payload["address"] = new_address.strip()
            if new_company.strip() != (profile.get("company_name") or ""):
                payload["company_name"] = new_company.strip()
            
            if payload:
                try:
                    r = requests.put(
                        f"{API_URL}/profile/",
                        json=payload,
                        headers=headers
                    )
                    if r.status_code == 200:
                        st.success("Personal information updated!")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Error updating profile"))
                except Exception as e:
                    st.error(f"Connection error: {e}")
            else:
                st.info("No changes detected.")
        
        st.markdown("---")
        
        # ── Change Password ──
        st.subheader("Change Password")
        old_pass = st.text_input("Current password", type="password", key="old_pass")
        new_pass = st.text_input("New password", type="password", key="new_pass")
        confirm_pass = st.text_input("Confirm new password", type="password", key="confirm_pass")
        
        if st.button("Change Password", use_container_width=True):
            if not old_pass or not new_pass:
                st.warning("Please fill in all password fields.")
            elif new_pass != confirm_pass:
                st.error("New passwords don't match!")
            elif len(new_pass) < 6:
                st.error("New password must be at least 6 characters.")
            else:
                try:
                    r = requests.put(
                        f"{API_URL}/change-password/",
                        json={"old_password": old_pass, "new_password": new_pass},
                        headers=headers
                    )
                    if r.status_code == 200:
                        st.success("Password changed successfully!")
                    else:
                        st.error(r.json().get("detail", "Error changing password"))
                except Exception as e:
                    st.error(f"Connection error: {e}")
    else:
        st.error("Error loading profile.")
except Exception as e:
    st.error(f"Connection error: {e}")
