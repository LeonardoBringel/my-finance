from models import CashFlowTemplate, CashFlowTemplateItem

from .base_repository import get_session


class CashFlowTemplateRepository:
    """Repositório para operações de leitura e escrita do template de fluxo de caixa."""

    @staticmethod
    def get_template(user_id: int) -> dict | None:
        """Retorna o template do usuário com seus itens, ou None se não existir."""
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
        """Cria ou substitui completamente os itens do template do usuário."""
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
