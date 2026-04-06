from datetime import timedelta

import streamlit as st
from streamlit_cookies_controller import CookieController

from repositories import UsersRepository
from utils.session import (
    COOKIE_NAME,
    TOKEN_EXPIRY_DAYS,
    create_session_token,
    decode_session_token,
)


def _get_cookie_controller() -> CookieController:
    """Retorna uma instância do CookieController para gravação/exclusão de cookies.

    Returns:
        Instância do CookieController renderizada no contexto Streamlit atual.
    """
    return CookieController(key="auth_cookie_ctrl")


def _set_session_cookie(token: str) -> None:
    """Grava o JWT de sessão no cookie do browser.

    Args:
        token: Token JWT a armazenar no cookie.
    """
    ctrl = _get_cookie_controller()
    ctrl.set(
        COOKIE_NAME,
        token,
        max_age=int(timedelta(days=TOKEN_EXPIRY_DAYS).total_seconds()),
    )


def _delete_session_cookie() -> None:
    """Remove o cookie de sessão do browser.

    O KeyError é ignorado quando o dict interno do CookieController não tem o cookie
    carregado ainda — o comando JavaScript de remoção já foi enviado ao browser.
    """
    ctrl = _get_cookie_controller()
    try:
        ctrl.remove(COOKIE_NAME)
    except KeyError:
        pass


def get_current_user() -> dict | None:
    """Retorna o dict do usuário autenticado na session_state, ou None se não houver sessão."""
    return st.session_state.get("current_user")


def require_login() -> None:
    """Garante que há uma sessão ativa. Tenta restaurar de cookie JWT antes de redirecionar ao login.

    Lê o cookie diretamente dos headers HTTP via st.context.cookies (síncrono, sem
    problemas de timing). Respeita o flag _logged_out para evitar restaurar sessão
    após logout explícito na mesma conexão WebSocket.
    Deve ser chamado no topo de cada página protegida.
    """
    if get_current_user():
        return

    # Não restaura sessão se o usuário acabou de fazer logout nesta conexão
    if st.session_state.get("_logged_out"):
        st.switch_page("pages/login.py")
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
    st.session_state.pop("_logged_out", None)
    token = create_session_token(current_user["id"])
    _set_session_cookie(token)
    return True, "Login realizado com sucesso!"


def logout() -> None:
    """Remove o usuário da session_state, marca flag de logout e apaga o cookie de sessão."""
    st.session_state.pop("current_user", None)
    st.session_state["_logged_out"] = True
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
