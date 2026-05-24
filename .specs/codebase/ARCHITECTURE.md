# Architecture

**Pattern:** Layered monolith — strict one-direction layering (Pages → Components → Repositories → Models → DB), with cross-cutting Utils (crypto, auth, formatting).

## High-Level Structure

```
Streamlit Page (pages/*.py)        ← route + UI orchestration, starts with require_login()
   ├─► Component (components/*.py)  ← reusable st.* widgets / dialogs
   │       └─► Repository (repositories/*.py)  ← all DB access, @staticmethod
   │                └─► Model ORM (models/*.py) ← columns + to_json(), crypto on read
   │                         └─► PostgreSQL
   └─► Utils (utils/*.py)          ← auth/session, crypto, password, formatting
```

The layering rules are codified in the project root `CLAUDE.md` and consistently followed:
- Models and Repositories never import `streamlit`.
- Repositories return `dict` / `list[dict]`, never ORM objects outside the `with get_session()` block (`expire_on_commit=False` makes detached dicts safe).
- `utils/auth.py` is the deliberate exception that touches `st.session_state` / `st.switch_page`.

## Identified Patterns

### Repository pattern (static methods)
**Location:** `repositories/*.py`, one file per table, classes named `<Entity>Repository`.
**Purpose:** Single choke-point for persistence; keeps SQLAlchemy out of the UI.
**Implementation:** All methods are `@staticmethod`; every DB touch wraps `with get_session() as s:` from `base_repository.py`.
**Example:** `repositories/transactions_repository.py:18` `create_transaction`.

### Singleton engine / session factory
**Location:** `repositories/base_repository.py`
**Purpose:** One SQLAlchemy engine + sessionmaker per process.
**Implementation:** Module-level `_engine` / `_session` lazily built; `get_session()` is a `@contextmanager` with auto-rollback on exception and `close()` in `finally`.

### Encryption-at-rest with HMAC lookup keys
**Location:** `utils/crypto.py`, applied in models/repositories.
**Purpose:** Sensitive fields (username, category name/type, transaction date/description/value) are Fernet-encrypted strings. Because Fernet ciphertext is non-deterministic, equality lookups use a parallel deterministic `*_hash` column (HMAC-SHA256 keyed by `FERNET_KEY`).
**Implementation:** `encrypt()`/`decrypt()` for storage; `hash_for_lookup()` for indexed `username_hash`, `description_hash`. Models decrypt in `get_*()` / `to_json()`. `decrypt()` falls back to returning the raw token on failure (legacy plaintext tolerance).
**Example:** `users_repository.py:115` `login` filters by `username_hash`; `transactions_repository.py:160` `get_descriptions_with_counts` groups by `description_hash` to avoid decrypting every row.

### Dialog / session-state UI state machine
**Location:** `components/new_transaction.py`, `components/advance_installments.py`, dialogs inside pages.
**Purpose:** Modal flows in a stateless rerun model.
**Implementation:** `@st.dialog(...)` functions; ephemeral flags in `st.session_state` (e.g. `show_form`, `advance_step`, `cf_edit_month`) gate rendering. Pages call `clear_*_dialog_states()` at top to prevent reopen on rerun. Form fields are namespaced with a `reset_key`/`filter_v` counter to force widget re-init.

### Onboarding scheduler
**Location:** `components/styles.py:58` `init_onboarding`.
**Purpose:** Show a welcome dialog once when a section has no data.
**Implementation:** Sets `<key>_show_onboarding` once; pages `pop` it to render.

## Data Flow

### Authentication / session restore
1. `pages/login.py` → `utils.auth.login()` → `UsersRepository.login()` verifies bcrypt against the row found by `username_hash`.
2. On success: user dict cached in `st.session_state["current_user"]`, a JWT (HS256, 30-day exp, signed with `FERNET_KEY`) is written to the `finance_session` cookie via `CookieController`.
3. Every protected page calls `require_login()` first: if no in-memory user, it reads the cookie from `st.context.cookies`, decodes the JWT, and rehydrates the user via `UsersRepository.get_user_by_id`. A `_logged_out` flag prevents auto-restore right after logout.
4. Failed logins optionally append a line to a fail2ban log (`utils/auth.py:_log_failed_login`).

### Dashboard aggregation
`pages/dashboard.py` calls the single `TransactionsRepository.get_dashboard_data(user_id, year, month)` (`transactions_repository.py:627`), which fetches the year's transactions (1–2 DB round-trips) and computes summary KPIs, per-category income/expense, per-description breakdown vs. previous month, per-day expense matrix, and annual evolution — all in Python after decryption.

### Transaction creation with installments
`new_transaction_dialog` → `create_transaction` (`transactions_repository.py:18`): when `installments > 1`, generates N rows sharing an `installment_group` UUID, one per consecutive month via `relativedelta`, each with the rounded per-installment value.

### Cash-flow planning
Template (`CashFlowTemplate` + items) defines recurring entries. Creating a month (`CashFlowMonthRepository.create_month`) copies template items into `CashFlowEntry` rows (day clamped to 28). `pages/cash_flow.py` renders an annual grid; note cash-flow values are stored as plaintext `Numeric`, unlike transactions.

## Code Organization

**Approach:** Layer-based (models / repositories / components / pages / utils), with one file per DB table in both `models/` and `repositories/`.

**Module boundaries:**
- `app.py` is a 3-line entry point that `st.switch_page`s to `pages/dashboard.py`.
- Each page re-inserts the project root onto `sys.path` (`sys.path.insert(0, ...)`) so absolute imports resolve when Streamlit runs a page file directly.
- `models/__init__.py` and `repositories/__init__.py` re-export all classes for `from models import X` / `from repositories import Y`.
