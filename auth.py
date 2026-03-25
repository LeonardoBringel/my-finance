import streamlit as st

from crypto import encrypt
from database import get_session
from repositories import UsersRepository

# ── Session ────────────────────────────────────────────────────────────────────


def get_current_user() -> dict | None:
    """Return current user dict from session_state, or None."""
    return st.session_state.get("current_user")


def require_login():
    """Redirect to login if no active session. Call at top of every page."""
    if not get_current_user():
        st.switch_page("pages/login.py")


def require_admin():
    """Redirect to dashboard if user is not admin."""
    user = get_current_user()
    if not user or not user.get("is_admin"):
        st.switch_page("app.py")


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (success, message).
    On success, sets st.session_state["current_user"].
    """
    current_user = UsersRepository.login(username, password)
    if not current_user:
        return False, "Usuário ou senha inválidos."
    st.session_state["current_user"] = current_user
    return True, "Login realizado com sucesso!"


def logout():
    st.session_state.pop("current_user", None)


def create_user(username: str, password: str) -> tuple[bool, str]:
    """Create a new user. First user becomes admin automatically."""
    if not UsersRepository.is_username_available(username):
        return False, "Usuário já existe."
    user = UsersRepository.create_user(username, password)

    with get_session() as session:  # TODO: extract
        # Seed default categories for new user
        _seed_categories(session, user.id)

    return True, f"Usuário '{username}' criado!" + (" (admin)" if is_first else "")


# ── Internal ───────────────────────────────────────────────────────────────────


def _seed_categories(session, user_id: int):
    from crypto import encrypt
    from models import Category

    defaults = [
        ("Casa", "saida"),
        ("Carro", "saida"),
        ("Estudo", "saida"),
        ("Outros", "ambos"),
        ("Recorrente", "saida"),
        ("Gatos", "saida"),
        ("Alimentação", "saida"),
        ("Mercado", "saida"),
        ("Farmácia", "saida"),
        ("Salário", "entrada"),
    ]
    for name, type_ in defaults:
        session.add(
            Category(
                user_id=user_id,
                name=encrypt(name),
                type=encrypt(type_),
            )
        )
