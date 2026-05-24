# Code Conventions

## Naming Conventions

**Files:** snake_case, singular per table in `models/` (`transaction.py`, `cash_flow_entry.py`) and matching `*_repository.py` in `repositories/`. Pages are lowercase route names (`dashboard.py`, `cash_flow.py`).

**Classes:** PascalCase. Models = entity name (`Transaction`, `CashFlowMonth`). Repositories = `<Entity>Repository` (`TransactionsRepository`).

**Functions/Methods:** snake_case. Repository methods are verbs (`create_transaction`, `list_categories`, `get_dashboard_data`, `has_any_category`). Private helpers prefixed `_` (`_build_url`, `_log_failed_login`, `_render_step_1`, `_month_to_dict`).

**Variables:** snake_case. Streamlit `session_state` keys are snake_case string literals (`show_form`, `form_reset_counter`, `cf_edit_month`, `confirm_del_id`).

**Constants:** UPPER_SNAKE module-level (`COOKIE_NAME`, `TOKEN_EXPIRY_DAYS`, `MONTH_NAMES`, `GREEN_MAIN`, `EXPENSE_COLORS`).

## Domain Vocabulary

- Transaction/category **type** is a Portuguese string literal: `"entrada"` (income), `"saida"` (expense), `"ambos"` (both). Compared everywhere as `t["type"] in ("saida", "ambos")`. Stored encrypted for categories.
- UI text, dialog copy, and docstrings are in **Portuguese (pt-BR)**. Identifiers are a mix of English (functions, columns) and Portuguese (some local vars: `entradas`, `saidas`, `saldo`, `parcelas`).

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
