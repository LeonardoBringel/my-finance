from models import (
    CashFlowEntry,
    CashFlowMonth,
    CashFlowTemplate,
    CashFlowTemplateItem,
)

from .base_repository import get_session


class CashFlowRepository:

    # ── Template ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_template(user_id: int) -> dict | None:
        with get_session() as s:
            tmpl = s.query(CashFlowTemplate).filter_by(user_id=user_id).first()
            if not tmpl:
                return None
            return {
                "id": tmpl.id,
                "items": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "day": i.day,
                        "value": float(i.value),
                        "type": i.type,
                    }
                    for i in sorted(tmpl.items, key=lambda x: (x.type, x.day))
                ],
            }

    @staticmethod
    def save_template(user_id: int, items: list[dict]) -> None:
        """Create or fully replace the user's template items."""
        with get_session() as s:
            tmpl = s.query(CashFlowTemplate).filter_by(user_id=user_id).first()
            if not tmpl:
                tmpl = CashFlowTemplate(user_id=user_id)
                s.add(tmpl)
                s.flush()
            else:
                s.query(CashFlowTemplateItem).filter_by(template_id=tmpl.id).delete()
            for item in items:
                s.add(
                    CashFlowTemplateItem(
                        template_id=tmpl.id,
                        name=item["name"],
                        day=int(item["day"]),
                        value=item["value"],
                        type=item["type"],
                    )
                )
            s.commit()

    # ── Months ─────────────────────────────────────────────────────────────────

    @staticmethod
    def has_any_month(user_id: int) -> bool:
        """Returns True if user has ever created any cash flow month."""
        with get_session() as s:
            return s.query(CashFlowMonth).filter_by(user_id=user_id).count() > 0

    @staticmethod
    def list_months(user_id: int, year: int) -> list[dict]:
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
        with get_session() as s:
            m = (
                s.query(CashFlowMonth)
                .filter_by(user_id=user_id, year=year, month=month)
                .first()
            )
            if not m:
                return None
            return CashFlowRepository._month_to_dict(m)

    @staticmethod
    def create_month(user_id: int, year: int, month: int) -> dict:
        """Create a month and seed from template if it exists."""
        with get_session() as s:
            # guard: already exists
            existing = (
                s.query(CashFlowMonth)
                .filter_by(user_id=user_id, year=year, month=month)
                .first()
            )
            if existing:
                return CashFlowRepository._month_to_dict(existing)

            m = CashFlowMonth(user_id=user_id, year=year, month=month)
            s.add(m)
            s.flush()

            # seed from template
            tmpl = s.query(CashFlowTemplate).filter_by(user_id=user_id).first()
            if tmpl:
                for item in tmpl.items:
                    s.add(
                        CashFlowEntry(
                            month_id=m.id,
                            name=item.name,
                            day=min(item.day, 28),  # safe for all months
                            value=item.value,
                            type=item.type,
                        )
                    )
            s.commit()
            # reload with entries
            s.refresh(m)
            return CashFlowRepository._month_to_dict(m)

    @staticmethod
    def delete_month(user_id: int, month_id: int) -> None:
        with get_session() as s:
            m = s.get(CashFlowMonth, month_id)
            if m and m.user_id == user_id:
                s.delete(m)
                s.commit()

    # ── Entries ────────────────────────────────────────────────────────────────

    @staticmethod
    def add_entry(month_id: int, name: str, day: int, value: float, type_: str) -> None:
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
        with get_session() as s:
            e = s.get(CashFlowEntry, entry_id)
            if e:
                s.delete(e)
                s.commit()

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _month_to_dict(m: CashFlowMonth) -> dict:
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
