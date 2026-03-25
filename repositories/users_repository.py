from crypto import encrypt, hash_password, verify_password
from models import User

from .base_repository import get_session


class UsersRepository:
    @staticmethod
    def is_username_available(username: str) -> bool:
        with get_session() as session:
            users = session.query(User).all()
            for (
                user
            ) in users:  # TODO: this can be simplified by adding hashed username field
                if user.get_username() == username:
                    return False
        return True

    @staticmethod
    def create_user(username: str, password: str) -> User:
        with get_session() as session:
            # first user is admin by default
            is_first_user = session.query(User).count() == 0
            user = User(
                username=encrypt(username),
                password_hash=hash_password(password),
                is_admin=is_first_user,
            )
            session.add(user)
            session.commit()
            return user

    @staticmethod
    def _update_user_password(
        user_id: int,
        new_password: str,
        current_password: str = None,
        force_as_admin: bool = False,
    ):
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return (False, "Usuário não encontrado.")
            if not force_as_admin:  # skip password check if admin
                if not verify_password(current_password, user.password_hash):
                    retun(False, "Senha atual incorreta.")
            user.password_hash = hash_password(new_password)
            session.commit()
        return (True, "Senha alterada com sucesso!")

    @staticmethod
    def update_user_password(
        user_id: int, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        return UsersRepository._update_user_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
        )

    @staticmethod
    def admin_update_user_password(user_id: int, new_password: str) -> tuple[bool, str]:
        return UsersRepository._update_user_password(
            user_id=user_id, new_password=new_password, force_as_admin=True
        )

    @staticmethod
    def list_users() -> list[dict]:
        with get_session() as session:
            users = session.query(User).order_by(User.id).all()
            return [user.to_json() for user in users]

    @staticmethod
    def delete_user(user_id: int) -> tuple[bool, str]:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "Usuário não encontrado."
            session.delete(user)
            session.commit()
        return True, "Usuário removido."

    @staticmethod
    def login(username: str, password: str):
        with get_session() as session:
            users = session.query(User).all()
            for user in users:
                if user.get_username() == username:
                    if not verify_password(password, user.password_hash):
                        break
                    return {
                        "id": user.id,
                        "username": username,
                        "is_admin": user.is_admin,
                    }
