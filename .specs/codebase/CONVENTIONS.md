# Code Conventions

## Naming Conventions

**Files:** snake_case, singular per table in `models/` (`transaction.py`, `cash_flow_entry.py`) and matching `*_repository.py` in `repositories/`. Pages are lowercase route names (`dashboard.py`, `cash_flow.py`).

**Classes:** PascalCase. Models = entity name (`Transaction`, `CashFlowMonth`). Repositories = `<Entity>Repository` (`TransactionsRepository`).

**Functions/Methods:** snake_case. Repository methods are verbs (`create_transaction`, `list_categories`, `get_dashboard_data`, `has_any_category`). Private helpers prefixed `_` (`_build_url`, `_log_failed_login`, `_render_step_1`, `_month_to_dict`).

**Variables:** snake_case. Streamlit `session_state` keys are snake_case string literals (`show_form`, `form_reset_counter`, `cf_edit_month`, `confirm_del_id`).

**Constants:** UPPER_SNAKE module-level (`COOKIE_NAME`, `TOKEN_EXPIRY_DAYS`, `MONTH_NAMES`, `GREEN_MAIN`, `EXPENSE_COLORS`).

## Domain Vocabulary

- Transaction/category **type** is a Portuguese string literal: `"entrada"` (income), `"saida"` (expense), `"ambos"` (both), `"investimento"` (investment). Compared everywhere via `utils/category_types.py` helpers. Stored encrypted for categories. **These are persisted data values, not UI text** — never routed through i18n.
- Docstrings and code comments are in **Portuguese (pt-BR)**. Identifiers are a mix of English (functions, columns) and Portuguese (some local vars: `entradas`, `saidas`, `saldo`, `parcelas`).

## i18n / UI Text

- **All user-facing text lives in `utils/locales/pt_BR.json`**, read via `t("dotted.key", **kwargs)` from `utils/i18n.py`. No text literals in `pages/`, `components/`, `repositories/` or `utils/` (including `st.error`/`st.success` messages returned by repositories).
- Single locale (pt-BR); no language selector. Adding `en_US.json` later requires no changes to `pages/`/`components/`.
- `t()` interpolates with `str.format`; missing keys raise `KeyError` (no silent fallback). Dynamic keys are forbidden except `f"domain.category_type.{tipo}"`.
- **Not i18n'd (kept in code):** `page_icon` emojis, `<style>`/CSS blocks, Streamlit color markup (`:green[...]`), and the domain type values above.
- Enforced by `tests/unit/test_i18n_guard.py` (no literal UI text, every `t()` key exists, no orphan keys).

## Code Organization

**Import order:** stdlib → third-party → local, isort with `profile = "black"`. Local imports grouped `models` → `repositories` → `utils` → `components`. Pages insert the repo root on `sys.path` *before* local imports:
```python
import os, sys
import streamlit as st
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from components.styles import inject_global_css
```

**Page file structure (consistent across pages):**
1. `inject_global_css()`
2. `st.set_page_config(...)`
3. per-page `<style>` markdown / `inject_subpage_css()`
4. `require_login()` (+ `require_admin()` where needed)
5. read `current_user` / `user_id` from session
6. dialog defs (`@st.dialog`)
7. data load via repositories
8. render
9. trigger dialogs at the bottom from `session_state` flags

**Repository method structure:** `@staticmethod`, immediate `with get_session() as session:` (or `as s:`), build/commit, return a `dict`/`list[dict]`. Ownership is enforced inline (`if not row or row.user_id != user_id: return`).

## Type Safety / Documentation

- Type hints on public function signatures and return types (`-> list[dict]`, `-> tuple[bool, str]`, `dict | None`). Not enforced by a type checker.
- Every method/function has a one-line Portuguese docstring; longer ones use `Args:` / `Returns:` blocks (Google style). This is a hard project rule (see `CLAUDE.md`).
- Section banners inside long files use box-drawing comments: `# ── Sidebar ──────────`.

## Error Handling

- Defensive `try/except` around parsing/IO with silent fallbacks: `decrypt()` returns the raw token on failure; `format_date`/`parse_value_text` swallow `ValueError`; date-parse loops `continue` on bad rows.
- Operations return `tuple[bool, str]` (success, pt-BR user message) rather than raising — surfaced via `st.success`/`st.error` (e.g. `create_category`, `update_user_password`).
- `get_session()` rolls back on any exception then re-raises; callers generally do not catch.

## Comments / Documentation

Comments are sparse and explain **why**, in Portuguese — e.g. timing notes about CookieController reruns in `login.py`/`auth.py`, "Dado legado em texto plano" in `crypto.py`, "seguro para todos os meses" when clamping day to 28. WHAT is left to the (Portuguese) docstrings and self-describing names.
