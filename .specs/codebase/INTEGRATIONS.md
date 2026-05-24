# External Integrations

## Database

**Service:** PostgreSQL (image `postgres:16-alpine` in docker-compose; `psycopg2-binary` driver).
**Purpose:** Primary data store for all entities (users, categories, transactions, cash-flow).
**Implementation:** SQLAlchemy engine built in `repositories/base_repository.py` (`create_engine(_build_url(), pool_pre_ping=True)`); Alembic builds the same URL in `alembic/env.py`.
**Configuration:** Env vars `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (default 5432), `DB_NAME`. In docker-compose, `DB_HOST=db` is injected and the rest come from `.env`.
**Authentication:** Postgres username/password from env. `pool_pre_ping=True` guards against stale connections.

## Encryption / Key Management

**Service:** `cryptography` Fernet (symmetric AES) + Python `hmac`/`hashlib`.
**Purpose:** Encrypt sensitive columns at rest; deterministic HMAC hashes for indexed equality lookups.
**Implementation:** `utils/crypto.py` — `encrypt`/`decrypt`/`decrypt_float` and `hash_for_lookup`.
**Configuration:** Single env var `FERNET_KEY`. Loaded at import; `crypto.py` raises `RuntimeError` if missing. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
**Note:** `FERNET_KEY` is reused for three distinct purposes — Fernet encryption, HMAC-SHA256 lookup keys, and JWT (HS256) signing. See CONCERNS.md (key separation).

## Session Tokens (JWT)

**Service:** PyJWT (HS256).
**Purpose:** Persistent login across browser sessions via a cookie.
**Implementation:** `utils/session.py` (`create_session_token`/`decode_session_token`), wired in `utils/auth.py`.
**Configuration:** `COOKIE_NAME = "finance_session"`, `TOKEN_EXPIRY_DAYS = 30`. Secret = `FERNET_KEY` (fallback literal `"missing-secret"` if unset — see CONCERNS.md).
**Cookie transport:** `streamlit-cookies-controller` (`CookieController`) writes/removes the cookie; reads use `st.context.cookies` directly for synchronous access.

## Password Hashing

**Service:** bcrypt.
**Purpose:** Store user passwords.
**Implementation:** `utils/password_utils.py` (`hash_password`/`verify_password`), used by `UsersRepository`.
**Configuration:** Default bcrypt cost (`gensalt()`).

## fail2ban (optional, deploy-time)

**Service:** fail2ban reading an application-written auth log.
**Purpose:** Throttle/ban brute-force login attempts at the host level.
**Implementation:** `utils/auth.py:_log_failed_login` appends `... [FAILED_LOGIN] ip=<ip>` lines on auth failure. Client IP read from the `X-Real-IP` header (`_get_client_ip`).
**Configuration:** `ENABLE_FAIL2BAN_LOGGING` (default `false`) and `FAIL2BAN_LOG_PATH` (default `/var/log/my-finance/auth.log`). docker-compose mounts `/var/log/my-finance` into the container. App only writes the log; the fail2ban jail/filter itself lives outside this repo.

## Reverse Proxy (assumed, deploy-time)

**Service:** nginx (not in repo).
**Purpose:** TLS termination and real-client-IP forwarding.
**Implementation:** App trusts the `X-Real-IP` request header for IP logging. docker-compose binds the app to `127.0.0.1:8501` (loopback only), implying a fronting proxy in production.

## API Integrations

None. The app exposes no outbound HTTP API clients and no inbound REST/GraphQL endpoints (Streamlit-internal `/_stcore/health` is used only by the Docker `HEALTHCHECK`).

## Webhooks

None.

## Background Jobs

No queue/scheduler. The closest to "scheduled" behavior is user-triggered: installment rows are pre-generated for future months at creation time, and `advance_installments` moves future installments into the current month on demand.
