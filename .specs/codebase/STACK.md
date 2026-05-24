# Tech Stack

**Analyzed:** 2026-05-23

## Core

- Framework: Streamlit >=1.55.0 (multi-page app)
- Language: Python >=3.13
- Runtime: CPython 3.13 (Docker base `python:3.13-slim`)
- Package manager: `uv` (lockfile `uv.lock`; `pyproject.toml` PEP 621)

## Frontend

- UI Framework: Streamlit (server-rendered widgets; no separate JS frontend)
- Styling: Inline CSS injected via `st.markdown(..., unsafe_allow_html=True)` — centralized in `components/styles.py`, plus per-page `<style>` blocks. Dark green theme.
- State Management: `st.session_state` (per-session dict) + JWT session cookie
- Cookie handling: `streamlit-cookies-controller` >=0.0.4, `extra-streamlit-components` >=0.1.81
- Charts: Plotly >=6.6.0 (`plotly.graph_objects`, `plotly.express`)

## Backend

- API Style: None (monolithic Streamlit app; no REST/GraphQL surface)
- Database: PostgreSQL (driver `psycopg2-binary` >=2.9.11), accessed via SQLAlchemy ORM >=2.0.48
- Migrations: Alembic >=1.18.4
- Authentication: bcrypt >=5.0.0 (password hashing) + PyJWT >=2.12.1 (session tokens, HS256)
- Encryption at rest: `cryptography` >=46.0.5 (Fernet symmetric) + HMAC-SHA256 for indexed lookups
- Config: `python-dotenv` >=1.2.2 (`.env` file)
- Date math: `python-dateutil` >=2.9.0 (`relativedelta` for installments)

## Testing

- Unit: **None** (no test framework in dependencies)
- Integration: **None**
- E2E: **None**

> No test infrastructure exists. See TESTING.md and CONCERNS.md.

## External Services

- Database: PostgreSQL 16 (docker-compose service `db`, image `postgres:16-alpine`)
- Intrusion prevention: fail2ban (optional, log-file based; app writes failed-login lines)
- Reverse proxy (deploy): nginx assumed (app reads `X-Real-IP` header)

## Development Tools

- Formatter: black (via pre-commit, pinned `22.3.0`)
- Import sorter: isort (pre-commit `6.0.1`, `profile = "black"`)
- Pre-commit: `pre-commit` >4.3.0 (dev dependency group)
- File watcher: watchdog >=6.0.0
- Containerization: Docker + docker-compose; `Makefile` target `deploy` builds and runs with `APP_VERSION` from `git describe`
- Versioning: git semver tags (`v*.*.*`); `.version` file baked into image, shown on login page
