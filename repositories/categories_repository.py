from models import Category
from utils.crypto import encrypt

from .base_repository import get_session


class CategoriesRepository:
    """Repositório para operações de leitura e escrita de categorias de transação."""

    @staticmethod
    def create_category(user_id: int, name: str, type: str) -> tuple[bool, str]:
        """Cria uma nova categoria para o usuário, validando duplicatas por nome.

        Returns:
            Tupla (sucesso, mensagem).
        """
        user_categories = CategoriesRepository.list_categories(user_id)
        if any(
            user_category["name"].lower() == name.lower()
            for user_category in user_categories
        ):
            return (False, "Categoria já existe")
        with get_session() as session:
            category = Category(name=encrypt(name), type=encrypt(type), user_id=user_id)
            session.add(category)
            session.commit()
        return (True, "Categoria adicionada!")

    @staticmethod
    def update_category(
        user_id: int, id: int, name: str, type: str
    ) -> tuple[bool, str]:
        """Atualiza o nome e tipo de uma categoria do usuário.

        Returns:
            Tupla (sucesso, mensagem).
        """
        user_categories = CategoriesRepository.list_categories(user_id)
        if any(
            user_category["name"].lower() == name.lower() and user_category["id"] != id
            for user_category in user_categories
        ):
            return (False, "Nome já existe.")
        with get_session() as session:
            category = session.query(Category).filter_by(user_id=user_id, id=id).first()
            if not category:
                return (False, "Categoria não encontrada.")
            category.name = encrypt(name)
            category.type = encrypt(type)
            session.commit()
        return (True, "Categoria atualizada!")

    @staticmethod
    def list_categories(user_id: int) -> list[dict]:
        """Lista todas as categorias do usuário ordenadas alfabeticamente por nome."""
        with get_session() as session:
            categories = session.query(Category).filter_by(user_id=user_id).all()
            return sorted(
                [category.to_json() for category in categories],
                key=lambda x: x["name"],
            )

    @staticmethod
    def delete_category(user_id: int, id: int) -> tuple[bool, str]:
        """Remove uma categoria do usuário pelo ID.

        Returns:
            Tupla (sucesso, mensagem).
        """
        with get_session() as session:
            category = session.get(Category, id)
            if not category or category.user_id != user_id:
                return False, "Categoria não encontrada"
            session.delete(category)
            session.commit()
        return (True, "Categoria removida")
