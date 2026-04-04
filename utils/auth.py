import streamlit as st

from repositories import UsersRepository
from repositories.base_repository import get_session


def get_current_user() -> dict | None:
    """Retorna o dict do usuário autenticado na session_state, ou None se não houver sessão."""
    return st.session_state.get("current_user")


def require_login() -> None:
    """Redireciona para a página de login se não houver sessão ativa. Deve ser chamado no topo de cada página."""
    if not get_current_user():
        st.switch_page("pages/login.py")


def require_admin() -> None:
    """Redireciona para o dashboard se o usuário não for administrador."""
    user = get_current_user()
    if not user or not user.get("is_admin"):
        st.switch_page("pages/dashboard.py")


def login(username: str, password: str) -> tuple[bool, str]:
    """Tenta autenticar o usuário. Em caso de sucesso, persiste o usuário na session_state.

    Returns:
        Tupla (sucesso, mensagem).
    """
    current_user = UsersRepository.login(username, password)
    if not current_user:
        return False, "Usuário ou senha inválidos."
    st.session_state["current_user"] = current_user
    return True, "Login realizado com sucesso!"


def logout() -> None:
    """Remove o usuário da session_state, encerrando a sessão."""
    st.session_state.pop("current_user", None)


def create_user(username: str, password: str) -> tuple[bool, str]:
    """Cria um novo usuário. O primeiro usuário registrado recebe permissão de administrador.

    Returns:
        Tupla (sucesso, mensagem).
    """
    if not UsersRepository.is_username_available(username):
        return False, "Usuário já existe."
    user = UsersRepository.create_user(username, password)

    with get_session() as session:
        _seed_categories(session, user.id)

    return True, f"Usuário '{username}' criado!" + (" (admin)" if user.is_admin else "")


def _seed_categories(session, user_id: int) -> None:
    """Popula as categorias padrão para um novo usuário."""
    from models import Category
    from utils.crypto import encrypt

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
