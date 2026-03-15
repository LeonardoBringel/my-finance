import sqlite3
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "finance.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('entrada', 'saida', 'ambos'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('entrada', 'saida')),
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            value REAL NOT NULL,
            installment_group TEXT,
            installment_number INTEGER,
            installment_total INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default categories
    default_categories = [
        ("Casa", "saida"), ("Carro", "saida"), ("Estudo", "saida"),
        ("Outros", "ambos"), ("Recorrente", "saida"), ("Gatos", "saida"),
        ("Alimentação", "saida"), ("Mercado", "saida"), ("Farmácia", "saida"),
        ("Salário", "entrada"), ("Freelance", "entrada"), ("Investimentos", "entrada"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
        default_categories
    )

    conn.commit()
    conn.close()


# ── Categories ────────────────────────────────────────────────────────────────

def get_all_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories_by_type(type_filter: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT name FROM categories WHERE type = ? OR type = 'ambos' ORDER BY name",
        (type_filter,)
    ).fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_category(name: str, type_: str):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type_))
        conn.commit()
        return True, "Categoria adicionada!"
    except sqlite3.IntegrityError:
        return False, "Categoria já existe."
    finally:
        conn.close()


def update_category(id_: int, name: str, type_: str):
    conn = get_connection()
    try:
        conn.execute("UPDATE categories SET name=?, type=? WHERE id=?", (name, type_, id_))
        conn.commit()
        return True, "Categoria atualizada!"
    except sqlite3.IntegrityError:
        return False, "Nome já existe."
    finally:
        conn.close()


def delete_category(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id=?", (id_,))
    conn.commit()
    conn.close()


# ── Transactions ──────────────────────────────────────────────────────────────

def add_transaction(type_: str, date_: str, category: str, description: str,
                    value: float, installments: int = 1):
    conn = get_connection()
    import uuid
    group_id = str(uuid.uuid4()) if installments > 1 else None
    base_date = datetime.strptime(date_, "%Y-%m-%d")
    installment_value = round(value / installments, 2)

    for i in range(installments):
        txn_date = base_date + relativedelta(months=i)
        conn.execute("""
            INSERT INTO transactions
                (type, date, category, description, value, installment_group,
                 installment_number, installment_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            type_, txn_date.strftime("%Y-%m-%d"), category, description,
            installment_value, group_id,
            i + 1 if installments > 1 else None,
            installments if installments > 1 else None,
        ))

    conn.commit()
    conn.close()


def get_transactions(year: int = None, month: int = None):
    conn = get_connection()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    if month:
        query += " AND strftime('%m', date) = ?"
        params.append(f"{month:02d}")
    query += " ORDER BY date DESC, id"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction_by_id(id_: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id=?", (id_,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_transaction(id_: int, type_: str, date_: str, category: str,
                       description: str, value: float):
    conn = get_connection()
    conn.execute("""
        UPDATE transactions
        SET type=?, date=?, category=?, description=?, value=?
        WHERE id=?
    """, (type_, date_, category, description, value, id_))
    conn.commit()
    conn.close()


def delete_transaction(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def get_autocomplete_values(field: str):
    """Return distinct non-empty values for autocomplete."""
    allowed = {"category", "description"}
    if field not in allowed:
        return []
    conn = get_connection()
    rows = conn.execute(
        f"SELECT DISTINCT {field} FROM transactions WHERE {field} IS NOT NULL AND {field} != '' ORDER BY {field}"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


# ── Dashboard Aggregations ─────────────────────────────────────────────────────

def get_monthly_summary(year: int, month: int):
    conn = get_connection()

    def scalar(q, p):
        r = conn.execute(q, p).fetchone()
        return r[0] or 0.0 if r else 0.0

    entradas = scalar(
        "SELECT SUM(value) FROM transactions WHERE type='entrada' AND strftime('%Y-%m', date)=?",
        (f"{year}-{month:02d}",)
    )
    saidas = scalar(
        "SELECT SUM(value) FROM transactions WHERE type='saida' AND strftime('%Y-%m', date)=?",
        (f"{year}-{month:02d}",)
    )
    saldo = entradas - saidas

    # Accumulated: all months up to and including selected
    acc_entradas = scalar(
        "SELECT SUM(value) FROM transactions WHERE type='entrada' AND strftime('%Y', date)=? AND strftime('%m', date)<=?",
        (str(year), f"{month:02d}")
    )
    acc_saidas = scalar(
        "SELECT SUM(value) FROM transactions WHERE type='saida' AND strftime('%Y', date)=? AND strftime('%m', date)<=?",
        (str(year), f"{month:02d}")
    )
    saldo_acumulado = acc_entradas - acc_saidas

    conn.close()
    return {
        "entradas": entradas,
        "saidas": saidas,
        "saldo": saldo,
        "saldo_acumulado": saldo_acumulado,
    }


def get_expenses_by_category(year: int, month: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT category, SUM(value) as total
        FROM transactions
        WHERE type='saida' AND strftime('%Y-%m', date)=?
        GROUP BY category ORDER BY total DESC
    """, (f"{year}-{month:02d}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_income_by_category(year: int, month: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT category, SUM(value) as total
        FROM transactions
        WHERE type='entrada' AND strftime('%Y-%m', date)=?
        GROUP BY category ORDER BY total DESC
    """, (f"{year}-{month:02d}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_trend(year: int):
    """Returns monthly in/out for all months in the year."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%m', date) as month,
               type,
               SUM(value) as total
        FROM transactions
        WHERE strftime('%Y', date)=?
        GROUP BY month, type
        ORDER BY month
    """, (str(year),)).fetchall()
    conn.close()

    months = {f"{i:02d}": {"entrada": 0.0, "saida": 0.0} for i in range(1, 13)}
    for r in rows:
        months[r["month"]][r["type"]] = r["total"]
    return months


def get_available_years():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT strftime('%Y', date) as yr FROM transactions ORDER BY yr"
    ).fetchall()
    conn.close()
    years = [int(r["yr"]) for r in rows]
    current_year = datetime.now().year
    if current_year not in years:
        years.append(current_year)
    return sorted(years)
