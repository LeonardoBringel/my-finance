import uuid
from datetime import datetime

from dateutil.relativedelta import relativedelta

from models import Category, Transaction
from utils.crypto import decrypt, decrypt_float, encrypt

from .base_repository import get_session


class TransactionsRepository:
    """Repositório para operações de leitura e escrita de transações financeiras."""

    @staticmethod
    def create_transaction(
        user_id: int,
        category_id: int,
        date: str,
        description: str,
        value: float,
        installments: int = 1,
    ) -> None:
        """Cria uma ou mais transações. Gera parcelas consecutivas mensais quando installments > 1."""
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
    ) -> None:
        """Atualiza os campos de uma transação existente pertencente ao usuário."""
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
        user_id: int,
        year: int = None,
        month: int = None,
        day: int = None,
        date_from=None,
        date_to=None,
    ) -> list[dict]:
        """Lista as transações do usuário com filtros opcionais por ano, mês, dia ou intervalo de datas.

        Args:
            user_id: ID do usuário.
            year: Filtro por ano (opcional).
            month: Filtro por mês (opcional).
            day: Filtro por dia (opcional).
            date_from: Filtro de data inicial inclusive (datetime.date, opcional).
            date_to: Filtro de data final inclusive (datetime.date, opcional).

        Returns:
            Lista de dicts com as transações, ordenadas por data decrescente.
        """
        with get_session() as session:
            rows = (
                session.query(Transaction, Category)
                .outerjoin(Category, Transaction.category_id == Category.id)
                .filter(Transaction.user_id == user_id)
                .all()
            )

        results = []
        for transaction, category in rows:
            result = transaction.to_json()
            try:
                txn_date = datetime.strptime(result["date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            if year and txn_date.year != year:
                continue
            if month and txn_date.month != month:
                continue
            if day and txn_date.day != day:
                continue
            if date_from and txn_date.date() < date_from:
                continue
            if date_to and txn_date.date() > date_to:
                continue
            result["category"] = (
                decrypt(category.name) if category else "(sem categoria)"
            )
            result["type"] = decrypt(category.type) if category else "saida"
            results.append(result)

        return sorted(
            results, key=lambda x: (x["date"], x["created_at"] or ""), reverse=True
        )

    @staticmethod
    def has_any_transaction(user_id: int) -> bool:
        """Retorna True se o usuário possui ao menos uma transação cadastrada."""
        with get_session() as session:
            return session.query(Transaction).filter_by(user_id=user_id).count() > 0

    @staticmethod
    def delete_transaction(user_id: int, id: int) -> None:
        """Remove uma transação pelo ID, validando que pertence ao usuário."""
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
        """Retorna lista ordenada e única de descrições de transações, opcionalmente filtrada por categoria."""
        with get_session() as session:
            transactions = session.query(Transaction).filter_by(user_id=user_id).all()

        descriptions = []
        for transaction in transactions:
            if category_id and transaction.category_id != category_id:
                continue
            if transaction.description:
                descriptions.append(decrypt(transaction.description))
        return sorted(set(descriptions))

    # ── Agregações para o Dashboard ────────────────────────────────────────────

    @staticmethod
    def get_monthly_summary(user_id: int, year: int, month: int) -> dict:
        """Retorna totais de entradas, saídas, saldo mensal, saldo acumulado e % de parcelas anteriores.

        Returns:
            Dict com entradas, saidas, saldo, saldo_acumulado e pct_installments.
        """
        txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
        entradas = sum(t["value"] for t in txns if t["type"] == "entrada")
        saidas = sum(t["value"] for t in txns if t["type"] in ("saida", "ambos"))

        installment_saidas = sum(
            t["value"]
            for t in txns
            if t["type"] in ("saida", "ambos")
            and t.get("installment_number")
            and t["installment_number"] > 1
        )
        pct_installments = (installment_saidas / saidas * 100) if saidas > 0 else 0.0

        all_year = TransactionsRepository.list_transactions(user_id, year=year)
        acc_in = sum(
            t["value"]
            for t in all_year
            if t["type"] == "entrada"
            and datetime.strptime(t["date"], "%Y-%m-%d").month <= month
        )
        acc_out = sum(
            t["value"]
            for t in all_year
            if t["type"] in ("saida", "ambos")
            and datetime.strptime(t["date"], "%Y-%m-%d").month <= month
        )

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas,
            "saldo_acumulado": acc_in - acc_out,
            "pct_installments": pct_installments,
        }

    @staticmethod
    def get_expenses_by_category(user_id: int, year: int, month: int) -> list[dict]:
        """Retorna totais de saídas agrupados por categoria, ordenados do maior para o menor."""
        txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
        totals: dict[str, float] = {}
        for t in txns:
            if t["type"] in ("saida", "ambos"):
                totals[t["category"]] = totals.get(t["category"], 0) + t["value"]
        return sorted(
            [{"category": k, "total": v} for k, v in totals.items()],
            key=lambda x: x["total"],
            reverse=True,
        )

    @staticmethod
    def get_income_by_category(user_id: int, year: int, month: int) -> list[dict]:
        """Retorna totais de entradas agrupados por categoria, ordenados do maior para o menor."""
        txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
        totals: dict[str, float] = {}
        for t in txns:
            if t["type"] == "entrada":
                totals[t["category"]] = totals.get(t["category"], 0) + t["value"]
        return sorted(
            [{"category": k, "total": v} for k, v in totals.items()],
            key=lambda x: x["total"],
            reverse=True,
        )

    @staticmethod
    def get_descriptions_by_category_for_dashboard(
        user_id: int, year: int, month: int
    ) -> dict:
        """Retorna detalhamento de saídas por categoria com total atual, anterior e percentual do mês.

        Formato retornado:
            { nome_categoria: { descriptions, total, total_prev, pct_of_month } }
        """
        from dateutil.relativedelta import relativedelta as rd

        from repositories.categories_repository import CategoriesRepository

        all_cats = CategoriesRepository.list_categories(user_id)
        saida_cats = [c for c in all_cats if c["type"] in ("saida", "ambos")]

        txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
        saida_txns = [t for t in txns if t["type"] in ("saida", "ambos")]
        total_month = sum(t["value"] for t in saida_txns)

        prev = datetime(year, month, 1) - rd(months=1)
        prev_txns = TransactionsRepository.list_transactions(
            user_id, year=prev.year, month=prev.month
        )
        prev_saida = [t for t in prev_txns if t["type"] in ("saida", "ambos")]

        result = {}
        for cat in saida_cats:
            cat_txns = [t for t in saida_txns if t["category"] == cat["name"]]
            totals: dict[str, float] = {}
            for t in cat_txns:
                desc = t["description"] or "(sem descrição)"
                totals[desc] = totals.get(desc, 0) + t["value"]
            cat_total = sum(totals.values())

            prev_cat_total = sum(
                t["value"] for t in prev_saida if t["category"] == cat["name"]
            )

            result[cat["name"]] = {
                "descriptions": sorted(
                    [{"description": k, "total": v} for k, v in totals.items()],
                    key=lambda x: x["total"],
                    reverse=True,
                ),
                "total": cat_total,
                "total_prev": prev_cat_total,
                "pct_of_month": (cat_total / total_month * 100)
                if total_month > 0
                else 0.0,
            }

        return result

    @staticmethod
    def get_annual_evolution(user_id: int, year: int) -> list[dict]:
        """Retorna evolução mensal de entradas, saídas e saldo acumulado para o ano.

        Formato retornado:
            [ { month, month_label, entrada, saida, saldo, saldo_acumulado }, ... ]
        """
        month_labels = [
            "Jan",
            "Fev",
            "Mar",
            "Abr",
            "Mai",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Out",
            "Nov",
            "Dez",
        ]
        all_txns = TransactionsRepository.list_transactions(user_id, year=year)

        months = {f"{i:02d}": {"entrada": 0.0, "saida": 0.0} for i in range(1, 13)}
        for t in all_txns:
            try:
                m = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%m")
            except (ValueError, TypeError):
                continue
            if t["type"] == "entrada":
                months[m]["entrada"] += t["value"]
            elif t["type"] in ("saida", "ambos"):
                months[m]["saida"] += t["value"]

        result = []
        saldo_acumulado = 0.0
        for i, (m, v) in enumerate(sorted(months.items())):
            saldo = v["entrada"] - v["saida"]
            saldo_acumulado += saldo
            result.append(
                {
                    "month": m,
                    "month_label": month_labels[int(m) - 1],
                    "entrada": v["entrada"],
                    "saida": v["saida"],
                    "saldo": saldo,
                    "saldo_acumulado": saldo_acumulado,
                }
            )
        return result

    @staticmethod
    def get_available_years(user_id: int) -> list[int]:
        """Retorna os anos com transações registradas, incluindo o ano atual."""
        txns = TransactionsRepository.list_transactions(user_id)
        years = {
            datetime.strptime(t["date"], "%Y-%m-%d").year for t in txns if t.get("date")
        }
        years.add(datetime.now().year)
        return sorted(years)
