import uuid
from datetime import datetime

from dateutil.relativedelta import relativedelta

from crypto import decrypt, decrypt_float, encrypt
from models import Category, Transaction

from .base_repository import get_session


class TransactionsRepository:
    @staticmethod
    def create_transaction(
        user_id: int,
        category_id: int,
        date: str,
        description: str,
        value: float,
        installments: int = 1,
    ):
        installments_group_id = str(uuid.uuid4()) if installments > 1 else None
        base_date = datetime.strptime(date, "%Y-%m-%d")
        installment_value = round(value / installments, 2)
        with get_session() as session:
            for i in range(installments):
                transaction_date = base_date + relativedelta(months=i)
                transaction = Transaction(
                    user_id=user_id,
                    category_id=category_id,
                    date=encrypt(transaction_date.strftime("%Y-%m-%d")),
                    description=encrypt(description) if description else None,
                    value=encrypt(str(installment_value)),
                    installment_group=installments_group_id,
                    installment_number=i + 1 if installments > 1 else None,
                    installment_total=installments if installments > 1 else None,
                )
                session.add(transaction)
            session.commit()

    @staticmethod
    def update_transaction(
        user_id: int, id: int, category_id: int, date: str, description: str, value: str
    ):
        with get_session() as session:
            transaction = session.get(Transaction, id)
            if not transaction or transaction.user_id != user_id:
                return
            transaction.category_id = category_id
            transaction.date = encrypt(date)
            transaction.description = encrypt(description) if description else None
            transaction.value = encrypt(str(value))
            session.commit()

    @staticmethod
    def list_transactions(
        user_id: int, year: int = None, month: int = None, day: int = None
    ) -> list[dict]:
        with get_session() as session:
            rows = (
                session.query(Transaction, Category)
                .outerjoin(Category, Transaction.category_id == Category.id)
                .filter(Transaction.user_id == user_id)
                .all()
            )

        result = []
        for transaction, category in rows:
            category_name = decrypt(category.name) if category else "(sem categoria)"
            category_type = decrypt(category.type) if category else "saida"
            transaction = TransactionsRepository._format_transaction(
                transaction, category_name, category_type
            )
            try:
                date = datetime.strptime(transaction["date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            if year and date.year != year:
                continue
            if month and date.month != month:
                continue
            result.append(transaction)

        return sorted(
            result, key=lambda x: (x["date"], x["created_at"] or ""), reverse=True
        )

    @staticmethod
    def delete_transaction(user_id: int, id: int):
        with get_session() as session:
            transaction = session.get(Transaction, id)
            if not transaction or transaction.user_id != user_id:
                return
            session.delete(transaction)
            session.commit()

    @staticmethod
    def list_descriptions_by_category(
        user_id: int, category_id: int = None
    ) -> list[str]:
        with get_session() as session:
            transactions = session.query(Transaction).filter_by(user_id=user_id).all()

        descriptions = []
        for transaction in transactions:
            if category_id and transaction.category_id != category_id:
                continue
            if transaction.description:
                descriptions.append(decrypt(transaction.description))
        return sorted(set(descriptions))

    @staticmethod
    def _format_transaction(
        transaction: Transaction, category_name: str, category_type: str
    ) -> dict:
        return {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "category_id": transaction.category_id,
            "category": category_name,
            "type": category_type,
            "date": decrypt(transaction.date),
            "description": decrypt(transaction.description),
            "value": decrypt_float(transaction.value),
            "installment_group": transaction.installment_group,
            "installment_number": transaction.installment_number,
            "installment_total": transaction.installment_total,
            "created_at": transaction.created_at.isoformat()
            if transaction.created_at
            else None,
        }
