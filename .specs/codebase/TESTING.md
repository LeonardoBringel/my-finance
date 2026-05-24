# Testing Infrastructure

## Test Frameworks

**Unit/Integration:** `pytest` (configured in `pyproject.toml` under `[tool.pytest.ini_options]`).
**Integration DB:** `testcontainers` — provisions an ephemeral PostgreSQL container per test session.
**Parallelism:** `pytest-xdist` (run with `-n auto`); each worker gets its own container.
**E2E:** None (Streamlit `AppTest` deferred to a later milestone).
**Coverage:** Not enforced (no threshold gate by design — the goal is a safety net on risky logic, not a coverage mandate).

## Test Organization

**Location:** `tests/`.
**Naming:** `tests/**/test_*.py`; test functions `test_*`.
**Structure:**

```
tests/
├── conftest.py          # harness: fixed FERNET_KEY, Postgres container, db_session, Docker auto-skip
├── unit/                # pure utils/, no DB
│   ├── test_crypto.py
│   ├── test_data_format_utils.py
│   ├── test_password_utils.py
│   └── test_session.py
└── integration/         # repositories/ against real Postgres (marked `integration`)
    ├── test_transactions_installments.py
    ├── test_dashboard_aggregation.py
    ├── test_description_ops.py
    └── test_repos_baseline.py
```

## Testing Patterns

### Unit Tests
Cover the pure helpers in `utils/`: `crypto` (encrypt/decrypt round-trip, `hash_for_lookup` determinism, `decrypt_float` fallback), `data_format_utils` (BRL currency, ISO↔BR dates, `parse_value_text`), `password_utils` (bcrypt round-trip), `session` (JWT create/decode, expiry, tampering). No database required.

### Integration Tests
Exercise the `repositories/` layer against a real PostgreSQL provisioned by Testcontainers. Highest-value targets covered: `create_transaction` installment generation, `get_dashboard_data` aggregation (incl. the January → previous-December path), bulk description ops (`rename`/`migrate`/`delete` + `description_hash` consistency), and baselines for users/categories/cash-flow.

**Harness (`tests/conftest.py`):**
- A fixed test `FERNET_KEY` is injected at import time, before any `utils.crypto`/model import.
- A **session-scoped** `pg_engine` fixture starts a Postgres container, points the `DB_*` env vars at it, and applies the schema via Alembic `upgrade head`.
- A **function-scoped** `db_session` fixture wraps each test in an outer transaction. All repository sessions are redirected onto that connection (`join_transaction_mode="create_savepoint"`), so repository `commit()`s become savepoints and the outer transaction is rolled back after each test → isolated, order-independent tests.
- Integration tests are marked `@pytest.mark.integration` and are **auto-skipped when Docker is unavailable** (unit tests still run).

## Test Execution

| Command | What it runs |
| ------- | ------------ |
| `uv run pytest tests/unit -q` | Unit suite only (no Docker needed) |
| `uv run pytest -q` | Full suite (unit + integration; integration auto-skips without Docker) |
| `uv run pytest -m integration -q` | Integration suite only |
| `uv run pytest -n auto -q` | Full suite in parallel (xdist; one container per worker) |

**Configuration:** `[tool.pytest.ini_options]` in `pyproject.toml` sets `testpaths = ["tests"]` and registers the `integration` marker.

## Coverage Targets

**Current:** Risky logic (crypto, HMAC lookups, installment generation, dashboard aggregation, bulk description ops) is covered. Unit suite: 21 tests. Integration suite: 14 tests.
**Goals:** Safety net on the encryption/query paths that M1 changes; not a coverage percentage.
**Enforcement:** A `pytest-unit` pre-commit hook runs the unit suite on every commit.

## Test Coverage Matrix

| Code Layer | Required Test Type | Location Pattern | Run Command |
| ---------- | ------------------ | ---------------- | ----------- |
| `utils/*.py` (pure) | unit | `tests/unit/test_*.py` | `uv run pytest tests/unit` |
| `repositories/*.py` | integration (real Postgres) | `tests/integration/test_*.py` | `uv run pytest tests/integration` |
| `models/*.py` | covered transitively by repo integration tests | — | — |
| `pages/*.py`, `components/*.py` | e2e (Streamlit `AppTest`) — not yet implemented | `tests/e2e/test_*.py` | `uv run pytest tests/e2e` |

## Parallelism Assessment

| Test Type | Parallel-Safe? | Isolation Model |
| --------- | -------------- | --------------- |
| unit | Yes | Pure functions, no shared mutable state |
| integration | Yes (under xdist) | Each xdist worker is a separate process → its own session-scoped container; per-test outer-transaction rollback in `db_session` keeps tests order-independent within a worker |

The module-level engine singletons in `repositories/base_repository.py` (`_engine`, `_session`) are overridden per test by the `db_session` fixture and restored afterward, so the singletons never leak across tests or workers.

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | fast feedback while coding | `uv run pytest tests/unit -q` |
| Full | before pushing / on schema or repo changes | `uv run pytest -q` |
| Build | full quality gate | `uv run pre-commit run --all-files && uv run pytest -q` |

Pre-commit runs `black` + `isort` + the `pytest-unit` hook (unit suite). The integration suite requires Docker; it is skipped automatically when Docker is not running.
