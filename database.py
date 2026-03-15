import sqlite3
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "finance.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Categories table ───────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE,
            type TEXT    NOT NULL CHECK(type IN ('entrada', 'saida', 'ambos'))
        )
    """)

    default_categories = [
        ("Casa", "saida"), ("Carro", "saida"), ("Estudo", "saida"),
        ("Outros", "ambos"), ("Recorrente", "saida"), ("Gatos", "saida"),
        ("Alimentação", "saida"), ("Mercado", "saida"), ("Farmácia", "saida"),
        ("Salário", "entrada"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
        default_categories
    )

    # ── Transactions table (new schema) ────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id        INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            date               TEXT    NOT NULL,
            description        TEXT,
            value              REAL    NOT NULL,
            installment_group  TEXT,
            installment_number INTEGER,
            installment_total  INTEGER,
            created_at         TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # ── Migration: old schema → new schema ────────────────────────────────────
    _migrate(conn)

    conn.close()


def _migrate(conn: sqlite3.Connection):
    """
    If transactions still has the legacy columns (type, category TEXT),
    migrate them to category_id and drop the old columns.

    Strategy:
    1. Check if legacy column 'type' still exists.
    2. If yes, for each transaction try to find a matching category by name.
       - If found → set category_id.
       - If not found → create the category (inheriting type from transaction)
         and set category_id.
    3. Rename old table, recreate with new schema, copy data, drop old.
    """
    c = conn.cursor()
    cols = [row[1] for row in c.execute("PRAGMA table_info(transactions)").fetchall()]

    if "type" not in cols:
        return  # already migrated

    print("[migration] Detected legacy schema — migrating transactions...")

    # Step 1: For every distinct (category, type) pair, ensure a category row exists
    legacy_rows = c.execute(
        "SELECT DISTINCT category, type FROM transactions WHERE category IS NOT NULL"
    ).fetchall()

    for cat_name, cat_type in legacy_rows:
        # Try to find existing category (case-insensitive)
        existing = c.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?)", (cat_name,)
        ).fetchone()
        if not existing:
            # Create missing category using the type from transactions
            # 'type' in old transactions is 'entrada'/'saida', valid for categories too
            c.execute(
                "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                (cat_name, cat_type)
            )

    conn.commit()

    # Step 2: Rebuild transactions table
    c.execute("ALTER TABLE transactions RENAME TO transactions_legacy")

    c.execute("""
        CREATE TABLE transactions (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id        INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            date               TEXT    NOT NULL,
            description        TEXT,
            value              REAL    NOT NULL,
            installment_group  TEXT,
            installment_number INTEGER,
            installment_total  INTEGER,
            created_at         TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 3: Copy data, resolving category name → category_id
    c.execute("""
        INSERT INTO transactions
            (id, category_id, date, description, value,
             installment_group, installment_number, installment_total, created_at)
        SELECT
            t.id,
            (SELECT c.id FROM categories c WHERE LOWER(c.name) = LOWER(t.category)),
            t.date,
            t.description,
            t.value,
            t.installment_group,
            t.installment_number,
            t.installment_total,
            t.created_at
        FROM transactions_legacy t
    """)

    c.execute("DROP TABLE transactions_legacy")
    conn.commit()

    migrated = c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    print(f"[migration] Done — {migrated} transactions migrated.")


# ── Categories ─────────────────────────────────────────────────────────────────

def get_all_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories_by_type(type_filter: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM categories WHERE type = ? OR type = 'ambos' ORDER BY name",
        (type_filter,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


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
    # FK is ON DELETE SET NULL — transactions keep existing but lose category link
    conn.execute("DELETE FROM categories WHERE id=?", (id_,))
    conn.commit()
    conn.close()


# ── Transactions ───────────────────────────────────────────────────────────────

def add_transaction(category_id: int, date_: str, description: str,
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
                (category_id, date, description, value,
                 installment_group, installment_number, installment_total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            category_id,
            txn_date.strftime("%Y-%m-%d"),
            description,
            installment_value,
            group_id,
            i + 1 if installments > 1 else None,
            installments if installments > 1 else None,
        ))

    conn.commit()
    conn.close()


def get_transactions(year: int = None, month: int = None):
    """Returns transactions joined with category name and type."""
    conn = get_connection()
    query = """
        SELECT
            t.id,
            t.category_id,
            COALESCE(c.name, '(sem categoria)') AS category,
            COALESCE(c.type, 'saida')           AS type,
            t.date,
            t.description,
            t.value,
            t.installment_group,
            t.installment_number,
            t.installment_total,
            t.created_at
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE 1=1
    """
    params = []
    if year:
        query += " AND strftime('%Y', t.date) = ?"
        params.append(str(year))
    if month:
        query += " AND strftime('%m', t.date) = ?"
        params.append(f"{month:02d}")
    query += " ORDER BY t.date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction_by_id(id_: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT t.*, COALESCE(c.name, '(sem categoria)') AS category,
               COALESCE(c.type, 'saida') AS type
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.id=?
    """, (id_,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_transaction(id_: int, category_id: int, date_: str,
                       description: str, value: float):
    conn = get_connection()
    conn.execute("""
        UPDATE transactions
        SET category_id=?, date=?, description=?, value=?
        WHERE id=?
    """, (category_id, date_, description, value, id_))
    conn.commit()
    conn.close()


def delete_transaction(id_: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def get_descriptions_by_category(category_id: int = None):
    """Return distinct non-empty descriptions, optionally filtered by category_id."""
    conn = get_connection()
    if category_id:
        rows = conn.execute(
            "SELECT DISTINCT description FROM transactions "
            "WHERE description IS NOT NULL AND description != '' "
            "AND category_id = ? ORDER BY description",
            (category_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT description FROM transactions "
            "WHERE description IS NOT NULL AND description != '' ORDER BY description"
        ).fetchall()
    conn.close()
    return [r[0] for r in rows]


# ── Dashboard Aggregations ─────────────────────────────────────────────────────

def get_monthly_summary(year: int, month: int):
    conn = get_connection()

    def scalar(q, p):
        r = conn.execute(q, p).fetchone()
        return r[0] or 0.0 if r else 0.0

    period = f"{year}-{month:02d}"

    entradas = scalar("""
        SELECT SUM(t.value) FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') = 'entrada'
          AND strftime('%Y-%m', t.date) = ?
    """, (period,))

    saidas = scalar("""
        SELECT SUM(t.value) FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') IN ('saida', 'ambos')
          AND strftime('%Y-%m', t.date) = ?
    """, (period,))

    acc_entradas = scalar("""
        SELECT SUM(t.value) FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') = 'entrada'
          AND strftime('%Y', t.date) = ?
          AND strftime('%m', t.date) <= ?
    """, (str(year), f"{month:02d}"))

    acc_saidas = scalar("""
        SELECT SUM(t.value) FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') IN ('saida', 'ambos')
          AND strftime('%Y', t.date) = ?
          AND strftime('%m', t.date) <= ?
    """, (str(year), f"{month:02d}"))

    conn.close()
    return {
        "entradas": entradas,
        "saidas": saidas,
        "saldo": entradas - saidas,
        "saldo_acumulado": acc_entradas - acc_saidas,
    }


def get_expenses_by_category(year: int, month: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT COALESCE(c.name, '(sem categoria)') AS category, SUM(t.value) AS total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') IN ('saida', 'ambos')
          AND strftime('%Y-%m', t.date) = ?
        GROUP BY category ORDER BY total DESC
    """, (f"{year}-{month:02d}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_income_by_category(year: int, month: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT COALESCE(c.name, '(sem categoria)') AS category, SUM(t.value) AS total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE COALESCE(c.type, 'saida') = 'entrada'
          AND strftime('%Y-%m', t.date) = ?
        GROUP BY category ORDER BY total DESC
    """, (f"{year}-{month:02d}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_trend(year: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%m', t.date) AS month,
               COALESCE(c.type, 'saida') AS type,
               SUM(t.value) AS total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE strftime('%Y', t.date) = ?
        GROUP BY month, type
        ORDER BY month
    """, (str(year),)).fetchall()
    conn.close()

    months = {f"{i:02d}": {"entrada": 0.0, "saida": 0.0} for i in range(1, 13)}
    for r in rows:
        t = r["type"]
        if t in ("saida", "ambos"):
            months[r["month"]]["saida"] += r["total"]
        else:
            months[r["month"]]["entrada"] += r["total"]
    return months


def get_available_years():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT strftime('%Y', date) AS yr FROM transactions ORDER BY yr"
    ).fetchall()
    conn.close()
    years = [int(r["yr"]) for r in rows]
    current_year = datetime.now().year
    if current_year not in years:
        years.append(current_year)
    return sorted(years)
