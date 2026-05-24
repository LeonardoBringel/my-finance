# Project Structure

**Root:** `/Users/leonardobringel/Documents/workspaces/python_workspace/my-finance`

## Directory Tree

```
my-finance/
├── app.py                      # Entry point → st.switch_page("pages/dashboard.py")
├── pyproject.toml / uv.lock    # Deps (uv) + black/isort config
├── alembic.ini                 # Alembic config (URL set dynamically in env.py)
├── Dockerfile / docker-compose.yml / Makefile
├── .env / .env.sample          # DB_*, FERNET_KEY, fail2ban flags
├── .version                    # App version string (shown on login)
├── .streamlit/config.toml      # Streamlit server/theme config
├── .pre-commit-config.yaml     # black + isort
├── CLAUDE.md                   # Architecture rules + git workflow (pt-BR)
├── alembic/
│   ├── env.py                  # Builds DB URL from .env, target = models.Base.metadata
│   └── versions/0001..000x*.py # x sequential migrations
├── models/                     # ORM, one file per table
│   ├── base.py                 # declarative_base()
│   ├── user.py  category.py  transaction.py
│   └── cash_flow_template.py  cash_flow_template_item.py
│       cash_flow_month.py  cash_flow_entry.py
├── repositories/               # DB access, one file per table
│   ├── base_repository.py      # get_engine() / get_session()
│   ├── users_repository.py  categories_repository.py  transactions_repository.py
│   └── cash_flow_{template,month,entry}_repository.py
├── components/                 # Reusable Streamlit widgets/dialogs
│   ├── styles.py               # CSS injectors, page_header, init_onboarding
│   ├── charts.py               # Plotly chart builders
│   ├── new_transaction.py      # Create/edit transaction dialog
│   └── advance_installments.py # 2-step advance-installments dialog
├── pages/                      # One file per route
│   ├── login.py  dashboard.py  transactions.py  cash_flow.py
│   └── categories.py  profile.py  admin.py
└── utils/                      # Pure-ish helpers
    ├── crypto.py  password_utils.py  data_format_utils.py
    └── auth.py  session.py     # auth.py is the only st.* exception
```

## Module Organization

### Models (`models/`)
**Purpose:** SQLAlchemy table definitions + serialization. **Key files:** `base.py` (Base), `transaction.py` (encrypted fields + installment cols + indexes), `user.py` (username_hash unique index). `__init__.py` re-exports all + `Base`.

### Repositories (`repositories/`)
**Purpose:** All persistence logic. **Key files:** `base_repository.py` (engine/session singletons), `transactions_repository.py` (largest — CRUD, description bulk ops, all dashboard aggregation).

### Components (`components/`)
**Purpose:** Shared UI. **Key files:** `styles.py` (CSS + `page_header` + `init_onboarding`), `charts.py` (donut, bar, annual evolution, expenses-by-day).

### Pages (`pages/`)
**Purpose:** Routes. Each enforces `require_login()`; `admin.py` adds `require_admin()`. Navigation via `st.switch_page("pages/<name>.py")`.

### Utils (`utils/`)
**Purpose:** Cross-cutting. **Key files:** `auth.py` (login/logout/guards/cookie), `session.py` (JWT encode/decode), `crypto.py` (Fernet + HMAC), `password_utils.py` (bcrypt), `data_format_utils.py` (BRL currency, dates, value parsing).

### Migrations (`alembic/`)
**Purpose:** Schema evolution. x linear revisions `0001`→`000x`: initial schema, timestamps, cash-flow tables, transaction `year` column, `username_hash`, missing indexes, `description_hash`.

## Where Things Live

**Transactions feature:**
- UI/Interface: `pages/transactions.py`, `pages/dashboard.py`, `components/new_transaction.py`, `components/advance_installments.py`, `components/charts.py`
- Business Logic: `repositories/transactions_repository.py`
- Data Access: same repository → `models/transaction.py`
- Config: indexes in `models/transaction.py` + migrations `0001/0004/0007`

**Auth / Users:**
- UI/Interface: `pages/login.py`, `pages/profile.py`, `pages/admin.py`
- Business Logic: `utils/auth.py`, `repositories/users_repository.py`
- Data Access: `models/user.py`
- Config: `FERNET_KEY` (.env) used for encryption, HMAC, and JWT signing

**Cash Flow:**
- UI/Interface: `pages/cash_flow.py`
- Business Logic: `repositories/cash_flow_{template,month,entry}_repository.py`
- Data Access: `models/cash_flow_*.py`

## Special Directories

**`.specs/`** — TLC spec-driven artifacts (this brownfield analysis lives in `.specs/codebase/`).
**`.streamlit/`** — server config: sidebar nav hidden, XSRF on, headless, port 8501.
**`alembic/versions/`** — numeric-prefixed migration scripts, linear chain.
