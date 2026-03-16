"""
Script de migração: SQLite → PostgreSQL

Lê os dados existentes no finance.db (SQLite) e os insere no PostgreSQL
como o usuário admin (primeiro usuário criado).

Uso:
    python scripts/migrate_sqlite.py --sqlite-path ./finance.db --admin-username admin --admin-password senha123

O script:
1. Conecta no PostgreSQL (via .env)
2. Cria o usuário admin (se não existir)
3. Migra categorias do SQLite → PostgreSQL (com seed + extras)
4. Migra transações, resolvendo category_id pelo nome da categoria
"""

import argparse
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import get_session, init_db
from models import User, Category, Transaction
from crypto import encrypt, decrypt
from auth import hash_password, _seed_categories


def get_sqlite_conn(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        print(f"[erro] Arquivo SQLite não encontrado: {path}")
        sys.exit(1)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_admin(session, username: str, password: str) -> User:
    """Return existing admin or create one."""
    all_users = session.query(User).all()
    for u in all_users:
        if decrypt(u.username) == username:
            print(f"[info] Usuário admin '{username}' já existe (id={u.id}).")
            return u

    is_first = session.query(User).count() == 0
    user = User(
        username=encrypt(username),
        password_hash=hash_password(password),
        is_admin=True,
    )
    session.add(user)
    session.flush()
    print(f"[info] Usuário admin '{username}' criado (id={user.id}, primeiro={is_first}).")
    return user


def migrate_categories(sqlite_conn, session, user: User) -> dict[int, int]:
    """
    Migrate categories from SQLite to PostgreSQL.
    Returns mapping: sqlite_category_id → postgres_category_id
    """
    # Detect schema: new schema has no 'type' column directly readable as plain text
    # but we check if 'type' column exists (old schema) or not
    cursor = sqlite_conn.execute("PRAGMA table_info(categories)")
    cols = [row[1] for row in cursor.fetchall()]

    sqlite_cats = sqlite_conn.execute("SELECT * FROM categories").fetchall()

    # Get existing postgres categories for this user (to avoid duplicates)
    existing_pg = session.query(Category).filter_by(user_id=user.id).all()
    existing_names = {decrypt(c.name).lower(): c for c in existing_pg}

    id_map: dict[int, int] = {}

    for row in sqlite_cats:
        row = dict(row)
        sqlite_id = row["id"]

        # Handle both old schema (plain text) and new schema (encrypted)
        raw_name = row.get("name", "")
        raw_type = row.get("type", "saida") if "type" in cols else "saida"

        # Try to decrypt — if it fails, it's already plain text
        try:
            name = decrypt(raw_name) or raw_name
        except Exception:
            name = raw_name

        try:
            type_ = decrypt(raw_type) or raw_type
        except Exception:
            type_ = raw_type

        # Validate type value
        if type_ not in ("entrada", "saida", "ambos"):
            type_ = "saida"

        # Check duplicate
        if name.lower() in existing_names:
            pg_cat = existing_names[name.lower()]
            id_map[sqlite_id] = pg_cat.id
            print(f"  [skip] Categoria '{name}' já existe (pg_id={pg_cat.id})")
            continue

        new_cat = Category(
            user_id=user.id,
            name=encrypt(name),
            type=encrypt(type_),
        )
        session.add(new_cat)
        session.flush()
        id_map[sqlite_id] = new_cat.id
        existing_names[name.lower()] = new_cat
        print(f"  [ok]   Categoria '{name}' ({type_}) → pg_id={new_cat.id}")

    return id_map


def migrate_transactions(sqlite_conn, session, user: User, cat_id_map: dict[int, int]):
    """Migrate transactions from SQLite to PostgreSQL."""
    # Detect columns
    cursor = sqlite_conn.execute("PRAGMA table_info(transactions)")
    cols = [row[1] for row in cursor.fetchall()]

    sqlite_txns = sqlite_conn.execute(
        "SELECT * FROM transactions ORDER BY id"
    ).fetchall()

    migrated = 0
    skipped  = 0

    for row in sqlite_txns:
        row = dict(row)

        # Resolve category_id
        pg_cat_id = None
        if "category_id" in cols and row.get("category_id"):
            pg_cat_id = cat_id_map.get(row["category_id"])
        elif "category" in cols and row.get("category"):
            # Old schema: match by name
            cat_name = row["category"]
            for sqlite_id, pg_id in cat_id_map.items():
                pg_cat = session.get(Category, pg_id)
                if pg_cat and decrypt(pg_cat.name).lower() == cat_name.lower():
                    pg_cat_id = pg_id
                    break

        # Resolve date
        raw_date = row.get("date", "")
        try:
            date_plain = decrypt(raw_date) or raw_date
        except Exception:
            date_plain = raw_date

        # Resolve value
        raw_value = row.get("value", "0")
        try:
            value_plain = decrypt(str(raw_value)) or str(raw_value)
        except Exception:
            value_plain = str(raw_value)

        try:
            float(value_plain)
        except ValueError:
            print(f"  [warn] Transação id={row['id']} com valor inválido '{value_plain}' — pulando.")
            skipped += 1
            continue

        # Resolve description
        raw_desc = row.get("description") or ""
        try:
            desc_plain = decrypt(raw_desc) if raw_desc else ""
        except Exception:
            desc_plain = raw_desc

        txn = Transaction(
            user_id=user.id,
            category_id=pg_cat_id,
            date=encrypt(date_plain),
            description=encrypt(desc_plain) if desc_plain else None,
            value=encrypt(value_plain),
            installment_group=row.get("installment_group"),
            installment_number=row.get("installment_number"),
            installment_total=row.get("installment_total"),
        )
        session.add(txn)
        migrated += 1

    session.flush()
    print(f"\n  [ok] {migrated} transação(ões) migrada(s), {skipped} ignorada(s).")


def main():
    parser = argparse.ArgumentParser(description="Migrar dados do SQLite para PostgreSQL")
    parser.add_argument("--sqlite-path",     default="./finance.db",  help="Caminho do arquivo finance.db")
    parser.add_argument("--admin-username",  default="admin",         help="Username do admin")
    parser.add_argument("--admin-password",  required=True,           help="Senha do admin")
    args = parser.parse_args()

    print("=" * 60)
    print("  Migração SQLite → PostgreSQL")
    print("=" * 60)

    # Init PostgreSQL tables
    print("\n[1/4] Inicializando banco PostgreSQL...")
    init_db()
    print("      OK")

    # Connect SQLite
    print(f"\n[2/4] Conectando ao SQLite: {args.sqlite_path}")
    sqlite_conn = get_sqlite_conn(args.sqlite_path)
    print("      OK")

    with get_session() as session:
        # Create admin
        print(f"\n[3/4] Criando/localizando usuário admin '{args.admin_username}'...")
        admin = get_or_create_admin(session, args.admin_username, args.admin_password)

        # Migrate categories
        print("\n[4a/4] Migrando categorias...")
        cat_id_map = migrate_categories(sqlite_conn, session, admin)

        # Migrate transactions
        print("\n[4b/4] Migrando transações...")
        migrate_transactions(sqlite_conn, session, admin, cat_id_map)

        session.commit()

    sqlite_conn.close()
    print("\n" + "=" * 60)
    print("  Migração concluída com sucesso!")
    print("=" * 60)
    print(f"\n  Acesse o app e faça login com:")
    print(f"  Usuário: {args.admin_username}")
    print(f"  Senha:   {args.admin_password}")
    print()


if __name__ == "__main__":
    main()
