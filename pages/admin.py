import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import inject_global_css, inject_subpage_css, page_header
from repositories import TransactionsRepository, UsersRepository
from utils.auth import (
    create_user,
    require_admin,
    require_login,
)
from utils.i18n import t
from utils.password_utils import validate_password

inject_global_css()

st.set_page_config(
    page_title=t("pages.admin.page_title"),
    page_icon="👥",
    layout="wide",
)

inject_subpage_css()

require_login()
require_admin()

current = st.session_state["current_user"]

page_header(
    t("pages.admin.header"),
    cleanup_keys=["show_form", "form_reset_counter"],
)

st.divider()

# ── Criar Usuário ──────────────────────────────────────────────────────────────
with st.expander(t("pages.admin.new_user"), expanded=False):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_username = st.text_input(
            t("pages.admin.username"), key="new_user_name"
        )
    with col2:
        new_password = st.text_input(
            t("pages.admin.password"), type="password", key="new_user_pass"
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            t("pages.admin.create"), type="primary", use_container_width=True
        ):
            if not new_username or not new_password:
                st.error(t("pages.admin.empty_fields"))
            else:
                ok, msg = create_user(new_username, new_password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ── Lista de Usuários ──────────────────────────────────────────────────────────
users = UsersRepository.list_users()
users_stats = TransactionsRepository.get_all_users_stats()
st.markdown(t("pages.admin.count", count=len(users)))
st.divider()

if not users:
    st.info(t("pages.admin.none_found"))
else:
    header = st.columns([2, 1.2, 1.5, 1, 1.5, 0.8, 0.8])
    for h, label in zip(
        header,
        [
            t("pages.admin.col_username"),
            t("pages.admin.col_role"),
            t("pages.admin.col_created"),
            t("pages.admin.col_transactions"),
            t("pages.admin.col_last_transaction"),
            "🔑",
            "🗑️",
        ],
    ):
        h.markdown(f"**{label}**")
    st.divider()

    for u in users:
        cols = st.columns([2, 1.2, 1.5, 1, 1.5, 0.8, 0.8])
        stats = users_stats.get(u["id"], {})
        cols[0].markdown(u["username"])
        cols[1].markdown(
            t("pages.admin.role_admin")
            if u["is_admin"]
            else t("pages.admin.role_user")
        )
        cols[2].markdown(
            u["created_at"].strftime("%d/%m/%Y")
            if u["created_at"]
            else t("common.empty_cell")
        )
        cols[3].markdown(str(stats.get("count", 0)))
        last_at = stats.get("last_at")
        cols[4].markdown(
            last_at.strftime("%d/%m/%Y") if last_at else t("common.empty_cell")
        )

        if cols[5].button("🔑", key=f"reset_{u['id']}"):
            st.session_state[f"resetting_{u['id']}"] = True

        if u["id"] != current["id"]:
            if cols[6].button("🗑️", key=f"del_u_{u['id']}"):
                st.session_state[f"confirm_del_u_{u['id']}"] = True

        if st.session_state.get(f"resetting_{u['id']}"):
            with st.container():
                r1, r2, r3 = st.columns([2, 2, 1])
                with r1:
                    new_pass = st.text_input(
                        t("pages.admin.new_password"),
                        type="password",
                        key=f"new_pass_{u['id']}",
                    )
                with r2:
                    confirm_pass = st.text_input(
                        t("pages.admin.confirm_password"),
                        type="password",
                        key=f"conf_pass_{u['id']}",
                    )
                with r3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(
                        "💾", key=f"save_pass_{u['id']}", type="primary"
                    ):
                        if not new_pass:
                            st.error(t("pages.admin.empty_password"))
                        elif new_pass != confirm_pass:
                            st.error(t("pages.admin.password_mismatch"))
                        elif not validate_password(new_pass)[0]:
                            st.error(validate_password(new_pass)[1])
                        else:
                            ok, msg = (
                                UsersRepository.admin_update_user_password(
                                    u["id"], new_pass
                                )
                            )
                            if ok:
                                st.success(msg)
                                st.session_state.pop(
                                    f"resetting_{u['id']}", None
                                )
                                st.rerun()
                            else:
                                st.error(msg)
                    if st.button("❌", key=f"cancel_reset_{u['id']}"):
                        st.session_state.pop(f"resetting_{u['id']}", None)
                        st.rerun()

        if st.session_state.get(f"confirm_del_u_{u['id']}"):
            st.warning(t("pages.admin.confirm_delete", username=u["username"]))
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button(
                t("pages.admin.confirm"),
                key=f"conf_del_u_{u['id']}",
                type="primary",
            ):
                UsersRepository.delete_user(u["id"])
                st.session_state.pop(f"confirm_del_u_{u['id']}", None)
                st.rerun()
            if c2.button(t("pages.admin.cancel"), key=f"canc_del_u_{u['id']}"):
                st.session_state.pop(f"confirm_del_u_{u['id']}", None)
                st.rerun()
