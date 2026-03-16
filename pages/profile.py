import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_login, change_password, logout
import database as db

st.set_page_config(page_title="Perfil", page_icon="👤", layout="centered")
db.init_db()

st.markdown("""
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 2rem; max-width: 480px; }
</style>
""", unsafe_allow_html=True)

require_login()
current = st.session_state["current_user"]

col_title, col_back = st.columns([3, 1])
with col_title:
    st.markdown(f"## 👤 Perfil — {current['username']}")
with col_back:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("app.py")

st.divider()
st.markdown("### 🔑 Alterar Senha")

current_pass  = st.text_input("Senha atual",    type="password")
new_pass      = st.text_input("Nova senha",      type="password")
confirm_pass  = st.text_input("Confirmar nova senha", type="password")

if st.button("💾 Salvar", type="primary", use_container_width=True):
    if not current_pass or not new_pass or not confirm_pass:
        st.error("Preencha todos os campos.")
    elif new_pass != confirm_pass:
        st.error("Nova senha e confirmação não conferem.")
    elif len(new_pass) < 4:
        st.error("A nova senha deve ter ao menos 4 caracteres.")
    else:
        ok, msg = change_password(current["id"], current_pass, new_pass)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

st.divider()
if st.button("🚪 Sair", use_container_width=True):
    logout()
    st.switch_page("pages/login.py")
