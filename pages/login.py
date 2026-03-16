import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import login, create_user
import database as db

from components.styles import inject_global_css
inject_global_css()

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")
db.init_db()

st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 4rem; max-width: 420px; }
</style>
""", unsafe_allow_html=True)

# Already logged in → go to dashboard
if st.session_state.get("current_user"):
    st.switch_page("app.py")

st.markdown("## 💰 Gestão Financeira")
st.markdown("##### Faça login para continuar")
st.divider()

username = st.text_input("Usuário", placeholder="seu usuário")
password = st.text_input("Senha", type="password", placeholder="sua senha")

if st.button("Entrar", type="primary", use_container_width=True):
    if not username or not password:
        st.error("Preencha usuário e senha.")
    else:
        ok, msg = login(username, password)
        if ok:
            st.rerun()
        else:
            st.error(msg)
