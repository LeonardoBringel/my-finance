import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import inject_global_css, page_header
from repositories import UsersRepository
from utils.auth import logout, require_login
from utils.i18n import t
from utils.password_utils import validate_password

inject_global_css()

st.set_page_config(
    page_title=t("pages.profile.page_title"),
    page_icon="👤",
    layout="centered",
)

st.markdown(
    """
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 2rem; max-width: 480px; }
</style>
""",
    unsafe_allow_html=True,
)

require_login()
current = st.session_state["current_user"]

page_header(
    t("pages.profile.header", username=current["username"]),
    cleanup_keys=["show_form", "form_reset_counter"],
)

st.divider()
st.markdown(t("pages.profile.change_password"))

current_pass = st.text_input(
    t("pages.profile.current_password"), type="password"
)
new_pass = st.text_input(t("pages.profile.new_password"), type="password")
confirm_pass = st.text_input(
    t("pages.profile.confirm_password"), type="password"
)

if st.button(t("pages.profile.save"), type="primary", use_container_width=True):
    if not current_pass or not new_pass or not confirm_pass:
        st.error(t("pages.profile.empty_fields"))
    elif new_pass != confirm_pass:
        st.error(t("pages.profile.password_mismatch"))
    elif not validate_password(new_pass)[0]:
        st.error(validate_password(new_pass)[1])
    else:
        ok, msg = UsersRepository.update_user_password(
            current["id"], current_pass, new_pass
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)

st.divider()
if st.button(t("pages.profile.logout"), use_container_width=True):
    logout()
    # Sem st.switch_page() — o CookieController aciona o rerun naturalmente após
    # remover o cookie; require_login() redireciona para login nesse rerun.
