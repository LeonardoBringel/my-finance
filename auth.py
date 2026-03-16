import bcrypt
import streamlit as st
from database import get_session
from models import User
from crypto import encrypt, decrypt


# ── Password hashing ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


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
    with get_session() as session:
        users = session.query(User).all()
        for u in users:
            if decrypt(u.username) == username:
                if verify_password(password, u.password_hash):
                    st.session_state["current_user"] = {
                        "id":       u.id,
                        "username": username,
                        "is_admin": u.is_admin,
                    }
                    return True, "Login realizado com sucesso!"
        return False, "Usuário ou senha inválidos."


def logout():
    st.session_state.pop("current_user", None)


# ── User management ────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> tuple[bool, str]:
    """Create a new user. First user becomes admin automatically."""
    with get_session() as session:
        # Check duplicate (decrypt all usernames)
        existing = session.query(User).all()
        for u in existing:
            if decrypt(u.username) == username:
                return False, "Usuário já existe."

        is_first = session.query(User).count() == 0

        new_user = User(
            username=encrypt(username),
            password_hash=hash_password(password),
            is_admin=is_first,
        )
        session.add(new_user)
        session.flush()

        # Seed default categories for new user
        _seed_categories(session, new_user.id)
        session.commit()

    return True, f"Usuário '{username}' criado!" + (" (admin)" if is_first else "")


def change_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return False, "Usuário não encontrado."
        if not verify_password(current_password, user.password_hash):
            return False, "Senha atual incorreta."
        user.password_hash = hash_password(new_password)
        session.commit()
    return True, "Senha alterada com sucesso!"


def admin_reset_password(user_id: int, new_password: str) -> tuple[bool, str]:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return False, "Usuário não encontrado."
        user.password_hash = hash_password(new_password)
        session.commit()
    return True, "Senha redefinida com sucesso!"


def list_users() -> list[dict]:
    with get_session() as session:
        users = session.query(User).order_by(User.id).all()
        return [
            {
                "id":         u.id,
                "username":   decrypt(u.username),
                "is_admin":   u.is_admin,
                "created_at": u.created_at,
            }
            for u in users
        ]


def delete_user(user_id: int) -> tuple[bool, str]:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return False, "Usuário não encontrado."
        session.delete(user)
        session.commit()
    return True, "Usuário removido."


# ── Internal ───────────────────────────────────────────────────────────────────

def _seed_categories(session, user_id: int):
    from models import Category
    from crypto import encrypt

    defaults = [
        ("Casa", "saida"), ("Carro", "saida"), ("Estudo", "saida"),
        ("Outros", "ambos"), ("Recorrente", "saida"), ("Gatos", "saida"),
        ("Alimentação", "saida"), ("Mercado", "saida"), ("Farmácia", "saida"),
        ("Salário", "entrada"),
    ]
    for name, type_ in defaults:
        session.add(Category(
            user_id=user_id,
            name=encrypt(name),
            type=encrypt(type_),
        ))
