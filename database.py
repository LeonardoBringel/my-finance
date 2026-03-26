import os
from contextlib import contextmanager
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from crypto import decrypt, decrypt_float, encrypt
from models import Base, Category, Transaction

load_dotenv()

# ── Engine ─────────────────────────────────────────────────────────────────────

_engine = None
_SessionLocal = None


def _build_url() -> str:
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
    )


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_build_url(), pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_session() -> Session:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create tables if they don't exist (fallback — prefer Alembic)."""
    Base.metadata.create_all(get_engine())


# ── Categories ─────────────────────────────────────────────────────────────────


def get_all_categories(user_id: int) -> list[dict]:
    with get_session() as s:
        rows = s.query(Category).filter_by(user_id=user_id).all()
        return sorted(
            [
                {"id": c.id, "name": decrypt(c.name), "type": decrypt(c.type)}
                for c in rows
            ],
            key=lambda x: x["name"],
        )


# ── Transactions ───────────────────────────────────────────────────────────────


def _decrypt_txn(t: Transaction, cat_name: str, cat_type: str) -> dict:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "category_id": t.category_id,
        "category": cat_name,
        "type": cat_type,
        "date": decrypt(t.date),
        "description": decrypt(t.description),
        "value": decrypt_float(t.value),
        "installment_group": t.installment_group,
        "installment_number": t.installment_number,
        "installment_total": t.installment_total,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def add_transaction(
    user_id: int,
    category_id: int,
    date_: str,
    description: str,
    value: float,
    installments: int = 1,
):
    import uuid

    group_id = str(uuid.uuid4()) if installments > 1 else None
    base_date = datetime.strptime(date_, "%Y-%m-%d")
    installment_value = round(value / installments, 2)

    with get_session() as s:
        for i in range(installments):
            txn_date = base_date + relativedelta(months=i)
            s.add(
                Transaction(
                    user_id=user_id,
                    category_id=category_id,
                    date=encrypt(txn_date.strftime("%Y-%m-%d")),
                    description=encrypt(description) if description else None,
                    value=encrypt(str(installment_value)),
                    installment_group=group_id,
                    installment_number=i + 1 if installments > 1 else None,
                    installment_total=installments if installments > 1 else None,
                )
            )
        s.commit()


def get_transactions(user_id: int, year: int = None, month: int = None) -> list[dict]:
    with get_session() as s:
        rows = (
            s.query(Transaction, Category)
            .outerjoin(Category, Transaction.category_id == Category.id)
            .filter(Transaction.user_id == user_id)
            .all()
        )

    result = []
    for t, c in rows:
        cat_name = decrypt(c.name) if c else "(sem categoria)"
        cat_type = decrypt(c.type) if c else "saida"
        txn = _decrypt_txn(t, cat_name, cat_type)
        try:
            d = datetime.strptime(txn["date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        if year and d.year != year:
            continue
        if month and d.month != month:
            continue
        result.append(txn)

    return sorted(
        result, key=lambda x: (x["date"], x["created_at"] or ""), reverse=True
    )


def update_transaction(
    user_id: int, id_: int, category_id: int, date_: str, description: str, value: float
):
    with get_session() as s:
        t = s.get(Transaction, id_)
        if not t or t.user_id != user_id:
            return
        t.category_id = category_id
        t.date = encrypt(date_)
        t.description = encrypt(description) if description else None
        t.value = encrypt(str(value))
        s.commit()


def delete_transaction(user_id: int, id_: int):
    with get_session() as s:
        t = s.get(Transaction, id_)
        if t and t.user_id == user_id:
            s.delete(t)
            s.commit()


def get_descriptions_by_category(user_id: int, category_id: int = None) -> list[str]:
    txns = get_transactions(user_id)
    seen = {}
    for t in txns:
        if category_id and t["category_id"] != category_id:
            continue
        if t["description"]:
            seen[t["description"]] = True
    return sorted(seen.keys())


# ── Dashboard Aggregations ─────────────────────────────────────────────────────


def get_monthly_summary(user_id: int, year: int, month: int) -> dict:
    txns = get_transactions(user_id, year=year, month=month)
    entradas = sum(t["value"] for t in txns if t["type"] == "entrada")
    saidas = sum(t["value"] for t in txns if t["type"] in ("saida", "ambos"))

    all_year = get_transactions(user_id, year=year)
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
    }


def get_expenses_by_category(user_id: int, year: int, month: int) -> list[dict]:
    txns = get_transactions(user_id, year=year, month=month)
    totals: dict[str, float] = {}
    for t in txns:
        if t["type"] in ("saida", "ambos"):
            totals[t["category"]] = totals.get(t["category"], 0) + t["value"]
    return sorted(
        [{"category": k, "total": v} for k, v in totals.items()],
        key=lambda x: x["total"],
        reverse=True,
    )


def get_income_by_category(user_id: int, year: int, month: int) -> list[dict]:
    txns = get_transactions(user_id, year=year, month=month)
    totals: dict[str, float] = {}
    for t in txns:
        if t["type"] == "entrada":
            totals[t["category"]] = totals.get(t["category"], 0) + t["value"]
    return sorted(
        [{"category": k, "total": v} for k, v in totals.items()],
        key=lambda x: x["total"],
        reverse=True,
    )


def get_expenses_by_category_and_description(
    user_id: int, year: int, month: int
) -> list[dict]:
    txns = get_transactions(user_id, year=year, month=month)
    totals: dict[tuple, float] = {}
    for t in txns:
        if t["type"] in ("saida", "ambos"):
            key = (t["category"], t["description"] or "(sem descrição)")
            totals[key] = totals.get(key, 0) + t["value"]
    result = [
        {"category": k[0], "description": k[1], "total": v} for k, v in totals.items()
    ]
    return sorted(result, key=lambda x: (x["category"], x["total"]), reverse=True)


def get_descriptions_by_category_for_dashboard(
    user_id: int, year: int, month: int
) -> dict:
    """
    Returns a dict: { category_name: { descriptions, total, total_prev_month } }
    for all saida categories of the user in the given month.
    """
    from dateutil.relativedelta import relativedelta as rd

    all_cats = get_all_categories(user_id)
    saida_cats = [c for c in all_cats if c["type"] in ("saida", "ambos")]

    # Current month transactions
    txns = get_transactions(user_id, year=year, month=month)
    saida_txns = [t for t in txns if t["type"] in ("saida", "ambos")]
    total_month = sum(t["value"] for t in saida_txns)

    # Previous month
    prev = datetime(year, month, 1) - rd(months=1)
    prev_txns = get_transactions(user_id, year=prev.year, month=prev.month)
    prev_saida = [t for t in prev_txns if t["type"] in ("saida", "ambos")]

    result = {}
    for cat in saida_cats:
        # Current month
        cat_txns = [t for t in saida_txns if t["category"] == cat["name"]]
        totals: dict[str, float] = {}
        for t in cat_txns:
            desc = t["description"] or "(sem descrição)"
            totals[desc] = totals.get(desc, 0) + t["value"]
        cat_total = sum(totals.values())

        # Previous month total for this category
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
            "pct_of_month": (cat_total / total_month * 100) if total_month > 0 else 0.0,
        }

    return result


def get_monthly_trend(user_id: int, year: int) -> dict:
    all_txns = get_transactions(user_id, year=year)
    months = {f"{i:02d}": {"entrada": 0.0, "saida": 0.0} for i in range(1, 13)}
    for t in all_txns:
        try:
            m = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%m")
        except (ValueError, TypeError):
            continue
        if t["type"] == "entrada":
            months[m]["entrada"] += t["value"]
        else:
            months[m]["saida"] += t["value"]
    return months


def get_annual_evolution(user_id: int, year: int) -> list[dict]:
    """
    Returns monthly entrada, saida and cumulative saldo for the year.
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
    all_txns = get_transactions(user_id, year=year)

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


def get_available_years(user_id: int) -> list[int]:
    txns = get_transactions(user_id)
    years = {
        datetime.strptime(t["date"], "%Y-%m-%d").year for t in txns if t.get("date")
    }
    years.add(datetime.now().year)
    return sorted(years)
