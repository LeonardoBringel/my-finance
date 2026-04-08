from models import User
from utils import password_utils
from utils.crypto import encrypt

from .base_repository import get_session


class UsersRepository:
    """Repositório para operações de leitura e escrita de usuários."""

    @staticmethod
    def is_username_available(username: str) -> bool:
        """Verifica se o nome de usuário não está em uso."""
        with get_session() as session:
            users = session.query(User).all()
            for user in users:
                if user.get_username() == username:
                    return False
        return True

    @staticmethod
    def create_user(username: str, password: str) -> dict:
        """Cria um novo usuário. O primeiro usuário cadastrado recebe permissão de administrador."""
        with get_session() as session:
            is_first_user = session.query(User).count() == 0
            user = User(
                username=encrypt(username),
                password_hash=password_utils.hash_password(password),
                is_admin=is_first_user,
            )
            session.add(user)
            session.commit()
            return {"id": user.id, "username": username, "is_admin": user.is_admin}

    @staticmethod
    def _update_user_password(
        user_id: int,
        new_password: str,
        current_password: str = None,
        force_as_admin: bool = False,
    ) -> tuple[bool, str]:
        """Atualiza a senha do usuário. Verifica a senha atual, exceto quando force_as_admin=True."""
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return (False, "Usuário não encontrado.")
            if not force_as_admin:
                if not password_utils.verify_password(
                    current_password, user.password_hash
                ):
                    return (False, "Senha atual incorreta.")
            user.password_hash = password_utils.hash_password(new_password)
            session.commit()
        return (True, "Senha alterada com sucesso!")

    @staticmethod
    def update_user_password(
        user_id: int, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        """Altera a senha do próprio usuário, exigindo a senha atual para confirmação."""
        return UsersRepository._update_user_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
        )

    @staticmethod
    def admin_update_user_password(user_id: int, new_password: str) -> tuple[bool, str]:
        """Altera a senha de qualquer usuário sem exigir a senha atual (uso exclusivo de admins)."""
        return UsersRepository._update_user_password(
            user_id=user_id, new_password=new_password, force_as_admin=True
        )

    @staticmethod
    def list_users() -> list[dict]:
        """Lista todos os usuários cadastrados ordenados por ID."""
        with get_session() as session:
            users = session.query(User).order_by(User.id).all()
            return [user.to_json() for user in users]

    @staticmethod
    def delete_user(user_id: int) -> tuple[bool, str]:
        """Remove um usuário e todos os seus dados associados (cascade).

        Returns:
            Tupla (sucesso, mensagem).
        """
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False, "Usuário não encontrado."
            session.delete(user)
            session.commit()
        return True, "Usuário removido."

    @staticmethod
    def get_user_by_id(user_id: int) -> dict | None:
        """Retorna o dict do usuário pelo ID, ou None se não encontrado.

        Returns:
            Dict com id, username e is_admin, ou None.
        """
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.get_username(),
                "is_admin": user.is_admin,
            }

    @staticmethod
    def login(username: str, password: str) -> dict | None:
        """Autentica o usuário verificando nome e senha.

        Returns:
            Dict com id, username e is_admin em caso de sucesso, ou None.
        """
        with get_session() as session:
            users = session.query(User).all()
            for user in users:
                if user.get_username() == username:
                    if not password_utils.verify_password(password, user.password_hash):
                        break
                    return {
                        "id": user.id,
                        "username": username,
                        "is_admin": user.is_admin,
                    }
