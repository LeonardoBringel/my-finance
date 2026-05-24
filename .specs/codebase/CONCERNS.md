# Concerns

**Analyzed:** 2026-05-23. Findings are evidence-backed (file:line). Ordered by risk/impact.

---

## Security & Privacy

### 1. Cash-flow data is stored in plaintext while transactions are encrypted
**Severity:** High (privacy inconsistency).
**Evidence:** `models/cash_flow_template_item.py:28-31` and `models/cash_flow_entry.py:26-29` store `name` (`Text`), `value` (`Numeric(12,2)`), `day`, `type` as **plaintext**. By contrast `models/transaction.py` encrypts `date`, `description`, `value` and `models/category.py` encrypts `name`/`type`. The stated project rule (`CLAUDE.md`) is that sensitive financial fields are Fernet-encrypted at rest.
**Impact:** A DB dump leaks every user's planned salary/rent/bills in clear text, defeating the encryption-at-rest model for a whole feature area.
**Fix approach:** Encrypt cash-flow `name`/`value` like transactions (store value as encrypted string, decrypt in repository serialization), or document an explicit decision that planned data is non-sensitive. If encrypting, add a migration to re-encrypt existing rows.

### 2. `FERNET_KEY` is reused for three cryptographic purposes
**Severity:** High.
**Evidence:** `utils/crypto.py:14` (Fernet encryption), `utils/crypto.py:51` (HMAC-SHA256 lookup secret), `utils/session.py:9` (`_SECRET = os.getenv("FERNET_KEY", ...)`, JWT HS256 signing).
**Impact:** Violates key separation. Rotating the encryption key invalidates every existing JWT and every `*_hash` lookup column simultaneously, and broadens blast radius if the key leaks. The HMAC and JWT secret should be independent of the data-encryption key.
**Fix approach:** Introduce separate env vars (`JWT_SECRET`, `HMAC_SECRET`) with their own rotation story; keep `FERNET_KEY` for encryption only.

### 3. JWT signing falls back to a hard-coded default secret
**Severity:** High (if `FERNET_KEY` ever unset for session module).
**Evidence:** `utils/session.py:9` `_SECRET = os.getenv("FERNET_KEY", "missing-secret")`.
**Impact:** If the env var is missing in the session module's context, JWTs are signed with a publicly-known string — anyone can forge a session token for any `user_id`. (`crypto.py` raises on missing key, which mitigates in practice, but the silent default is a latent footgun.)
**Fix approach:** Fail fast — raise if the signing secret is unset, mirroring `crypto.py`.

### 4. Sessions cannot be revoked; 30-day token lifetime
**Severity:** Medium.
**Evidence:** `utils/session.py:13` `TOKEN_EXPIRY_DAYS = 30`; `utils/auth.py:logout` only clears the cookie + a per-connection `_logged_out` flag.
**Impact:** A stolen/leaked token is valid for up to 30 days with no server-side invalidation (no jti/blocklist, no per-user token version). Logout on one device does not invalidate the token elsewhere. Password change does not rotate a signing version either.
**Fix approach:** Add a token version/`jti` claim checked against the DB, or shorten lifetime + refresh.

### 5. Weak / inconsistent password policy
**Severity:** Medium.
**Evidence:** Minimum length of **4** enforced only in `pages/profile.py:49`. User creation (`utils/auth.py:create_user` → `pages/admin.py`, and self-registration via `UsersRepository.create_user`) enforces **no** minimum at all (`pages/admin.py:41` only checks non-empty).
**Impact:** Trivially weak passwords accepted at account creation; bcrypt also silently truncates input beyond 72 bytes.
**Fix approach:** Centralize a password policy (length/complexity) in one validator used by all creation/change paths; pre-hash long inputs (e.g. SHA-256) before bcrypt if >72 bytes is expected.

---

## Performance & Scaling

### 6. `list_transactions` loads and decrypts ALL of a user's transactions, then filters in Python
**Severity:** High at scale.
**Evidence:** `repositories/transactions_repository.py:92-125` — the query is `filter(Transaction.user_id == user_id).all()` with no date/year predicate; year/month/day/range filtering happens in a Python loop after `to_json()` decrypts every row. The indexed `year` column (`models/transaction.py:23`, migration `0004`) is **not** used to push the filter into SQL.
**Impact:** Cost grows linearly with a user's lifetime transaction count for *every* dashboard render and *every* filtered list, plus full-table decryption each time. `get_dashboard_data` mitigates round-trips but still pulls the whole year (or whole prior year for January).
**Fix approach:** Push the `year` predicate into the SQL `filter` (it's already indexed). Date encryption blocks month/day SQL filtering — consider a plaintext `month`/`day` column (like `year`) or a date range encoded for indexing if finer SQL filtering is needed.

### 7. N+1 queries when rendering the cash-flow annual grid
**Severity:** Medium.
**Evidence:** `pages/cash_flow.py:451-456` calls `CashFlowMonthRepository.get_month_with_entries(...)` once per existing month inside a loop (after already calling `list_months`).
**Impact:** Up to 12 extra round-trips per page load for a fully-populated year.
**Fix approach:** Add a repository method that loads all months + entries for a (user, year) in one query (eager-load `entries`).

---

## Maintainability / Tech Debt

### 8. No automated tests
**Severity:** High (project-wide risk multiplier).
**Evidence:** No test framework in `pyproject.toml`; no `tests/` dir or `*test*` files (verified 2026-05-23). Pre-commit runs only black + isort.
**Impact:** Refactors and the crypto/installment/aggregation logic (the riskiest code) are unguarded. See TESTING.md for a suggested starting matrix.
**Fix approach:** Add `pytest`, start with pure-function unit tests in `utils/`, then repository integration tests against a throwaway Postgres.

### 9. Dead code
**Severity:** Low.
**Evidence:**
- `components/charts.py:267` `saldo_gauge` — defined, never imported/used anywhere.
- `repositories/transactions_repository.py` — `get_monthly_summary` (:296), `get_expenses_by_category` (:338), `get_income_by_category` (:352), `get_descriptions_by_category_for_dashboard` (:366), `get_annual_evolution` (:417) are all superseded by the consolidated `get_dashboard_data` (:627) and have no remaining callers.
**Impact:** ~250 lines of unused, duplicated aggregation logic that can drift from the live `get_dashboard_data` path and mislead maintainers.
**Fix approach:** Delete the five superseded methods and `saldo_gauge` (confirm no external callers first).

### 10. black configuration is under a typo'd table and is therefore ignored
**Severity:** Low.
**Evidence:** `pyproject.toml:28` `[tool.back]` (should be `[tool.black]`) with `line-length = 80`. The pre-commit black hook is also pinned to a stale `22.3.0` (`.pre-commit-config.yaml:3`) while isort is `6.0.1`.
**Impact:** black runs with its default line length (88), not the intended 80, so formatting silently diverges from the documented intent. No linter (flake8/ruff) or type-checker (mypy) in the gate despite type hints throughout.
**Fix approach:** Rename to `[tool.black]`, bump the black pin, and consider adding ruff + mypy to pre-commit.

### 11. `decrypt()` silently returns ciphertext on failure
**Severity:** Low–Medium.
**Evidence:** `utils/crypto.py:33-35` returns the raw token on any exception ("Dado legado em texto plano").
**Impact:** Intended for legacy plaintext tolerance, but it also masks key mismatches and data corruption — a wrong `FERNET_KEY` would surface as garbled-but-non-erroring values rather than a clear failure, and could display raw ciphertext to users.
**Fix approach:** Once legacy plaintext is known to be migrated, log the failure (without leaking data) or fail loudly; gate the fallback behind an explicit flag.

---

## Operational Notes (not bugs)

- `.version` is `v1.0.0` but the latest git tag is `v0.9.2`; the login page strips a `-suffix` from the version string. Confirm the release/tag process keeps these in sync (`Makefile` injects `git describe` as `APP_VERSION` at build).
- App binds to `127.0.0.1:8501` in docker-compose, implying a required external reverse proxy (nginx) for TLS and public exposure — not part of this repo.
