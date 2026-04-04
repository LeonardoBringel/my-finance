from models import CashFlowEntry, CashFlowMonth, CashFlowTemplate

from .base_repository import get_session


class CashFlowMonthRepository:
    """Repositório para operações de leitura e escrita dos meses do fluxo de caixa."""

    @staticmethod
    def has_any_month(user_id: int) -> bool:
        """Retorna True se o usuário já criou algum mês de fluxo de caixa."""
        with get_session() as s:
            return s.query(CashFlowMonth).filter_by(user_id=user_id).count() > 0

    @staticmethod
    def list_months(user_id: int, year: int) -> list[dict]:
        """Lista os meses criados pelo usuário em um determinado ano."""
        with get_session() as s:
            months = (
                s.query(CashFlowMonth)
                .filter_by(user_id=user_id, year=year)
                .order_by(CashFlowMonth.month)
                .all()
            )
            return [{"id": m.id, "year": m.year, "month": m.month} for m in months]

    @staticmethod
    def get_month_with_entries(user_id: int, year: int, month: int) -> dict | None:
        """Retorna um mês com todos os seus lançamentos, ou None se não existir."""
        with get_session() as s:
            m = (
                s.query(CashFlowMonth)
                .filter_by(user_id=user_id, year=year, month=month)
                .first()
            )
            if not m:
                return None
            return CashFlowMonthRepository._month_to_dict(m)

    @staticmethod
    def create_month(user_id: int, year: int, month: int) -> dict:
        """Cria um mês e preenche com os itens do template, se existir."""
        with get_session() as s:
            existing = (
                s.query(CashFlowMonth)
                .filter_by(user_id=user_id, year=year, month=month)
                .first()
            )
            if existing:
                return CashFlowMonthRepository._month_to_dict(existing)

            m = CashFlowMonth(user_id=user_id, year=year, month=month)
            s.add(m)
            s.flush()

            tmpl = s.query(CashFlowTemplate).filter_by(user_id=user_id).first()
            if tmpl:
                for item in tmpl.items:
                    s.add(
                        CashFlowEntry(
                            month_id=m.id,
                            name=item.name,
                            day=min(item.day, 28),  # seguro para todos os meses
                            value=item.value,
                            type=item.type,
                        )
                    )
            s.commit()
            s.refresh(m)
            return CashFlowMonthRepository._month_to_dict(m)

    @staticmethod
    def delete_month(user_id: int, month_id: int) -> None:
        """Remove um mês e todos os seus lançamentos (cascade)."""
        with get_session() as s:
            m = s.get(CashFlowMonth, month_id)
            if m and m.user_id == user_id:
                s.delete(m)
                s.commit()

    @staticmethod
    def _month_to_dict(m: CashFlowMonth) -> dict:
        """Serializa um CashFlowMonth com seus lançamentos para dict."""
        return {
            "id": m.id,
            "year": m.year,
            "month": m.month,
            "entries": [
                {
                    "id": e.id,
                    "name": e.name,
                    "day": e.day,
                    "value": float(e.value),
                    "type": e.type,
                }
                for e in sorted(m.entries, key=lambda x: (x.day, x.type))
            ],
        }
