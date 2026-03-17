import streamlit as st
import requests

st.set_page_config(page_title="Autentificare", page_icon="🔒")

# --- GESTIONAREA SESIUNII ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

st.title("Sistem de Detecție Deepfake")

# Dacă utilizatorul NU este logat
if st.session_state['user'] is None:
    
    tab_login, tab_register = st.tabs(["Login", "Register"])
    
    # --- TAB LOGIN ---
    with tab_login:
        email_login = st.text_input("Email", key="login_email").strip().lower()
        pass_login = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary"):
            try:
                # Trimitem datele (JSON) către FastAPI
                response = requests.post(
                    "http://localhost:8000/login/", 
                    json={"email": email_login, "password": pass_login}
                )
                
                if response.status_code == 200:
                    date_primite = response.json()
                    st.session_state['user'] = date_primite['user_email']
                    st.success("Logare reușită!")
                    st.switch_page("pages/2_Detector.py")
                else:
                    st.error("Email sau parolă incorectă!")
                    
            except requests.exceptions.ConnectionError:
                st.error("Nu mă pot conecta la serverul backend. Asigură-te că FastAPI rulează!")
                
    # --- TAB REGISTER ---
    with tab_register:
        email_reg = st.text_input("Email", key="reg_email").strip().lower()
        pass_reg = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Register", type="primary"):
            try:
                # Trimitem datele către FastAPI
                response = requests.post(
                    f"http://localhost:8000/register/?email={email_reg}&password={pass_reg}"
                )
                
                if response.status_code == 200:
                    date_primite = response.json()
                    st.session_state['user'] = date_primite['user_email']
                    st.success("Account created! Redirecting...")
                    st.switch_page("pages/2_Detector.py")
                elif response.status_code == 400:
                    # Afișăm eroarea exactă de la FastAPI (ex: "Acest email este deja înregistrat")
                    st.error(response.json().get("detail", "Eroare la creare"))
                else:
                    st.error("A apărut o eroare necunoscută.")
                    
            except requests.exceptions.ConnectionError:
                st.error("Nu mă pot conecta la serverul backend. Asigură-te că FastAPI rulează!")

# Dacă utilizatorul ESTE logat
else:
    st.success(f"Atenție! Ești deja conectat cu contul {st.session_state['user']}!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mergi la Detector", type="primary"):
            st.switch_page("pages/2_Detector.py")
    with col2:
        if st.button("Deconectare"):
            st.session_state['user'] = None
            st.rerun()