import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import inject_global_css
from utils.auth import login

inject_global_css()

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

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

logging_in = st.session_state.get("logging_in", False)

username = st.text_input(
    "Usuário", placeholder="seu usuário", key="login_username", disabled=logging_in
)
password = st.text_input(
    "Senha",
    type="password",
    placeholder="sua senha",
    key="login_password",
    disabled=logging_in,
)

if st.button("Entrar", type="primary", use_container_width=True, disabled=logging_in):
    if not username or not password:
        st.error("Preencha usuário e senha.")
    else:
        st.session_state["logging_in"] = True
        st.rerun()

if logging_in:
    with st.spinner("Autenticando..."):
        ok, msg = login(
            st.session_state.get("login_username", ""),
            st.session_state.get("login_password", ""),
        )
    st.session_state.pop("logging_in", None)
    if not ok:
        st.error(msg)
    # Sem st.rerun() — o CookieController aciona o rerun naturalmente após
    # gravar o cookie no browser; o check de current_user no topo da página
    # redireciona para o dashboard nesse rerun.

st.markdown(
    f"<p style='text-align: center; color: rgba(255,255,255,0.15); font-size: 0.9rem;'>{app_version}</p>",
    unsafe_allow_html=True,
)
