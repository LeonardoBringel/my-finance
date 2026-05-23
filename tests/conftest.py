"""Shared pytest fixtures and harness for the my-finance test suite.

This module MUST set a fixed ``FERNET_KEY`` and put the project root on
``sys.path`` *before* any project module (``utils.crypto``, models,
repositories) is imported, because ``utils.crypto`` reads ``FERNET_KEY`` at
import time and raises if it is missing.
"""

import base64
import os
import pathlib
import shutil
import subprocess
import sys

# ── Bootstrap: runs at import time, before any project import ──────────────────
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Fixed, deterministic 32-byte url-safe base64 key (valid Fernet key).
os.environ["FERNET_KEY"] = base64.urlsafe_b64encode(
    b"my_finance_test_fernet_key_32byt"
).decode()

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


def _docker_available() -> bool:
    """Return True if a usable Docker daemon is reachable."""
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=15,
            check=True,
        )
        return True
    except Exception:
        return False


DOCKER_AVAILABLE = _docker_available()


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration-marked tests when Docker is unavailable."""
    if DOCKER_AVAILABLE:
        return
    skip = pytest.mark.skip(reason="Docker unavailable; integration suite skipped")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def pg_engine():
    """Session-scoped ephemeral Postgres with the schema applied via Alembic.

    Each pytest-xdist worker is a separate process, so each worker provisions
    its own container — the module-level engine singleton never leaks across
    workers.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as postgres:
        # Point both the Alembic env and the app engine at this container.
        os.environ["DB_USER"] = postgres.username
        os.environ["DB_PASSWORD"] = postgres.password
        os.environ["DB_HOST"] = postgres.get_container_host_ip()
        os.environ["DB_PORT"] = str(postgres.get_exposed_port(5432))
        os.environ["DB_NAME"] = postgres.dbname

        url = (
            f"postgresql+psycopg2://{postgres.username}:{postgres.password}"
            f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{postgres.dbname}"
        )

        # Apply the real schema. alembic/env.py builds its URL from the DB_*
        # env vars set above, so just invoke upgrade head.
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(_ROOT / "alembic"))
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(url, pool_pre_ping=True)
        try:
            yield engine
        finally:
            engine.dispose()


@pytest.fixture
def db_session(pg_engine):
    """Function-scoped session bound to a rolled-back outer transaction.

    All sessions opened by repositories (via ``base_repository.get_session``)
    are redirected onto a single connection wrapped in one outer transaction.
    Repository ``commit()`` calls become savepoints
    (``join_transaction_mode="create_savepoint"``); the outer transaction is
    rolled back after each test, so tests are isolated and order-independent.
    """
    import repositories.base_repository as base_repository

    connection = pg_engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    orig_engine = base_repository._engine
    orig_session = base_repository._session
    base_repository._engine = pg_engine
    base_repository._session = TestSession

    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        base_repository._engine = orig_engine
        base_repository._session = orig_session
        transaction.rollback()
        connection.close()
