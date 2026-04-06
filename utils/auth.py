from datetime import datetime, timedelta, timezone

import extra_streamlit_components as stx
import streamlit as st

from repositories import UsersRepository
from utils.session import (
    COOKIE_NAME,
    TOKEN_EXPIRY_DAYS,
    create_session_token,
    decode_session_token,
)


@st.cache_resource
def _get_cookie_manager() -> stx.CookieManager:
    """Retorna a instância singleton do CookieManager (cached por processo).

    Returns:
        Instância do CookieManager do extra-streamlit-components.
    """
    return stx.CookieManager()


def _set_session_cookie(token: str) -> None:
    """Grava o JWT de sessão no cookie do browser via CookieManager.

    Args:
        token: Token JWT a armazenar no cookie.
    """
    cm = _get_cookie_manager()
    expires_at = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    cm.set(COOKIE_NAME, token, expires_at=expires_at, key="set_session")


def _delete_session_cookie() -> None:
    """Remove o cookie de sessão via CookieManager."""
    cm = _get_cookie_manager()
    cm.delete(COOKIE_NAME, key="del_session")


def get_current_user() -> dict | None:
    """Retorna o dict do usuário autenticado na session_state, ou None se não houver sessão."""
    return st.session_state.get("current_user")


def require_login() -> None:
    """Garante que há uma sessão ativa. Tenta restaurar de cookie JWT antes de redirecionar ao login.

    Lê o cookie diretamente dos headers HTTP via st.context.cookies (síncrono, sem
    problemas de timing). Deve ser chamado no topo de cada página protegida.
    """
    if get_current_user():
        return

    token = st.context.cookies.get(COOKIE_NAME)
    if token:
        user_id = decode_session_token(token)
        if user_id:
            user = UsersRepository.get_user_by_id(user_id)
            if user:
                st.session_state["current_user"] = user
                return

    st.switch_page("pages/login.py")


def require_admin() -> None:
    """Redireciona para o dashboard se o usuário não for administrador."""
    user = get_current_user()
    if not user or not user.get("is_admin"):
        st.switch_page("pages/dashboard.py")


def login(username: str, password: str) -> tuple[bool, str]:
    """Tenta autenticar o usuário. Em caso de sucesso, persiste na session_state e grava cookie JWT.

    Args:
        username: Nome do usuário.
        password: Senha em texto plano.

    Returns:
        Tupla (sucesso, mensagem).
    """
    current_user = UsersRepository.login(username, password)
    if not current_user:
        return False, "Usuário ou senha inválidos."
    st.session_state["current_user"] = current_user
    token = create_session_token(current_user["id"])
    _set_session_cookie(token)
    return True, "Login realizado com sucesso!"


def logout() -> None:
    """Remove o usuário da session_state e apaga o cookie de sessão."""
    st.session_state.pop("current_user", None)
    _delete_session_cookie()


def create_user(username: str, password: str) -> tuple[bool, str]:
    """Cria um novo usuário. O primeiro usuário registrado recebe permissão de administrador.

    Args:
        username: Nome de usuário desejado.
        password: Senha em texto plano.

    Returns:
        Tupla (sucesso, mensagem).
    """
    if not UsersRepository.is_username_available(username):
        return False, "Usuário já existe."
    user = UsersRepository.create_user(username, password)
    return True, f"Usuário '{username}' criado!" + (" (admin)" if user.is_admin else "")
