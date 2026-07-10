from sqlalchemy import func

from models import Category, Transaction
from utils.crypto import encrypt
from utils.i18n import t

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
            return (False, t("messages.categories.already_exists"))
        with get_session() as session:
            category = Category(
                name=encrypt(name), type=encrypt(type), user_id=user_id
            )
            session.add(category)
            session.commit()
        return (True, t("messages.categories.added"))

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
            user_category["name"].lower() == name.lower()
            and user_category["id"] != id
            for user_category in user_categories
        ):
            return (False, t("messages.categories.name_taken"))
        with get_session() as session:
            category = (
                session.query(Category)
                .filter_by(user_id=user_id, id=id)
                .first()
            )
            if not category:
                return (False, t("messages.categories.not_found"))
            category.name = encrypt(name)
            category.type = encrypt(type)
            session.commit()
        return (True, t("messages.categories.updated"))

    @staticmethod
    def list_categories(user_id: int, type_: str | None = None) -> list[dict]:
        """Lista as categorias do usuário ordenadas alfabeticamente por nome.

        Args:
            user_id: ID do usuário.
            type_: Filtro opcional por tipo ('entrada' ou 'saida'). Se None, retorna todas.

        Returns:
            Lista de dicts representando as categorias.
        """
        with get_session() as session:
            categories = (
                session.query(Category).filter_by(user_id=user_id).all()
            )
            result = sorted(
                [category.to_json() for category in categories],
                key=lambda x: x["name"],
            )
        if type_ is not None:
            result = [c for c in result if c["type"] == type_]
        return result

    @staticmethod
    def has_any_category(user_id: int) -> bool:
        """Retorna True se o usuário possui ao menos uma categoria cadastrada."""
        with get_session() as session:
            return (
                session.query(Category).filter_by(user_id=user_id).count() > 0
            )

    @staticmethod
    def get_transaction_counts_by_category(user_id: int) -> dict[int, int]:
        """Retorna contagem de transações por category_id para o usuário.

        Returns:
            Dict mapeando category_id para contagem de transações.
        """
        with get_session() as session:
            rows = (
                session.query(
                    Transaction.category_id, func.count(Transaction.id)
                )
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.category_id.isnot(None),
                )
                .group_by(Transaction.category_id)
                .all()
            )
        return {category_id: count for category_id, count in rows}

    @staticmethod
    def delete_category(user_id: int, id: int) -> tuple[bool, str]:
        """Remove uma categoria do usuário pelo ID.

        Returns:
            Tupla (sucesso, mensagem).
        """
        with get_session() as session:
            category = session.get(Category, id)
            if not category or category.user_id != user_id:
                return False, t("messages.categories.not_found")
            session.delete(category)
            session.commit()
        return (True, t("messages.categories.removed"))
