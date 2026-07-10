import os
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.charts import (
    annual_evolution_chart,
    bar_chart_expenses,
    donut_chart,
    expenses_by_day_chart,
)
from components.new_transaction import new_transaction_dialog
from components.styles import init_onboarding, inject_global_css
from repositories import (
    CategoriesRepository,
    TransactionsRepository,
)
from utils.auth import logout, require_login
from utils.category_types import is_investment
from utils.data_format_utils import MONTH_NAMES, format_currency
from utils.i18n import t

# Rótulo da barra que agrega todas as categorias de investimento do mês.
INVESTMENT_BAR_LABEL = t("pages.dashboard.investment_bar_label")

st.set_page_config(
    page_title=t("pages.dashboard.page_title"),
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()

current_user = st.session_state["current_user"]
user_id = current_user["id"]

inject_global_css()
st.markdown(
    """
<style>
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid rgba(76,175,80,0.4);
        transition: all 0.2s;
    }
    .stButton > button:hover { border-color: #4CAF50; color: #4CAF50; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(t("pages.dashboard.sidebar_title"))
    st.markdown(
        t("pages.dashboard.sidebar_user", username=current_user["username"])
    )
    st.divider()

    years = TransactionsRepository.get_available_years(user_id)
    current_year = datetime.now().year
    default_year_idx = (
        years.index(current_year) if current_year in years else len(years) - 1
    )
    selected_year = st.selectbox(
        t("pages.dashboard.year"), years, index=default_year_idx
    )

    selected_month_name = st.selectbox(
        t("pages.dashboard.month"), MONTH_NAMES, index=datetime.now().month - 1
    )
    selected_month = MONTH_NAMES.index(selected_month_name) + 1

    st.divider()

    if st.button(
        t("pages.dashboard.new_record"),
        type="primary",
        use_container_width=True,
    ):
        st.session_state["show_form"] = True
        st.session_state.setdefault("form_reset_counter", 0)

    if st.button(
        t("pages.dashboard.view_transactions"), use_container_width=True
    ):
        st.switch_page("pages/transactions.py")

    if st.button(t("pages.dashboard.cash_flow"), use_container_width=True):
        st.switch_page("pages/cash_flow.py")

    if st.button(t("pages.dashboard.categories"), use_container_width=True):
        st.switch_page("pages/categories.py")

    if st.button(t("pages.dashboard.profile"), use_container_width=True):
        st.switch_page("pages/profile.py")

    if current_user.get("is_admin"):
        if st.button(t("pages.dashboard.users"), use_container_width=True):
            st.switch_page("pages/admin.py")

    st.divider()
    if st.button(t("pages.dashboard.logout"), use_container_width=True):
        logout()
        # Sem st.switch_page() — o CookieController aciona o rerun naturalmente após
        # remover o cookie; require_login() redireciona para login nesse rerun.


# ── Onboarding ─────────────────────────────────────────────────────────────────
@st.dialog(t("pages.dashboard.onboarding_title"), width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com instruções para novos usuários do dashboard."""
    st.markdown(t("pages.dashboard.onboarding_body"))
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.dashboard.onboarding_create_categories"),
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("pages/categories.py")
    with c2:
        if st.button(
            t("pages.dashboard.onboarding_explore"),
            use_container_width=True,
        ):
            st.rerun()


init_onboarding(
    "dash",
    not CategoriesRepository.has_any_category(user_id)
    and not TransactionsRepository.has_any_transaction(user_id),
)


# ── New Transaction Modal ──────────────────────────────────────────────────────
if st.session_state.pop("dash_show_onboarding", False):
    onboarding_dialog()

if st.session_state.get("show_form"):
    new_transaction_dialog(user_id)


# ── Load Data ──────────────────────────────────────────────────────────────────
_dash = TransactionsRepository.get_dashboard_data(
    user_id, selected_year, selected_month
)
summary = _dash["summary"]
expenses_by_cat = _dash["expenses_by_cat"]
income_by_cat = _dash["income_by_cat"]
desc_by_cat = _dash["descriptions_by_cat"]
annual_data = _dash["annual"]
expenses_by_day_cat = _dash["expenses_by_day_cat"]

# ── Dashboard Header ───────────────────────────────────────────────────────────
st.markdown(
    t("pages.dashboard.header", month=selected_month_name, year=selected_year)
)
st.divider()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric(
        t("pages.dashboard.kpi_income"), format_currency(summary["entradas"])
    )
with col2:
    st.metric(
        t("pages.dashboard.kpi_expenses"), format_currency(summary["saidas"])
    )
with col3:
    st.metric(
        t("pages.dashboard.kpi_invested"),
        format_currency(summary["investimentos"]),
        help=t("pages.dashboard.kpi_invested_help"),
    )
with col4:
    saldo = summary["saldo"]
    st.metric(
        t("pages.dashboard.kpi_balance"),
        "",
        delta=format_currency(saldo),
        delta_color="normal" if saldo >= 0 else "inverse",
        help=t("pages.dashboard.kpi_balance_help"),
    )
with col5:
    sacc = summary["saldo_acumulado"]
    st.metric(
        t("pages.dashboard.kpi_cumulative_balance"),
        "",
        delta=format_currency(sacc),
        delta_color="normal" if sacc >= 0 else "inverse",
    )
with col6:
    pct_inst = summary["pct_installments"]
    st.metric(
        t("pages.dashboard.kpi_installments"),
        f"{pct_inst:.1f}%",
        help=t("pages.dashboard.kpi_installments_help"),
    )

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    labels_in = [r["category"] for r in income_by_cat]
    values_in = [r["total"] for r in income_by_cat]
    st.plotly_chart(
        donut_chart(
            labels_in, values_in, t("pages.dashboard.income_by_category")
        ),
        width="stretch",
        key="donut_inc",
    )

with col_right:
    cats = [r["category"] for r in expenses_by_cat]
    vals = [r["total"] for r in expenses_by_cat]
    # A barra agregada de investimento entra no mesmo gráfico para que o
    # denominador dos percentuais vire "despesas + investimentos".
    if summary["investimentos"] > 0:
        cats.append(INVESTMENT_BAR_LABEL)
        vals.append(summary["investimentos"])
    st.plotly_chart(
        bar_chart_expenses(cats, vals, t("pages.dashboard.expenses_breakdown")),
        width="stretch",
        key="bar_exp",
    )

# ── Evolução Anual ────────────────────────────────────────────────────────────
st.plotly_chart(
    annual_evolution_chart(
        annual_data, t("pages.dashboard.annual_evolution", year=selected_year)
    ),
    width="stretch",
    key="annual_evolution",
)

# ── Detalhamento por Categoria ─────────────────────────────────────────────────
st.divider()
st.markdown(t("pages.dashboard.breakdown_by_category"))

MAX_COLS = 4
cat_names = list(desc_by_cat.keys())
expense_cats = [
    c for c in cat_names if not is_investment(desc_by_cat[c]["type"])
]
investment_cats = [
    c for c in cat_names if is_investment(desc_by_cat[c]["type"])
]


def render_cat_donuts(names: list[str]) -> None:
    """Renderiza uma grade de donuts de descrições, um por categoria.

    Args:
        names: Nomes das categorias a exibir, na ordem desejada.
    """
    for row_start in range(0, len(names), MAX_COLS):
        row_cats = names[row_start : row_start + MAX_COLS]
        cols = st.columns(MAX_COLS)
        for col_idx in range(MAX_COLS):
            with cols[col_idx]:
                if col_idx >= len(row_cats):
                    st.empty()
                    continue

                cat_name = row_cats[col_idx]
                data = desc_by_cat[cat_name]
                total = data["total"]
                pct = data["pct_of_month"]
                prev = data["total_prev"]
                # Para investimento, crescer é bom: a leitura do delta inverte.
                investing = is_investment(data["type"])

                if prev > 0:
                    delta_pct = ((total - prev) / prev) * 100
                    delta_str = t(
                        "pages.dashboard.delta_vs_previous", pct=delta_pct
                    )
                    grew = delta_pct > 0
                    delta_color = "green" if grew == investing else "red"
                elif total > 0:
                    delta_str = t("pages.dashboard.delta_new_this_month")
                    delta_color = "green"
                else:
                    delta_str = (
                        t("pages.dashboard.delta_no_investments")
                        if investing
                        else t("pages.dashboard.delta_no_expenses")
                    )
                    delta_color = "gray"

                st.markdown(
                    t(
                        "pages.dashboard.card",
                        name=cat_name,
                        value=format_currency(total),
                        pct=pct,
                        color=delta_color,
                        delta=delta_str,
                    ),
                    unsafe_allow_html=True,
                )

                items = data["descriptions"]
                if not items:
                    fig = donut_chart([], [], "")
                else:
                    labels = [it["description"] for it in items]
                    values = [it["total"] for it in items]
                    fig = donut_chart(labels, values, "")
                st.plotly_chart(
                    fig, width="stretch", key=f"donut_cat_{cat_name}"
                )


if not cat_names:
    st.info(t("pages.dashboard.none_found"))
else:
    if expense_cats:
        st.markdown(t("pages.dashboard.section_expenses"))
        render_cat_donuts(expense_cats)
    if investment_cats:
        st.markdown(t("pages.dashboard.section_investments"))
        render_cat_donuts(investment_cats)

# ── Gastos por Categoria por Dia ───────────────────────────────────────────────
st.divider()
st.plotly_chart(
    expenses_by_day_chart(
        expenses_by_day_cat,
        t(
            "pages.dashboard.expenses_by_day",
            month=selected_month_name,
            year=selected_year,
        ),
        selected_year,
        selected_month,
    ),
    width="stretch",
    key="expenses_by_day",
)
