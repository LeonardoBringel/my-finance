from models import CashFlowEntry

from .base_repository import get_session


class CashFlowEntryRepository:
    """Repositório para operações de leitura e escrita de lançamentos do fluxo de caixa."""

    @staticmethod
    def add_entry(month_id: int, name: str, day: int, value: float, type_: str) -> None:
        """Adiciona um novo lançamento a um mês do fluxo de caixa."""
        with get_session() as s:
            s.add(
                CashFlowEntry(
                    month_id=month_id, name=name, day=day, value=value, type=type_
                )
            )
            s.commit()

    @staticmethod
    def update_entry(
        entry_id: int, name: str, day: int, value: float, type_: str
    ) -> None:
        """Atualiza os dados de um lançamento existente."""
        with get_session() as s:
            e = s.get(CashFlowEntry, entry_id)
            if not e:
                return
            e.name = name
            e.day = day
            e.value = value
            e.type = type_
            s.commit()

    @staticmethod
    def delete_entry(entry_id: int) -> None:
        """Remove um lançamento pelo seu ID."""
        with get_session() as s:
            e = s.get(CashFlowEntry, entry_id)
            if e:
                s.delete(e)
                s.commit()
