import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_login, require_admin, create_user, admin_reset_password, delete_user, list_users
import database as db

st.set_page_config(page_title="Administração", page_icon="👥", layout="wide")
db.init_db()

st.markdown("""
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

require_login()
require_admin()

current = st.session_state["current_user"]

col_title, col_back = st.columns([4, 1])
with col_title:
    st.markdown("## 👥 Gerenciar Usuários")
with col_back:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("app.py")

st.divider()

# ── Create User ────────────────────────────────────────────────────────────────
with st.expander("➕ Novo Usuário", expanded=False):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_username = st.text_input("Usuário", key="new_user_name")
    with col2:
        new_password = st.text_input("Senha", type="password", key="new_user_pass")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Criar", type="primary", use_container_width=True):
            if not new_username or not new_password:
                st.error("Preencha usuário e senha.")
            else:
                ok, msg = create_user(new_username, new_password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ── User List ──────────────────────────────────────────────────────────────────
users = list_users()
st.markdown(f"**{len(users)} usuário(s) cadastrado(s)**")
st.divider()

if not users:
    st.info("Nenhum usuário encontrado.")
else:
    header = st.columns([2.5, 1.5, 2, 1, 1])
    for h, label in zip(header, ["Usuário", "Perfil", "Criado em", "🔑", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for u in users:
        cols = st.columns([2.5, 1.5, 2, 1, 1])
        cols[0].markdown(u["username"])
        cols[1].markdown("👑 Admin" if u["is_admin"] else "👤 Usuário")
        cols[2].markdown(u["created_at"].strftime("%d/%m/%Y") if u["created_at"] else "—")

        # Reset password
        if cols[3].button("🔑", key=f"reset_{u['id']}"):
            st.session_state[f"resetting_{u['id']}"] = True

        # Delete (can't delete yourself)
        if u["id"] != current["id"]:
            if cols[4].button("🗑️", key=f"del_u_{u['id']}"):
                st.session_state[f"confirm_del_u_{u['id']}"] = True

        # Reset password form
        if st.session_state.get(f"resetting_{u['id']}"):
            with st.container():
                r1, r2, r3 = st.columns([2, 2, 1])
                with r1:
                    new_pass = st.text_input("Nova senha", type="password",
                                             key=f"new_pass_{u['id']}")
                with r2:
                    confirm_pass = st.text_input("Confirmar", type="password",
                                                 key=f"conf_pass_{u['id']}")
                with r3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾", key=f"save_pass_{u['id']}", type="primary"):
                        if not new_pass:
                            st.error("Digite a nova senha.")
                        elif new_pass != confirm_pass:
                            st.error("Senhas não conferem.")
                        else:
                            ok, msg = admin_reset_password(u["id"], new_pass)
                            if ok:
                                st.success(msg)
                                st.session_state.pop(f"resetting_{u['id']}", None)
                                st.rerun()
                            else:
                                st.error(msg)
                    if st.button("❌", key=f"cancel_reset_{u['id']}"):
                        st.session_state.pop(f"resetting_{u['id']}", None)
                        st.rerun()

        # Delete confirm
        if st.session_state.get(f"confirm_del_u_{u['id']}"):
            st.warning(f"⚠️ Excluir usuário **{u['username']}** e todos os seus dados?")
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("✅ Confirmar", key=f"conf_del_u_{u['id']}", type="primary"):
                delete_user(u["id"])
                st.session_state.pop(f"confirm_del_u_{u['id']}", None)
                st.rerun()
            if c2.button("❌ Cancelar", key=f"canc_del_u_{u['id']}"):
                st.session_state.pop(f"confirm_del_u_{u['id']}", None)
                st.rerun()
