"""Integration tests for the cash-flow encryption migration (0008).

Provisionam um Postgres efêmero próprio, aplicam o schema antigo (0007) com
``value`` ainda ``Numeric`` e ``name``/``value`` em texto plano, rodam o
``alembic upgrade head`` e verificam que as colunas ficam encriptadas em
repouso enquanto os repositórios devolvem os valores originais. Cobrem também
idempotência (sem dupla encriptação) e o ``downgrade`` reverso.
"""

import contextlib
import os
import pathlib
import shutil
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

from utils.crypto import decrypt, decrypt_float, encrypt

pytestmark = pytest.mark.integration

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def _alembic_bin() -> str:
    """Localiza o console script do alembic do ambiente atual."""
    return shutil.which("alembic") or str(
        pathlib.Path(sys.executable).parent / "alembic"
    )


def _run_alembic(target: str, env: dict) -> None:
    """Roda ``alembic <target>`` na raiz do projeto, abortando em falha."""
    result = subprocess.run(
        [_alembic_bin(), *target.split()],
        cwd=str(_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic {target} failed:\n{result.stdout}\n{result.stderr}"
        )


@contextlib.contextmanager
def _container_at_0007():
    """Sobe um Postgres efêmero no schema 0007 e devolve (engine, env)."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as postgres:
        env = os.environ.copy()
        env["DB_USER"] = postgres.username
        env["DB_PASSWORD"] = postgres.password
        env["DB_HOST"] = postgres.get_container_host_ip()
        env["DB_PORT"] = str(postgres.get_exposed_port(5432))
        env["DB_NAME"] = postgres.dbname

        _run_alembic("upgrade 0007", env)

        url = (
            f"postgresql+psycopg2://{postgres.username}:{postgres.password}"
            f"@{env['DB_HOST']}:{env['DB_PORT']}/{postgres.dbname}"
        )
        engine = create_engine(url, pool_pre_ping=True)
        try:
            yield engine, env
        finally:
            engine.dispose()


@contextlib.contextmanager
def _repositories_bound_to(engine):
    """Aponta o base_repository para ``engine`` durante o bloco e restaura depois."""
    from sqlalchemy.orm import sessionmaker

    import repositories.base_repository as base_repository

    orig_engine = base_repository._engine
    orig_session = base_repository._session
    base_repository._engine = engine
    base_repository._session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield
    finally:
        base_repository._engine = orig_engine
        base_repository._session = orig_session


def _seed_user_month_template(conn) -> dict:
    """Insere um usuário, mês e template com itens no schema 0007. Retorna os ids."""
    uid = conn.execute(
        text(
            "INSERT INTO users (username, password_hash, is_admin)"
            " VALUES (:u, :p, false) RETURNING id"
        ),
        {"u": encrypt("alice"), "p": "hash"},
    ).scalar()
    month_id = conn.execute(
        text(
            "INSERT INTO cash_flow_months (user_id, year, month)"
            " VALUES (:uid, 2026, 7) RETURNING id"
        ),
        {"uid": uid},
    ).scalar()
    tmpl_id = conn.execute(
        text(
            "INSERT INTO cash_flow_templates (user_id) VALUES (:uid) RETURNING id"
        ),
        {"uid": uid},
    ).scalar()
    return {"uid": uid, "month_id": month_id, "tmpl_id": tmpl_id}


def test_upgrade_encrypts_and_repository_reads_originals():
    """upgrade encripta name/value em repouso; repositórios devolvem os originais."""
    from repositories.cash_flow_month_repository import CashFlowMonthRepository
    from repositories.cash_flow_template_repository import (
        CashFlowTemplateRepository,
    )

    with _container_at_0007() as (engine, env):
        with engine.begin() as conn:
            ids = _seed_user_month_template(conn)
            conn.execute(
                text(
                    "INSERT INTO cash_flow_entries (month_id, name, day, value, type)"
                    " VALUES (:m, 'Aluguel', 10, 1500.00, 'saida')"
                ),
                {"m": ids["month_id"]},
            )
            conn.execute(
                text(
                    "INSERT INTO cash_flow_template_items"
                    " (template_id, name, day, value, type)"
                    " VALUES (:t, 'Salario', 5, 4000.00, 'entrada')"
                ),
                {"t": ids["tmpl_id"]},
            )

        _run_alembic("upgrade head", env)

        # Ciphertext em repouso
        with engine.connect() as conn:
            e = conn.execute(
                text("SELECT name, value FROM cash_flow_entries")
            ).one()
            assert e.name != "Aluguel"
            assert decrypt(e.name) == "Aluguel"
            assert decrypt_float(e.value) == pytest.approx(1500.0)

            ti = conn.execute(
                text("SELECT name, value FROM cash_flow_template_items")
            ).one()
            assert ti.name != "Salario"
            assert decrypt(ti.name) == "Salario"
            assert decrypt_float(ti.value) == pytest.approx(4000.0)

        # Leitura via repositório devolve os valores originais
        with _repositories_bound_to(engine):
            month = CashFlowMonthRepository.get_month_with_entries(
                ids["uid"], 2026, 7
            )
            assert month["entries"][0]["name"] == "Aluguel"
            assert month["entries"][0]["value"] == pytest.approx(1500.0)

            tmpl = CashFlowTemplateRepository.get_template(ids["uid"])
            assert tmpl["items"][0]["name"] == "Salario"
            assert tmpl["items"][0]["value"] == pytest.approx(4000.0)


def test_upgrade_is_idempotent_for_already_encrypted_name():
    """upgrade não re-encripta um name que já é ciphertext."""
    with _container_at_0007() as (engine, env):
        with engine.begin() as conn:
            ids = _seed_user_month_template(conn)
            conn.execute(
                text(
                    "INSERT INTO cash_flow_entries (month_id, name, day, value, type)"
                    " VALUES (:m, :n, 10, 1500.00, 'saida')"
                ),
                {"m": ids["month_id"], "n": encrypt("Aluguel")},
            )

        _run_alembic("upgrade head", env)

        with engine.connect() as conn:
            name = conn.execute(
                text("SELECT name FROM cash_flow_entries")
            ).scalar()
            # Uma única descriptografia recupera o original (sem dupla encriptação)
            assert decrypt(name) == "Aluguel"


def test_downgrade_restores_plaintext_and_numeric():
    """downgrade descriptografa name/value e restaura value como Numeric."""
    with _container_at_0007() as (engine, env):
        with engine.begin() as conn:
            ids = _seed_user_month_template(conn)
            conn.execute(
                text(
                    "INSERT INTO cash_flow_entries (month_id, name, day, value, type)"
                    " VALUES (:m, 'Aluguel', 10, 1500.00, 'saida')"
                ),
                {"m": ids["month_id"]},
            )

        _run_alembic("upgrade head", env)
        _run_alembic("downgrade 0007", env)

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT name, value FROM cash_flow_entries")
            ).one()
            assert row.name == "Aluguel"
            assert float(row.value) == pytest.approx(1500.0)
            col_type = conn.execute(
                text(
                    "SELECT data_type FROM information_schema.columns"
                    " WHERE table_name = 'cash_flow_entries' AND column_name = 'value'"
                )
            ).scalar()
            assert col_type == "numeric"
