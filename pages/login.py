import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import inject_global_css
from repositories import init_db
from utils.auth import create_user, login

inject_global_css()

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")
init_db()

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version_file = os.path.join(root_dir, ".version")
app_version = (
    open(version_file).read().strip() if os.path.exists(version_file) else "latest"
)
if "-" in app_version:
    app_version = app_version.split("-")[0]

st.markdown(
    """
<style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 4rem; max-width: 420px; }
</style>
""",
    unsafe_allow_html=True,
)

# Já autenticado → vai para o dashboard
if st.session_state.get("current_user"):
    st.switch_page("pages/dashboard.py")

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

st.markdown(
    f"<p style='text-align: center; color: rgba(255,255,255,0.15); font-size: 0.9rem;'>{app_version}</p>",
    unsafe_allow_html=True,
)
