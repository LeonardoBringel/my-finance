from crypto import encrypt
from models import Category

from .base_repository import get_session


class CategoriesRepository:
    @staticmethod
    def create_category(user_id: int, name: str, type: str) -> tuple[bool, str]:
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
        with get_session() as session:
            categories = session.query(Category).filter_by(user_id=user_id).all()
            return sorted(
                [category.to_json() for category in categories],
                key=lambda x: x["name"],
            )

    @staticmethod
    def delete_category(user_id: int, id: int) -> tuple[bool, str]:
        with get_session() as session:
            category = session.get(Category, id)
            if not category or category.user_id != user_id:
                return False, "Categoria não encontrada"
            session.delete(category)
            session.commit()
        return (True, "Categoria removida")
