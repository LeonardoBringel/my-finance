import os
from contextlib import contextmanager
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from crypto import decrypt, decrypt_float, encrypt
from models import Base, Category, Transaction
from repositories import CategoriesRepository, TransactionsRepository

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


# ── Transactions ───────────────────────────────────────────────────────────────


# ── Dashboard Aggregations ─────────────────────────────────────────────────────


def get_monthly_summary(user_id: int, year: int, month: int) -> dict:
    txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
    entradas = sum(t["value"] for t in txns if t["type"] == "entrada")
    saidas = sum(t["value"] for t in txns if t["type"] in ("saida", "ambos"))

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
    }


def get_expenses_by_category(user_id: int, year: int, month: int) -> list[dict]:
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


def get_income_by_category(user_id: int, year: int, month: int) -> list[dict]:
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


def get_expenses_by_category_and_description(
    user_id: int, year: int, month: int
) -> list[dict]:
    txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
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

    all_cats = CategoriesRepository.list_categories(user_id)
    saida_cats = [c for c in all_cats if c["type"] in ("saida", "ambos")]

    # Current month transactions
    txns = TransactionsRepository.list_transactions(user_id, year=year, month=month)
    saida_txns = [t for t in txns if t["type"] in ("saida", "ambos")]
    total_month = sum(t["value"] for t in saida_txns)

    # Previous month
    prev = datetime(year, month, 1) - rd(months=1)
    prev_txns = TransactionsRepository.list_transactions(
        user_id, year=prev.year, month=prev.month
    )
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
    all_txns = TransactionsRepository.list_transactions(user_id, year=year)
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


def get_available_years(user_id: int) -> list[int]:
    txns = TransactionsRepository.list_transactions(user_id)
    years = {
        datetime.strptime(t["date"], "%Y-%m-%d").year for t in txns if t.get("date")
    }
    years.add(datetime.now().year)
    return sorted(years)
